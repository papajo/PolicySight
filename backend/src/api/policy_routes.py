"""
Policy Decoder API Routes
Handles SLIP document upload, paste, and parsing.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.ai.client import LLMService
from src.ai.ocr import OCRService
from src.config.settings import get_settings
from src.core.policy_decoder import PolicyDecoder, ParsedPolicy
from src.db.base import get_db

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg")


class PolicyTextInput(BaseModel):
    """Request model for pasting policy text directly."""
    text: str


@router.post("/decode", response_model=ParsedPolicy)
async def decode_policy(
    file: UploadFile | None = File(None),
):
    """
    Upload a SLIP document and receive a structured breakdown
    of your policy limits, coverage gaps, and recommendations.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")

    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF, PNG, or JPG policy document.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large. Maximum size is 10 MB.")

    raw_text = await OCRService.extract_text(content, file.filename)
    if not OCRService.has_meaningful_text(raw_text):
        raise HTTPException(
            status_code=422,
            detail="We could not extract enough readable text from this document. Please upload a clearer PDF or image.",
        )

    return await _parse_policy(raw_text)


@router.post("/decode-text", response_model=ParsedPolicy)
async def decode_policy_text(input_data: PolicyTextInput):
    """
    Paste your policy text directly for structured analysis.
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Please paste at least 20 characters of policy text.",
        )

    return await _parse_policy(input_data.text)


async def _parse_policy(raw_text: str) -> ParsedPolicy:
    """Common parsing logic used by both upload and paste endpoints."""
    parsed = PolicyDecoder.parse_policy_text(raw_text)

    settings = get_settings()
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)
    llm_enhanced = await llm.parse_slip(raw_text)

    # Merge: prefer deterministic extraction where available, LLM fills gaps
    merged_dict = parsed.model_dump()
    llm_dict = llm_enhanced.model_dump(exclude_none=True)
    for key, val in llm_dict.items():
        if merged_dict.get(key) is None and val is not None:
            merged_dict[key] = val
    merged = ParsedPolicy(**merged_dict)
    merged.raw_text = raw_text
    merged.coverage_gaps = PolicyDecoder.detect_coverage_gaps(merged)
    merged.plain_english_summary = PolicyDecoder.generate_plain_english_summary(merged)
    return merged


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
