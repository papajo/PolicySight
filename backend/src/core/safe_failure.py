"""
Safe Failure Mode (PDF REQ-017)
When the system lacks enough information, it must explicitly say "I don't know",
provide a checklist of what's needed, and recommend next actions.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class RequiredInfoItem(BaseModel):
    field: str
    label: str
    reason: str
    how_to_find: str


class NextActionItem(BaseModel):
    action: str
    detail: str
    priority: str  # high, medium, low


class SafeFailureAnalysis(BaseModel):
    overall_status: str  # determinate, partial, indeterminate
    assessment: str
    required_info: list[RequiredInfoItem]
    next_actions: list[NextActionItem]


KEY_FIELDS = [
    ("liability_limit", "Liability coverage limit"),
    ("property_limit", "Property damage limit"),
    ("medical_limit", "Medical payments limit"),
    ("uninsured_motorist_limit", "UM/UIM coverage limit"),
    ("collision_deductible", "Collision deductible"),
    ("comprehensive_deductible", "Comprehensive deductible"),
]

FIELD_HELP = {
    "liability_limit": {
        "reason": "Determines how much protection you have if you cause an accident. Without it, we cannot assess your risk of personal liability.",
        "how_to_find": "Look for 'Liability' or 'Bodily Injury' on your declarations page — typically shown as three numbers like $100,000 / $300,000 / $50,000.",
    },
    "property_limit": {
        "reason": "Determines coverage for damage you cause to others' property. Missing this means we cannot evaluate your property damage risk.",
        "how_to_find": "Found under 'Property Damage Liability' on your declarations page, usually a single dollar amount.",
    },
    "medical_limit": {
        "reason": "Covers medical bills for you and your passengers regardless of fault. Missing this means we cannot evaluate medical payment protection.",
        "how_to_find": "Look for 'Medical Payments', 'Med Pay', or 'PIP' on your declarations page.",
    },
    "uninsured_motorist_limit": {
        "reason": "Protects you if hit by an uninsured or underinsured driver. Without this, you may have no coverage for hit-and-run accidents.",
        "how_to_find": "Found under 'Uninsured Motorist' or 'UM/UIM' on your declarations page.",
    },
    "collision_deductible": {
        "reason": "Determines your out-of-pocket cost for collision repairs. Missing this means we cannot estimate your claim costs.",
        "how_to_find": "Look for 'Collision Deductible' on your declarations page — typically $500 or $1,000.",
    },
    "comprehensive_deductible": {
        "reason": "Determines your out-of-pocket cost for non-collision claims like theft, hail, or animal strikes.",
        "how_to_find": "Look for 'Comprehensive Deductible' on your declarations page — often $250 or $500.",
    },
}

ADDITIONAL_FIELDS = [
    ("rental_reimbursement", "Rental reimbursement coverage"),
    ("roadside_assistance", "Roadside assistance coverage"),
    ("loan_lease_payoff", "Loan/lease payoff (gap) coverage"),
    ("effective_date", "Policy effective date"),
    ("expiration_date", "Policy expiration date"),
]

ADDITIONAL_HELP = {
    "rental_reimbursement": {
        "reason": "Pays for a rental car while your vehicle is in the shop. Missing this means you could pay $30-50/day out of pocket.",
        "how_to_find": "Look for 'Rental Reimbursement' or 'Transportation Expense' on your declarations page.",
    },
    "roadside_assistance": {
        "reason": "Covers towing, flat tires, lockouts, and jump-starts. Without it, a single tow could cost $100-250.",
        "how_to_find": "Check for 'Roadside Assistance', 'Towing', or 'Emergency Road Service' on your policy.",
    },
    "loan_lease_payoff": {
        "reason": "Pays the gap between your car's value and what you owe after a total loss. Critical if you have a loan or lease.",
        "how_to_find": "Look for 'Gap Coverage', 'Loan/Lease Payoff', or 'Total Loss Protection' on your policy.",
    },
    "effective_date": {
        "reason": "Confirms when your coverage started and whether the policy is currently active.",
        "how_to_find": "Find 'Effective Date' or 'Policy Period' near the top of your declarations page.",
    },
    "expiration_date": {
        "reason": "Shows when your coverage ends. Without this, you may not realize your policy has lapsed.",
        "how_to_find": "Look for 'Expiration Date' or 'Policy Period' dates on your declarations page.",
    },
}


def analyze_policy_safety(parsed: ParsedPolicy) -> SafeFailureAnalysis:
    required: list[RequiredInfoItem] = []
    next_actions: list[NextActionItem] = []

    missing_key = 0
    total_key = len(KEY_FIELDS)

    for attr, label in KEY_FIELDS:
        val = getattr(parsed, attr, None)
        if val is None or val == "":
            missing_key += 1
            help_info = FIELD_HELP.get(attr, {})
            required.append(RequiredInfoItem(
                field=attr,
                label=label,
                reason=help_info.get("reason", "Required for accurate coverage assessment."),
                how_to_find=help_info.get("how_to_find", "Check your declarations page."),
            ))

    for attr, label in ADDITIONAL_FIELDS:
        val = getattr(parsed, attr, None)
        if val is None or val == "":
            help_info = ADDITIONAL_HELP.get(attr, {})
            required.append(RequiredInfoItem(
                field=attr,
                label=label,
                reason=help_info.get("reason", "Useful for a complete coverage picture."),
                how_to_find=help_info.get("how_to_find", "Check your declarations page."),
            ))

    unclear_count = len(parsed.unclear_fields)

    if missing_key == 0 and unclear_count == 0 and len(required) == 0:
        overall_status = "determinate"
        assessment = "All key coverage fields have been identified. The analysis below should be reliable."
        next_actions.append(NextActionItem(
            action="Review coverage details",
            detail="Review the extracted coverage limits and gaps shown below for accuracy.",
            priority="medium",
        ))
    elif missing_key >= total_key // 2:
        overall_status = "indeterminate"
        assessment = (
            "I cannot provide a reliable coverage analysis — most key fields are missing from the policy text you provided. "
            "The information below may be incomplete or inaccurate."
        )
        next_actions.insert(0, NextActionItem(
            action="Provide a complete declarations page",
            detail="Upload or paste the full declarations page from your policy document. This contains all coverage limits and deductibles.",
            priority="high",
        ))
        next_actions.append(NextActionItem(
            action="Contact your agent",
            detail="If you cannot locate your declarations page, request a copy from your insurance agent or broker.",
            priority="high",
        ))
    else:
        overall_status = "partial"
        found_count = total_key - missing_key
        assessment = (
            f"I found {found_count} of {total_key} key coverage fields. "
            f"{'Some fields have low confidence and should be verified.' if unclear_count else ''} "
            "The analysis below is partially complete — please review the missing items and verify any uncertain values."
        )
        next_actions.insert(0, NextActionItem(
            action="Provide missing information",
            detail=f"{missing_key} key coverage field(s) are missing. Locate these on your declarations page and paste an updated version.",
            priority="high",
        ))
        if unclear_count > 0:
            next_actions.append(NextActionItem(
                action="Verify uncertain fields",
                detail=f"{unclear_count} field(s) were detected with low confidence. Cross-check against your physical policy document.",
                priority="medium",
            ))

    if required and len(required) <= 3:
        next_actions.append(NextActionItem(
            action="Manual entry",
            detail="You can manually enter the missing values if you know them from your policy document.",
            priority="low",
        ))

    return SafeFailureAnalysis(
        overall_status=overall_status,
        assessment=assessment,
        required_info=required,
        next_actions=next_actions,
    )


def analyze_explain_safety(parsed: ParsedPolicy) -> Optional[SafeFailureAnalysis]:
    """Return a safe failure analysis focused on explanation gaps."""
    full = analyze_policy_safety(parsed)
    if full.overall_status == "determinate":
        return None
    return full


def assess_decision_confidence(
    claim_description: str,
    missing_coverage_types: list[str],
) -> str:
    """
    Return explicit uncertainty language for a claim decision when key info is missing.
    """
    if not missing_coverage_types:
        return ""

    types = ", ".join(missing_coverage_types)
    return (
        f"I cannot fully determine coverage for this claim. "
        f"The following coverage types were not found in your policy: {types}. "
        f"Without this information, any payout estimate may be incomplete."
    )
