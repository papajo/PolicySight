"""
Coverage Explanation Engine + Policy Evidence Mapper (REQ-002, REQ-003)
Generates per-coverage-type plain-English explanations with source citations and confidence levels.
"""

from pydantic import BaseModel
from typing import Optional

from src.core.policy_decoder import ParsedPolicy
from src.core.safe_failure import analyze_policy_safety


class CoverageExplanation(BaseModel):
    """Plain-English explanation for a single coverage type."""
    coverage_type: str
    limit: Optional[str] = None
    what_is_covered: str
    what_is_not_covered: str
    what_needs_review: str = ""
    confidence: str  # high, medium, low
    source_text: Optional[str] = None
    citation: Optional[str] = None


class CoverageExplanationSet(BaseModel):
    """Complete set of explanations for a parsed policy."""
    explanations: list[CoverageExplanation]
    overall_confidence: str
    safe_failure_assessment: str = ""
    safe_failure_required_info: list[dict] = []
    safe_failure_next_actions: list[dict] = []


class EvidenceAnswer(BaseModel):
    """An answer grounded in policy text with citations."""
    question: str
    answer: str
    citations: list[str]
    confidence: str
    is_assumption: bool
    missing_info: list[str] = []


COVERAGE_KNOWLEDGE = {
    "liability": {
        "covered": "Pays for injuries or property damage you cause to others in an at-fault accident. Includes legal defense costs.",
        "not_covered": "Does not cover your own injuries or damage to your own vehicle. Does not cover intentional acts or business use of your vehicle.",
        "needs_review": "If you have a multi-car policy or umbrella policy, verify whether liability limits are stacked or shared across vehicles.",
    },
    "medical": {
        "covered": "Pays medical expenses for you and your passengers after an accident, regardless of who was at fault. Covers hospital visits, surgery, and follow-up care.",
        "not_covered": "Does not cover lost wages or pain and suffering. Does not cover injuries from non-accident medical events.",
        "needs_review": "Does your health insurance have accident exclusions? MedPay can fill gaps that health insurance may not cover.",
    },
    "property": {
        "covered": "Pays for damage you cause to someone else's property, including their vehicle, fence, building, or other structures.",
        "not_covered": "Does not cover damage to your own vehicle (that requires collision coverage). Does not cover property you borrowed or rented.",
        "needs_review": "If your property damage limit is below $50,000, a multi-vehicle accident could exceed your limit.",
    },
    "um_uim": {
        "covered": "Pays your medical bills and lost wages when you're hit by a driver with no insurance or insufficient insurance. Also covers hit-and-run accidents.",
        "not_covered": "Does not cover property damage to your vehicle in all states. Does not apply if the at-fault driver is identified and adequately insured.",
        "needs_review": "UM/UIM is not required in all states. If declined, confirm you signed a waiver.",
    },
    "collision": {
        "covered": "Pays to repair or replace your vehicle after a collision with another vehicle or object, regardless of fault.",
        "not_covered": "Does not cover non-collision events (theft, vandalism, weather — that's comprehensive). Does not cover wear and tear or mechanical failure.",
        "needs_review": "If your vehicle is worth less than 10x your deductible, collision coverage may not be cost-effective.",
    },
    "comprehensive": {
        "covered": "Pays for damage to your vehicle from non-collision events: theft, vandalism, fire, flood, hail, falling objects, and animal strikes.",
        "not_covered": "Does not cover collision-related damage, mechanical breakdown, or normal wear and tear.",
        "needs_review": "Comprehensive claims are typically not your fault, so rates may not increase as much as collision claims.",
    },
    "rental": {
        "covered": "Pays for a rental car while your vehicle is being repaired after a covered claim. Reimbursement is typically per-day with a maximum total.",
        "not_covered": "Does not cover rental for routine maintenance, wear-and-tear repairs, or voluntary vehicle upgrades.",
        "needs_review": "Check whether the daily limit and maximum days cover your expected repair timeline.",
    },
    "roadside": {
        "covered": "Covers emergency services: towing, flat tire changes, battery jumps, lockout assistance, and fuel delivery.",
        "not_covered": "Does not cover pre-existing mechanical issues, repairs, or roadside services for non-covered vehicles.",
        "needs_review": "Verify whether roadside assistance is per-incident or per-member and whether there's a service call limit.",
    },
}


