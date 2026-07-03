"""
State Rules API Routes (PDF REQ-013)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.state_rules import list_states, get_state_rules, get_state_specific_warnings

router = APIRouter()


@router.get("/states")
async def list_states_endpoint():
    """List all available states with rules."""
    return list_states()


@router.get("/states/{state_code}")
async def get_state(state_code: str):
    """Get insurance rules and requirements for a specific state."""
    rule = get_state_rules(state_code.upper())
    if not rule:
        raise HTTPException(status_code=404, detail=f"No rules found for state '{state_code.upper()}'.")
    return rule


class StateCheckRequest(BaseModel):
    state: str
    has_um_uim: bool = False
    has_medical: bool = False
    property_limit: float = 0
    liability_limit: float = 0


@router.post("/states/check")
async def check_state_compliance(input_data: StateCheckRequest):
    """Check a policy against state-specific requirements."""
    warnings = get_state_specific_warnings(
        state_code=input_data.state,
        has_um_uim=input_data.has_um_uim,
        has_medical=input_data.has_medical,
        property_limit_val=input_data.property_limit,
        liability_limit_val=input_data.liability_limit,
    )
    rule = get_state_rules(input_data.state.upper())
    return {
        "state": input_data.state.upper(),
        "state_name": rule.state_name if rule else "Unknown",
        "warnings": warnings,
        "warnings_count": len(warnings),
    }
