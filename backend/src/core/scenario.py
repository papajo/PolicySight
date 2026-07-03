"""
Scenario-Based Coverage Check (REQ-006)
Evaluates natural-language scenarios against parsed policy data.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class ScenarioResult(BaseModel):
    """Result of evaluating a scenario against a policy."""
    scenario: str
    summary: str
    coverages: list[dict]
    deductible: Optional[str] = None
    limitations: list[str] = []
    is_covered: bool
    confidence: str
    citations: list[str] = []


SCENARIO_RULES = {
    "collision": {
        "keywords": ["hit", "crash", "collision", "accident", "rear-end", "rear ended", "side-swiped", "sideswiped", "fender bender", "wreck"],
        "coverage_type": "collision",
        "deductible_field": "collision_deductible",
        "cover": lambda p: p.collision_deductible is not None,
        "cover_text": "Collision",
        "extends_to": [],
    },
    "comprehensive": {
        "keywords": ["deer", "hail", "flood", "fire", "theft", "stolen", "vandalism", "tree", "animal", "fallen object", "windstorm", "lightning", "explosion", "riot", "missile"],
        "coverage_type": "comprehensive",
        "deductible_field": "comprehensive_deductible",
        "cover": lambda p: p.comprehensive_deductible is not None,
        "cover_text": "Comprehensive",
        "extends_to": [],
    },
    "liability": {
        "keywords": ["sue", "sued", "lawsuit", "injury to others", "i hit someone", "i injured someone", "damage to their car", "other driver", "at fault"],
        "coverage_type": "liability",
        "deductible_field": None,
        "cover": lambda p: p.liability_limit is not None,
        "cover_text": "Liability",
        "extends_to": [],
    },
    "medical": {
        "keywords": ["hospital", "medical bill", "ambulance", "doctor", "surgery", "injury", "injured", "my medical", "my injury"],
        "coverage_type": "medical",
        "deductible_field": None,
        "cover": lambda p: p.medical_limit is not None,
        "cover_text": "Medical Payments",
        "extends_to": [],
    },
    "uninsured": {
        "keywords": ["uninsured", "hit and run", "hit-and-run", "no insurance", "underinsured"],
        "coverage_type": "um_uim",
        "deductible_field": None,
        "cover": lambda p: p.uninsured_motorist_limit is not None,
        "cover_text": "Uninsured/Underinsured Motorist",
        "extends_to": [],
    },
    "rental": {
        "keywords": ["rental car", "rental", "loaner", "need a car", "transportation"],
        "coverage_type": "rental",
        "deductible_field": None,
        "cover": lambda p: p.rental_reimbursement is not None,
        "cover_text": "Rental Reimbursement",
        "extends_to": [],
    },
    "roadside": {
        "keywords": ["tow", "towing", "flat tire", "battery", "jump start", "lockout", "locked out", "fuel", "out of gas", "stranded"],
        "coverage_type": "roadside",
        "deductible_field": None,
        "cover": lambda p: p.roadside_assistance is not None,
        "cover_text": "Roadside Assistance",
        "extends_to": [],
    },
}


def evaluate_scenario(parsed: ParsedPolicy, scenario_text: str) -> ScenarioResult:
    """
    Evaluate a natural-language scenario against a parsed policy.
    Returns what coverages apply, deductibles, and limitations.
    """
    s = scenario_text.lower()
    matched: list[dict] = []
    limitations: list[str] = []
    citations: list[str] = []

    for rule_id, rule in SCENARIO_RULES.items():
        if any(kw in s for kw in rule["keywords"]):
            is_covered = rule["cover"](parsed)
            deductible = None
            if rule["deductible_field"]:
                val = getattr(parsed, rule["deductible_field"], None)
                if val:
                    deductible = val

            matched.append({
                "coverage": rule["cover_text"],
                "covered": is_covered,
                "deductible": deductible,
                "details": _get_coverage_detail(parsed, rule, is_covered),
            })

            if is_covered:
                citations.append(f"{rule['cover_text']}: {deductible or 'included'} — {_get_source(parsed, rule['coverage_type'])}")
            else:
                limitations.append(f"{rule['cover_text']} is not detected in your policy")

    if not matched:
        # No specific scenario matched — classify by general keywords
        for rule_id, rule in SCENARIO_RULES.items():
            is_covered = rule["cover"](parsed)
            matched.append({
                "coverage": rule["cover_text"],
                "covered": is_covered,
                "deductible": getattr(parsed, rule["deductible_field"], None) if rule["deductible_field"] else None,
                "details": _get_coverage_detail(parsed, rule, is_covered),
            })

    is_any_covered = any(m["covered"] for m in matched)
    covered_count = sum(1 for m in matched if m["covered"])

    if is_any_covered:
        summary = f"Based on your policy, {covered_count} coverage type(s) may apply to this scenario."
    else:
        summary = "This scenario does not appear to be covered by your current policy limits."

    deductibles = [m["deductible"] for m in matched if m.get("deductible")]
    primary_deductible = deductibles[0] if deductibles else None

    return ScenarioResult(
        scenario=scenario_text,
        summary=summary,
        coverages=matched,
        deductible=primary_deductible,
        limitations=limitations,
        is_covered=is_any_covered,
        confidence="high" if is_any_covered else "medium",
        citations=[c for c in citations if c],
    )


def _get_source(parsed: ParsedPolicy, coverage_type: str) -> str:
    mapping = {
        "collision": parsed.collision_deductible_source,
        "comprehensive": parsed.comprehensive_deductible_source,
        "liability": parsed.liability_source,
        "medical": parsed.medical_source,
        "um_uim": parsed.uninsured_motorist_source,
        "rental": parsed.rental_reimbursement_source,
        "roadside": parsed.roadside_assistance_source,
    }
    src = mapping.get(coverage_type)
    return f"Source: \"{src[:200]}\"" if src else ""


def _get_coverage_detail(parsed: ParsedPolicy, rule: dict, is_covered: bool) -> str:
    if is_covered:
        return f"Your policy includes this coverage. Applicable limits and deductibles are shown above."
    return f"Your policy does not appear to include this coverage, or it could not be detected in the provided text."
