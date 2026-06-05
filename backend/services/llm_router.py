"""Pluggable LLM router — Claude → OpenAI → Ollama fallback chain.

Real API calls with graceful degradation:
  1. Try Claude API (primary) — uses anthropic SDK
  2. Try OpenAI API (fallback) — uses openai SDK
  3. Fall back to local Ollama (privacy-first default)
  4. Ultimate fallback: deterministic template

All API keys loaded from config (env vars). User can force local-only mode.
"""

import logging
from dataclasses import dataclass

from backend.config import (
    CLAUDE_API_KEY,
    LLM_BACKEND_ORDER,
    OLLAMA_BASE_URL,
    OPENAI_API_KEY,
)

logger = logging.getLogger(__name__)


@dataclass
class SpendingContext:
    product_name: str
    price: float
    monthly_avg: float
    similar_items_count: int
    score: float
    days_of_salary: float = 0.0


def _build_prompt(context: SpendingContext) -> str:
    """Build the narrative prompt template."""
    system = (
        "You are a brutally honest financial advisor. Generate a 2-3 sentence "
        "cold financial analysis of this purchase. Be specific, data-driven, and "
        "empathetic but firm. Do NOT moralize. Do NOT use markdown or bold text. "
        "Speak directly to the user in plain English."
    )

    salary_line = ""
    if context.days_of_salary > 0:
        salary_line = (
            f"This item costs {context.days_of_salary:.1f} days of their "
            f"estimated income. "
        )

    user = (
        f"The user is about to buy: {context.product_name} for "
        f"${context.price:.2f}.\n"
        f"Their monthly average spending is ${context.monthly_avg:.0f}.\n"
        f"They already own {context.similar_items_count} similar items.\n"
        f"{salary_line}"
        f"Their impulsivity score is {context.score:.2f}/1.0 "
        f"(higher = more impulsive).\n"
        f"Generate the financial reality check message."
    )

    return f"<system>{system}</system>\n\n<user>{user}</user>"


def _call_claude(context: SpendingContext) -> str | None:
    """Call Claude API via anthropic SDK."""
    if not CLAUDE_API_KEY:
        logger.debug("No CLAUDE_API_KEY configured")
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        prompt = _build_prompt(context)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=prompt.split("<system>")[1].split("</system>")[0].strip(),
            messages=[{"role": "user", "content": prompt.split("<user>")[1].split("</user>")[0].strip()}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.warning("Claude API call failed: %s", e)
        return None


def _call_openai(context: SpendingContext) -> str | None:
    """Call OpenAI API via openai SDK."""
    if not OPENAI_API_KEY:
        logger.debug("No OPENAI_API_KEY configured")
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = _build_prompt(context)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": prompt.split("<system>")[1].split("</system>")[0].strip()},
                {"role": "user", "content": prompt.split("<user>")[1].split("</user>")[0].strip()},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("OpenAI API call failed: %s", e)
        return None


def _call_ollama(context: SpendingContext) -> str | None:
    """Call local Ollama model."""
    try:
        import ollama

        prompt = _build_prompt(context)
        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {"role": "system", "content": prompt.split("<system>")[1].split("</system>")[0].strip()},
                {"role": "user", "content": prompt.split("<user>")[1].split("</user>")[0].strip()},
            ],
            options={"num_predict": 300},
        )
        return response["message"]["content"].strip()
    except Exception as e:
        logger.warning("Ollama API call failed: %s", e)
        return None


def _fallback_narrative(context: SpendingContext) -> str:
    """Deterministic template when all backends fail."""
    if context.days_of_salary > 0:
        money_context = f"costs you {context.days_of_salary:.1f} days of work"
    else:
        money_context = f"is ${context.price:.2f}"

    if context.score >= 0.7:
        return (
            f"Hold up. '{context.product_name}' {money_context}. "
            f"You already have {context.similar_items_count} similar items you haven't used. "
            f"Your impulse score is {context.score:.2f}/1.0 — that's high. "
            "Take a breath. Do you really need this?"
        )
    elif context.score >= 0.4:
        return (
            f"Think for a moment. '{context.product_name}' {money_context}. "
            f"Your monthly average spend is ${context.monthly_avg:.0f}. "
            f"Impulse score: {context.score:.2f}/1.0 — moderate risk. "
            "Is this a want or a need?"
        )
    return (
        f"Quick check: '{context.product_name}' {money_context}. "
        f"Low impulse risk ({context.score:.2f}/1.0). "
        "Still — wait 2 minutes before deciding."
    )


_BACKEND_CALLERS = {
    "claude": _call_claude,
    "openai": _call_openai,
    "ollama": _call_ollama,
}


def generate_narrative(context: SpendingContext) -> str:
    """Generate financial narrative via priority backend chain.

    Order is configured via AIB_LLM_ORDER env var (default: ollama,claude,openai).
    Falls back through chain until one succeeds, then to deterministic template.
    """
    for backend_name in LLM_BACKEND_ORDER:
        caller = _BACKEND_CALLERS.get(backend_name.strip().lower())
        if caller:
            result = caller(context)
            if result:
                logger.info("Narrative generated via %s", backend_name)
                return result

    logger.info("All LLM backends failed. Using deterministic fallback narrative.")
    return _fallback_narrative(context)
