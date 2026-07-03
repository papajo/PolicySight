"""
Claims Advocate API Routes
Handles claim submission, sub-limit valuation, and structured intake.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.ai.client import LLMService, ClaimValuation
from src.config.settings import get_settings
from src.core.claims import get_intake_steps, submit_intake, get_intakes, ClaimIntake
from src.core.audit import log_action

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
    user_id: int,
    carrier_id: str,
    description: str,
    db: Session = Depends(get_db),
):
    """File a new claim record in the database."""
    from src.db.models import Claim

    claim = Claim(
        user_id=user_id,
        carrier_id=carrier_id,
        status="filed",
        description=description,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return {"id": claim.id, "status": claim.status, "filed_date": claim.filed_date}