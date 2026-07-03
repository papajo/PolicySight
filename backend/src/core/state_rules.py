"""
State-Specific Rules Layer (PDF REQ-013)
Applies state-specific auto insurance rules separated from AI reasoning.
"""

from typing import Optional
from pydantic import BaseModel


class StateRule(BaseModel):
    state: str
    state_name: str
    is_no_fault: bool
    requires_pip: bool
    pip_min_limit: Optional[str] = None
    requires_um_uim: bool
    um_uim_min_limit: Optional[str] = None
    requires_medpay: bool = False
    glass_deductible_rule: str = ""  # "full_deductible", "separate_glass", "zero_deductible"
    small_claims_rule: str = ""
    late_reporting_rule: str = ""
    notes: list[str] = []


STATE_RULES: list[StateRule] = [
    StateRule(state="CA", state_name="California", is_no_fault=False, requires_pip=False, requires_um_uim=True, um_uim_min_limit="$30,000/$60,000", glass_deductible_rule="full_deductible", notes=["California requires UM/UIM by default unless explicitly waived in writing.", "Lowest minimum liability limits in US: $15k/$30k/$5k.", "Proposition 213 may limit pain and suffering for uninsured drivers."]),
    StateRule(state="FL", state_name="Florida", is_no_fault=True, requires_pip=True, pip_min_limit="$10,000", requires_um_uim=False, glass_deductible_rule="zero_deductible", notes=["Florida is a no-fault state with mandatory PIP of $10,000.", "Property damage liability required ($10k min).", "Medical expenses go through PIP first.", "Florida has a $0 glass deductible law for comprehensive claims."]),
    StateRule(state="NY", state_name="New York", is_no_fault=True, requires_pip=True, pip_min_limit="$50,000", requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["New York is a no-fault state with $50,000 minimum PIP.", "Supplementary uninsured/underinsured motorist (SUM) coverage is available.", "No-fault threshold limits lawsuits to serious injury cases.", "Required liability: $25k/$50k/$10k."]),
    StateRule(state="MI", state_name="Michigan", is_no_fault=True, requires_pip=True, pip_min_limit="$250,000", requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["Michigan has unlimited lifetime PIP medical benefits (or $250k/$500k if opted out).", "Property protection insurance (PPI) covers damage to other property.", "Requires mini-tort for deductible recovery from at-fault drivers.", "Highest auto insurance costs in the US due to unlimited PIP."]),
    StateRule(state="TX", state_name="Texas", is_no_fault=False, requires_pip=False, requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["Texas requires liability only ($30k/$60k/$25k).", "UM/UIM is not required and must be offered and rejected in writing.", "Right to sue is unrestricted since Texas is a tort state.", "Personal injury protection (PIP) must be offered but can be rejected."]),
    StateRule(state="PA", state_name="Pennsylvania", is_no_fault=True, requires_pip=True, pip_min_limit="$5,000", requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["Pennsylvania is a 'choice no-fault' state.", "Drivers can choose limited tort (lower premium) or full tort (right to sue).", "Limited tort restricts pain and suffering claims.", "$5,000 minimum medical benefits coverage required."]),
    StateRule(state="NJ", state_name="New Jersey", is_no_fault=True, requires_pip=True, pip_min_limit="$15,000", requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["New Jersey is a no-fault state with $15,000 PIP minimum.", "Drivers choose between basic and standard policies.", "UM/UIM not required but must be offered.", "Verbal threshold limits lawsuit rights."]),
    StateRule(state="OH", state_name="Ohio", is_no_fault=False, requires_pip=False, requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["Ohio is a tort state with low minimums ($25k/$50k/$25k).", "UM/UIM may be rejected in writing but is a common addition.", "No PIP or MedPay required, but MedPay is commonly available as an option."]),
    StateRule(state="IL", state_name="Illinois", is_no_fault=False, requires_pip=False, requires_um_uim=True, um_uim_min_limit="$20,000/$40,000", glass_deductible_rule="full_deductible", notes=["Illinois requires UM/UIM coverage equal to liability limits.", "Tort state — no PIP requirements.", "Minimum liability: $25k/$50k/$20k."]),
    StateRule(state="GA", state_name="Georgia", is_no_fault=False, requires_pip=False, requires_um_uim=True, um_uim_min_limit="$25,000/$50,000", glass_deductible_rule="full_deductible", notes=["Georgia requires UM/UIM but allows written rejection.", "Tort state — no PIP requirement.", "Serves as a 'matching' state for UM/UIM limits."]),
    StateRule(state="WA", state_name="Washington", is_no_fault=False, requires_pip=False, requires_um_uim=False, glass_deductible_rule="full_deductible", notes=["Washington is a tort state.", "No mandatory PIP or UM/UIM.", "Minimum liability: $25k/$50k/$10k."]),
]


def get_state_rules(state_code: str) -> Optional[StateRule]:
    """Get rules for a specific state."""
    for rule in STATE_RULES:
        if rule.state == state_code.upper():
            return rule
    return None


def list_states() -> list[dict]:
    """List all available states with codes."""
    return [{"code": r.state, "name": r.state_name} for r in STATE_RULES]


def get_state_specific_warnings(
    state_code: Optional[str],
    has_um_uim: bool,
    has_medical: bool,
    property_limit_val: Optional[float],
    liability_limit_val: Optional[float],
) -> list[dict]:
    """Get state-specific coverage warnings based on parsed policy."""
    if not state_code:
        return []

    rule = get_state_rules(state_code.upper())
    if not rule:
        return []

    warnings: list[dict] = []

    if rule.requires_um_uim and not has_um_uim:
        warnings.append({
            "type": "state_requirement",
            "severity": "high",
            "detail": f"{rule.state_name} requires UM/UIM coverage.",
            "rule": f"Minimum UM/UIM: {rule.um_uim_min_limit or 'equal to liability limits'}",
        })

    if rule.requires_pip and not has_medical:
        warnings.append({
            "type": "state_requirement",
            "severity": "high",
            "detail": f"{rule.state_name} is a no-fault state requiring PIP (minimum {rule.pip_min_limit}).",
            "rule": f"PIP minimum: {rule.pip_min_limit}",
        })

    if rule.is_no_fault and has_medical:
        warnings.append({
            "type": "state_info",
            "severity": "info",
            "detail": f"{rule.state_name} is a no-fault state — medical bills are paid by your PIP coverage first, regardless of fault.",
            "rule": "No-fault state rules apply to injury claims",
        })

    if rule.glass_deductible_rule == "zero_deductible":
        warnings.append({
            "type": "state_benefit",
            "severity": "info",
            "detail": f"{rule.state_name} has $0 glass deductible — windshield claims are fully covered under comprehensive.",
            "rule": f"Glass deductible rule: {rule.glass_deductible_rule}",
        })

    for note in rule.notes:
        warnings.append({
            "type": "state_note",
            "severity": "info",
            "detail": note,
            "rule": f"General note for {rule.state_name}",
        })

    return warnings
