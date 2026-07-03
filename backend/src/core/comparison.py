"""
Policy Comparison Tool (PDF REQ-018)
Side-by-side comparison of limits, deductibles, exclusions, endorsements.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class FieldDiff(BaseModel):
    field: str
    label: str
    policy_a_value: Optional[str] = None
    policy_b_value: Optional[str] = None
    change_type: str  # improved, reduced, unchanged, added, removed, different
    confidence_a: str = "high"
    confidence_b: str = "high"


class ComparisonResult(BaseModel):
    policy_a_label: str
    policy_b_label: str
    diffs: list[FieldDiff]
    improvements: list[str]
    reductions: list[str]
    gaps_bridged: list[str] = []
    overall_assessment: str


COVERAGE_FIELDS = [
    ("liability_limit", "Liability Limit"),
    ("medical_limit", "Medical Payments"),
    ("property_limit", "Property Damage"),
    ("uninsured_motorist_limit", "UM/UIM"),
    ("collision_deductible", "Collision Deductible"),
    ("comprehensive_deductible", "Comprehensive Deductible"),
    ("rental_reimbursement", "Rental Reimbursement"),
    ("roadside_assistance", "Roadside Assistance"),
    ("loan_lease_payoff", "Loan/Lease Payoff"),
]


def _parse_numeric(val: Optional[str]) -> Optional[float]:
    if not val:
        return None
    import re
    nums = re.findall(r'[\d,]+', val.replace(",", ""))
    if nums:
        return float(nums[0])
    return None


def compare_policies(policy_a: ParsedPolicy, policy_b: ParsedPolicy) -> ComparisonResult:
    diffs: list[FieldDiff] = []
    improvements: list[str] = []
    reductions: list[str] = []
    gaps_bridged: list[str] = []

    for field, label in COVERAGE_FIELDS:
        val_a = getattr(policy_a, field, None)
        val_b = getattr(policy_b, field, None)
        conf_a = getattr(policy_a, f"{field.replace('limit', 'confidence').replace('deductible', 'confidence')}", "high") if hasattr(policy_a, f"{field.replace('limit', 'confidence').replace('deductible', 'confidence')}") else "high"
        conf_b = getattr(policy_b, f"{field.replace('limit', 'confidence').replace('deductible', 'confidence')}", "high") if hasattr(policy_b, f"{field.replace('limit', 'confidence').replace('deductible', 'confidence')}") else "high"

        num_a = _parse_numeric(val_a)
        num_b = _parse_numeric(val_b)

        change = "different"
        if val_a == val_b:
            change = "unchanged"
        elif val_a is None and val_b is not None:
            change = "added"
            gaps_bridged.append(f"{label} was missing in prior policy, now present ({val_b})")
            improvements.append(f"{label} — added ({val_b})")
        elif val_a is not None and val_b is None:
            change = "removed"
            reductions.append(f"{label} — removed (was {val_a})")
        elif num_a is not None and num_b is not None:
            if "deductible" in field:
                if num_b < num_a:
                    change = "improved"
                    improvements.append(f"{label}: ${num_a:,.0f} → ${num_b:,.0f} (lower deductible)")
                elif num_b > num_a:
                    change = "reduced"
                    reductions.append(f"{label}: ${num_a:,.0f} → ${num_b:,.0f} (higher deductible)")
            else:  # limits — higher is better
                if num_b > num_a:
                    change = "improved"
                    improvements.append(f"{label}: ${num_a:,.0f} → ${num_b:,.0f}")
                elif num_b < num_a:
                    change = "reduced"
                    reductions.append(f"{label}: ${num_a:,.0f} → ${num_b:,.0f}")

        diffs.append(FieldDiff(
            field=field,
            label=label,
            policy_a_value=val_a,
            policy_b_value=val_b,
            change_type=change,
        ))

    # Exclusions comparison
    excl_a = set(e.lower().strip() for e in policy_a.exclusions)
    excl_b = set(e.lower().strip() for e in policy_b.exclusions)
    added_excl = excl_b - excl_a
    removed_excl = excl_a - excl_b
    for e in added_excl:
        diffs.append(FieldDiff(field="exclusion", label="Exclusion", policy_a_value=None, policy_b_value=e[:100], change_type="added"))
    for e in removed_excl:
        diffs.append(FieldDiff(field="exclusion", label="Exclusion", policy_a_value=e[:100], policy_b_value=None, change_type="removed"))
        improvements.append(f"Previous exclusion removed: {e[:80]}")

    # Gaps bridged analysis
    gaps_detected_a = [g.field for g in (getattr(policy_a, 'coverage_gaps', []) or []) if "missing" in g.detail.lower() or "no " in g.detail.lower()]
    gaps_detected_b = [g.field for g in (getattr(policy_b, 'coverage_gaps', []) or []) if "missing" in g.detail.lower() or "no " in g.detail.lower()]
    bridged = set(gaps_detected_a) - set(gaps_detected_b)
    for field in bridged:
        for fname, flabel in COVERAGE_FIELDS:
            if fname == field:
                gaps_bridged.append(f"{flabel} — gap closed in new policy")

    # Overall assessment
    if len(improvements) > len(reductions):
        overall = f"New policy shows {len(improvements)} improvement(s) vs {len(reductions)} reduction(s). Overall recommendation: upgrade is beneficial."
    elif len(improvements) < len(reductions):
        overall = f"New policy shows {len(reductions)} reduction(s) vs {len(improvements)} improvement(s). Consider whether the lower premium justifies the reduction in coverage."
    else:
        overall = f"New policy has {len(improvements)} improvement(s) and {len(reductions)} reduction(s). Review the specific changes to decide if this policy meets your needs."

    return ComparisonResult(
        policy_a_label="Current / Prior Policy",
        policy_b_label="New / Proposed Policy",
        diffs=diffs,
        improvements=improvements,
        reductions=reductions,
        gaps_bridged=gaps_bridged,
        overall_assessment=overall,
    )
