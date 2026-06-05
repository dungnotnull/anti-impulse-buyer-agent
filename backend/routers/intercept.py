"""POST /api/intercept — main checkout interception endpoint.

Full pipeline:
  1. Classify product (BART-MNLI → keyword fallback)
  2. Semantic essential-item matching (MiniLM → Jaccard fallback)
  3. Sentiment analysis (Twitter-RoBERTa → neutral)
  4. Composite impulsivity score (all 5 factors)
  5. LLM narrative generation (Claude → OpenAI → Ollama → template)
  6. Dark pattern detection on page content
  7. Return score, narrative, challenge info, warnings
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import EssentialItem, SpendingEvent, UserProfile
from backend.schemas.schemas import InterceptRequest, InterceptResponse
from backend.services.challenge_generator import get_challenge
from backend.services.dark_pattern_detector import get_dark_pattern_warnings
from backend.services.impulsivity_score import compute_impulsivity_score
from backend.services.llm_router import SpendingContext, generate_narrative
from backend.ml_services.tasks import (
    classify_product_async,
    compute_similarity_async,
    analyze_sentiment_async,
    get_browsing_session_texts,
)

router = APIRouter(prefix="/api", tags=["intercept"])


@router.post("/intercept", response_model=InterceptResponse)
def intercept_checkout(req: InterceptRequest, db: Session = Depends(get_db)):
    """Main intercept flow: classify → score → narrate → return challenge info."""
    timestamp = req.timestamp or datetime.now(timezone.utc)

    # 1. Classify product (BART-MNLI with graceful fallback)
    category = req.category or classify_product_async(req.product_name)

    # 2. Fetch essential items for semantic matching
    essentials = db.query(EssentialItem.name).all()
    essential_names = [e.name for e in essentials]
    essential_similarity = compute_similarity_async(
        req.product_name, essential_names
    )

    # 3. Sentiment analysis from browsing context
    browsing_texts = get_browsing_session_texts()
    sentiment_multiplier = analyze_sentiment_async(browsing_texts)

    # 4. Fetch user profile
    profile = db.query(UserProfile).first()
    monthly_avg = profile.monthly_avg_spend if profile else 0.0

    # 5. Count recent purchases (last 48h)
    from_ts = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    recent_count = (
        db.query(func.count(SpendingEvent.id))
        .filter(SpendingEvent.created_at >= from_ts)
        .scalar()
        or 0
    )
    baseline = max(recent_count, 1)

    # 6. Count similar items owned
    similar_count = 0
    if category != "other":
        similar_count = (
            db.query(func.count(SpendingEvent.id))
            .filter(SpendingEvent.category == category)
            .filter(SpendingEvent.decision.in_(["proceeded"]))
            .scalar()
            or 0
        )

    # 7. Compute impulsivity score (all 5 factors + sentiment)
    score, tier = compute_impulsivity_score(
        product_name=req.product_name,
        price=req.price,
        category=category,
        timestamp=timestamp,
        recent_purchase_count=recent_count,
        recent_purchase_baseline=baseline,
        essential_similarity=essential_similarity,
        monthly_avg_spend=monthly_avg,
        sentiment_multiplier=sentiment_multiplier,
    )

    # 8. Generate financial narrative via LLM router
    days_of_salary = 0.0
    if profile and profile.monthly_income > 0:
        daily_salary = profile.monthly_income / 30
        if daily_salary > 0:
            days_of_salary = req.price / daily_salary

    context = SpendingContext(
        product_name=req.product_name,
        price=req.price,
        monthly_avg=monthly_avg,
        similar_items_count=similar_count,
        score=score,
        days_of_salary=days_of_salary,
    )
    narrative = generate_narrative(context)

    # 9. Dark pattern detection on page title/url context
    dark_pattern_warnings = get_dark_pattern_warnings(req.page_title or "")

    # 10. Determine challenge difficulty
    diff_map = {"low": "easy", "medium": "medium", "high": "hard"}
    challenge_diff = diff_map[tier]

    return InterceptResponse(
        impulsivity_score=score,
        score_tier=tier,
        narrative=narrative,
        challenge_difficulty=challenge_diff,
        similar_owned_count=similar_count,
        dark_pattern_warnings=dark_pattern_warnings,
    )
