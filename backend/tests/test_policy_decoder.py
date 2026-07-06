"""
Unit tests for the Policy Decoder service.
"""

import pytest
from src.core.policy_decoder import PolicyDecoder, ParsedPolicy


class TestPolicyDecoder:
    def test_detect_low_property_limit(self):
        policy = ParsedPolicy(property_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any(g.field == "property_limit" for g in gaps)

    def test_detect_property_limit_ok(self):
        policy = ParsedPolicy(property_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any(g.field == "property_limit" for g in gaps)

    def test_detect_low_medical_limit(self):
        policy = ParsedPolicy(medical_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any(g.field == "medical_limit" for g in gaps)

    def test_detect_medical_limit_ok(self):
        policy = ParsedPolicy(medical_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any(g.field == "medical_limit" for g in gaps)

    def test_detect_no_gaps(self):
        policy = ParsedPolicy(
            liability_limit="$100,000 / $300,000",
            property_limit="$100,000",
            medical_limit="$100,000",
            uninsured_motorist_limit="$100,000",
            rental_reimbursement="$30/day",
            roadside_assistance="Yes",
            loan_lease_payoff="Yes",
            collision_deductible="$500",
            comprehensive_deductible="$500",
            exclusions=["exclusion 1", "exclusion 2"],
        )
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert len(gaps) == 0

    def test_generate_llm_prompt(self):
        prompt = PolicyDecoder.generate_llm_prompt("Sample policy text")
        assert "Sample policy text" in prompt
        assert "liability limit" in prompt.lower()
        assert "plain-English" in prompt

    def test_national_averages_present(self):
        assert "liability" in PolicyDecoder.NATIONAL_AVERAGES
        assert "medical" in PolicyDecoder.NATIONAL_AVERAGES
        assert "property" in PolicyDecoder.NATIONAL_AVERAGES