"""
Policy Decoder Service
Handles SLIP document parsing and validation logic.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel


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
    Uses deterministic extraction first and optional guarded enrichment later.
    """

    NATIONAL_AVERAGES = {
        "liability": "$250,000 / $500,000 / $250,000",
        "medical": "$50,000",
        "property": "$25,000",
        "uninsured_motorist": "$100,000",
    }

    MONEY_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?")
    COMBINED_LIMIT_RE = re.compile(
        r"(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?)"
        r"(?:\s*(?:each\s+person|per\s+person))?\s*/\s*"
        r"(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?)"
        r"(?:\s*(?:each\s+accident|per\s+accident))?"
        r"(?:\s*/\s*(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?))?",
        re.IGNORECASE,
    )

    OCR_KEYWORD_NORMALIZATIONS = {
        "L1MIT": "LIMIT",
        "L1M1T": "LIMIT",
        "L1AB1LITY": "LIABILITY",
        "LIAB1LITY": "LIABILITY",
        "LNJURY": "INJURY",
        "M0TORIST": "MOTORIST",
        "PR0PERTY": "PROPERTY",
        "C0LLISION": "COLLISION",
        "DEDUCT1BLE": "DEDUCTIBLE",
        "DEDUCTIB1E": "DEDUCTIBLE",
        "C0MPREHENSIVE": "COMPREHENSIVE",
        "UNDERINSURED": "UNDERINSURED",
        "UNINSURED": "UNINSURED",
        "B.L.": "BODILY INJURY",
        "BI": "BI",
    }

    @classmethod
    def normalize_text(cls, raw_text: str) -> str:
        normalized_lines: list[str] = []
        for line in raw_text.splitlines():
            cleaned = re.sub(r"\s+", " ", line).strip()
            if not cleaned:
                continue
            upper = cleaned.upper()
            for source, target in cls.OCR_KEYWORD_NORMALIZATIONS.items():
                upper = upper.replace(source, target)
            normalized_lines.append(upper)
        return "\n".join(normalized_lines)

    @classmethod
    def parse_policy_text(cls, raw_text: str) -> ParsedPolicy:
        normalized = cls.normalize_text(raw_text)
        parsed = ParsedPolicy(
            liability_limit=cls._extract_liability_limit(normalized),
            medical_limit=cls._extract_single_limit(normalized, ["MEDICAL PAYMENTS", "MEDICAL LIMIT", "MED PAY"]),
            property_limit=cls._extract_single_limit(normalized, ["PROPERTY DAMAGE LIABILITY", "PROPERTY DAMAGE", "PROPERTY LIMIT"]),
            uninsured_motorist_limit=cls._extract_uninsured_motorist_limit(normalized),
            deductible=cls._extract_deductible(normalized),
        )
        parsed.coverage_gaps = cls.detect_coverage_gaps(parsed)
        parsed.plain_english_summary = cls.generate_plain_english_summary(parsed)
        return parsed

    @staticmethod
    def detect_coverage_gaps(parsed: ParsedPolicy) -> list[str]:
        """Analyze parsed limits and flag potential coverage gaps."""
        gaps: list[str] = []

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

        if not parsed.uninsured_motorist_limit:
            gaps.append("No uninsured motorist limit was confidently detected. Review this coverage manually.")

        return gaps

    @staticmethod
    def generate_llm_prompt(raw_text: str) -> str:
        return f"""You are an expert auto insurance policy analyst.
Extract the following coverage limits from this Summary of Liability
Insurance Policy (SLIP) document. Return the data in a structured JSON format.

Document text:
{raw_text[:4000]}

Extract these fields:
1. Liability limit (per person / per accident / property damage)
2. Medical payments limit
3. Property damage limit
4. Uninsured/underinsured motorist limit
5. Deductible amount
6. Any coverage gaps or unusual exclusions

Only return fields that are actually supported by the document text.
Do not guess or invent values.
Also provide a plain-English summary of what this policy covers,
as if explaining to the policyholder."""

    @classmethod
    def generate_plain_english_summary(cls, parsed: ParsedPolicy) -> str:
        parts: list[str] = []

        if parsed.liability_limit:
            parts.append(f"Liability coverage appears to be {parsed.liability_limit}.")
        else:
            parts.append("Liability coverage could not be confidently identified.")

        if parsed.property_limit:
            parts.append(f"Property damage coverage appears to be {parsed.property_limit}.")
        if parsed.medical_limit:
            parts.append(f"Medical payments coverage appears to be {parsed.medical_limit}.")
        if parsed.uninsured_motorist_limit:
            parts.append(
                f"Uninsured or underinsured motorist coverage appears to be {parsed.uninsured_motorist_limit}."
            )
        if parsed.deductible:
            parts.append(f"A deductible of {parsed.deductible} was detected.")

        if parsed.coverage_gaps:
            parts.append("Potential gaps were detected and should be reviewed carefully.")
        else:
            parts.append(
                "No obvious gap was detected from the extracted limits, but the full policy should still be reviewed."
            )

        return " ".join(parts)

    @classmethod
    def _extract_liability_limit(cls, text: str) -> Optional[str]:
        for line in text.splitlines():
            if "LIABILITY" in line and "PROPERTY" not in line:
                match = cls.COMBINED_LIMIT_RE.search(line)
                if match:
                    return cls._normalize_money_expression(match.groups())
        return None

    @classmethod
    def _extract_uninsured_motorist_limit(cls, text: str) -> Optional[str]:
        for line in text.splitlines():
            if "UNINSURED" in line or "UNDERINSURED" in line:
                match = cls.COMBINED_LIMIT_RE.search(line)
                if match:
                    return cls._normalize_money_expression(match.groups())
                single = cls.MONEY_RE.search(line)
                if single:
                    return cls._normalize_money(single.group(0))
        return None

    @classmethod
    def _extract_single_limit(cls, text: str, keywords: list[str]) -> Optional[str]:
        for line in text.splitlines():
            if any(keyword in line for keyword in keywords):
                match = cls.MONEY_RE.search(line)
                if match:
                    return cls._normalize_money(match.group(0))
        return None

    @classmethod
    def _extract_deductible(cls, text: str) -> Optional[str]:
        deductibles: list[int] = []
        for line in text.splitlines():
            if "DEDUCT" in line:
                for match in cls.MONEY_RE.findall(line):
                    try:
                        deductibles.append(int(cls._normalize_money(match).replace("$", "").replace(",", "")))
                    except ValueError:
                        continue
        if not deductibles:
            return None
        return f"${min(deductibles):,}"

    @staticmethod
    def _normalize_money(raw: str) -> str:
        digits = raw.replace("$", "").replace(" ", "").replace(",", "")
        value = float(digits)
        if value.is_integer():
            return f"${int(value):,}"
        return f"${value:,.2f}"

    @classmethod
    def _normalize_money_expression(cls, groups: tuple[Optional[str], Optional[str], Optional[str]]) -> str:
        normalized_parts = [cls._normalize_money(part) for part in groups if part]
        return " / ".join(normalized_parts)
