"""
Claims Advocate Service
Handles claim valuation and sub-limit aggregation logic.
"""

from pydantic import BaseModel
from typing import Optional


class ClaimValuation(BaseModel):
    """Structured representation of a claim valuation."""
    total_claim_amount: float = 0.0
    carrier_offer: float = 0.0
    estimated_payout: float = 0.0
    sub_limit_breakdown: dict[str, float] = {}
    verdict: str = ""
    confidence_score: float = 0.0


class ClaimValuationEngine:
    """
    Core engine for valuating insurance claims.
    Cross-references parsed policy limits against claim line items
    to determine what should be paid vs. what the carrier is offering.
    """

    @staticmethod
    def calculate_payout(
        policy_limits: dict[str, float],
        claim_line_items: dict[str, float],
    ) -> dict[str, float]:
        """
        Calculate payout per sub-limit based on policy limits and claim items.
        Each claim line item is matched to the appropriate coverage type.
        """
        payout: dict[str, float] = {}

        for coverage_type, amount in claim_line_items.items():
            limit = policy_limits.get(coverage_type, 0.0)
            payout[coverage_type] = min(amount, limit)

        return payout

    @staticmethod
    def generate_verdict(
        estimated_payout: float,
        carrier_offer: float,
        confidence: float,
    ) -> str:
        """Generate a human-readable verdict comparing payout vs offer."""
        if carrier_offer <= 0:
            return (
                "No carrier offer provided. Based on your policy limits, "
                f"the estimated payout is ${estimated_payout:,.2f}. "
                "Use this figure as your baseline for negotiations."
            )

        difference = estimated_payout - carrier_offer

        if difference > 0:
            return (
                f"The carrier's offer of ${carrier_offer:,.2f} is "
                f"${difference:,.2f} below the estimated payout of "
                f"${estimated_payout:,.2f}. Based on your policy limits, "
                "you are entitled to additional compensation. "
                "Recommend disputing the offer with the following breakdown."
            )
        elif difference < 0:
            return (
                f"The carrier's offer of ${carrier_offer:,.2f} exceeds "
                f"the estimated payout of ${estimated_payout:,.2f} by "
                f"${abs(difference):,.2f}. This is a favorable offer."
            )
        else:
            return (
                f"The carrier's offer matches the estimated payout of "
                f"${estimated_payout:,.2f}. This appears to be a fair settlement."
            )

    @staticmethod
    def generate_llm_prompt(
        policy_summary: str,
        claim_description: str,
        carrier_offer: float,
    ) -> str:
        """Generate the LLM prompt for claim valuation analysis."""
        return f"""You are an expert insurance claims analyst. 
Analyze the following claim against the policyholder's coverage.

Policy Summary:
{policy_summary}

Claim Description:
{claim_description}

Carrier Offer: ${carrier_offer:,.2f}

Provide a detailed breakdown:
1. Which sub-limits apply to each damage/medical item
2. The estimated payout per sub-limit
3. Total estimated payout
4. Whether the carrier's offer is fair
5. A clear verdict with recommended next steps"""