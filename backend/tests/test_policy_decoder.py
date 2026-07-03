"""
Unit tests for the Policy Decoder service.
"""

from src.core.policy_decoder import PolicyDecoder, ParsedPolicy


class TestPolicyDecoder:
    def test_detect_low_property_limit(self):
        policy = ParsedPolicy(property_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any("Property limit" in g for g in gaps)

    def test_detect_property_limit_ok(self):
        policy = ParsedPolicy(property_limit="$100,000", uninsured_motorist_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any("Property limit" in g for g in gaps)

    def test_detect_low_medical_limit(self):
        policy = ParsedPolicy(medical_limit="$25,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert any("Medical limit" in g for g in gaps)

    def test_detect_medical_limit_ok(self):
        policy = ParsedPolicy(medical_limit="$100,000", uninsured_motorist_limit="$100,000")
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert not any("Medical limit" in g for g in gaps)

    def test_detect_no_gaps(self):
        policy = ParsedPolicy(
            property_limit="$100,000",
            medical_limit="$100,000",
            uninsured_motorist_limit="$100,000",
        )
        gaps = PolicyDecoder.detect_coverage_gaps(policy)
        assert len(gaps) == 0

    def test_generate_llm_prompt(self):
        prompt = PolicyDecoder.generate_llm_prompt("Sample policy text")
        assert "Sample policy text" in prompt
        assert "liability limit" in prompt.lower()
        assert "Do not guess" in prompt

    def test_national_averages_present(self):
        assert "liability" in PolicyDecoder.NATIONAL_AVERAGES
        assert "medical" in PolicyDecoder.NATIONAL_AVERAGES
        assert "property" in PolicyDecoder.NATIONAL_AVERAGES

    def test_parse_policy_text_extracts_core_limits(self):
        raw_text = """
        Bodily Injury Liability Limit: $25,000 each person / $50,000 each accident
        Property Damage Liability Limit: $15,000 each accident
        Medical Payments Limit: $1,000 each person
        Uninsured / Underinsured Motorist Bodily Injury: $25,000 each person / $50,000 each accident
        Collision Deductible: $2,000
        Comprehensive Deductible: $1,500
        """
        parsed = PolicyDecoder.parse_policy_text(raw_text)
        assert parsed.liability_limit == "$25,000 / $50,000"
        assert parsed.property_limit == "$15,000"
        assert parsed.medical_limit == "$1,000"
        assert parsed.uninsured_motorist_limit == "$25,000 / $50,000"
        assert parsed.deductible == "$1,500"
        assert parsed.plain_english_summary

    def test_parse_policy_text_handles_ocr_noise(self):
        raw_text = """
        Bodily lnjury Liability L1mit: $50,000 each person / $100,000 each accident
        Property Damage Liability L1mit: $20,000 each accident
        Medical Payments L1mit: $2,500 each person
        Uninsured / Underinsured Motorist B.l.: $25,000 each person / $50,000 each accident
        Deductib1e: $750
        """
        parsed = PolicyDecoder.parse_policy_text(raw_text)
        assert parsed.liability_limit == "$50,000 / $100,000"
        assert parsed.property_limit == "$20,000"
        assert parsed.medical_limit == "$2,500"
        assert parsed.uninsured_motorist_limit == "$25,000 / $50,000"
        assert parsed.deductible == "$750"
