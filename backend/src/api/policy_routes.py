"""
Policy Decoder API Routes
Handles SLIP document upload, paste, parsing, explanation, and evidence queries.
"""

from typing import Optional
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
from src.core.edge_cases import classify_edge_cases, EdgeCaseResult
from src.core.cost_estimator import estimate_costs, CostEstimate
from src.core.comparison import compare_policies, ComparisonResult
from src.core.safe_failure import analyze_policy_safety, assess_decision_confidence
from src.core.policy_period import validate_policy_period
from src.core.vehicle_match import match_vehicle
from src.core.ocr_confidence import analyze_ocr_confidence
from src.core.endorsement_analyzer import analyze_endorsements
from src.core.rag_pipeline import RagPipeline
from src.core.audit import log_action

RAG = RagPipeline()
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
    llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model, base_url=settings.openai_base_url)
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

    # Safe failure analysis (PDF REQ-017)
    safe = analyze_policy_safety(merged)
    merged.safe_failure_overall_status = safe.overall_status
    merged.safe_failure_assessment = safe.assessment
    merged.safe_failure_required_info = [r.model_dump() for r in safe.required_info]
    merged.safe_failure_next_actions = [a.model_dump() for a in safe.next_actions]

    # OCR confidence analysis (FDE Test Case #6)
    ocr = analyze_ocr_confidence(raw_text)
    merged.ocr_confidence = ocr.overall_confidence
    merged.ocr_issues = [i.model_dump() for i in ocr.issues]

    # Endorsement conflict analysis (FDE Test Case #7)
    conflicts = analyze_endorsements(merged)
    merged.endorsement_conflicts = [c.model_dump() for c in conflicts]

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

    safe = analyze_policy_safety(parsed)
    result = CoverageExplainer.explain(parsed)
    if safe.overall_status != "determinate":
        result.safe_failure_assessment = safe.assessment
        result.safe_failure_required_info = [r.model_dump() for r in safe.required_info]
        result.safe_failure_next_actions = [a.model_dump() for a in safe.next_actions]

    log_action("policy_explain", "policy", f"Generated {len(result.explanations)} coverage explanations (confidence: {result.overall_confidence})")
    return result


@router.post("/ask", response_model=EvidenceAnswer)
async def ask_policy_question(input_data: AskRequest):
    """
    Answer a natural-language question about a policy
    using extracted data, coverage rules, and RAG-retrieved sections. (REQ-002)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")
    if not input_data.question or len(input_data.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please provide a question about the policy.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    result = CoverageExplainer.answer_question(parsed, input_data.question)

    try:
        doc_id = f"policy_{hash(input_data.text) % 2**31}"
        RAG.delete_document(doc_id)
        RAG.ingest(input_data.text, doc_id)
        retrieved = RAG.retrieve(input_data.question, k=3, doc_id=doc_id)
        for chunk in retrieved:
            if chunk.score >= 0.5:
                citation = f"[RAG: {chunk.section}] {chunk.content[:200]}"
                if citation not in result.citations:
                    result.citations.insert(0, citation)
        if retrieved:
            result.confidence = "high" if any(c.score >= 0.7 for c in retrieved) else "medium"
    except Exception as exc:
        import logging
        logging.getLogger("policysight.api").warning("RAG enrichment failed: %s", exc)

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
    accident_date: Optional[str] = None
    accident_vehicle: Optional[str] = None


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

    # Policy period validation
    period = validate_policy_period(parsed.effective_date, parsed.expiration_date, input_data.accident_date)
    if period.status != "no_dates":
        result.validations.append({
            "type": "policy_period",
            "status": period.status,
            "message": period.message,
        })
        if period.status in ("before_period", "after_period"):
            result.next_steps.insert(0, f"⚠ {period.message}")

    # Vehicle matching
    policy_vehicles = []
    if parsed.vehicle_year_make_model:
        policy_vehicles = [v.strip() for v in parsed.vehicle_year_make_model.split(";") if v.strip()]
    vehicle = match_vehicle(input_data.accident_vehicle, policy_vehicles)
    if vehicle.status != "no_claim_vehicle":
        result.validations.append({
            "type": "vehicle_match",
            "status": vehicle.status,
            "message": vehicle.message,
        })
        if vehicle.status == "not_listed":
            result.next_steps.insert(0, f"⚠ {vehicle.message}")

    # Prepend safe failure uncertainty if key coverage types are missing
    safe = analyze_policy_safety(parsed)
    if safe.overall_status != "determinate":
        missing_types = [r.label for r in safe.required_info if r.field in ("liability_limit", "collision_deductible", "medical_limit")]
        uncertainty = assess_decision_confidence(input_data.claim, missing_types)
        if uncertainty:
            result.next_steps.insert(0, uncertainty)

    log_action("coverage_decision", "policy", f"Claim: {input_data.claim[:100]} → escalation: {result.escalation_level}, confidence: {result.overall_confidence}")
    return result


class EdgeCaseRequest(BaseModel):
    """Request model for edge case classification."""
    text: str
    scenario: str


@router.post("/edge-cases", response_model=EdgeCaseResult)
async def check_edge_cases(input_data: EdgeCaseRequest):
    """
    Classify a scenario for edge cases: rideshare, excluded drivers,
    borrowed vehicles, hit-and-run, late reporting, etc. (PDF REQ-010)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")
    if not input_data.scenario or len(input_data.scenario.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please describe the scenario.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    parsed.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed)
    result = classify_edge_cases(parsed, input_data.scenario)
    log_action("edge_case_check", "policy", f"Scenario: {input_data.scenario[:100]} → {len([f for f in result.flags if f.applies])} flags, primary: {result.primary_concern}")
    return result


