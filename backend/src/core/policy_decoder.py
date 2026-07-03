"""
Policy Decoder Service
Handles SLIP document parsing and validation logic.
"""

from pydantic import BaseModel
from typing import Optional


class ParsedPolicy(BaseModel):
    """Structured representation of a parsed insurance policy."""
    liability_limit: Optional[str] = None
    medical_limit: Optional[str] = None
    property_limit: Optional[str] = None
    uninsured_motorist_limit: Optional[str] = None
    deductible: Optional[str] = None
    coverage_gaps: list[str] = []
    plain_english_summary: str = ""


class PolicyDecoder:
    """
    Core service for decoding SLIP documents.
    Orchestrates OCR, LLM parsing, and limit validation.
    """

    # Standard US auto insurance coverage limits for comparison
    NATIONAL_AVERAGES = {
        "liability": "$250,000 / $500,000 / $250,000",
        "medical": "$50,000",
        "property": "$25,000",
        "uninsured_motorist": "$100,000",
    }

    @staticmethod
    def detect_coverage_gaps(parsed: ParsedPolicy) -> list[str]:
        """Analyze parsed limits and flag potential coverage gaps."""
        gaps: list[str] = []

        # Property limit check
        if parsed.property_limit:
            try:
                prop_val = int(parsed.property_limit.replace("$", "").replace(",", ""))
                if prop_val < 50000:
                    gaps.append(
                        f"Property limit caps payout at ${prop_val:,}. "
                        f"Consider increasing to $50,000+ to cover a total loss."
                    )
            except (ValueError, AttributeError):
                pass

        # Medical limit check
        if parsed.medical_limit:
            try:
                med_val = int(parsed.medical_limit.replace("$", "").replace(",", ""))
                if med_val < 50000:
                    gaps.append(
                        f"Medical limit of ${med_val:,} is below the national average "
                        f"of $50,000. Consider increasing coverage."
                    )
            except (ValueError, AttributeError):
                pass

        return gaps

    @staticmethod
    def generate_llm_prompt(raw_text: str) -> str:
        """
        Generate the LLM prompt for SLIP parsing.
        This prompt template is designed to extract structured
        insurance policy data from dense legal text.
        """
        return f"""You are an expert auto insurance policy analyst. 
Extract the following coverage limits from this Summary of Liability 
Insurance Policy (SLIP) document. Return the data in a structured format.

Document text:
{raw_text[:4000]}

Extract these fields:
1. Liability limit (per person / per accident / property damage)
2. Medical payments limit
3. Property damage limit
4. Uninsured/underinsured motorist limit
5. Deductible amount
6. Any coverage gaps or unusual exclusions

Also provide a plain-English summary of what this policy covers,
as if explaining to the policyholder."""