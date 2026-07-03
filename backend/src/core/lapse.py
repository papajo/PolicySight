"""
Lapse Bridge Service
Handles coverage gap detection and automated bridge policy logic.
"""

from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional


class CoverageStatus(BaseModel):
    """Structured representation of a user's coverage status."""
    user_id: int
    is_covered: bool
    current_carrier: Optional[str] = None
    renewal_date: Optional[datetime] = None
    days_until_lapse: int = 0
    bridge_active: bool = False
    bridge_carrier: Optional[str] = None


class CoverageGapBridge:
    """
    Core service for monitoring and preventing coverage lapses.
    Acts as an automated fail-safe during carrier switches.
    """

    # Default bridge policy parameters
    BRIDGE_POLICY_DURATION_DAYS = 30
    BRIDGE_POLICY_COST_PER_DAY = 5.0  # $5/day placeholder rate

    @staticmethod
    def check_coverage_status(
        renewal_date: Optional[datetime],
        has_active_policy: bool,
    ) -> CoverageStatus:
        """
        Check if a user's coverage is at risk of lapsing.
        Returns the current status and days until potential lapse.
        """
        now = datetime.utcnow()

        if has_active_policy and renewal_date:
            days_until = (renewal_date - now).days
            return CoverageStatus(
                user_id=0,
                is_covered=True,
                days_until_lapse=max(0, days_until),
                renewal_date=renewal_date,
            )
        elif has_active_policy:
            return CoverageStatus(
                user_id=0,
                is_covered=True,
                days_until_lapse=30,  # Default check window
            )
        else:
            return CoverageStatus(
                user_id=0,
                is_covered=False,
                days_until_lapse=0,
            )

    @staticmethod
    def should_trigger_bridge(status: CoverageStatus) -> bool:
        """
        Determine if the bridge policy should be triggered.
        Triggers when:
        - User is not covered
        - Renewal date has passed without a new policy
        - Less than 7 days until lapse and no new carrier confirmed
        """
        if not status.is_covered:
            return True

        if status.days_until_lapse <= 7 and not status.bridge_active:
            return True

        return False

    @staticmethod
    def calculate_bridge_cost(days: int = BRIDGE_POLICY_DURATION_DAYS) -> dict:
        """Calculate the cost of a bridge policy."""
        total_cost = days * CoverageGapBridge.BRIDGE_POLICY_COST_PER_DAY
        return {
            "days": days,
            "daily_rate": CoverageGapBridge.BRIDGE_POLICY_COST_PER_DAY,
            "total_cost": total_cost,
            "currency": "USD",
        }

    @staticmethod
    def generate_lapse_alert(status: CoverageStatus) -> str:
        """Generate a human-readable alert about coverage status."""
        if not status.is_covered:
            return (
                "⚠️ **Coverage Lapse Detected!** "
                "You are currently not covered by any auto insurance policy. "
                "This can result in higher premiums for years. "
                "Activate our bridge policy immediately to protect your record."
            )

        if status.days_until_lapse <= 7:
            return (
                f"⚠️ **Coverage at Risk!** "
                f"Your policy renews in {status.days_until_lapse} day(s). "
                "If you haven't confirmed a new carrier, your coverage will lapse. "
                "We can bridge the gap automatically."
            )

        if status.days_until_lapse <= 30:
            return (
                f"📅 **Renewal Reminder.** "
                f"Your policy renews in {status.days_until_lapse} day(s). "
                "Use the Rate Trajectory tool to see if you should switch carriers."
            )

        return (
            f"✅ **Coverage is active.** "
            f"Your next renewal is in {status.days_until_lapse} day(s)."
        )