"""
Feedback Loop API Routes (PDF REQ-016)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.feedback import submit_feedback, get_feedback, get_feedback_summary
from src.core.audit import log_action

router = APIRouter()


class FeedbackInput(BaseModel):
    action: str
    rating: str  # correct, incorrect, incomplete, unclear
    comment: str = ""
    details: str = ""


@router.post("/feedback")
async def add_feedback(input_data: FeedbackInput):
    """Submit feedback rating for an AI response."""
    valid_ratings = {"correct", "incorrect", "incomplete", "unclear"}
    if input_data.rating not in valid_ratings:
        raise HTTPException(status_code=400, detail=f"Rating must be one of: {', '.join(sorted(valid_ratings))}")
    result = submit_feedback(
        action=input_data.action,
        rating=input_data.rating,
        comment=input_data.comment,
        details=input_data.details,
    )
    log_action("feedback_submitted", "feedback", f"Action: {input_data.action}, rating: {input_data.rating}")
    return result


@router.get("/feedback")
async def list_feedback():
    """List recent feedback entries."""
    return get_feedback()


@router.get("/feedback/summary")
async def feedback_summary():
    """Get feedback summary statistics."""
    return get_feedback_summary()
