"""
Endorsement Conflict Detector (FDE Test Case #7)
Detects when endorsements modify or override base policy coverage.
"""

import re
from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class EndorsementConflict(BaseModel):
    coverage_area: str
    endorsement_text: str
    base_policy_coverage: Optional[str] = None
    conflict_type: str  # "removed", "limited", "excluded", "modified"
    severity: str  # "high", "medium", "low"
    message: str


# Keywords that signal an endorsement removes/limits a coverage
REMOVAL_PATTERNS = [
    "no coverage", "does not apply", "not covered", "eliminat",
    "remove", "delete", "waive", "void", "cancel",
]

# Keywords that signal limitation
LIMITATION_PATTERNS = [
    "limit", "restrict", "reduce", "maximum", "not to exceed",
    "subje", "only when", "except",
]

COVERAGE_MAP = {
    "rental": ["rental", "transportation", "loaner", "car rental", "temporary transportation"],
    "glass": ["glass", "windshield", "windows"],
    "liability": ["liability", "bodily injury", "property damage"],
    "medical": ["medical", "pip", "personal injury protection"],
    "collision": ["collision"],
    "comprehensive": ["comprehensive"],
    "um_uim": ["uninsured", "underinsured", "um/uim"],
    "roadside": ["roadside", "towing", "emergency road"],
    "gap": ["gap", "loan/lease", "loan payoff"],
}


def analyze_endorsements(parsed: ParsedPolicy) -> list[EndorsementConflict]:
    """
    Analyze each endorsement for conflicts with the base policy coverages.
    Returns a list of identified conflicts.
    """
    conflicts: list[EndorsementConflict] = []

    if not parsed.endorsements:
        return conflicts

    # Build a map of coverage areas present in the base policy
    present_coverages: dict[str, Optional[str]] = {}
    if parsed.rental_reimbursement:
        present_coverages["rental"] = parsed.rental_reimbursement
    if parsed.roadside_assistance:
        present_coverages["roadside"] = parsed.roadside_assistance
    if parsed.loan_lease_payoff:
        present_coverages["gap"] = parsed.loan_lease_payoff
    if parsed.liability_limit:
        present_coverages["liability"] = parsed.liability_limit
    if parsed.medical_limit:
        present_coverages["medical"] = parsed.medical_limit
    if parsed.collision_deductible:
        present_coverages["collision"] = parsed.collision_deductible
    if parsed.comprehensive_deductible:
        present_coverages["comprehensive"] = parsed.comprehensive_deductible
    if parsed.uninsured_motorist_limit:
        present_coverages["um_uim"] = parsed.uninsured_motorist_limit

    for endorsement_text in parsed.endorsements:
        end_lower = endorsement_text.lower()

        for coverage_area, keywords in COVERAGE_MAP.items():
            # Check if this endorsement mentions this coverage area
            if not any(kw in end_lower for kw in keywords):
                continue

            if coverage_area not in present_coverages:
                continue

            conflict_type: str = "modified"
            severity: str = "medium"

            if any(pat in end_lower for pat in REMOVAL_PATTERNS):
                conflict_type = "removed"
                severity = "high"
            elif any(pat in end_lower for pat in LIMITATION_PATTERNS):
                conflict_type = "limited"
                severity = "high"

            message = (
                f"An endorsement mentions {coverage_area} coverage. The base policy shows "
                f"{present_coverages[coverage_area]} for this coverage, but the endorsement may "
            )
            if conflict_type == "removed":
                message += "remove or eliminate this coverage entirely."
            elif conflict_type == "limited":
                message += "impose additional limits or restrictions."
            else:
                message += "modify the terms of this coverage."

            conflicts.append(EndorsementConflict(
                coverage_area=coverage_area,
                endorsement_text=endorsement_text[:200],
                base_policy_coverage=present_coverages[coverage_area],
                conflict_type=conflict_type,
                severity=severity,
                message=message,
            ))

    return conflicts
