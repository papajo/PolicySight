"""
Edge Case Classifier (PDF REQ-010)
Detects messy real-world insurance situations and flags risks.
Maps directly to testing-scenarios.txt cases.
"""

from typing import Optional
from pydantic import BaseModel

from src.core.policy_decoder import ParsedPolicy


class EdgeCaseFlag(BaseModel):
    scenario_type: str
    severity: str  # high, medium, low
    detected: bool
    title: str
    description: str
    risk: str
    recommendation: str
    applies: bool = False


class EdgeCaseResult(BaseModel):
    description: str
    flags: list[EdgeCaseFlag]
    primary_concern: Optional[str] = None
    requires_underwriting: bool = False
    requires_supervisor: bool = False


# Each rule maps to scenarios from testing-scenarios.txt
EDGE_CASE_RULES = [
    {
        "id": "delivery_rideshare",
        "scenario_type": "commercial_delivery",
        "title": "Rideshare / Delivery Use",
        "keywords": ["doordash", "uber", "lyft", "delivery", "rideshare", "food delivery", "gig", "instacart", "grubhub", "postmates", "driving for", "working for"],
        "severity": "high",
        "description": "Personal auto policies generally exclude commercial delivery or rideshare activities.",
        "risk": "Your claim could be denied if you were logged into a delivery or rideshare app at the time of the accident.",
        "recommendation": "Check whether a rideshare/delivery endorsement exists on the policy. If not, ask the carrier about coverage gaps during app-on periods. Platform liability coverage may apply while actively on a trip.",
        "scenario_ref": 4,
    },
    {
        "id": "borrowed_vehicle",
        "scenario_type": "permissive_use",
        "title": "Borrowed / Non-Owned Vehicle",
        "keywords": ["borrowed", "borrowing", "friend's car", "rental", "driving someone else's", "not my car", "other person's car", "someone else's car"],
        "severity": "medium",
        "description": "Insurance typically follows the vehicle first, not the driver. The vehicle owner's policy is primary.",
        "risk": "If the owner's insurance is insufficient or denies coverage, your policy may provide excess coverage — but only if you have non-owned auto liability.",
        "recommendation": "File a claim under the vehicle owner's policy first. Your personal policy may act as secondary/excess coverage. Verify permission was given.",
        "scenario_ref": 3,
    },
    {
        "id": "excluded_driver",
        "scenario_type": "excluded_driver",
        "title": "Excluded Household Driver",
        "keywords": ["excluded", "household", "not listed", "roommate", "family member not on policy", "other driver lives with me", "not on my policy"],
        "severity": "high",
        "description": "If a driver is specifically excluded on the policy, there is likely NO coverage if they cause an accident using your vehicle.",
        "risk": "Named-driver exclusion bars all coverage when the excluded driver is operating the vehicle. This can result in a complete denial and potential personal liability.",
        "recommendation": "Confirm whether the driver is listed on the declarations page or an exclusion endorsement. If excluded, do not permit them to drive your vehicle.",
        "scenario_ref": 9,
    },
    {
        "id": "unauthorized_use",
        "scenario_type": "unauthorized_use",
        "title": "Unauthorized Use / Theft by Known Person",
        "keywords": ["without permission", "unauthorized", "took my car", "drove without asking", "stole my keys", "took without consent", "didn't have permission"],
        "severity": "high",
        "description": "If someone drove your vehicle without permission, coverage may be denied depending on the relationship and prior access.",
        "risk": "Insurers may treat this as theft (comprehensive claim) or deny coverage if the driver had prior permission or household access.",
        "recommendation": "File a police report immediately. Indicate whether the driver had prior permission or regular access to the vehicle.",
        "scenario_ref": 8,
    },
    {
        "id": "hit_and_run",
        "scenario_type": "hit_and_run",
        "title": "Hit-and-Run / Unidentified Driver",
        "keywords": ["hit and run", "hit-and-run", "fled", "drove off", "didn't stop", "left the scene", "unknown driver", "no note", "can't find"],
        "severity": "medium",
        "description": "Coverage for hit-and-run depends on whether you have collision or uninsured motorist property damage coverage.",
        "risk": "Not all states allow UMPD for hit-and-run. Physical contact between vehicles is often required for UM/UIM claims.",
        "recommendation": "Check collision and UMPD coverage. File a police report. If you have collision, your deductible applies but may be waived under some UMPD laws.",
        "scenario_ref": 2,
    },
    {
        "id": "late_reporting",
        "scenario_type": "late_notice",
        "title": "Late Reported Accident",
        "keywords": ["weeks ago", "last month", "late", "didn't report", "forgot to report", "just found", "a while ago", "delayed"],
        "severity": "medium",
        "description": "Most policies require prompt notice of an accident or claim. Late reporting can jeopardize coverage.",
        "risk": "If the delay prejudiced the insurer's ability to investigate, they may deny coverage. The longer the delay, the higher the risk.",
        "recommendation": "Report the claim immediately. Provide a reasonable explanation for the delay. The insurer must show prejudice to deny in many states.",
        "scenario_ref": 15,
    },
    {
        "id": "total_loss_gap",
        "scenario_type": "total_loss",
        "title": "Total Loss / Loan Balance Gap",
        "keywords": ["total loss", "totaled", "loan balance", "owe more", "upside down", "negative equity", "gap", "payoff", "still owe"],
        "severity": "high",
        "description": "Standard auto insurance pays Actual Cash Value (ACV), not the loan payoff amount. If ACV is less than the loan balance, you owe the difference.",
        "risk": "Without gap coverage or a loan/lease payoff endorsement, you could owe thousands out of pocket after a total loss.",
        "recommendation": "Check whether the policy includes gap/loan-lease payoff coverage. If not, you may need to pay the difference between ACV and the loan balance.",
        "scenario_ref": 12,
    },
    {
        "id": "aftermarket_parts",
        "scenario_type": "custom_equipment",
        "title": "Aftermarket / Custom Parts",
        "keywords": ["aftermarket", "custom", "modified", "upgraded", "aftermarket parts", "accessories", "rims", "stereo", "lift kit", "tinted"],
        "severity": "medium",
        "description": "Standard policies provide limited coverage for aftermarket parts and custom equipment unless specifically endorsed.",
        "risk": "Aftermarket parts may only be covered up to a small sub-limit ($1,000-$5,000) unless you have a custom equipment endorsement.",
        "recommendation": "Check for a custom parts/equipment endorsement. If modifications exceed your policy's sub-limit, consider adding coverage.",
        "scenario_ref": 11,
    },
    {
        "id": "glass_damage",
        "scenario_type": "glass_claim",
        "title": "Windshield / Glass Damage",
        "keywords": ["windshield", "crack", "chip", "glass", "rock", "debris", "shattered"],
        "severity": "low",
        "description": "Glass damage is typically covered under comprehensive, but deductible rules vary by state.",
        "risk": "Some states have $0 glass deductible laws. In others, the full comprehensive deductible applies.",
        "recommendation": "Comprehensive coverage should apply. Check whether your state has a separate glass deductible or full-glass endorsement.",
        "scenario_ref": 14,
    },
    {
        "id": "medical_state_rules",
        "scenario_type": "medical_coverage",
        "title": "Medical Bills / PIP State Rules",
        "keywords": ["medical bills", "hospital", "ambulance", "injury", "pip", "no-fault", "medpay"],
        "severity": "medium",
        "description": "Medical coverage after an accident depends on state no-fault/PIP rules, MedPay limits, and health insurance coordination.",
        "risk": "In no-fault states, PIP pays first regardless of fault. In tort states, MedPay or health insurance may apply. Coordination of benefits can be complex.",
        "recommendation": "Check whether your state is no-fault or tort. Verify PIP/MedPay limits. Medical bills may need to be submitted to health insurance first in some states.",
        "scenario_ref": 13,
    },
    {
        "id": "rental_while_traveling",
        "scenario_type": "rental_exposure",
        "title": "Rental Car While Traveling",
        "keywords": ["rental car", "rental while traveling", "on vacation", "out of state", "hertz", "avis", "enterprise", "turo"],
        "severity": "medium",
        "description": "Your personal auto policy may extend coverage to rental cars, but limitations apply for territory, business use, and loss-of-use fees.",
        "risk": "Some policies limit rental coverage to the U.S. and Canada. Loss-of-use and administrative fees charged by rental companies may not be covered.",
        "recommendation": "Check whether your policy covers rental cars and confirm territorial limits. Credit card coverage may provide secondary protection. Consider the rental company's LDW.",
        "scenario_ref": 10,
    },
]


