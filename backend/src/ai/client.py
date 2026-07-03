"""
AI Client for PolicySight.
Uses OpenAI API for SLIP parsing, claim valuation, and rate forecasting.
Falls back to mock responses when no API key is configured.
"""

from typing import Optional
from pydantic import BaseModel
import json


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
    LLM service that uses OpenAI for intelligent policy analysis.
    Falls back to mock responses if no API key is configured.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self._openai = None

        if api_key and api_key != "sk-placeholder":
            try:
                from openai import AsyncOpenAI
                self._openai = AsyncOpenAI(api_key=api_key)
            except Exception:
                self._openai = None

    @property
    def use_real_llm(self) -> bool:
        """Check if we have a real API key configured."""
        return self._openai is not None

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM with system and user prompts."""
        if not self.use_real_llm:
            raise RuntimeError("No API key configured")

        response = await self._openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    async def parse_slip(self, raw_text: str) -> ParsedPolicy:
        """
        Parse a SLIP document and return structured policy data.
        Uses OpenAI when available, otherwise returns mock data.
        """
        if not self.use_real_llm:
            return self._mock_parse_slip(raw_text)

        system_prompt = """You are an expert auto insurance policy analyst. 
Extract structured data from insurance policy documents. 
Return ONLY valid JSON with these fields:
{
  "liability_limit": "string or null",
  "medical_limit": "string or null", 
  "property_limit": "string or null",
  "uninsured_motorist_limit": "string or null",
  "deductible": "string or null",
  "coverage_gaps": ["list of strings describing gaps"],
  "plain_english_summary": "string explaining coverage in simple terms"
}"""

        try:
            result = await self._call_llm(system_prompt, f"Parse this insurance policy document:\n\n{raw_text[:6000]}")
            data = json.loads(result)
            return ParsedPolicy(**data)
        except Exception:
            return self._mock_parse_slip(raw_text)

    async def valuate_claim(
        self,
        policy: ParsedPolicy,
        claim_description: str,
        carrier_offer: float = 0.0,
    ) -> ClaimValuation:
        """
        Valuate a claim against policy limits.
        Uses OpenAI when available, otherwise returns mock data.
        """
        if not self.use_real_llm:
            return self._mock_valuate_claim(policy, claim_description, carrier_offer)

        system_prompt = """You are an expert insurance claims analyst.
Analyze a claim against policy limits and return ONLY valid JSON:
{
  "total_claim_amount": float,
  "carrier_offer": float,
  "estimated_payout": float,
  "sub_limit_breakdown": {"coverage_type": amount},
  "verdict": "detailed analysis string",
  "confidence_score": float between 0 and 1
}"""

        user_prompt = f"""
Policy Summary: {policy.plain_english_summary}
Policy Limits: Liability={policy.liability_limit}, Medical={policy.medical_limit}, Property={policy.property_limit}

Claim Description: {claim_description}
Carrier Offer: ${carrier_offer:,.2f}
"""

        try:
            result = await self._call_llm(system_prompt, user_prompt)
            data = json.loads(result)
            return ClaimValuation(**data)
        except Exception:
            return self._mock_valuate_claim(policy, claim_description, carrier_offer)

    async def forecast_rate(
        self,
        current_rate: float,
        claims_history: list[dict],
        peer_avg_rate: float = 0.0,
    ) -> dict:
        """
        Forecast next year's premium.
        Uses OpenAI when available, otherwise returns mock data.
        """
        if not self.use_real_llm:
            return self._mock_forecast_rate(current_rate, claims_history, peer_avg_rate)

        system_prompt = """You are an expert auto insurance rate analyst.
Forecast the user's future premium and return ONLY valid JSON:
{
  "current_rate": float,
  "forecasted_rate": float,
  "peer_average": float,
  "recommendation": "Stay or Switch",
  "savings_amount": float,
  "confidence": float between 0 and 1
}"""

        claims_str = json.dumps(claims_history) if claims_history else "No claims"
        user_prompt = f"""
Current Monthly Premium: ${current_rate:,.2f}
Claims History: {claims_str}
Peer Average Rate: ${peer_avg_rate:,.2f}
"""

        try:
            result = await self._call_llm(system_prompt, user_prompt)
            return json.loads(result)
        except Exception:
            return self._mock_forecast_rate(current_rate, claims_history, peer_avg_rate)

    # ─── Mock fallback methods ──────────────────────────────────────────

    def _mock_parse_slip(self, raw_text: str) -> ParsedPolicy:
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

    def _mock_valuate_claim(
        self,
        policy: ParsedPolicy,
        claim_description: str,
        carrier_offer: float = 0.0,
    ) -> ClaimValuation:
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
                f"The carrier's offer of ${carrier_offer or 80000:,.2f} is below "
                f"the estimated payout of $120,000. Based on your policy limits, "
                f"you are entitled to an additional ${max(0, 120000 - (carrier_offer or 80000)):,.2f}. "
                "Recommend disputing the offer."
            ),
            confidence_score=0.85,
        )

    def _mock_forecast_rate(
        self,
        current_rate: float,
        claims_history: list[dict],
        peer_avg_rate: float = 0.0,
    ) -> dict:
        return {
            "current_rate": current_rate,
            "forecasted_rate": round(current_rate * 1.12, 2),
            "peer_average": peer_avg_rate or round(current_rate * 0.95, 2),
            "recommendation": "Switch",
            "savings_amount": round(current_rate * 0.15, 2),
            "confidence": 0.78,
        }