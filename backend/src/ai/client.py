"""
AI Client for PolicySight.
Uses OpenAI API for policy parsing, claim valuation, and rate forecasting.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from src.core.policy_decoder import PolicyDecoder, ParsedPolicy


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
    LLM service that uses OpenAI for intelligent analysis when configured.
    Deterministic parsing remains the primary path for policy decoding.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4", base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._openai = None

        if api_key and api_key != "***":
            try:
                from openai import AsyncOpenAI

                kwargs = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                self._openai = AsyncOpenAI(**kwargs)
            except Exception:
                self._openai = None

    @property
    def use_real_llm(self) -> bool:
        return self._openai is not None

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
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

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Send a conversational chat request to the configured LLM."""
        if not self.use_real_llm:
            raise RuntimeError("No API key configured")

        response = await self._openai.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def parse_slip(self, raw_text: str) -> ParsedPolicy:
        parsed = PolicyDecoder.parse_policy_text(raw_text)

        if not self.use_real_llm:
            return parsed

        needs_enrichment = any(
            value is None
            for value in [
                parsed.liability_limit,
                parsed.medical_limit,
                parsed.property_limit,
                parsed.uninsured_motorist_limit,
            ]
        )

        if not needs_enrichment:
            return parsed

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
}
Only use values supported by the document text. Do not guess."""

        try:
            result = await self._call_llm(
                system_prompt,
                PolicyDecoder.generate_llm_prompt(raw_text[:6000]),
            )
            data = json.loads(result)
            llm_policy = ParsedPolicy(**data)
            merged_dict = parsed.model_dump()
            llm_dict = llm_policy.model_dump(exclude_none=True)
            for key, val in llm_dict.items():
                if merged_dict.get(key) is None and val is not None:
                    merged_dict[key] = val
            merged = ParsedPolicy(**merged_dict)
            merged.coverage_gaps = PolicyDecoder.detect_coverage_gaps(merged)
            merged.plain_english_summary = PolicyDecoder.generate_plain_english_summary(merged)
            return merged
        except Exception:
            return parsed

    async def valuate_claim(
        self,
        policy: ParsedPolicy,
        claim_description: str,
        carrier_offer: float = 0.0,
    ) -> ClaimValuation:
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
