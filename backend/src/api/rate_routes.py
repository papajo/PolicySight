"""
Rate Trajectory API Routes
Handles premium forecasting and peer comparison.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.ai.client import LLMService
from src.config.settings import get_settings

router = APIRouter()


@router.get("/forecast")
async def forecast_rate(
    user_id: int,
    current_rate: float,
    db: Session = Depends(get_db),
):
    """
    Predict what your insurance premium will be next year.
    Compares your driving profile against anonymized peer market data
    and returns a "Stay" or "Switch" recommendation.
    """
    from src.db.models import RateSnapshot, Claim

    # Fetch user's rate history
    rate_history = (
        db.query(RateSnapshot)
        .filter(RateSnapshot.user_id == user_id)
        .all()
    )

    # Fetch user's claims history
    claims_history = (
        db.query(Claim)
        .filter(Claim.user_id == user_id)
        .all()
    )

    claims_data = [
        {"id": c.id, "status": c.status, "filed_date": str(c.filed_date)}
        for c in claims_history
    ]

    settings = get_settings()
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)

    # Calculate peer average from rate history
    peer_avg = 0.0
    if rate_history:
        peer_avg = sum(r.rate for r in rate_history) / len(rate_history)

    forecast = await llm.forecast_rate(
        current_rate=current_rate,
        claims_history=claims_data,
        peer_avg_rate=peer_avg,
    )

    return forecast


@router.post("/snapshot")
async def record_rate_snapshot(
    user_id: int,
    carrier_id: str,
    rate: float,
    db: Session = Depends(get_db),
):
    """Record a rate snapshot for trajectory tracking."""
    from src.db.models import RateSnapshot

    snapshot = RateSnapshot(
        user_id=user_id,
        carrier_id=carrier_id,
        rate=rate,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return {"id": snapshot.id, "status": "recorded", "rate": rate}