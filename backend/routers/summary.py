"""Spending summary dashboard endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import SpendingEvent
from backend.schemas.schemas import SpendingSummaryResponse

router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/summary", response_model=SpendingSummaryResponse)
def get_summary(days: int = 30, db: Session = Depends(get_db)):
    """Aggregate spending summary for the dashboard."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None)

    events = (
        db.query(SpendingEvent)
        .filter(SpendingEvent.created_at >= since)
        .all()
    )

    total_blocked = sum(1 for e in events if e.decision == "blocked")
    total_proceeded = sum(1 for e in events if e.decision == "proceeded")
    total_wishlisted = sum(1 for e in events if e.decision == "wishlisted")

    # Money saved = sum of blocked + wishlisted prices
    money_saved = sum(
        e.price for e in events if e.decision in ("blocked", "wishlisted")
    )

    # Recent events (last 10)
    recent = sorted(events, key=lambda e: e.created_at, reverse=True)[:10]
    recent_list = [
        {
            "id": e.id,
            "product_name": e.product_name,
            "price": e.price,
            "category": e.category,
            "decision": e.decision,
            "impulsivity_score": e.impulsivity_score,
            "score_tier": e.score_tier,
            "created_at": e.created_at.isoformat(),
        }
        for e in recent
    ]

    # Current streak = consecutive days with no "proceeded" events
    streak = 0
    check_date = datetime.now(timezone.utc).date()
    today_events = [e for e in events if e.created_at.date() == check_date]
    has_proceeded_today = any(e.decision == "proceeded" for e in today_events)

    if not has_proceeded_today:
        for i in range(365):
            day = check_date - timedelta(days=i)
            day_events = [e for e in events if e.created_at.date() == day]
            if any(e.decision == "proceeded" for e in day_events):
                break
            streak += 1

    return SpendingSummaryResponse(
        total_blocked=total_blocked,
        total_proceeded=total_proceeded,
        total_wishlisted=total_wishlisted,
        money_saved=round(money_saved, 2),
        recent_events=recent_list,
        current_streak_days=streak,
    )