class EstimateRequest(BaseModel):
    text: str
    damage_estimate: float = 5000.0
    has_injuries: bool = False
    needs_rental_days: int = 14
    collision_applies: bool = True
    comprehensive_applies: bool = False


@router.post("/estimate-costs", response_model=CostEstimate)
async def estimate_out_of_pocket(input_data: EstimateRequest):
    """
    Estimate out-of-pocket costs for a claim based on policy limits,
    deductibles, and rental coverage. (PDF REQ-008)
    """
    if not input_data.text or len(input_data.text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters of policy text.")

    parsed = PolicyDecoder.parse_policy_text(input_data.text)
    result = estimate_costs(
        parsed,
        damage_estimate=input_data.damage_estimate,
        has_injuries=input_data.has_injuries,
        needs_rental_days=input_data.needs_rental_days,
        collision_applies=input_data.collision_applies,
        comprehensive_applies=input_data.comprehensive_applies,
    )
    log_action("cost_estimate", "policy", f"Damage est: ${input_data.damage_estimate:,.0f} → OOP: ${result.total_out_of_pocket:,.0f}")
    return result


class CompareRequest(BaseModel):
    policy_a_text: str
    policy_b_text: str
    label_a: str = "Current Policy"
    label_b: str = "New Policy"


@router.post("/compare", response_model=ComparisonResult)
async def compare_policies_endpoint(input_data: CompareRequest):
    """
    Compare two policies side-by-side. (PDF REQ-018)
    Shows improvements, reductions, bridged gaps between policies.
    """
    if not input_data.policy_a_text or len(input_data.policy_a_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters for Policy A.")
    if not input_data.policy_b_text or len(input_data.policy_b_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please provide at least 20 characters for Policy B.")

    parsed_a = PolicyDecoder.parse_policy_text(input_data.policy_a_text)
    parsed_b = PolicyDecoder.parse_policy_text(input_data.policy_b_text)
    parsed_a.raw_text = input_data.policy_a_text
    parsed_b.raw_text = input_data.policy_b_text
    parsed_a.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed_a)
    parsed_b.coverage_gaps = PolicyDecoder.detect_coverage_gaps(parsed_b)

    result = compare_policies(parsed_a, parsed_b)
    result.policy_a_label = input_data.label_a
    result.policy_b_label = input_data.label_b
    log_action("policy_compare", "policy", f"Compared policies: {len(result.diffs)} diffs, {len(result.improvements)} improvements, {len(result.reductions)} reductions")
    return result
