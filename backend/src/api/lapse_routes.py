"""
Lapse Bridge API Routes
Handles coverage gap monitoring and bridge policy activation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.base import get_db
from src.core.lapse import CoverageGapBridge, CoverageStatus

router = APIRouter()


@router.post("/register")
async def register_bridge(
    user_id: int,
    current_carrier: str,
    renewal_date: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Register for the Lapse Bridge service.
    Monitors your coverage window and automatically activates
    a bridge policy if a gap is detected.
    """
    from src.db.models import Policy

    # Check if user has an active policy in the DB
    active_policy = (
        db.query(Policy)
        .filter(Policy.user_id == user_id, Policy.status == "active")
        .first()
    )

    renewal_dt = None
    if renewal_date:
        try:
            renewal_dt = datetime.fromisoformat(renewal_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO format (e.g., 2024-12-31).",
            )

    bridge = CoverageGapBridge()
    has_coverage = bool(active_policy) or bool(current_carrier)
    status = bridge.check_coverage_status(
        renewal_date=renewal_dt,
        has_active_policy=has_coverage,
        carrier=current_carrier if not active_policy else None,
    )

    should_trigger = bridge.should_trigger_bridge(status)
    product = bridge.select_product(
        has_active_policy=has_coverage,
        carrier=current_carrier or (active_policy.carrier_id if active_policy else None),
        renewal_date=renewal_dt,
    )
    alert = bridge.generate_lapse_alert(status)

    return {
        "registered": True,
        "coverage_status": status.model_dump(),
        "bridge_triggered": should_trigger,
        "bridge_product": product.model_dump(),
        "alert": alert,
        "message": "You are now protected by the Lapse Bridge. We'll monitor your renewal window.",
    }


@router.get("/status/{user_id}")
async def get_bridge_status(
    user_id: int,
    current_carrier: str | None = None,
    renewal_date: str | None = None,
    db: Session = Depends(get_db),
):
    """Check your current bridge protection status."""
    from src.db.models import Policy

    active_policy = (
        db.query(Policy)
        .filter(Policy.user_id == user_id, Policy.status == "active")
        .first()
    )

    renewal_dt = None
    if renewal_date:
        try:
            renewal_dt = datetime.fromisoformat(renewal_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO format (e.g., 2024-12-31).",
            )

    has_coverage = bool(active_policy) or bool(current_carrier)
    bridge = CoverageGapBridge()
    status = bridge.check_coverage_status(
        renewal_date=renewal_dt,
        has_active_policy=has_coverage,
        carrier=current_carrier if not active_policy else None,
    )

    should_trigger = bridge.should_trigger_bridge(status)
    product = bridge.select_product(
        has_active_policy=has_coverage,
        carrier=current_carrier or (active_policy.carrier_id if active_policy else None),
        renewal_date=renewal_dt,
    )
    alert = bridge.generate_lapse_alert(status)

    return {
        "user_id": user_id,
        "coverage_status": status.model_dump(),
        "bridge_needed": should_trigger,
        "bridge_product": product.model_dump(),
        "alert": alert,
    }