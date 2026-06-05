"""Prompt improvement loop for LLM narrative generation.

Analyzes user feedback data (whether users proceeded, blocked, or wishlisted
after seeing a narrative) and suggests prompt refinements to make the
narratives more effective at preventing impulse purchases.

Runs weekly as part of the SECOND-KNOWLEDGE-BRAIN auto-update cycle.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_feedback(db_session=None) -> dict[str, Any]:
    """Analyze purchase decisions as feedback on narrative effectiveness.

    Returns aggregate metrics on which narrative approaches work best.
    Falls back to sample data if no DB connection.
    """
    feedback = {
        "total_intercepts": 0,
        "proceeded": 0,
        "blocked": 0,
        "wishlisted": 0,
        "block_rate_by_tier": {"low": 0, "medium": 0, "high": 0},
        "total_by_tier": {"low": 0, "medium": 0, "high": 0},
    }

    if db_session:
        from backend.models.models import SpendingEvent

        events = db_session.query(SpendingEvent).all()
        feedback["total_intercepts"] = len(events)

        for e in events:
            if e.decision == "proceeded":
                feedback["proceeded"] += 1
            elif e.decision == "blocked":
                feedback["blocked"] += 1
            elif e.decision == "wishlisted":
                feedback["wishlisted"] += 1

            tier = e.score_tier or "low"
            feedback["total_by_tier"][tier] = feedback["total_by_tier"].get(tier, 0) + 1
            if e.decision in ("blocked", "wishlisted"):
                feedback["block_rate_by_tier"][tier] = (
                    feedback["block_rate_by_tier"].get(tier, 0) + 1
                )

        # Calculate rates
        for tier in feedback["block_rate_by_tier"]:
            total = feedback["total_by_tier"].get(tier, 0)
            blocked = feedback["block_rate_by_tier"].get(tier, 0)
            feedback["block_rate_by_tier"][tier] = (
                round(blocked / total, 4) if total > 0 else 0
            )
    else:
        # Sample data for testing
        feedback = {
            "total_intercepts": 100,
            "proceeded": 20,
            "blocked": 55,
            "wishlisted": 25,
            "block_rate_by_tier": {"low": 0.3, "medium": 0.6, "high": 0.85},
            "total_by_tier": {"low": 30, "medium": 40, "high": 30},
        }

    feedback["overall_block_rate"] = round(
        (feedback["blocked"] + feedback["wishlisted"])
        / max(feedback["total_intercepts"], 1),
        4,
    )
    return feedback


def generate_prompt_suggestions(feedback: dict[str, Any]) -> list[str]:
    """Generate prompt improvement suggestions based on feedback."""
    suggestions = []

    overall_block_rate = feedback.get("overall_block_rate", 0)

    if overall_block_rate < 0.5:
        suggestions.append(
            "Narratives are only blocking {:.0f}% of purchases. "
            "Consider making them more direct and specific about dollar amounts.".format(
                overall_block_rate * 100
            )
        )

    # Check low-tier effectiveness
    low_block = feedback.get("block_rate_by_tier", {}).get("low", 0)
    if low_block < 0.4:
        suggestions.append(
            "Low-score purchases have only {:.0f}% block rate. "
            "For low scores, emphasize the 'still waiting' angle — "
            "remind users that even small purchases add up.".format(low_block * 100)
        )

    high_block = feedback.get("block_rate_by_tier", {}).get("high", 0)
    if high_block < 0.75:
        suggestions.append(
            "High-score purchases have only {:.0f}% block rate. "
            "For high scores, add salary-calibrated language ('this costs X days of work') "
            "and reference the user's specific monthly spending.".format(high_block * 100)
        )

    if not suggestions:
        suggestions.append(
            "Current narrative effectiveness is within expected range. "
            "Monitor trends weekly for degradation."
        )

    return suggestions


def run_prompt_optimization(db_session=None) -> dict[str, Any]:
    """Run the full prompt optimization loop."""
    logger.info("Running prompt optimization...")

    feedback = analyze_feedback(db_session)
    suggestions = generate_prompt_suggestions(feedback)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feedback": feedback,
        "suggestions": suggestions,
    }

    logger.info("Prompt optimization complete. %d suggestion(s).", len(suggestions))
    for s in suggestions:
        logger.info("  - %s", s)

    return result


if __name__ == "__main__":
    run_prompt_optimization()
