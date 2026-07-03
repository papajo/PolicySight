"""
Out-of-Pocket Cost Estimator (PDF REQ-008)
Estimates user costs based on deductible, limits, rental, and uncovered expenses.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class CostLineItem(BaseModel):
    category: str
    estimated_cost: float
    covered_by_insurance: float
    out_of_pocket: float
    detail: str


class CostEstimate(BaseModel):
    total_out_of_pocket: float
    total_covered: float
    deductible: float
    line_items: list[CostLineItem]
    breakdown_summary: str
    recommendations: list[str] = []
    max_exposure: float


def parse_dollar(val: Optional[str]) -> float:
    """Parse a dollar string like '$500', '$100,000', '$30/day'."""
    if not val:
        return 0.0
    import re
    m = re.search(r'\$?([\d,]+)', val.replace(",", ""))
    if m:
        return float(m.group(1))
    return 0.0


def estimate_costs(
    parsed: ParsedPolicy,
    damage_estimate: float = 5000.0,
    has_injuries: bool = False,
    needs_rental_days: int = 14,
    collision_applies: bool = True,
    comprehensive_applies: bool = False,
) -> CostEstimate:
    """
    Estimate out-of-pocket costs for a claim scenario.
    damage_estimate: estimated vehicle repair/replacement cost
    has_injuries: whether medical claims are expected
    needs_rental_days: days a rental car is needed
    """
    line_items: list[CostLineItem] = []
    total_covered = 0.0
    total_oop = 0.0

    # Deductible
    collision_ded = parse_dollar(parsed.collision_deductible)
    comp_ded = parse_dollar(parsed.comprehensive_deductible)
    deductible = 0.0

    # Vehicle damage
    if collision_applies and collision_ded > 0:
        deductible = collision_ded
        covered = max(0, damage_estimate - collision_ded)
        oop = min(damage_estimate, collision_ded)
        line_items.append(CostLineItem(
            category="Vehicle Repair (Collision)",
            estimated_cost=damage_estimate,
            covered_by_insurance=covered,
            out_of_pocket=oop,
            detail=f"Repair cost ${damage_estimate:,.0f} minus ${collision_ded:,.0f} deductible",
        ))
        total_covered += covered
        total_oop += oop
    elif comprehensive_applies and comp_ded > 0:
        deductible = comp_ded
        covered = max(0, damage_estimate - comp_ded)
        oop = min(damage_estimate, comp_ded)
        line_items.append(CostLineItem(
            category="Vehicle Repair (Comprehensive)",
            estimated_cost=damage_estimate,
            covered_by_insurance=covered,
            out_of_pocket=oop,
            detail=f"Repair cost ${damage_estimate:,.0f} minus ${comp_ded:,.0f} deductible",
        ))
        total_covered += covered
        total_oop += oop
    else:
        # No applicable coverage
        line_items.append(CostLineItem(
            category="Vehicle Repair",
            estimated_cost=damage_estimate,
            covered_by_insurance=0,
            out_of_pocket=damage_estimate,
            detail="No applicable collision or comprehensive coverage detected",
        ))
        total_oop += damage_estimate

    # Rental costs
    rental_per_day = parse_dollar(parsed.rental_reimbursement)
    rental_max = 900.0  # common max
    if rental_per_day > 0 and needs_rental_days > 0:
        covered_rental = min(rental_per_day * needs_rental_days, rental_max)
        total_rental = 45.0 * needs_rental_days  # avg $45/day market rate
        oop_rental = max(0, total_rental - covered_rental)
        line_items.append(CostLineItem(
            category="Rental Car",
            estimated_cost=total_rental,
            covered_by_insurance=covered_rental,
            out_of_pocket=oop_rental,
            detail=f"${rental_per_day:,.0f}/day reimbursement, ${needs_rental_days} days, ${rental_max:,.0f} max",
        ))
        total_covered += covered_rental
        total_oop += oop_rental
    elif needs_rental_days > 0:
        total_rental = 45.0 * needs_rental_days
        line_items.append(CostLineItem(
            category="Rental Car",
            estimated_cost=total_rental,
            covered_by_insurance=0,
            out_of_pocket=total_rental,
            detail="No rental reimbursement coverage detected",
        ))
        total_oop += total_rental

    # Medical costs
    medical_limit = parse_dollar(parsed.medical_limit)
    if has_injuries:
        med_estimate = 2000.0
        if medical_limit > 0:
            covered_med = min(med_estimate, medical_limit)
            oop_med = med_estimate - covered_med
            line_items.append(CostLineItem(
                category="Medical Expenses",
                estimated_cost=med_estimate,
                covered_by_insurance=covered_med,
                out_of_pocket=oop_med,
                detail=f"MedPay limit ${medical_limit:,.0f}",
            ))
            total_covered += covered_med
            total_oop += oop_med
        else:
            line_items.append(CostLineItem(
                category="Medical Expenses",
                estimated_cost=med_estimate,
                covered_by_insurance=0,
                out_of_pocket=med_estimate,
                detail="No MedPay coverage detected — may be covered by health insurance",
            ))
            total_oop += med_estimate

    # Maximum exposure
    max_exposure = total_oop + (damage_estimate * 0.2)  # 20% buffer

    # Generate recommendations
    recommendations = []
    if collision_ded > 500:
        recommendations.append(f"Consider lowering your collision deductible (currently ${collision_ded:,.0f}) to reduce out-of-pocket costs.")
    if not parsed.rental_reimbursement:
        recommendations.append("Add rental reimbursement coverage to avoid paying full rental costs out of pocket.")
    if not parsed.medical_limit and has_injuries:
        recommendations.append("Medical payments (MedPay) coverage helps pay medical bills regardless of fault — consider adding it.")
    if damage_estimate > 10000 and not parsed.loan_lease_payoff:
        recommendations.append("For high-value claims, consider gap/loan-lease coverage if you have an auto loan.")

    summary_parts = []
    if total_oop > 0:
        summary_parts.append(f"Estimated out-of-pocket: ${total_oop:,.0f}")
    if total_covered > 0:
        summary_parts.append(f"Insurance covers approximately ${total_covered:,.0f}")
    summary_parts.append(f"Maximum potential exposure: ${max_exposure:,.0f}")
    breakdown_summary = ". ".join(summary_parts) + "."

    return CostEstimate(
        total_out_of_pocket=total_oop,
        total_covered=total_covered,
        deductible=deductible,
        line_items=line_items,
        breakdown_summary=breakdown_summary,
        recommendations=recommendations,
        max_exposure=max_exposure,
    )
