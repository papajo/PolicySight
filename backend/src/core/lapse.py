"""
Lapse Bridge Service
Handles coverage gap detection, product selection, and automated bridge policy logic.
"""

from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class BridgeProductType(str, Enum):
    BINDER = "binder"
    SHORT_RATE = "short_rate"
    NON_OWNER = "non_owner"
    NAMED_OPERATOR = "named_operator"


BRIDGE_PRODUCTS = {
    BridgeProductType.BINDER: {
        "name": "Temporary Binder",
        "description": "Short-term coverage bridging your renewal gap while your new policy is being underwritten.",
        "daily_rate": 6.50,
        "default_days": 30,
        "max_days": 60,
        "eligibility": "Active carrier with upcoming renewal",
    },
    BridgeProductType.SHORT_RATE: {
        "name": "Short-Rate Policy",
        "description": "Mid-term cancellation coverage. Covers the penalty gap when switching carriers before your term ends.",
        "daily_rate": 9.00,
        "default_days": 45,
        "max_days": 90,
        "eligibility": "Switching carriers mid-term",
    },
    BridgeProductType.NON_OWNER: {
        "name": "Non-Owner Policy",
        "description": "Liability-only coverage for drivers who don't own a vehicle but need to maintain continuous insurance.",
        "daily_rate": 1.75,
        "default_days": 30,
        "max_days": 180,
        "eligibility": "No vehicle ownership, liability gap only",
    },
    BridgeProductType.NAMED_OPERATOR: {
        "name": "Named Operator Policy",
        "description": "Coverage tied to a specific driver rather than a vehicle. Ideal for non-standard risk profiles.",
        "daily_rate": 3.50,
        "default_days": 30,
        "max_days": 90,
        "eligibility": "Driver-specific coverage needed",
    },
}


class CoverageStatus(BaseModel):
    """Structured representation of a user's coverage status."""
    user_id: int
    is_covered: bool
    current_carrier: Optional[str] = None
    renewal_date: Optional[datetime] = None
    days_until_lapse: int = 0
    bridge_active: bool = False
    bridge_carrier: Optional[str] = None


class BridgeProduct(BaseModel):
    """Selected bridge product with pricing and rationale."""
    product_type: BridgeProductType
    name: str
    description: str
    daily_rate: float
    term_days: int
    total_cost: float
    selection_rationale: str


class CoverageGapBridge:
    """
    Core service for monitoring and preventing coverage lapses.
    Selects the appropriate bridge product based on the user's situation.
    """

    @staticmethod
    def select_product(
        has_active_policy: bool,
        carrier: Optional[str] = None,
        renewal_date: Optional[datetime] = None,
    ) -> BridgeProduct:
        """
        Select the appropriate bridge product type based on user context.
        Uses real insurance logic to match the right product.
        """
        now = datetime.utcnow()

        if has_active_policy and renewal_date:
            days_until = (renewal_date - now).days
            if days_until <= 60:
                term = min(max(days_until + 14, 14), 60)
                product = BridgeProductType.BINDER
                rationale = (
                    f"Your {carrier or 'current'} policy renews in {max(0, days_until)} day(s). "
                    "A Temporary Binder bridges the underwriting gap until your new policy takes effect."
                )
            else:
                term = 45
                product = BridgeProductType.SHORT_RATE
                rationale = (
                    f"Your renewal is {days_until} days away. A Short-Rate policy covers the "
                    "cancellation penalty window if you switch carriers mid-term."
                )

        elif has_active_policy:
            term = 45
            product = BridgeProductType.SHORT_RATE
            rationale = (
                f"No renewal date provided. A Short-Rate policy protects you when switching "
                "carriers mid-term, covering the unearned premium penalty."
            )

        elif not carrier and not renewal_date:
            term = 30
            product = BridgeProductType.NON_OWNER
            rationale = (
                "No current carrier or vehicle on record. A Non-Owner policy provides "
                "liability-only coverage to maintain continuous insurance history."
            )

        else:
            term = 30
            product = BridgeProductType.NAMED_OPERATOR
            rationale = (
                "Driver-specific coverage selected. A Named Operator policy keeps you "
                "covered regardless of which vehicle you drive."
            )

        info = BRIDGE_PRODUCTS[product]
        total = round(term * info["daily_rate"], 2)

        return BridgeProduct(
            product_type=product,
            name=info["name"],
            description=info["description"],
            daily_rate=info["daily_rate"],
            term_days=term,
            total_cost=total,
            selection_rationale=rationale,
        )

    @staticmethod
    def check_coverage_status(
        renewal_date: Optional[datetime],
        has_active_policy: bool,
        carrier: Optional[str] = None,
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
                current_carrier=carrier,
            )
        elif has_active_policy:
            return CoverageStatus(
                user_id=0,
                is_covered=True,
                days_until_lapse=30,
                current_carrier=carrier,
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
        """
        if not status.is_covered:
            return True

        if status.days_until_lapse <= 7 and not status.bridge_active:
            return True

        return False

    @staticmethod
    def calculate_bridge_cost(days: int = 30) -> dict:
        """Legacy — use select_product instead."""
        return {
            "days": days,
            "daily_rate": 5.0,
            "total_cost": days * 5.0,
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
