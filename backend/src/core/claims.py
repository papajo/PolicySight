"""
Claim Intake Assistant (REQ-007)
Structured guided intake for insurance claims.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PartyInfo(BaseModel):
    name: str = ""
    role: str = ""  # claimant, policyholder, witness, other_driver
    insurance_info: str = ""
    contact: str = ""


class DamageInfo(BaseModel):
    description: str = ""
    estimated_amount: Optional[float] = None
    type: str = ""  # vehicle, property, injury


class ClaimIntake(BaseModel):
    """Structured claim intake record."""
    policy_number: str = ""
    date_of_loss: str = ""
    time_of_loss: str = ""
    location: str = ""
    description: str = ""
    parties: list[PartyInfo] = []
    damages: list[DamageInfo] = []
    witness_info: str = ""
    police_report: bool = False
    police_report_number: str = ""
    reported_by: str = ""
    reported_date: str = ""


class IntakeStep(BaseModel):
    """A single step in the guided intake process."""
    step_id: str
    label: str
    prompt: str
    field_type: str  # text, date, time, textarea, select, boolean, number
    options: list[str] = []
    required: bool = True


INTAKE_STEPS = [
    IntakeStep(step_id="policy_number", label="Policy Number", prompt="What is your policy number?", field_type="text"),
    IntakeStep(step_id="date_of_loss", label="Date of Loss", prompt="When did the incident happen?", field_type="date", required=True),
    IntakeStep(step_id="time_of_loss", label="Time of Loss", prompt="Approximately what time did it happen?", field_type="time"),
    IntakeStep(step_id="location", label="Location", prompt="Where did the incident occur?", field_type="text", required=True),
    IntakeStep(step_id="description", label="Description", prompt="Describe what happened in detail.", field_type="textarea", required=True),
    IntakeStep(step_id="other_driver", label="Other Driver", prompt="Was another driver involved? If so, what is their name, insurance, and contact info?", field_type="textarea"),
    IntakeStep(step_id="vehicle_damage", label="Vehicle Damage", prompt="Describe the damage to your vehicle and estimated repair cost (if known).", field_type="textarea", required=True),
    IntakeStep(step_id="injuries", label="Injuries", prompt="Were you or any passengers injured? Describe.", field_type="textarea"),
    IntakeStep(step_id="witnesses", label="Witnesses", prompt="Were there any witnesses? Provide names and contact info.", field_type="textarea"),
    IntakeStep(step_id="police_report", label="Police Report", prompt="Was a police report filed?", field_type="select", options=["Yes", "No", "Unsure"]),
]


# In-memory store for demo
_intakes: list[ClaimIntake] = []


def get_intake_steps() -> list[IntakeStep]:
    return INTAKE_STEPS


def submit_intake(responses: dict[str, str]) -> ClaimIntake:
    """Convert raw form responses into a structured claim intake."""
    damages: list[DamageInfo] = []
    if responses.get("vehicle_damage"):
        damages.append(DamageInfo(
            description=responses["vehicle_damage"],
            type="vehicle",
        ))

    parties: list[PartyInfo] = []
    if responses.get("other_driver"):
        parties.append(PartyInfo(
            name=responses["other_driver"],
            role="other_driver",
        ))

    if responses.get("injuries"):
        damages.append(DamageInfo(
            description=responses["injuries"],
            type="injury",
        ))

    intake = ClaimIntake(
        policy_number=responses.get("policy_number", ""),
        date_of_loss=responses.get("date_of_loss", ""),
        time_of_loss=responses.get("time_of_loss", ""),
        location=responses.get("location", ""),
        description=responses.get("description", ""),
        parties=parties,
        damages=damages,
        witness_info=responses.get("witnesses", ""),
        police_report=responses.get("police_report") == "Yes",
        police_report_number=responses.get("police_report_number", ""),
        reported_by="Demo User",
        reported_date=datetime.now().isoformat(),
    )
    _intakes.append(intake)
    return intake


def get_intakes() -> list[ClaimIntake]:
    return _intakes
