"""
Claim Coverage Decision Draft (REQ-008) + Confidence & Escalation (REQ-009)
Evaluates a claim against policy coverage and produces a structured decision
with confidence levels and escalation recommendations.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class CoverageDetermination(BaseModel):
    coverage_type: str
    limit: Optional[str] = None
    deductible: Optional[str] = None
    estimated_payout: Optional[str] = None
    applies: bool
    confidence: str  # high, medium, low
    reasoning: str
    needs_review: bool = False
    escalation_reason: Optional[str] = None


class CoverageDecision(BaseModel):
    claim_summary: str
    determinations: list[CoverageDetermination]
    total_estimated_payout: Optional[str] = None
    overall_confidence: str
    escalation_level: str  # auto_adjudicate, supervisor_review, underwriting_review
    escalation_reason: Optional[str] = None
    next_steps: list[str] = []
    validations: list[dict] = []


# Keywords to estimate which coverages a claim description maps to
CLAIM_COVERAGE_MAP = {
    "collision": ["hit", "crash", "rear-end", "rear ended", "sideswiped", "collision", "fender bender", "wreck", "bumped", "struck", "ran into", "pulled out", "t-boned"],
    "comprehensive": ["deer", "hail", "flood", "fire", "theft", "stolen", "vandalism", "tree", "animal", "hailstorm", "wind", "lightning", "fallen"],
    "liability": ["sue", "lawsuit", "injury to others", "other driver injured", "at fault", "my fault"],
    "medical": ["hospital", "ambulance", "injured", "injury", "medical", "ambulance", "surgery", "doctor", "paramedic"],
    "um_uim": ["uninsured", "hit and run", "underinsured", "no insurance"],
    "rental": ["rental", "loaner", "transportation", "need a car"],
}


def estimate_payout(
    coverage_type: str,
    applies: bool,
    deductible_str: Optional[str],
    limit_str: Optional[str],
) -> tuple[Optional[str], str]:
    """
    Estimate a payout range based on coverage type, limits, and deductibles.
    Returns (payout_str, reasoning).
    """
    if not applies:
        return (None, "Coverage does not apply to this claim.")

    limit = None
    deductible = 0
    if limit_str:
        try:
            limit = float(limit_str.replace("$", "").replace(",", "").split("/")[0].strip())
        except ValueError:
            pass
    if deductible_str:
        try:
            deductible = float(deductible_str.replace("$", "").replace(",", ""))
        except ValueError:
            pass

    base = {
        "collision": (1000, 15000),
        "comprehensive": (500, 8000),
        "liability": (5000, limit or 50000),
        "medical": (500, limit or 5000),
        "um_uim": (2000, limit or 25000),
        "rental": (300, limit or 900),
    }

    low, high = base.get(coverage_type, (0, 0))
    min_payout = max(0, low - deductible)
    max_payout = max(min_payout, high - deductible)
    if limit:
        max_payout = min(max_payout, limit - deductible)

    if max_payout <= 0:
        return (None, "Deductible exceeds or equals estimated damage amount.")

    payout = f"${min_payout:,} – ${max_payout:,}" if min_payout != max_payout else f"${min_payout:,}"
    reasoning = f"Estimated payout after ${deductible:,} deductible: {payout}"
    return (payout, reasoning)


def generate_decision(
    parsed: ParsedPolicy,
    claim_description: str,
) -> CoverageDecision:
    """
    Generate a structured coverage decision for a claim description.
    Includes confidence levels, escalation flags, and next steps.
    """
    cd = claim_description.lower()
    determinations: list[CoverageDetermination] = []
    total_min = 0
    total_max = 0
    needs_escalation = False
    escalation_reasons: list[str] = []

    coverage_configs = [
        ("Collision", "collision", parsed.collision_deductible, parsed.collision_deductible_source),
        ("Comprehensive", "comprehensive", parsed.comprehensive_deductible, parsed.comprehensive_deductible_source),
        ("Liability", "liability", parsed.liability_limit, parsed.liability_source),
        ("Medical Payments", "medical", parsed.medical_limit, parsed.medical_source),
        ("UM/UIM", "um_uim", parsed.uninsured_motorist_limit, parsed.uninsured_motorist_source),
        ("Rental Reimbursement", "rental", parsed.rental_reimbursement, parsed.rental_reimbursement_source),
    ]

    matched_any = False

    for display_name, key, limit_or_ded, source in coverage_configs:
        triggers = CLAIM_COVERAGE_MAP.get(key, [])
        keywords_found = [kw for kw in triggers if kw in cd]
        applies = len(keywords_found) > 0 and bool(limit_or_ded)
        if len(keywords_found) > 0:
            matched_any = True

        has_coverage = bool(limit_or_ded)

        if keywords_found and not has_coverage:
            # Claim keywords match but no coverage found — flag for review
            approx_payout, reasoning = estimate_payout(key, False, None, None)
            determinations.append(CoverageDetermination(
                coverage_type=display_name,
                limit=None,
                deductible=None,
                estimated_payout=approx_payout,
                applies=False,
                confidence="low",
                reasoning=f"Your description suggests {display_name} may be needed, but this coverage was not detected in your policy.",
                needs_review=True,
                escalation_reason="Claim scenario matches coverage type that is not present on the policy",
            ))
            needs_escalation = True
            escalation_reasons.append(f"{display_name} potentially needed but not found")
        elif applies:
            payout, reasoning = estimate_payout(key, True, limit_or_ded if key in ("collision", "comprehensive") else None,
                                                limit_or_ded if key in ("liability", "medical", "um_uim", "rental") else None)

            # Parse estimated payout for totals
            if payout:
                try:
                    parts = payout.replace("$", "").replace(",", "").split(" – ")
                    total_min += float(parts[0])
                    total_max += float(parts[1]) if len(parts) > 1 else float(parts[0])
                except ValueError:
                    pass

            determinations.append(CoverageDetermination(
                coverage_type=display_name,
                limit=str(limit_or_ded) if limit_or_ded else None,
                deductible=str(limit_or_ded) if key in ("collision", "comprehensive") else None,
                estimated_payout=payout,
                applies=True,
                confidence="high" if has_coverage else "medium",
                reasoning=reasoning,
                needs_review=False,
            ))
        else:
            determinations.append(CoverageDetermination(
                coverage_type=display_name,
                limit=str(limit_or_ded) if limit_or_ded else None,
                applies=False,
                confidence="medium",
                reasoning=f"This coverage type is not indicated by the claim description.",
            ))

    if not matched_any:
        needs_escalation = True
        escalation_reasons.append("Claim description did not clearly match any coverage type")

    total_payout = None
    if total_max > 0:
        total_payout = f"${total_min:,.0f} – ${total_max:,.0f}" if total_min != total_max else f"${total_min:,.0f}"

    confidences = [d.confidence for d in determinations if d.applies]
    if not confidences:
        overall_conf = "low"
    elif all(c == "high" for c in confidences):
        overall_conf = "high"
    elif any(c == "low" for c in confidences):
        overall_conf = "low"
    else:
        overall_conf = "medium"

    # Determine escalation level
    if needs_escalation:
        escalation_level = "supervisor_review"
    elif overall_conf == "low":
        escalation_level = "supervisor_review"
    elif overall_conf == "medium":
        escalation_level = "auto_adjudicate"
    else:
        escalation_level = "auto_adjudicate"

    next_steps = []
    if escalation_level == "auto_adjudicate":
        next_steps.append("Coverage determination can proceed to auto-adjudication.")
        next_steps.append("Review estimated payouts against policy limits.")
    elif escalation_level == "supervisor_review":
        next_steps.append("Route to claims supervisor for manual review.")
        next_steps.append("Verify coverage limits and claim details before proceeding.")

    if total_payout and float(total_payout.replace("$", "").split(" – ")[0].replace(",", "")) > 50000:
        next_steps.append("Estimated payout exceeds $50,000 threshold — requires underwriting approval.")
        escalation_level = "underwriting_review"

    return CoverageDecision(
        claim_summary=claim_description,
        determinations=determinations,
        total_estimated_payout=total_payout,
        overall_confidence=overall_conf,
        escalation_level=escalation_level,
        escalation_reason="; ".join(escalation_reasons) if escalation_reasons else None,
        next_steps=next_steps,
    )
