"""
Rate Trajectory API Routes
Handles premium forecasting and peer comparison.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.trajectory import RateTrajectory
from src.db.base import get_db

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
    from src.db.models import Claim, RateSnapshot

    if user_id <= 0:
        raise HTTPException(status_code=400, detail="A valid user_id is required.")
    if current_rate <= 0:
        raise HTTPException(status_code=400, detail="Current rate must be greater than zero.")
    if current_rate > 10000:
        raise HTTPException(status_code=400, detail="Current rate is outside the supported range.")

    try:
        rate_history = (
            db.query(RateSnapshot)
            .filter(RateSnapshot.user_id == user_id)
            .all()
        )
        claims_history = (
            db.query(Claim)
            .filter(Claim.user_id == user_id)
            .all()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Rate history is temporarily unavailable.") from exc

    claims_count = len(claims_history)
    peer_avg = 0.0
    if rate_history:
        peer_avg = sum(r.rate for r in rate_history) / len(rate_history)

    forecast = RateTrajectory.calculate_forecast(
        current_rate=current_rate,
        claims_count=claims_count,
        peer_avg_rate=peer_avg,
        years_with_carrier=max(len(rate_history), 1),
    )

    return forecast.model_dump()


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
