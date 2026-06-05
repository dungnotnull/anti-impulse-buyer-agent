"""Data export endpoint — download spending history as CSV."""

import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import SpendingEvent, WishListItem

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/events-csv")
def export_events_csv(days: int = 365, db: Session = Depends(get_db)):
    """Download spending events as CSV."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None)

    events = (
        db.query(SpendingEvent)
        .filter(SpendingEvent.created_at >= since)
        .order_by(SpendingEvent.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "product_name", "price", "category", "url",
        "impulsivity_score", "score_tier", "decision",
        "challenge_difficulty", "challenge_passed", "created_at",
    ])

    for e in events:
        writer.writerow([
            e.id, e.product_name, e.price, e.category, e.url,
            e.impulsivity_score, e.score_tier, e.decision,
            e.challenge_difficulty, e.challenge_passed, e.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aib_spending_events.csv"},
    )


@router.get("/wishlist-csv")
def export_wishlist_csv(db: Session = Depends(get_db)):
    """Download wish list items as CSV."""
    items = (
        db.query(WishListItem)
        .order_by(WishListItem.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "product_name", "price", "category", "url",
        "created_at", "reviewed",
    ])

    for item in items:
        writer.writerow([
            item.id, item.product_name, item.price, item.category,
            item.url, item.created_at.isoformat(), item.reviewed,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aib_wishlist.csv"},
    )


@router.post("/purge")
def purge_data(db: Session = Depends(get_db)):
    """One-click data purge — deletes all events and wish list items."""
    db.query(SpendingEvent).delete()
    db.query(WishListItem).delete()
    db.commit()
    return {"status": "purged", "message": "All spending data deleted."}
