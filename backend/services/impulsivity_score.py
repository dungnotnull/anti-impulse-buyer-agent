"""Impulsivity Score computation engine."""

from datetime import datetime, timezone

from backend.config import IMPULSE_DEFAULTS


def compute_impulsivity_score(
    product_name: str,
    price: float,
    category: str,
    timestamp: datetime | None = None,
    recent_purchase_count: int = 0,
    recent_purchase_baseline: int = 1,
    essential_similarity: float = 0.0,
    monthly_avg_spend: float = 0.0,
    sentiment_multiplier: float = 1.0,
) -> tuple[float, str]:
    """Compute composite impulsivity score (0.0–1.0) and tier string.

    Args:
        essential_similarity: 0.0 (not essential) to 1.0 (matches essential list).
    Returns:
        (score, tier) where tier is 'low' (0-0.4), 'medium' (0.4-0.7), 'high' (0.7-1.0).
    """
    now = timestamp or datetime.now(timezone.utc)
    hour = now.hour

    # 1. Time-of-day factor: 0.0 at noon, 1.0 at midnight (1 AM peak)
    midnight = IMPULSE_DEFAULTS["midnight_weight"]
    afternoon = IMPULSE_DEFAULTS["afternoon_weight"]
    # Parabolic curve peaking at 1 AM
    time_of_day = midnight - (abs(hour - 1) / 12) * (midnight - afternoon)

    # 2. Essential similarity inverse: 0 = matches essentials, 1 = not essential
    essential_inv = 1.0 - essential_similarity

    # 3. Recent purchase frequency
    freq = (
        recent_purchase_count / max(recent_purchase_baseline, 1)
        if recent_purchase_baseline > 0
        else 0.0
    )
    recent_freq = min(freq, 1.0)

    # 4. Price-to-monthly ratio
    daily_spend = max(monthly_avg_spend / 30, 1.0)
    price_ratio = min(price / daily_spend, 1.0)

    # 5. Category impulse weight (hardcoded defaults; will be learned later)
    category_weights = {
        "fashion": 0.9,
        "electronics": 0.8,
        "accessories": 0.85,
        "toys": 0.75,
        "home_decor": 0.6,
        "books": 0.3,
        "groceries": 0.2,
        "health": 0.25,
        "fitness": 0.3,
        "tools": 0.4,
        "auto": 0.5,
        "office": 0.35,
        "pet": 0.3,
        "baby": 0.3,
        "food": 0.15,
    }
    cat_weight = category_weights.get(category.lower(), 0.5)

    # Composite formula
    score = (
        0.25 * time_of_day
        + 0.20 * essential_inv
        + 0.20 * recent_freq
        + 0.20 * price_ratio
        + 0.15 * cat_weight
    ) * sentiment_multiplier

    score = max(0.0, min(score, 1.0))

    # Determine tier
    if score < 0.4:
        tier = "low"
    elif score < 0.7:
        tier = "medium"
    else:
        tier = "high"

    return round(score, 4), tier
