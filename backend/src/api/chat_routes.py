"""
General Chat Assistant API Route
Handles conversational queries about insurance, the app, and guidance.
Context-aware: adapts responses based on the page the user is viewing.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.db.models import User
from src.core.auth import get_current_user_optional

logger = logging.getLogger("policysight.chat")

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


PAGE_FALLBACKS = {
    "/": (
        "Welcome to the **PolicySight Home**! PolicySight is a neutral third-party middleware "
        "connecting your Policy, Premium, and Claim into one intelligent dashboard.\n\n"
        "Try asking me:\n"
        "• **\"What can you do?\"** — for a list of all features\n"
        "• **\"How does this work?\"** — for a general overview\n"
        "• **\"Is my data safe?\"** — for security information"
    ),
    "/decoder": (
        "You are on the **Policy Decoder** page. Here, you can upload or paste your "
        "insurance policy declarations (SLIP document). Our system parses the legalese into "
        "plain English and identifies any coverage gaps or risks.\n\n"
        "Try asking me:\n"
        "• **\"What is a coverage gap?\"**\n"
        "• **\"How does the decoder work?\"**\n"
        "• **\"What are the recommended limits?\"**"
    ),
    "/claims": (
        "You are on the **Claims Advocate** page. This tool helps you prepare for claims, "
        "compares your carrier's settlement offer against your policy's sub-limits, "
        "and guides you in arguing for a fair payout.\n\n"
        "Try asking me:\n"
        "• **\"How do I file a claim?\"**\n"
        "• **\"What if my carrier offers too little?\"**\n"
        "• **\"What is a sub-limit?\"**"
    ),
    "/trajectory": (
        "You are on the **Rate Forecast** page. The Rate Trajectory Bot (Renewal Oracle) predicts next year's premium "
        "by comparing your current rates with anonymous peer market trends, offering a "
        "Stay or Switch recommendation.\n\n"
        "Try asking me:\n"
        "• **\"What affects my rate?\"**\n"
        "• **\"How does rate forecasting work?\"**\n"
        "• **\"Should I switch carriers?\"**"
    ),
    "/lapse": (
        "You are on the **Lapse Bridge** page. Covr-Shift acts as an automated fail-safe during "
        "carrier transitions, monitoring your renewal window to trigger a temporary bridge policy "
        "if needed to prevent a coverage gap.\n\n"
        "Try asking me:\n"
        "• **\"What is a coverage lapse?\"**\n"
        "• **\"How does Lapse Bridge prevent gaps?\"**\n"
        "• **\"How is a bridge policy triggered?\"**"
    ),
    "/scenario": (
        "You are on the **Scenario Checker** page. Test hypothetical situations "
        "(like rideshare driving, family members borrowing your car, or hit-and-run) "
        "against your policy to see if you would be covered.\n\n"
        "Try asking me:\n"
        "• **\"What scenario checks can I run?\"**\n"
        "• **\"Am I covered if I drive for Uber?\"**\n"
        "• **\"What is a non-owned vehicle exclusion?\"**"
    ),
    "/cost-estimator": (
        "You are on the **Cost Estimator** page. Estimate out-of-pocket expenses "
        "based on your deductibles, co-pays, and policy limits for different accident severities.\n\n"
        "Try asking me:\n"
        "• **\"How do deductibles affect my out-of-pocket cost?\"**\n"
        "• **\"What is estimated in my out-of-pocket expense?\"**"
    ),
    "/states": (
        "You are on the **State Rules** page. Review minimum liability coverages, "
        "no-fault rules, and state-specific regulations for auto insurance.\n\n"
        "Try asking me:\n"
        "• **\"What are state minimum coverages?\"**\n"
        "• **\"What is no-fault insurance?\"**"
    ),
    "/compare": (
        "You are on the **Policy Comparison** page. Upload two different policy "
        "declarations side-by-side to compare coverages, limits, deductibles, and gap alerts.\n\n"
        "Try asking me:\n"
        "• **\"How do I compare two policies?\"**\n"
        "• **\"What details are shown in policy comparison?\"**"
    ),
    "/copilot": (
        "You are on the **Copilot Dashboard**. View your active policies, "
        "recent claim status, rate trends, and overall coverage health scores at a glance.\n\n"
        "Try asking me:\n"
        "• **\"What is the Copilot Dashboard?\"**\n"
        "• **\"What does my coverage score mean?\"**"
    ),
}

LOCAL_KB = {
    ("rate", "premium", "cost", "price", "trajectory", "oracle", "affect"): (
        "Auto insurance premiums are affected by several factors:\n\n"
        "• **Your Record**: At-fault accidents, speeding tickets, and violations raise rates.\n"
        "• **Location**: High-traffic zip codes and areas with high theft rates typically have higher premiums.\n"
        "• **Vehicle**: Safer cars with high crash-test ratings and security features cost less to insure.\n"
        "• **Deductible**: Raising your deductible lowers your monthly premium, while lowering it raises your premium.\n\n"
        "Visit the **Rate Forecast** page to predict your next renewal premium based on peer market data."
    ),
    ("deductible", "collision", "comprehensive"): (
        "A **deductible** is the out-of-pocket amount you pay before insurance covers repairs:\n\n"
        "• **Collision Deductible**: Applies when you hit another vehicle or object (regardless of fault).\n"
        "• **Comprehensive Deductible**: Applies to non-collision damage (theft, storm damage, fire, animal strike).\n\n"
        "A lower deductible reduces your claim expense but increases your premium."
    ),
    ("accident", "claim", "file", "intake", "crash", "settlement"): (
        "If you are in an accident:\n\n"
        "1. **Safety First**: Move to safety, check for injuries, and call 911 if needed.\n"
        "2. **Document Everything**: Take photos of both vehicles, license plates, and the scene. Get names and numbers.\n"
        "3. **Claim Intake**: Use our **Claim Intake** page to upload details, photos, and police reports.\n"
        "4. **Advocate**: The **Claims Advocate** page compares your carrier's settlement offer against policy sub-limits to fight low-ball offers."
    ),
    ("gap", "exclusion", "underinsured", "uninsured", "um", "uim"): (
        "A **coverage gap** is a risk of out-of-pocket expense due to missing or too-low coverage limits:\n\n"
        "• **Uninsured Motorist (UM/UIM)**: Crucial gap if an at-fault driver has no insurance.\n"
        "• **Low Property Damage**: Recommended minimum is $50,000 to cover multi-car accidents.\n"
        "• **Exclusions**: Intentional acts, track racing, and commercial driving (e.g., ridesharing) are typically excluded without endorsements."
    ),
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
    _current_user: User = Depends(get_current_user_optional),
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
        "policy decoder": "/decoder",
        "decoder": "/decoder",
        "decode": "/decoder",
        "upload": "/decoder",
        "claims advocate": "/claims",
        "claims": "/claims",
        "claim": "/claims",
        "file a claim": "/claims",
        "rate forecast": "/trajectory",
        "forecast": "/trajectory",
        "trajectory": "/trajectory",
        "lapse bridge": "/lapse",
        "lapse": "/lapse",
        "coverage gap": "/lapse",
        "timeline": "/timeline",
        "scenario checker": "/scenario",
        "scenario": "/scenario",
        "claim intake": "/intake",
        "intake": "/intake",
        "decision draft": "/decision",
        "decision": "/decision",
        "audit trail": "/audit",
        "audit": "/audit",
        "edge cases": "/edge-cases",
        "edge case": "/edge-cases",
        "cost estimator": "/cost-estimator",
        "out of pocket": "/cost-estimator",
        "state rules": "/states",
        "policy comparison": "/compare",
        "compare": "/compare",
        "copilot dashboard": "/copilot",
        "copilot": "/copilot",
    }
    navigation_phrases = (
        "take me",
        "go to",
        "open",
        "show me",
        "navigate",
        "send me",
        "start",
        "launch",
        "bring me",
    )
    wants_navigation = any(phrase in user_lower for phrase in navigation_phrases)

    if wants_navigation:
        for keyword, route in nav_routes.items():
            if keyword in user_lower and route != page:
                feature_name = PAGE_CONTEXT.get(route, {}).get("name", route)
                return ChatResponse(
                    reply=f"I can take you to **{feature_name}**.",
                    action="navigate",
                    action_target=route,
                )

    # ── Quick answers (no LLM needed) ──
    quick_answers = {
        "what is policysight": "PolicySight is an AI-powered auto insurance middleware that helps you understand your policy, file smarter claims, and forecast rate changes — all in plain English.",
        "how does this work": "PolicySight analyzes your insurance policy (SLIP document), explains coverages in plain English, helps you advocate for fair claim settlements, and predicts future premium trends. Upload your policy or paste the text to get started.",
        "what can you do": "I can help you with:\n\n• **Policy Decoder** — Upload your SLIP document for a plain-English breakdown\n• **Claims Advocate** — Get sub-limit valuations and fair settlement guidance\n• **Rate Forecast** — Predict next year's premium and get Stay/Switch advice\n• **Scenario Checker** — Test hypothetical situations against your policy\n• **Cost Estimator** — Calculate out-of-pocket costs for a claim\n• **Policy Comparison** — Compare two policies side-by-side\n\nWhich would you like to explore?",
        "is this free": "PolicySight offers a free tier for basic policy analysis. Advanced features like claims advocacy and rate forecasting may require a subscription. Check the Copilot Dashboard for current plan details.",
        "is my data safe": "PolicySight is designed to minimize unnecessary data sharing. Your requests are sent to the PolicySight backend for processing, and you should avoid uploading information that is not needed for the task. For exact retention, deletion, and compliance guarantees, check the product privacy policy or ask the PolicySight team.",
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

            reply = await llm.chat(
                api_messages,
                max_tokens=500,
                temperature=0.7,
            )
            if not reply:
                reply = "I'm not sure how to help with that."

            # Detect navigation intent in the response
            action = None
            target = None
            for keyword, route in nav_routes.items():
                if keyword in reply.lower() and route != page:
                    action = "navigate"
                    target = route
                    break

            return ChatResponse(reply=reply, action=action, action_target=target)

        except Exception as exc:
            logger.warning("LLM chat response failed; using deterministic fallback: %s", exc)

    # ── Local KB lookup (no LLM needed fallback) ──
    for keywords, answer in LOCAL_KB.items():
        if any(kw in user_lower for kw in keywords):
            return ChatResponse(reply=answer)

    # ── Fallback response ──
    page_name = page_info.get("name", "this page")
    fallback_reply = PAGE_FALLBACKS.get(
        page,
        f"I'm the PolicySight Assistant. You're currently on the **{page_name}** page. "
        f"I can help you understand insurance concepts, navigate the app, and answer questions "
        f"about your policy, claims, or rates.\n\n"
        f"Try asking me:\n"
        f"• \"What can you do?\"\n"
        f"• \"How does the policy decoder work?\"\n"
        f"• \"What if I'm in a car accident?\"\n"
        f"• \"Help me file a claim\"\n\n"
        f"For specific claim decisions or legal advice, please confirm details with "
        f"a licensed insurance professional or your carrier."
    )
    return ChatResponse(reply=fallback_reply)


@router.get("/pages")
async def list_pages():
    """Return available page contexts for the frontend to use."""
    return {
        page: info["name"]
        for page, info in PAGE_CONTEXT.items()
    }
