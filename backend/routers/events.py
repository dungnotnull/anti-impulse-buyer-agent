"""Event logging endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import SpendingEvent, WishListItem
from backend.schemas.schemas import EventLogRequest, EventLogResponse

router = APIRouter(prefix="/api", tags=["events"])


@router.post("/events", response_model=EventLogResponse)
def log_event(req: EventLogRequest, db: Session = Depends(get_db)):
    """Log a purchase intercept decision."""
    event = SpendingEvent(
        product_name=req.product_name,
        price=req.price,
        category=req.category,
        url=req.url,
        impulsivity_score=req.impulsivity_score,
        score_tier=req.score_tier,
        decision=req.decision,
        narrative=req.narrative,
        challenge_difficulty=req.challenge_difficulty,
        challenge_passed=req.challenge_passed,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return EventLogResponse(id=event.id, created_at=event.created_at)


@router.post("/wishlist")
def add_to_wishlist(
    product_name: str,
    price: float,
    category: str = "",
    url: str = "",
    source_event_id: int = None,
    db: Session = Depends(get_db),
):
    """Add a deferred purchase to the wish list."""
    item = WishListItem(
        product_name=product_name,
        price=price,
        category=category,
        url=url,
        source_event_id=source_event_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": "wishlisted"}


@router.get("/events/recent")
def get_recent_events(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch recent purchase events."""
    events = (
        db.query(SpendingEvent)
        .order_by(SpendingEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
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
        for e in events
    ]
