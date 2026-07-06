"""
Rate Trajectory API Routes
Handles premium forecasting, peer comparison, and time-series analytics
via TimescaleDB continuous aggregates.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional

from src.core.trajectory import RateTrajectory
from src.core.auth import get_current_user
from src.db.base import get_db
from src.db.models import User

router = APIRouter()


@router.get("/forecast")
async def forecast_rate(
    user_id: int,
    current_rate: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Predict what your insurance premium will be next year.
    Uses TimescaleDB continuous aggregate for fast peer comparison.
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

        # Use continuous aggregate for faster claim count lookup
        claim_count_query = text("""
            SELECT COALESCE(SUM(total_claims), 0)
            FROM claims_daily_summary
            WHERE day > NOW() - INTERVAL '2 years'
        """)

        # Fallback to raw table if aggregate is empty
        result = db.execute(claim_count_query).scalar()
        if result == 0:
            claims_history = (
                db.query(Claim)
                .filter(Claim.user_id == user_id)
                .all()
            )
            claims_count = len(claims_history)
        else:
            claims_count = int(result)

    except Exception as exc:
        raise HTTPException(status_code=503, detail="Rate history is temporarily unavailable.") from exc

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
    carrier_id: str,
    rate: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a rate snapshot for trajectory tracking. Requires authentication."""
    from src.db.models import RateSnapshot

    snapshot = RateSnapshot(
        user_id=current_user.id,
        carrier_id=carrier_id,
        rate=rate,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return {"id": snapshot.id, "status": "recorded", "rate": rate}


# ── TimescaleDB Continuous Aggregate Endpoints ──────────────────────────────


class RateSummary(BaseModel):
    day: str
    carrier_id: str
    avg_rate: float
    min_rate: float
    max_rate: float
    snapshot_count: int


class RatesSummaryResponse(BaseModel):
    days: int
    data: list[RateSummary]


@router.get("/summary", response_model=RatesSummaryResponse)
async def rates_summary(
    carrier_id: Optional[str] = Query(None, description="Filter by carrier"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Daily rate trajectory powered by TimescaleDB continuous aggregate.
    Returns pre-computed daily avg/min/max rates per carrier.
    This query runs in milliseconds even on millions of snapshots.
    """
    base_query = """
        SELECT
            day::text,
            carrier_id,
            ROUND(avg_rate::numeric, 2) as avg_rate,
            ROUND(min_rate::numeric, 2) as min_rate,
            ROUND(max_rate::numeric, 2) as max_rate,
            snapshot_count
        FROM rate_daily_summary
        WHERE day > NOW() - (:days || ' days')::INTERVAL
    """

    params = {"days": days}

    if carrier_id:
        base_query += " AND carrier_id = :carrier_id"
        params["carrier_id"] = carrier_id

    base_query += " ORDER BY day DESC, carrier_id"

    result = db.execute(text(base_query), params)
    rows = result.fetchall()

    return RatesSummaryResponse(
        days=days,
        data=[
            RateSummary(
                day=row[0],
                carrier_id=row[1],
                avg_rate=float(row[2]),
                min_rate=float(row[3]),
                max_rate=float(row[4]),
                snapshot_count=row[5],
            )
            for row in rows
        ],
    )


@router.get("/trajectory")
async def rate_trajectory(
    carrier_id: Optional[str] = Query(None, description="Filter by carrier"),
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Rate trajectory with trend analysis from the continuous aggregate.
    Shows direction and volatility for management dashboards.
    """
    query = text("""
        SELECT
            carrier_id,
            ROUND(AVG(avg_rate)::numeric, 2) as avg_rate,
            ROUND(MIN(min_rate)::numeric, 2) as period_low,
            ROUND(MAX(max_rate)::numeric, 2) as period_high,
            SUM(snapshot_count) as total_snapshots,
            ROUND(
                CASE WHEN AVG(avg_rate) > 0
                    THEN (MAX(avg_rate) - MIN(avg_rate)) / AVG(avg_rate) * 100
                    ELSE 0
                END, 1
            ) as volatility_pct
        FROM rate_daily_summary
        WHERE day > NOW() - (:days || ' days')::INTERVAL
    """)

    params = {"days": days}
    if carrier_id:
        query = text(str(query) + " AND carrier_id = :carrier_id")
        params["carrier_id"] = carrier_id

    query = text(str(query) + " GROUP BY carrier_id ORDER BY total_snapshots DESC")

    result = db.execute(query, params)
    rows = result.fetchall()

    return {
        "days": days,
        "carriers": [
            {
                "carrier_id": row[0],
                "avg_rate": float(row[1]),
                "period_low": float(row[2]),
                "period_high": float(row[3]),
                "total_snapshots": row[4],
                "volatility_pct": float(row[5]),
            }
            for row in rows
        ],
    }
