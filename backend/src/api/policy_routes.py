"""
Policy Decoder API Routes
Handles SLIP document upload and parsing.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.ai.client import LLMService, ParsedPolicy
from src.config.settings import get_settings

router = APIRouter()


@router.post("/decode", response_model=ParsedPolicy)
async def decode_policy(
    file: UploadFile = File(...),
):
    """
    Upload a SLIP document and receive a plain-English breakdown
    of your policy limits, coverage gaps, and recommendations.
    """
    if not file.filename or not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF or image of your SLIP document.",
        )

    # Read file content (binary safe)
    content = await file.read()
    # For images, we'd use OCR; for now, pass raw bytes as placeholder
    raw_text = content.decode("utf-8", errors="replace")

    # Call LLM service (placeholder returns mock data)
    settings = get_settings()
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)
    parsed_policy = await llm.parse_slip(raw_text)

    return parsed_policy


@router.post("/save")
async def save_policy_snapshot(
    policy_id: int,
    raw_slip_content: str,
    parsed_limits: dict,
    db: Session = Depends(get_db),
):
    """Save a parsed policy snapshot to the database."""
    from src.db.models import PolicySnapshot

    snapshot = PolicySnapshot(
        policy_id=policy_id,
        raw_slip_content=raw_slip_content,
        parsed_limits=parsed_limits,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return {"id": snapshot.id, "status": "saved"}