"""
Timeline API Routes (REQ-004)
Coverage period timeline with gap detection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.timeline import build_timeline, add_policy_to_demo, PolicyPeriod, TimelineResult

router = APIRouter()


class AddPolicyRequest(BaseModel):
    policy_number: str
    carrier: str = "Unknown"
    effective_date: str
    expiration_date: str
    coverage_types: list[str] = []


@router.get("/timeline", response_model=TimelineResult)
async def get_timeline():
    """Get the coverage timeline with gap detection and lapse risk."""
    return build_timeline()


@router.post("/timeline/policies", response_model=TimelineResult)
async def add_policy(input_data: AddPolicyRequest):
    """Add a new policy to the timeline and return updated analysis."""
    new_policy = PolicyPeriod(
        policy_number=input_data.policy_number,
        carrier=input_data.carrier,
        effective_date=input_data.effective_date,
        expiration_date=input_data.expiration_date,
        coverage_types=input_data.coverage_types,
    )
    add_policy_to_demo(new_policy)
    return build_timeline()
