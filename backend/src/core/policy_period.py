"""
Policy Period Validation (FDE Test Case #11)
Checks whether an accident date falls within the policy's effective period.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class PeriodValidation(BaseModel):
    status: str  # "within_period", "before_period", "after_period", "no_dates"
    accident_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    message: str


def _parse_date(date_str: str) -> Optional[date]:
    formats = ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def validate_policy_period(
    effective_date_str: Optional[str],
    expiration_date_str: Optional[str],
    accident_date_str: Optional[str],
) -> PeriodValidation:
    """
    Determine whether the accident date falls within the policy period.
    Returns a PeriodValidation with status and a plain-English message.
    """
    if not accident_date_str:
        return PeriodValidation(
            status="no_dates",
            message="No accident date provided. Provide an accident date to check if the policy was active.",
        )

    accident = _parse_date(accident_date_str)
    if not accident:
        return PeriodValidation(
            status="no_dates",
            accident_date=accident_date_str,
            message=f"Could not parse accident date '{accident_date_str}'. Expected format: MM/DD/YYYY.",
        )

    if not effective_date_str or not expiration_date_str:
        return PeriodValidation(
            status="no_dates",
            accident_date=accident_date_str,
            message="Policy effective and expiration dates are not available. Cannot determine if the policy was active on the accident date.",
        )

    effective = _parse_date(effective_date_str)
    expiration = _parse_date(expiration_date_str)

    if not effective or not expiration:
        return PeriodValidation(
            status="no_dates",
            accident_date=accident_date_str,
            effective_date=effective_date_str,
            expiration_date=expiration_date_str,
            message="Could not parse policy dates. Expected format: MM/DD/YYYY.",
        )

    if accident < effective:
        return PeriodValidation(
            status="before_period",
            accident_date=accident_date_str,
            effective_date=effective_date_str,
            expiration_date=expiration_date_str,
            message=f"The accident date ({accident_date_str}) is before the policy effective date ({effective_date_str}). This policy likely does not cover that accident.",
        )

    if accident > expiration:
        return PeriodValidation(
            status="after_period",
            accident_date=accident_date_str,
            effective_date=effective_date_str,
            expiration_date=expiration_date_str,
            message=f"The accident date ({accident_date_str}) is after the policy expiration date ({expiration_date_str}). This policy likely does not cover that accident.",
        )

    return PeriodValidation(
        status="within_period",
        accident_date=accident_date_str,
        effective_date=effective_date_str,
        expiration_date=expiration_date_str,
        message=f"The accident date ({accident_date_str}) falls within the policy period ({effective_date_str} – {expiration_date_str}).",
    )