def classify_edge_cases(
    parsed: ParsedPolicy,
    scenario_text: str,
) -> EdgeCaseResult:
    """Classify a scenario against known edge case patterns."""
    s = scenario_text.lower()
    flags: list[EdgeCaseFlag] = []
    has_high = False

    for rule in EDGE_CASE_RULES:
        detected = any(kw in s for kw in rule["keywords"])
        if detected:
            flag = EdgeCaseFlag(
                scenario_type=rule["scenario_type"],
                severity=rule["severity"],
                detected=True,
                title=rule["title"],
                description=rule["description"],
                risk=rule["risk"],
                recommendation=rule["recommendation"],
                applies=True,
            )
            flags.append(flag)
            if rule["severity"] == "high":
                has_high = True

    # If no specific edge case matched, return a summary
    if not flags:
        flags.append(EdgeCaseFlag(
            scenario_type="general",
            severity="low",
            detected=False,
            title="No Edge Cases Detected",
            description="The scenario does not match known edge case patterns.",
            risk="Standard coverage rules apply.",
            recommendation="Proceed with normal claim handling procedures.",
            applies=False,
        ))

    primary = None
    high_flags = [f for f in flags if f.severity == "high"]
    if high_flags:
        primary = high_flags[0].title
    elif flags:
        primary = flags[0].title

    return EdgeCaseResult(
        description=scenario_text,
        flags=flags,
        primary_concern=primary,
        requires_underwriting=has_high,
        requires_supervisor=has_high,
    )
