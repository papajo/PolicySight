"""
Claims Advocate API Routes
Handles claim submission, sub-limit valuation, structured intake,
and time-series analytics via TimescaleDB continuous aggregates.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from src.db.base import get_db
from src.ai.client import LLMService, ClaimValuation
from src.config.settings import get_settings
from src.core.claims import get_intake_steps, submit_intake, get_intakes, ClaimIntake
from src.core.audit import log_action
from src.core.auth import get_current_user, get_current_user_optional
from src.db.models import User

router = APIRouter()


@router.get("/intake/steps")
async def list_intake_steps():
    """Get the guided claim intake steps. (REQ-007)"""
    return get_intake_steps()


class IntakeSubmitRequest(BaseModel):
    responses: dict[str, str]


@router.post("/intake/submit", response_model=ClaimIntake)
async def submit_claim_intake(input_data: IntakeSubmitRequest):
    """Submit a completed claim intake form. (REQ-007)"""
    result = submit_intake(input_data.responses)
    log_action("claim_intake", "claims", f"Claim filed: {result.date_of_loss} at {result.location}")
    return result


@router.get("/intake/list")
async def list_intakes():
    """List submitted claim intakes."""
    return get_intakes()


@router.post("/advocate", response_model=ClaimValuation)
async def advocate_claim(
    file: UploadFile = File(...),
    description: str = Form(...),
    carrier_offer: float = Form(0.0),
    current_user: User = Depends(get_current_user),
):
    """
    Upload accident photos and a description of the claim.
    Returns a sub-limit breakdown comparing what your policy covers
    vs. what the carrier is offering.
    """
    if not file.filename or not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a photo or PDF of the accident.",
        )

    content = await file.read()
    raw_text = content.decode("utf-8", errors="ignore")

    settings = get_settings()
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)

    # Get parsed policy (in production, fetch from DB for the user)
    policy = await llm.parse_slip("")

    # Valuate the claim
    valuation = await llm.valuate_claim(
        policy=policy,
        claim_description=description,
        carrier_offer=carrier_offer,
    )

    return valuation


@router.post("/file")
async def file_claim(
    carrier_id: str,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """File a new claim record in the database. Requires authentication."""
    from src.db.models import Claim

    claim = Claim(
        user_id=current_user.id,
        carrier_id=carrier_id,
        status="filed",
        description=description,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return {"id": claim.id, "status": claim.status, "filed_date": claim.filed_date}


# ── TimescaleDB Continuous Aggregate Endpoints ──────────────────────────────


class ClaimSummary(BaseModel):
    day: str
    carrier_id: str
    total_claims: int
    approved: int
    denied: int
    pending: int


class ClaimsSummaryResponse(BaseModel):
    user_id: Optional[int] = None
    days: int
    data: list[ClaimSummary]


@router.get("/summary", response_model=ClaimsSummaryResponse)
async def claims_summary(
    user_id: Optional[int] = Query(None, description="Filter by user (optional)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Daily claims summary powered by TimescaleDB continuous aggregate.
    Returns pre-computed daily rollups of claims by carrier and status.
    This query runs in milliseconds even on millions of rows.
    """
    query = text("""
        SELECT
            day::text,
            carrier_id,
            total_claims,
            approved,
            denied,
            pending
        FROM claims_daily_summary
        WHERE day > NOW() - (:days || ' days')::INTERVAL
        ORDER BY day DESC, carrier_id
    """)

    result = db.execute(query, {"days": days})
    rows = result.fetchall()

    return ClaimsSummaryResponse(
        user_id=user_id,
        days=days,
        data=[
            ClaimSummary(
                day=row[0],
                carrier_id=row[1] or "unknown",
                total_claims=row[2],
                approved=row[3],
                denied=row[4],
                pending=row[5],
            )
            for row in rows
        ],
    )


@router.get("/carrier-summary")
async def claims_by_carrier(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Aggregated claim stats per carrier from the continuous aggregate.
    Useful for Claims Advocate to compare carrier behavior.
    """
    query = text("""
        SELECT
            carrier_id,
            SUM(total_claims) as total_claims,
            SUM(approved) as total_approved,
            SUM(denied) as total_denied,
            SUM(pending) as total_pending,
            ROUND(
                CASE WHEN SUM(total_claims) > 0
                    THEN SUM(approved)::numeric / SUM(total_claims) * 100
                    ELSE 0
                END, 1
            ) as approval_rate_pct
        FROM claims_daily_summary
        WHERE day > NOW() - (:days || ' days')::INTERVAL
        GROUP BY carrier_id
        ORDER BY total_claims DESC
    """)

    result = db.execute(query, {"days": days})
    rows = result.fetchall()

    return {
        "days": days,
        "carriers": [
            {
                "carrier_id": row[0] or "unknown",
                "total_claims": row[1],
                "approved": row[2],
                "denied": row[3],
                "pending": row[4],
                "approval_rate_pct": float(row[5]),
            }
            for row in rows
        ],
    }