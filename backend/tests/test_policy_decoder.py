"""
Unit tests for the Policy Decoder service.
"""

import pytest
from src.core.policy_decoder import PolicyDecoder, ParsedPolicy


class TestPolicyDecoder:
    def test_detect_low_property_limit(self):
        policy = ParsedPolicy(property_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any("Property limit" in g for g in gaps)

    def test_detect_property_limit_ok(self):
        policy = ParsedPolicy(property_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any("Property limit" in g for g in gaps)

    def test_detect_low_medical_limit(self):
        policy = ParsedPolicy(medical_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any("Medical limit" in g for g in gaps)

    def test_detect_medical_limit_ok(self):
        policy = ParsedPolicy(medical_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any("Medical limit" in g for g in gaps)

    def test_detect_no_gaps(self):
        policy = ParsedPolicy(
            property_limit="$100,000",
            medical_limit="$100,000",
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