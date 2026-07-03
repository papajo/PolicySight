"""
Placeholder AI client for PolicySight.
Will be replaced with actual LLM integration in Phase 3.
"""

from typing import Optional
from pydantic import BaseModel


class ParsedPolicy(BaseModel):
    """Model representing a parsed insurance policy from a SLIP document."""
    liability_limit: Optional[str] = None
    medical_limit: Optional[str] = None
    property_limit: Optional[str] = None
    uninsured_motorist_limit: Optional[str] = None
    deductible: Optional[str] = None
    coverage_gaps: list[str] = []
    plain_english_summary: str = ""


class ClaimValuation(BaseModel):
    """Model representing a claim valuation breakdown."""
    total_claim_amount: float = 0.0
    carrier_offer: float = 0.0
    estimated_payout: float = 0.0
    sub_limit_breakdown: dict[str, float] = {}
    verdict: str = ""
    confidence_score: float = 0.0


class LLMService:
    """
    Placeholder LLM service.
    Returns mock responses for development and testing.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    async def parse_slip(self, raw_text: str) -> ParsedPolicy:
        """
        Parse a SLIP document and return structured policy data.
        Placeholder: returns mock data.
        """
        return ParsedPolicy(
            liability_limit="$250,000 / $500,000 / $250,000",
            medical_limit="$50,000",
            property_limit="$25,000",
            uninsured_motorist_limit="$100,000",
            deductible="$1,000",
            coverage_gaps=[
                "Property limit caps payout at $25,000 — consider increasing to $50,000",
                "No rental car coverage detected",
            ],
            plain_english_summary=(
                "Your policy provides $250k in liability coverage per person "
                "(up to $500k per accident) and $250k for property damage. "
                "Medical payments are capped at $50k. Your property damage "
                "limit of $25k may be low if you drive a newer vehicle."
            ),
        )

    async def valuate_claim(
        self,
        policy: ParsedPolicy,
        claim_description: str,
        carrier_offer: float = 0.0,
    ) -> ClaimValuation:
        """
        Valuate a claim against policy limits.
        Placeholder: returns mock data.
        """
        return ClaimValuation(
            total_claim_amount=150000.0,
            carrier_offer=carrier_offer or 80000.0,
            estimated_payout=120000.0,
            sub_limit_breakdown={
                "Medical Payments": 50000.0,
                "Property Damage": 25000.0,
                "Liability (Other Party)": 45000.0,
            },
            verdict=(
                "The carrier's offer of $80,000 is below the estimated "
                "payout of $120,000. Based on your policy limits, you "
                "are entitled to an additional $40,000. Recommend "
                "disputing the offer."
            ),
            confidence_score=0.85,
        )

    async def forecast_rate(
        self,
        current_rate: float,
        claims_history: list[dict],
        peer_avg_rate: float = 0.0,
    ) -> dict:
        """
        Forecast next year's premium.
        Placeholder: returns mock data.
        """
        return {
            "current_rate": current_rate,
            "forecasted_rate": round(current_rate * 1.12, 2),
            "peer_average": peer_avg_rate or round(current_rate * 0.95, 2),
            "recommendation": "Switch",
            "savings_amount": round(current_rate * 0.15, 2),
            "confidence": 0.78,
        }