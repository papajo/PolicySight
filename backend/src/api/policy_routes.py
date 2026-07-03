"""
Policy Decoder API Routes
Handles SLIP document upload and parsing.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.ai.client import LLMService, ParsedPolicy
from src.ai.ocr import OCRService
from src.config.settings import get_settings
from src.db.base import get_db

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg")


@router.post("/decode", response_model=ParsedPolicy)
async def decode_policy(
    file: UploadFile = File(...),
):
    """
    Upload a SLIP document and receive a plain-English breakdown
    of your policy limits, coverage gaps, and recommendations.
    """
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

    ocr = OCRService()
    raw_text = await ocr.extract_text(content, file.filename)

    if not OCRService.has_meaningful_text(raw_text):
        raise HTTPException(
            status_code=422,
            detail="We could not extract enough readable text from this document. Please upload a clearer PDF or image.",
        )

    settings = get_settings()
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)
    parsed_policy = await llm.parse_slip(raw_text)

    if not any(
        [
            parsed_policy.liability_limit,
            parsed_policy.medical_limit,
            parsed_policy.property_limit,
            parsed_policy.uninsured_motorist_limit,
            parsed_policy.deductible,
        ]
    ):
        raise HTTPException(
            status_code=422,
            detail="We extracted text, but could not confidently identify policy limits. Please upload a clearer declarations page.",
        )

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
