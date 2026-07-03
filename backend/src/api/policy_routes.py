"""
Policy Decoder API Routes
Handles SLIP document upload, paste, parsing, explanation, and evidence queries.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.ai.client import LLMService
from src.ai.ocr import OCRService
from src.config.settings import get_settings
from src.core.policy_decoder import PolicyDecoder, ParsedPolicy
from src.core.explainer import CoverageExplainer, CoverageExplanationSet, EvidenceAnswer
from src.core.scenario import evaluate_scenario, ScenarioResult
from src.core.decision import generate_decision, CoverageDecision
from src.core.audit import log_action
from src.db.base import get_db

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg")


class PolicyTextInput(BaseModel):
    """Request model for pasting policy text directly."""
    text: str


class ExplainRequest(BaseModel):
    """Request model for coverage explanation."""
    text: str


class AskRequest(BaseModel):
    """Request model for asking a question about a policy."""
    text: str
    question: str


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

    result = await _parse_policy(raw_text)
    log_action("policy_decode", "policy", f"Decoded policy from file: {file.filename}")
    return result


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

    result = await _parse_policy(input_data.text)
    log_action("policy_decode", "policy", "Decoded policy from pasted text")
    return result


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


@router.post("/explain", response_model=CoverageExplanationSet)
async def explain_coverage(input_data: ExplainRequest):
    """
    Generate per-coverage-type plain-English explanations
    with source citations and confidence levels. (REQ-003)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    parsed.plain_english_summary = PolicyDecoder.generate_plain_english_summary(parsed)
    result = CoverageExplainer.explain(parsed)
    log_action("policy_explain", "policy", f"Generated {len(result.explanations)} coverage explanations (confidence: {result.overall_confidence})")
    return result


@router.post("/ask", response_model=EvidenceAnswer)
async def ask_policy_question(input_data: AskRequest):
    """
    Answer a natural-language question about a policy
    using only extracted data and known coverage rules. (REQ-002)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")
    if not input_data.question or len(input_data.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please provide a question about the policy.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    result = CoverageExplainer.answer_question(parsed, input_data.question)
    log_action("policy_ask", "policy", f"Q: {input_data.question[:100]} → confidence: {result.confidence}")
    return result


class ScenarioRequest(BaseModel):
    """Request model for scenario-based coverage check."""
    text: str
    scenario: str


@router.post("/scenario", response_model=ScenarioResult)
async def check_scenario(input_data: ScenarioRequest):
    """
    Evaluate a natural-language scenario against a policy
    to determine which coverages apply. (REQ-006)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")
    if not input_data.scenario or len(input_data.scenario.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please describe the scenario.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    result = evaluate_scenario(parsed, input_data.scenario)
    log_action("scenario_check", "policy", f"Scenario: {input_data.scenario[:100]} → covered={result.is_covered}")
    return result


class DecisionRequest(BaseModel):
    """Request model for coverage decision."""
    text: str
    claim: str


@router.post("/decision", response_model=CoverageDecision)
async def coverage_decision(input_data: DecisionRequest):
    """
    Generate a structured claim coverage decision draft
    with confidence levels and escalation recommendations. (REQ-008, REQ-009)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")
    if not input_data.claim or len(input_data.claim.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please describe the claim.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    result = generate_decision(parsed, input_data.claim)
    log_action("coverage_decision", "policy", f"Claim: {input_data.claim[:100]} → escalation: {result.escalation_level}, confidence: {result.overall_confidence}")
    return result
