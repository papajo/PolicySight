"""
Policy Decoder Service
Handles SLIP document parsing, structured extraction, and coverage analysis.
Each extracted field links back to source text. Missing/unclear fields are flagged.
"""

from __future__ import annotations

import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class SourceCitation(BaseModel):
    """Links an extracted value to its original policy text."""
    value: Optional[str] = None
    source_text: Optional[str] = None
    confidence: str = "missing"  # high, medium, low, missing


class CoverageGap(BaseModel):
    """A detected coverage gap with explanation."""
    field: str
    detail: str
    why_it_matters: str
    potential_consequence: str


class ParsedPolicy(BaseModel):
    # Liability
    liability_limit: Optional[str] = None
    liability_source: Optional[str] = None
    liability_confidence: str = "missing"

    # Medical payments
    medical_limit: Optional[str] = None
    medical_source: Optional[str] = None
    medical_confidence: str = "missing"

    # Property damage
    property_limit: Optional[str] = None
    property_source: Optional[str] = None
    property_confidence: str = "missing"

    # Uninsured / underinsured motorist
    uninsured_motorist_limit: Optional[str] = None
    uninsured_motorist_source: Optional[str] = None
    uninsured_motorist_confidence: str = "missing"

    # Deductibles (collision vs comprehensive)
    collision_deductible: Optional[str] = None
    collision_deductible_source: Optional[str] = None
    comprehensive_deductible: Optional[str] = None
    comprehensive_deductible_source: Optional[str] = None

    # Additional coverages
    rental_reimbursement: Optional[str] = None
    rental_reimbursement_source: Optional[str] = None
    roadside_assistance: Optional[str] = None
    roadside_assistance_source: Optional[str] = None
    loan_lease_payoff: Optional[str] = None
    loan_lease_payoff_source: Optional[str] = None

    # Policy metadata
    policy_number: Optional[str] = None
    named_insured: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    vehicle_year_make_model: Optional[str] = None

    # Exclusions and endorsements
    exclusions: list[str] = []
    endorsements: list[str] = []

    # Analysis
    coverage_gaps: list[CoverageGap] = []
    missing_fields: list[str] = []
    unclear_fields: list[str] = []
    plain_english_summary: str = ""
    raw_text: str = ""

    # Safe failure mode (PDF REQ-017)
    safe_failure_overall_status: str = ""
    safe_failure_assessment: str = ""
    safe_failure_required_info: list[dict] = []
    safe_failure_next_actions: list[dict] = []

    # OCR confidence (FDE Test Case #6)
    ocr_confidence: str = "high"
    ocr_issues: list[dict] = []

    # Endorsement conflicts (FDE Test Case #7)
    endorsement_conflicts: list[dict] = []


