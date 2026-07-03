"""
Temporal Coverage Timeline (REQ-004)
Computes coverage periods, detects gaps/lapses, and builds a timeline view.
"""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class PolicyPeriod(BaseModel):
    """A single policy coverage period."""
    policy_number: str
    carrier: str = "Unknown"
    effective_date: str
    expiration_date: Optional[str] = None
    coverage_types: list[str] = []
    status: str = "active"  # active, expired, lapsed


class CoverageEvent(BaseModel):
    """An event on the coverage timeline."""
    date: str
    event_type: str  # start, end, gap_start, gap_end
    label: str
    policy_number: Optional[str] = None


class TimelineResult(BaseModel):
    """Complete timeline analysis."""
    periods: list[PolicyPeriod]
    events: list[CoverageEvent]
    gaps: list[dict]
    has_active_coverage: bool
    days_until_lapse: Optional[int] = None


# Demo data — in production this comes from DB per user
DEMO_POLICIES = [
    PolicyPeriod(
        policy_number="POL-2024-001",
        carrier="StateFarm",
        effective_date="2024-01-15",
        expiration_date="2025-01-15",
        coverage_types=["liability", "collision", "comprehensive"],
        status="expired",
    ),
    PolicyPeriod(
        policy_number="POL-2025-001",
        carrier="Progressive",
        effective_date="2025-02-01",
        expiration_date="2026-02-01",
        coverage_types=["liability", "collision", "comprehensive", "rental"],
        status="expired",
    ),
    PolicyPeriod(
        policy_number="POL-2026-001",
        carrier="GEICO",
        effective_date="2026-01-01",
        expiration_date="2027-01-01",
        coverage_types=["liability", "collision", "comprehensive", "rental", "roadside"],
        status="active",
    ),
]


def _parse_date(s: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}")


def build_timeline(
    policies: Optional[list[PolicyPeriod]] = None,
    reference_date: Optional[str] = None,
) -> TimelineResult:
    """
    Build a timeline from a list of policy periods.
    Detects gaps, sorts chronologically, and computes lapse risk.
    """
    if policies is None:
        policies = DEMO_POLICIES

    if reference_date:
        ref = _parse_date(reference_date)
    else:
        ref = datetime.now()

    sorted_policies = sorted(policies, key=lambda p: _parse_date(p.effective_date))

    periods: list[PolicyPeriod] = []
    events: list[CoverageEvent] = []
    gaps: list[dict] = []

    prev_expiration: Optional[datetime] = None

    for i, policy in enumerate(sorted_policies):
        eff = _parse_date(policy.effective_date)
        exp = _parse_date(policy.expiration_date) if policy.expiration_date else eff + timedelta(days=365)

        # Mark status relative to reference date
        if eff <= ref <= exp:
            status = "active"
        elif exp < ref:
            status = "expired"
        else:
            status = "upcoming"

        period = policy.model_copy(update={"status": status})
        periods.append(period)

        events.append(CoverageEvent(
            date=policy.effective_date,
            event_type="start",
            label=f"{policy.carrier} #{policy.policy_number} starts",
            policy_number=policy.policy_number,
        ))

        events.append(CoverageEvent(
            date=policy.expiration_date or (eff + timedelta(days=365)).strftime("%Y-%m-%d"),
            event_type="end",
            label=f"{policy.carrier} #{policy.policy_number} ends",
            policy_number=policy.policy_number,
        ))

        # Detect gap between previous expiration and this effective date
        if prev_expiration is not None:
            gap_days = (eff - prev_expiration).days
            if gap_days > 1:
                gap_start = prev_expiration.strftime("%Y-%m-%d")
                gap_end = eff.strftime("%Y-%m-%d")
                gaps.append({
                    "from": gap_start,
                    "to": gap_end,
                    "days": gap_days,
                    "severity": "high" if gap_days > 30 else "medium" if gap_days > 7 else "low",
                })
                events.append(CoverageEvent(
                    date=gap_start,
                    event_type="gap_start",
                    label=f"Coverage gap begins ({gap_days} days)",
                ))
                events.append(CoverageEvent(
                    date=gap_end,
                    event_type="gap_end",
                    label="Coverage gap ends",
                ))

        prev_expiration = exp

    events.sort(key=lambda e: e.date)

    has_active = any(p.status == "active" for p in periods)
    days_until_lapse = None
    if has_active:
        # Find the earliest upcoming expiration
        for p in sorted(periods, key=lambda p: _parse_date(p.effective_date)):
            if p.status == "active" and p.expiration_date:
                exp = _parse_date(p.expiration_date)
                if exp > ref:
                    days_until_lapse = (exp - ref).days
                    break

    return TimelineResult(
        periods=periods,
        events=events,
        gaps=gaps,
        has_active_coverage=has_active,
        days_until_lapse=days_until_lapse,
    )


def add_policy_to_demo(policy: PolicyPeriod):
    """Add a new policy to the demo store."""
    DEMO_POLICIES.append(policy)
