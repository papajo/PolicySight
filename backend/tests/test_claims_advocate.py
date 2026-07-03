"""
Unit tests for the Claims Advocate service.
"""

import pytest
from src.core.claims_advocate import ClaimValuationEngine, ClaimValuation


class TestClaimValuationEngine:
    def test_calculate_payout_within_limits(self):
        limits = {"Medical Payments": 50000.0, "Property Damage": 25000.0}
        items = {"Medical Payments": 30000.0, "Property Damage": 15000.0}
        payout = ClaimValuationEngine.calculate_payout(limits, items)
        assert payout["Medical Payments"] == 30000.0
        assert payout["Property Damage"] == 15000.0

    def test_calculate_payout_exceeds_limits(self):
        limits = {"Medical Payments": 50000.0}
        items = {"Medical Payments": 75000.0}
        payout = ClaimValuationEngine.calculate_payout(limits, items)
        assert payout["Medical Payments"] == 50000.0  # Capped at limit

    def test_calculate_payout_empty(self):
        payout = ClaimValuationEngine.calculate_payout({}, {})
        assert payout == {}

    def test_generate_verdict_offer_low(self):
        verdict = ClaimValuationEngine.generate_verdict(
            estimated_payout=100000.0,
            carrier_offer=60000.0,
            confidence=0.85,
        )
        assert "below" in verdict
        assert "$100,000" in verdict
        assert "$60,000" in verdict

    def test_generate_verdict_offer_fair(self):
        verdict = ClaimValuationEngine.generate_verdict(
            estimated_payout=100000.0,
            carrier_offer=100000.0,
            confidence=0.85,
        )
        assert "matches" in verdict

    def test_generate_verdict_offer_high(self):
        verdict = ClaimValuationEngine.generate_verdict(
            estimated_payout=80000.0,
            carrier_offer=100000.0,
            confidence=0.85,
        )
        assert "exceeds" in verdict

    def test_generate_verdict_no_offer(self):
        verdict = ClaimValuationEngine.generate_verdict(
            estimated_payout=100000.0,
            carrier_offer=0.0,
            confidence=0.85,
        )
        assert "No carrier offer" in verdict
        assert "$100,000" in verdict

    def test_generate_llm_prompt(self):
        prompt = ClaimValuationEngine.generate_llm_prompt(
            policy_summary="Sample policy",
            claim_description="Rear-ended at stop",
            carrier_offer=50000.0,
        )
        assert "Sample policy" in prompt
        assert "Rear-ended at stop" in prompt
        assert "$50,000" in prompt