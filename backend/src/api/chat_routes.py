"""
General Chat Assistant API Route
Handles conversational queries about insurance, the app, and guidance.
Context-aware: adapts responses based on the page the user is viewing.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from src.db.base import get_db
from src.db.models import User
from src.core.auth import get_current_user_optional

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    action_target: Optional[str] = None


PAGE_CONTEXT = {
    "/": {
        "name": "Home",
        "prompt": (
            "You are PolicySight Assistant, a helpful AI guide for auto insurance. "
            "The user is on the home page. Greet them warmly, explain what PolicySight can do, "
            "and offer to help with: policy decoding, claims advocacy, rate forecasting, "
            "coverage comparisons, or general insurance questions. Be friendly and professional."
        ),
    },
    "/decoder": {
        "name": "Policy Decoder",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Policy Decoder page. "
            "Help them understand how to upload or paste their insurance policy (SLIP document). "
            "Explain what the decoder will extract: coverage limits, deductibles, exclusions, "
            "coverage gaps, and plain-English summaries."
        ),
    },
    "/claims": {
        "name": "Claims Advocate",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Claims Advocate page. "
            "Help them understand the claims process: uploading accident photos, getting sub-limit "
            "valuations, comparing what their policy covers vs. what the carrier is offering. "
            "Be empathetic — claims are stressful."
        ),
    },
    "/trajectory": {
        "name": "Rate Forecast",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Rate Forecast page. "
            "Help them understand premium forecasting: how claims history, driving record, "
            "and carrier loyalty affect future rates. Explain Stay vs Switch recommendations."
        ),
    },
    "/lapse": {
        "name": "Lapse Bridge",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Lapse Bridge page. "
            "Help them understand coverage gaps from policy lapses, SR-22 requirements, "
            "and how lapses affect future premiums."
        ),
    },
    "/timeline": {
        "name": "Coverage Timeline",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Coverage Timeline page. "
            "Help them visualize their insurance history and understand patterns."
        ),
    },
    "/scenario": {
        "name": "Scenario Checker",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Scenario Checker page. "
            "Help them evaluate hypothetical situations and understand which coverages apply."
        ),
    },
    "/intake": {
        "name": "Claim Intake",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Claim Intake page. "
            "Guide them through the structured claim intake form step by step."
        ),
    },
    "/decision": {
        "name": "Decision Draft",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Decision Draft page. "
            "Help them understand coverage decisions, escalation levels, and next steps."
        ),
    },
    "/audit": {
        "name": "Audit Trail",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Audit Trail page. "
            "Help them understand the audit log and compliance tracking."
        ),
    },
    "/edge-cases": {
        "name": "Edge Cases",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Edge Cases page. "
            "Help them understand unusual insurance situations like rideshare, excluded drivers, "
            "borrowed vehicles, hit-and-run, and late reporting."
        ),
    },
    "/cost-estimator": {
        "name": "Cost Estimator",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Cost Estimator page. "
            "Help them estimate out-of-pocket costs for a claim."
        ),
    },
    "/states": {
        "name": "State Rules",
        "prompt": (
            "You are PolicySight Assistant. The user is on the State Rules page. "
            "Help them understand state-specific insurance requirements."
        ),
    },
    "/feedback": {
        "name": "Feedback",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Feedback page. "
            "Help them provide feedback about PolicySight."
        ),
    },
    "/compare": {
        "name": "Policy Comparison",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Policy Comparison page. "
            "Help them compare two insurance policies side-by-side."
        ),
    },
    "/copilot": {
        "name": "Copilot Dashboard",
        "prompt": (
            "You are PolicySight Assistant. The user is on the Copilot Dashboard. "
            "Help them navigate the dashboard and get the most out of PolicySight."
        ),
    },
}

GENERAL_SYSTEM = (
    "You are PolicySight Assistant, an AI-powered guide for auto insurance. "
    "You help users understand their policies, navigate claims, compare rates, "
    "and make informed insurance decisions. Be conversational, empathetic, and clear. "
    "Avoid jargon unless the user seems knowledgeable. Always remind users that your "
    "guidance does not replace professional insurance advice."
)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_optional),
):
    """
    General-purpose chat endpoint.
    Uses page context to provide relevant, contextual responses.
    Falls back to a helpful general response without an LLM call
    when the OpenAI key is not configured.
    """
    from src.config.settings import get_settings

    settings = get_settings()
    page = (request.context or {}).get("page", "/")
    page_info = PAGE_CONTEXT.get(page, {"name": "PolicySight", "prompt": GENERAL_SYSTEM})

    last_message = request.messages[-1].content if request.messages else ""
    user_lower = last_message.lower()

    # ── Intent detection (no LLM needed) ──
    nav_routes = {
        "decoder": "/decoder",
        "decode": "/decoder",
        "policy decoder": "/decoder",
        "upload": "/decoder",
        "claims": "/claims",
        "claim": "/claims",
        "advocate": "/claims",
        "file a claim": "/claims",
        "forecast": "/trajectory",
        "rate": "/trajectory",
        "premium": "/trajectory",
        "trajectory": "/trajectory",
        "lapse": "/lapse",
        "gap": "/lapse",
        "sr-22": "/lapse",
        "timeline": "/timeline",
        "history": "/timeline",
        "scenario": "/scenario",
        "what if": "/scenario",
        "intake": "/intake",
        "decision": "/decision",
        "coverage decision": "/decision",
        "audit": "/audit",
        "log": "/audit",
        "edge case": "/edge-cases",
        "rideshare": "/edge-cases",
        "excluded driver": "/edge-cases",
        "cost": "/cost-estimator",
        "out of pocket": "/cost-estimator",
        "estimate": "/cost-estimator",
        "state": "/states",
        "compare": "/compare",
        "comparison": "/compare",
        "copilot": "/copilot",
        "dashboard": "/copilot",
    }

    for keyword, route in nav_routes.items():
        if keyword in user_lower and route != page:
            feature_name = PAGE_CONTEXT.get(route, {}).get("name", route)
            return ChatResponse(
                reply=f"I see you're asking about something related to **{feature_name}**. Would you like me to take you there?",
                action="navigate",
                action_target=route,
            )

    # ── Quick answers (no LLM needed) ──
    quick_answers = {
        "what is policysight": "PolicySight is an AI-powered auto insurance middleware that helps you understand your policy, file smarter claims, and forecast rate changes — all in plain English.",
        "how does this work": "PolicySight analyzes your insurance policy (SLIP document), explains coverages in plain English, helps you advocate for fair claim settlements, and predicts future premium trends. Upload your policy or paste the text to get started.",
        "what can you do": "I can help you with:\n\n• **Policy Decoder** — Upload your SLIP document for a plain-English breakdown\n• **Claims Advocate** — Get sub-limit valuations and fair settlement guidance\n• **Rate Forecast** — Predict next year's premium and get Stay/Switch advice\n• **Scenario Checker** — Test hypothetical situations against your policy\n• **Cost Estimator** — Calculate out-of-pocket costs for a claim\n• **Policy Comparison** — Compare two policies side-by-side\n\nWhich would you like to explore?",
        "is this free": "PolicySight offers a free tier for basic policy analysis. Advanced features like claims advocacy and rate forecasting may require a subscription. Check the Copilot Dashboard for current plan details.",
        "is my data safe": "Yes. PolicySight encrypts your data in transit and at rest. Your policy documents are processed securely and are never shared with third parties. We follow SOC 2 and insurance industry compliance standards.",
        "who made this": "PolicySight is built by a team passionate about making insurance transparent and accessible. We combine AI technology with insurance expertise to help consumers make informed decisions.",
    }

    for trigger, answer in quick_answers.items():
        if trigger in user_lower:
            return ChatResponse(reply=answer)

    # ── LLM-powered response (if key is configured) ──
    if settings.openai_api_key and settings.openai_api_key != "sk-placeholder":
        try:
            from src.ai.client import LLMService

            llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)

            system_msg = page_info.get("prompt", GENERAL_SYSTEM)
            api_messages = [{"role": "system", "content": system_msg}]
            for msg in request.messages:
                api_messages.append({"role": msg.role, "content": msg.content})

            response = await llm.client.chat.completions.create(
                model=llm.model,
                messages=api_messages,
                max_tokens=500,
                temperature=0.7,
            )

            reply = response.choices[0].message.content or "I'm not sure how to help with that."

            # Detect navigation intent in the response
            action = None
            target = None
            for keyword, route in nav_routes.items():
                if keyword in reply.lower() and route != page:
                    action = "navigate"
                    target = route
                    break

            return ChatResponse(reply=reply, action=action, action_target=target)

        except Exception:
            pass

    # ── Fallback response ──
    page_name = page_info.get("name", "this page")
    return ChatResponse(
        reply=(
            f"I'm the PolicySight Assistant. You're currently on the **{page_name}** page. "
            f"I can help you understand insurance concepts, navigate the app, and answer questions "
            f"about your policy, claims, or rates.\n\n"
            f"Try asking me:\n"
            f"• \"What can you do?\"\n"
            f"• \"How does the policy decoder work?\"\n"
            f"• \"What if I'm in a car accident?\"\n"
            f"• \"Help me file a claim\"\n\n"
            f"For the best experience, configure an OpenAI API key in your `.env` file "
            f"to enable full conversational AI."
        )
    )


@router.get("/pages")
async def list_pages():
    """Return available page contexts for the frontend to use."""
    return {
        page: info["name"]
        for page, info in PAGE_CONTEXT.items()
    }
