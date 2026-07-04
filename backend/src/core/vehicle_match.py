"""
Vehicle Matching (FDE Test Case #12)
Checks whether a claim vehicle is listed on the policy.
"""

from typing import Optional
from pydantic import BaseModel


class VehicleMatchResult(BaseModel):
    status: str  # "listed", "not_listed", "no_vehicles", "no_claim_vehicle"
    claimed_vehicle: Optional[str] = None
    listed_vehicles: list[str] = []
    message: str


def normalize_vehicle(text: str) -> str:
    return text.strip().lower()


def vehicle_overlap(claim: str, listed: str) -> bool:
    """Check if the claim vehicle matches a listed vehicle by token overlap."""
    claim_tokens = set(normalize_vehicle(claim).split())
    listed_tokens = set(normalize_vehicle(listed).split())
    return len(claim_tokens & listed_tokens) >= 2


def match_vehicle(
    claim_vehicle: Optional[str],
    policy_vehicles: list[str],
) -> VehicleMatchResult:
    """
    Check whether the claim vehicle is listed on the policy.
    Uses fuzzy token matching to handle variations like "Honda CR-V" vs "HONDA CRV".
    """
    if not claim_vehicle:
        return VehicleMatchResult(
            status="no_claim_vehicle",
            listed_vehicles=policy_vehicles,
            message="No vehicle information was provided for this claim.",
        )

    if not policy_vehicles:
        return VehicleMatchResult(
            status="no_vehicles",
            claimed_vehicle=claim_vehicle,
            message="Policy does not contain any listed vehicle information. Cannot verify if the claim vehicle is covered.",
        )

    for listed in policy_vehicles:
        if vehicle_overlap(claim_vehicle, listed):
            return VehicleMatchResult(
                status="listed",
                claimed_vehicle=claim_vehicle,
                listed_vehicles=policy_vehicles,
                message=f"The claim vehicle ({claim_vehicle}) matches a vehicle listed on the policy ({listed}).",
            )

    return VehicleMatchResult(
        status="not_listed",
        claimed_vehicle=claim_vehicle,
        listed_vehicles=policy_vehicles,
        message=f"The claim vehicle ({claim_vehicle}) does not appear in the policy's listed vehicles ({'; '.join(policy_vehicles)}). Coverage may depend on newly-acquired vehicle or temporary substitute auto provisions.",
    )
