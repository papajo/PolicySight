"""
Feedback Loop (PDF REQ-016)
Users/adjusters rate AI responses for quality improvement.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class FeedbackEntry(BaseModel):
    id: int
    timestamp: str
    action: str
    rating: str  # correct, incorrect, incomplete, unclear
    comment: str = ""
    details: str = ""


_feedback_log: list[FeedbackEntry] = []
_next_id: int = 1


def submit_feedback(
    action: str,
    rating: str,
    comment: str = "",
    details: str = "",
) -> FeedbackEntry:
    global _next_id
    entry = FeedbackEntry(
        id=_next_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        action=action,
        rating=rating,
        comment=comment,
        details=details,
    )
    _feedback_log.append(entry)
    _next_id += 1
    return entry


def get_feedback(limit: int = 50) -> list[FeedbackEntry]:
    return list(reversed(_feedback_log))[:limit]


def get_feedback_summary() -> dict:
    total = len(_feedback_log)
    by_rating: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for entry in _feedback_log:
        by_rating[entry.rating] = by_rating.get(entry.rating, 0) + 1
        by_action[entry.action] = by_action.get(entry.action, 0) + 1
    return {
        "total": total,
        "by_rating": by_rating,
        "by_action": by_action,
        "accuracy_rate": round(by_rating.get("correct", 0) / total * 100, 1) if total > 0 else 0,
    }
