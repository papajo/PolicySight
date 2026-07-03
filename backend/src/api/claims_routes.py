"""
Claims Advocate API Routes
Handles claim submission and sub-limit valuation.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.ai.client import LLMService, ClaimValuation
from src.config.settings import get_settings

router = APIRouter()


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