class CoverageExplainer:
    """Generates per-coverage plain-English explanations with source evidence."""

    @staticmethod
    def explain(parsed: ParsedPolicy) -> CoverageExplanationSet:
        explanations: list[CoverageExplanation] = []
        confidences: list[int] = []

        coverage_map = [
            ("Liability", "liability", parsed.liability_limit, parsed.liability_source, parsed.liability_confidence),
            ("Medical Payments", "medical", parsed.medical_limit, parsed.medical_source, parsed.medical_confidence),
            ("Property Damage", "property", parsed.property_limit, parsed.property_source, parsed.property_confidence),
            ("UM/UIM", "um_uim", parsed.uninsured_motorist_limit, parsed.uninsured_motorist_source, parsed.uninsured_motorist_confidence),
            ("Collision", "collision", parsed.collision_deductible, parsed.collision_deductible_source, "high" if parsed.collision_deductible else "missing"),
            ("Comprehensive", "comprehensive", parsed.comprehensive_deductible, parsed.comprehensive_deductible_source, "high" if parsed.comprehensive_deductible else "missing"),
            ("Rental Reimbursement", "rental", parsed.rental_reimbursement, parsed.rental_reimbursement_source, "high" if parsed.rental_reimbursement else "missing"),
            ("Roadside Assistance", "roadside", parsed.roadside_assistance, parsed.roadside_assistance_source, "high" if parsed.roadside_assistance else "missing"),
        ]

        for display_name, key, limit, source, confidence in coverage_map:
            knowledge = COVERAGE_KNOWLEDGE.get(key, {})
            has_limit = limit is not None

            if has_limit:
                confidence_level = "high" if confidence in ("high", "medium") else "low"
            else:
                confidence_level = "low"

            conf_map = {"high": 3, "medium": 2, "low": 1, "missing": 0}
            confidences.append(conf_map.get(confidence_level, 0))

            display_limit = limit if limit else "Not found in policy"

            explanations.append(CoverageExplanation(
                coverage_type=display_name,
                limit=display_limit,
                what_is_covered=knowledge.get("covered", ""),
                what_is_not_covered=knowledge.get("not_covered", ""),
                what_needs_review=knowledge.get("needs_review", ""),
                confidence=confidence_level,
                source_text=source,
                citation=source[:200] if source else None,
            ))

        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        overall = "high" if avg_conf >= 2.5 else "medium" if avg_conf >= 1.5 else "low"

        safe = analyze_policy_safety(parsed)
        return CoverageExplanationSet(
            explanations=explanations,
            overall_confidence=overall,
            safe_failure_assessment=safe.assessment if safe.overall_status != "determinate" else "",
            safe_failure_required_info=[r.model_dump() for r in safe.required_info],
            safe_failure_next_actions=[a.model_dump() for a in safe.next_actions],
        )

    @staticmethod
    def answer_question(parsed: ParsedPolicy, question: str) -> EvidenceAnswer:
        """
        Answer a natural-language question about the policy using only
        extracted data and known coverage rules. (REQ-002 / REQ-019)
        """
        q = question.lower()
        citations: list[str] = []
        missing_info: list[str] = []
        is_assumption = False

        coverage_keywords = {
            "liability": ("liability_limit", parsed.liability_limit, parsed.liability_source),
            "medical": ("medical_limit", parsed.medical_limit, parsed.medical_source),
            "property": ("property_limit", parsed.property_limit, parsed.property_source),
            "um": ("uninsured_motorist_limit", parsed.uninsured_motorist_limit, parsed.uninsured_motorist_source),
            "uim": ("uninsured_motorist_limit", parsed.uninsured_motorist_limit, parsed.uninsured_motorist_source),
            "uninsured": ("uninsured_motorist_limit", parsed.uninsured_motorist_limit, parsed.uninsured_motorist_source),
            "rental": ("rental_reimbursement", parsed.rental_reimbursement, parsed.rental_reimbursement_source),
            "collision": ("collision_deductible", parsed.collision_deductible, parsed.collision_deductible_source),
            "comprehensive": ("comprehensive_deductible", parsed.comprehensive_deductible, parsed.comprehensive_deductible_source),
            "roadside": ("roadside_assistance", parsed.roadside_assistance, parsed.roadside_assistance_source),
        }

        # Find which coverage type the question is about
        matched_field = None
        matched_label = None
        for keyword, (field, val, src) in coverage_keywords.items():
            if keyword in q:
                matched_field = (field, val, src)
                matched_label = keyword
                break

        if matched_field:
            field_name, val, src = matched_field
            if val:
                answer = f"Your policy shows {field_name.replace('_', ' ')}: {val}."
                if src:
                    citations.append(f"Source: \"{src[:200]}\"")
                confidence = "high"
            else:
                answer = f"Your policy does not appear to include {matched_label} coverage, or it could not be detected."
                is_assumption = False
                missing_info.append(f"{matched_label.replace('_', ' ')} limit was not found in the provided policy text")
                confidence = "low"

        elif "gap" in q or "missing" in q or "weak" in q:
            if parsed.coverage_gaps:
                gaps = [g.detail for g in parsed.coverage_gaps]
                answer = f"{len(parsed.coverage_gaps)} gap(s) detected: " + " ".join(gaps)
            else:
                answer = "No coverage gaps were detected from the extracted limits. Full policy review is still recommended."
            confidence = "medium"

        elif "cover" in q or "am i covered" in q or "do i have" in q:
            # General coverage question without specific type
            found = []
            missing = []
            for label, val in [
                ("Liability", parsed.liability_limit),
                ("Medical payments", parsed.medical_limit),
                ("Property damage", parsed.property_limit),
                ("UM/UIM", parsed.uninsured_motorist_limit),
                ("Collision", parsed.collision_deductible),
                ("Comprehensive", parsed.comprehensive_deductible),
                ("Rental reimbursement", parsed.rental_reimbursement),
            ]:
                if val:
                    found.append(label)
                else:
                    missing.append(label)

            answer = f"Your policy includes: {', '.join(found)}. " if found else "No coverage types could be identified. "
            if missing:
                answer += f"Not detected in this document: {', '.join(missing)}."
            confidence = "medium"
            if not found:
                confidence = "low"

        else:
            answer = f"I found information about {len([f for f in [parsed.liability_limit, parsed.medical_limit, parsed.property_limit, parsed.uninsured_motorist_limit] if f])} coverage types in your policy. Try asking about a specific coverage like liability, collision, or rental."
            is_assumption = False
            confidence = "medium"

        return EvidenceAnswer(
            question=question,
            answer=answer,
            citations=citations,
            confidence=confidence,
            is_assumption=is_assumption,
            missing_info=missing_info,
        )