class PolicyDecoder:
    """
    Core service for decoding insurance policy documents.
    Uses deterministic regex extraction with source-text tracking.
    """

    NATIONAL_AVERAGES = {
        "liability": "$250,000 / $500,000 / $250,000",
        "medical": "$50,000",
        "property": "$25,000",
        "uninsured_motorist": "$100,000",
        "rental": "$30/day $900 max",
    }

    MONEY_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?")
    DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})|(\d{4}-\d{2}-\d{2})")
    COMBINED_LIMIT_RE = re.compile(
        r"(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?)"
        r"(?:\s*(?:each\s+person|per\s+person))?\s*/\s*"
        r"(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?)"
        r"(?:\s*(?:each\s+accident|per\s+accident))?"
        r"(?:\s*/\s*(\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s?\d+(?:\.\d{2})?))?",
        re.IGNORECASE,
    )
    POLICY_NUMBER_RE = re.compile(r"(?:policy\s*(?:#|no|number|num)[:\s]*)\s*([A-Z0-9\-/]{5,30})", re.IGNORECASE)
    EFFECTIVE_RE = re.compile(r"(?:effective|from|period)[:\s]*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
    EXPIRATION_RE = re.compile(r"(?:expir|to|through|until)[:\s]*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)

    OCR_KEYWORD_NORMALIZATIONS = {
        "L1MIT": "LIMIT", "L1M1T": "LIMIT",
        "L1AB1LITY": "LIABILITY", "LIAB1LITY": "LIABILITY",
        "LNJURY": "INJURY", "M0TORIST": "MOTORIST",
        "PR0PERTY": "PROPERTY", "C0LLISION": "COLLISION",
        "COLLISI0N": "COLLISION",
        "DEDUCT1BLE": "DEDUCTIBLE", "DEDUCTIB1E": "DEDUCTIBLE",
        "C0MPREHENSIVE": "COMPREHENSIVE",
        "B.L.": "BODILY INJURY",
        "RENTAL REIMBURSEMENT": "RENTAL",
        "R0ADSIDE": "ROADSIDE",
        "LNCLUDED": "INCLUDED",
        "LOAN/LEASE": "LOAN LEASE",
    }

    EXCLUSION_KEYWORDS = [
        "EXCLUSION", "THIS POLICY DOES NOT COVER", "NOT COVERED",
        "EXCLUDED", "WE WILL NOT PAY", "NO COVERAGE",
    ]
    ENDORSEMENT_KEYWORDS = [
        "ENDORSEMENT", "AMENDATORY", "THIS ENDORSEMENT CHANGES",
        "SCHEDULED PERSONAL PROPERTY",
    ]

    GAP_DESCRIPTIONS = {
        "low_liability": {
            "why_it_matters": "Low liability limits leave your assets at risk if you cause a serious accident.",
            "consequence": "You could be personally sued for damages exceeding your limit.",
        },
        "missing_um": {
            "why_it_matters": "Without UM/UIM, you have no coverage if an uninsured driver hits you.",
            "consequence": "You pay out-of-pocket for injuries and damages caused by an uninsured motorist.",
        },
        "missing_rental": {
            "why_it_matters": "Without rental reimbursement, you pay for a replacement car out-of-pocket while yours is being repaired.",
            "consequence": "Could cost $30-50/day for weeks during repairs.",
        },
        "high_deductible": {
            "why_it_matters": "A high deductible means more out-of-pocket cost before insurance kicks in.",
            "consequence": "A $2,000 deductible on a $5,000 claim leaves you paying 40%.",
        },
        "low_property": {
            "why_it_matters": "Low property damage limits may not cover the full cost of a vehicle you damage.",
            "consequence": "You could be personally liable for the difference if you cause a multi-vehicle accident.",
        },
        "missing_medical": {
            "why_it_matters": "Without medical payments coverage, your health insurance and out-of-pocket costs cover accident injuries.",
            "consequence": "Could lead to significant medical bills not covered by health plans.",
        },
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
        lines = normalized.splitlines()

        parsed = ParsedPolicy(raw_text=raw_text)

        # Liability
        liab_val, liab_src, liab_conf = cls._extract_liability(normalized, lines)
        parsed.liability_limit = liab_val
        parsed.liability_source = liab_src
        parsed.liability_confidence = liab_conf

        # Medical
        med_val, med_src, med_conf = cls._extract_field(normalized, lines, ["MEDICAL PAYMENTS", "MEDICAL LIMIT", "MED PAY", "PIP"])
        parsed.medical_limit = med_val
        parsed.medical_source = med_src
        parsed.medical_confidence = med_conf

        # Property damage
        prop_val, prop_src, prop_conf = cls._extract_field(normalized, lines, ["PROPERTY DAMAGE LIABILITY", "PROPERTY DAMAGE", "PROPERTY LIMIT"])
        parsed.property_limit = prop_val
        parsed.property_source = prop_src
        parsed.property_confidence = prop_conf

        # UM/UIM
        um_val, um_src, um_conf = cls._extract_uninsured(normalized, lines)
        parsed.uninsured_motorist_limit = um_val
        parsed.uninsured_motorist_source = um_src
        parsed.uninsured_motorist_confidence = um_conf

        # Deductibles (collision vs comprehensive)
        coll_val, coll_src = cls._extract_deductible(lines, "COLLISION")
        parsed.collision_deductible = coll_val
        parsed.collision_deductible_source = coll_src
        comp_val, comp_src = cls._extract_deductible(lines, "COMPREHENSIVE")
        parsed.comprehensive_deductible = comp_val
        parsed.comprehensive_deductible_source = comp_src
        if not parsed.collision_deductible:
            gen_val, gen_src = cls._extract_generic_deductible(lines)
            parsed.collision_deductible = gen_val
            parsed.collision_deductible_source = gen_src

        # Additional coverages
        rent_val, rent_src, _ = cls._extract_field(normalized, lines, ["RENTAL", "RENTAL REIMBURSEMENT", "TRANSPORTATION EXPENSE"])
        parsed.rental_reimbursement = rent_val
        parsed.rental_reimbursement_source = rent_src
        road_val, road_src, _ = cls._extract_field(normalized, lines, ["ROADSIDE", "TOWING", "EMERGENCY ROAD"])
        parsed.roadside_assistance = road_val
        parsed.roadside_assistance_source = road_src
        loan_val, loan_src, _ = cls._extract_field(normalized, lines, ["LOAN/LEASE", "GAP", "LOAN LEASE"])
        parsed.loan_lease_payoff = loan_val
        parsed.loan_lease_payoff_source = loan_src

        # Policy metadata
        parsed.policy_number = cls._extract_policy_number(lines)
        parsed.effective_date, parsed.expiration_date = cls._extract_dates(lines)

        # Exclusions and endorsements
        parsed.exclusions = cls._extract_sections(normalized, cls.EXCLUSION_KEYWORDS)
        parsed.endorsements = cls._extract_sections(normalized, cls.ENDORSEMENT_KEYWORDS)

        # Missing field flags
        parsed.missing_fields = cls._find_missing_fields(parsed)
        parsed.unclear_fields = cls._find_unclear_fields(parsed)

        # Coverage gaps
        parsed.coverage_gaps = cls.detect_coverage_gaps(parsed)

        # Summary
        parsed.plain_english_summary = cls.generate_plain_english_summary(parsed)

        return parsed

    @classmethod
    def _extract_liability(cls, text: str, lines: list[str]) -> tuple[Optional[str], Optional[str], str]:
        for i, line in enumerate(lines):
            if "LIABILITY" in line and "PROPERTY" not in line:
                match = cls.COMBINED_LIMIT_RE.search(line)
                if match:
                    return cls._normalize_money_expression(match.groups()), line, "high"
                # Limit often on the next line after coverage name
                for j in range(i + 1, min(i + 4, len(lines))):
                    match = cls.COMBINED_LIMIT_RE.search(lines[j])
                    if match:
                        return cls._normalize_money_expression(match.groups()), lines[j], "medium"
                return None, line, "low"
        return None, None, "missing"

    @classmethod
    def _extract_uninsured(cls, text: str, lines: list[str]) -> tuple[Optional[str], Optional[str], str]:
        for i, line in enumerate(lines):
            if "UNINSURED" in line or "UNDERINSURED" in line:
                match = cls.COMBINED_LIMIT_RE.search(line)
                if match:
                    return cls._normalize_money_expression(match.groups()), line, "high"
                single = cls.MONEY_RE.search(line)
                if single:
                    return cls._normalize_money(single.group(0)), line, "medium"
                # Limit often on the next line after coverage name
                for j in range(i + 1, min(i + 4, len(lines))):
                    match = cls.COMBINED_LIMIT_RE.search(lines[j])
                    if match:
                        return cls._normalize_money_expression(match.groups()), lines[j], "medium"
                    single = cls.MONEY_RE.search(lines[j])
                    if single:
                        return cls._normalize_money(single.group(0)), lines[j], "low"
                return None, line, "low"
        return None, None, "missing"

    @classmethod
    def _extract_field(cls, text: str, lines: list[str], keywords: list[str]) -> tuple[Optional[str], Optional[str], str]:
        for i, line in enumerate(lines):
            if any(k in line for k in keywords):
                matches = cls.MONEY_RE.findall(line)
                if matches:
                    val = cls._normalize_money_expression(matches)
                    return val, line, "high"
                # Try next 2 lines (coverage name and limit often on separate lines in OCR output)
                for j in range(i + 1, min(i + 3, len(lines))):
                    matches = cls.MONEY_RE.findall(lines[j])
                    if matches:
                        val = cls._normalize_money_expression(matches)
                        return val, lines[j], "medium"
                return None, line, "low"
        return None, None, "missing"

    @classmethod
    def _extract_deductible(cls, lines: list[str], coverage_type: str) -> tuple[Optional[str], Optional[str]]:
        for i, line in enumerate(lines):
            if coverage_type in line:
                if "DEDUCT" in line:
                    match = cls.MONEY_RE.search(line)
                    if match:
                        return cls._normalize_money(match.group(0)), line
                # Deductible often on the next line after coverage name
                for j in range(i + 1, min(i + 4, len(lines))):
                    if "DEDUCT" in lines[j]:
                        match = cls.MONEY_RE.search(lines[j])
                        if match:
                            return cls._normalize_money(match.group(0)), lines[j]
        return None, None

    @classmethod
    def _extract_generic_deductible(cls, lines: list[str]) -> tuple[Optional[str], Optional[str]]:
        values: list[tuple[int, str, str]] = []
        for line in lines:
            if "DEDUCT" in line:
                for match in cls.MONEY_RE.findall(line):
                    try:
                        val = int(match.replace("$", "").replace(",", "").replace(" ", ""))
                        values.append((val, line, match))
                    except ValueError:
                        continue
        if values:
            best = min(values, key=lambda x: x[0])
            return cls._normalize_money(best[2]), best[1]
        return None, None

    @classmethod
    def _extract_policy_number(cls, lines: list[str]) -> Optional[str]:
        for line in lines:
            match = cls.POLICY_NUMBER_RE.search(line)
            if match:
                return match.group(1)
        return None

    @classmethod
    def _extract_dates(cls, lines: list[str]) -> tuple[Optional[str], Optional[str]]:
        eff, exp = None, None
        for line in lines:
            if not eff:
                m = cls.EFFECTIVE_RE.search(line)
                if m:
                    eff = m.group(1)
            if not exp:
                m = cls.EXPIRATION_RE.search(line)
                if m:
                    exp = m.group(1)
        return eff, exp

    @classmethod
    def _extract_sections(cls, text: str, keywords: list[str]) -> list[str]:
        found: list[str] = []
        for line in text.splitlines():
            if any(k in line for k in keywords):
                found.append(line.strip())
        return found[:10]

    @classmethod
    def _find_missing_fields(cls, parsed: ParsedPolicy) -> list[str]:
        missing = []
        checks = [
            ("liability_limit", "Liability coverage"),
            ("property_limit", "Property damage coverage"),
            ("medical_limit", "Medical payments coverage"),
            ("uninsured_motorist_limit", "UM/UIM coverage"),
            ("collision_deductible", "Collision deductible"),
        ]
        for attr, label in checks:
            if getattr(parsed, attr) is None:
                missing.append(f"{label} was not found in the document")
        return missing

    @classmethod
    def _find_unclear_fields(cls, parsed: ParsedPolicy) -> list[str]:
        unclear = []
        conf_checks = [
            ("liability_confidence", "Liability limit"),
            ("medical_confidence", "Medical payments limit"),
            ("property_confidence", "Property damage limit"),
        ]
        for attr, label in conf_checks:
            if getattr(parsed, attr) == "low":
                unclear.append(f"{label} was detected with low confidence — verify manually")
        return unclear

    @staticmethod
    def detect_coverage_gaps(parsed: ParsedPolicy) -> list[CoverageGap]:
        gaps: list[CoverageGap] = []

        if parsed.property_limit:
            try:
                val = int(parsed.property_limit.replace("$", "").replace(",", ""))
                if val < 50000:
                    info = PolicyDecoder.GAP_DESCRIPTIONS["low_property"]
                    gaps.append(CoverageGap(
                        field="property_limit",
                        detail=f"Property damage limit of ${val:,} is below recommended $50,000 minimum.",
                        why_it_matters=info["why_it_matters"],
                        potential_consequence=info["consequence"],
                    ))
            except (ValueError, AttributeError):
                pass

        if not parsed.uninsured_motorist_limit:
            info = PolicyDecoder.GAP_DESCRIPTIONS["missing_um"]
            gaps.append(CoverageGap(
                field="uninsured_motorist_limit",
                detail="No uninsured/underinsured motorist coverage confidently detected.",
                why_it_matters=info["why_it_matters"],
                potential_consequence=info["consequence"],
            ))

        if not parsed.rental_reimbursement:
            info = PolicyDecoder.GAP_DESCRIPTIONS["missing_rental"]
            gaps.append(CoverageGap(
                field="rental_reimbursement",
                detail="No rental reimbursement coverage detected.",
                why_it_matters=info["why_it_matters"],
                potential_consequence=info["consequence"],
            ))

        if not parsed.medical_limit:
            info = PolicyDecoder.GAP_DESCRIPTIONS["missing_medical"]
            gaps.append(CoverageGap(
                field="medical_limit",
                detail="No medical payments coverage detected.",
                why_it_matters=info["why_it_matters"],
                potential_consequence=info["consequence"],
            ))

        if not parsed.roadside_assistance:
            info = PolicyDecoder.GAP_DESCRIPTIONS.get("missing_roadside", {
                "why_it_matters": "Roadside assistance provides towing, flat tire, lockout, and battery jump services.",
                "consequence": "Without roadside, a single tow could cost $100-$250 out of pocket in an emergency.",
            })
            gaps.append(CoverageGap(
                field="roadside_assistance",
                detail="No roadside assistance coverage detected.",
                why_it_matters=info.get("why_it_matters", ""),
                potential_consequence=info.get("consequence", ""),
            ))

        if not parsed.loan_lease_payoff:
            info = PolicyDecoder.GAP_DESCRIPTIONS.get("missing_gap", {
                "why_it_matters": "Gap/loan-lease coverage pays the difference between ACV and loan balance after a total loss.",
                "consequence": "Without gap coverage, you could owe thousands if your car is totaled and you owe more than it's worth.",
            })
            gaps.append(CoverageGap(
                field="loan_lease_payoff",
                detail="No loan/lease payoff (gap) coverage detected.",
                why_it_matters=info.get("why_it_matters", ""),
                potential_consequence=info.get("consequence", ""),
            ))

        if parsed.collision_deductible:
            try:
                val = int(parsed.collision_deductible.replace("$", "").replace(",", ""))
                if val > 1000:
                    info = PolicyDecoder.GAP_DESCRIPTIONS["high_deductible"]
                    gaps.append(CoverageGap(
                        field="collision_deductible",
                        detail=f"Collision deductible of ${val:,} is considered high.",
                        why_it_matters=info["why_it_matters"],
                        potential_consequence=info["consequence"],
                    ))
            except (ValueError, AttributeError):
                pass

        if parsed.collision_deductible and parsed.comprehensive_deductible:
            try:
                col = int(parsed.collision_deductible.replace("$", "").replace(",", ""))
                comp = int(parsed.comprehensive_deductible.replace("$", "").replace(",", ""))
                if col >= comp * 2:
                    gaps.append(CoverageGap(
                        field="deductible_mismatch",
                        detail=f"Collision deductible (${col:,}) is much higher than comprehensive (${comp:,}).",
                        why_it_matters="A large gap between deductibles can create confusion about which coverage applies.",
                        potential_consequence="Filing under the wrong coverage could mean paying a higher deductible than necessary.",
                    ))
            except (ValueError, AttributeError):
                pass

        if parsed.liability_limit:
            try:
                parts = parsed.liability_limit.replace("$", "").replace(",", "").split("/")
                per_person = float(parts[0].strip())
                if per_person < 50000:
                    gaps.append(CoverageGap(
                        field="liability_limit",
                        detail=f"Liability limit of ${per_person:,.0f} per person is below recommended $100,000.",
                        why_it_matters="Low liability limits leave personal assets at risk in a serious accident.",
                        potential_consequence="You could be personally sued for amounts above your policy limits.",
                    ))
            except (ValueError, IndexError, AttributeError):
                pass

        if not parsed.exclusions or len(parsed.exclusions) <= 1:
            gaps.append(CoverageGap(
                field="exclusions",
                detail="Few or no exclusions detected in the policy text.",
                why_it_matters="Policies always have exclusions — missing exclusions may indicate incomplete document parsing.",
                potential_consequence="Critical coverage limitations may be overlooked during claim evaluation.",
            ))

        return gaps

    @staticmethod
    def generate_plain_english_summary(parsed: ParsedPolicy) -> str:
        parts: list[str] = []
        found = 0

        if parsed.liability_limit:
            parts.append(f"Liability coverage: {parsed.liability_limit}.")
            found += 1
        if parsed.property_limit:
            parts.append(f"Property damage: {parsed.property_limit}.")
            found += 1
        if parsed.medical_limit:
            parts.append(f"Medical payments: {parsed.medical_limit}.")
            found += 1
        if parsed.uninsured_motorist_limit:
            parts.append(f"UM/UIM: {parsed.uninsured_motorist_limit}.")
            found += 1
        if parsed.collision_deductible:
            parts.append(f"Collision deductible: {parsed.collision_deductible}.")
            found += 1
        if parsed.comprehensive_deductible:
            parts.append(f"Comprehensive deductible: {parsed.comprehensive_deductible}.")
            found += 1
        if parsed.rental_reimbursement:
            parts.append(f"Rental reimbursement: {parsed.rental_reimbursement}.")
            found += 1
        if parsed.roadside_assistance:
            parts.append("Roadside assistance included.")
            found += 1

        if found == 0:
            parts.append("No coverage limits could be confidently extracted from this document.")

        if parsed.missing_fields:
            parts.append(f"Note: {len(parsed.missing_fields)} coverage area(s) were not found and need manual review.")

        gap_count = len(parsed.coverage_gaps)
        if gap_count > 0:
            parts.append(f"{gap_count} coverage gap(s) detected — see details below.")

        return " ".join(parts)

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
5. Deductible amount (collision and comprehensive separately if visible)
6. Rental reimbursement coverage
7. Policy effective and expiration dates
8. Any coverage gaps or unusual exclusions

Only return fields that are actually supported by the document text.
Do not guess or invent values.
Also provide a plain-English summary of what this policy covers,
as if explaining to the policyholder."""

    @staticmethod
    def _normalize_money(raw: str) -> str:
        digits = raw.replace("$", "").replace(" ", "").replace(",", "")
        value = float(digits)
        return f"${int(value):,}" if value.is_integer() else f"${value:,.2f}"

    @classmethod
    def _normalize_money_expression(cls, groups: tuple[Optional[str], Optional[str], Optional[str]]) -> str:
        normalized_parts = [cls._normalize_money(part) for part in groups if part]
        return " / ".join(normalized_parts)
