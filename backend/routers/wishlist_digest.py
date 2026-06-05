"""Wish List weekly digest generation via LLM router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import UserProfile, WishListItem
from backend.services.llm_router import SpendingContext, generate_narrative

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("/digest")
def generate_digest(db: Session = Depends(get_db)):
    """Generate a weekly wish list digest narrative.

    Reviews all unreviewed wish list items and generates
    a summary narrative via the LLM router.
    """
    profile = db.query(UserProfile).first()
    items = (
        db.query(WishListItem)
        .filter(WishListItem.reviewed == 0)
        .order_by(WishListItem.created_at.desc())
        .all()
    )

    if not items:
        return {"digest": "No items in your wish list this week. Great job resisting impulse purchases!"}

    total_cost = sum(item.price for item in items)
    monthly_avg = profile.monthly_avg_spend if profile else 0

    digest_entries = []
    for item in items:
        ctx = SpendingContext(
            product_name=item.product_name,
            price=item.price,
            monthly_avg=monthly_avg / 30 if monthly_avg else 0,
            similar_items_count=0,
            score=0.5,
            days_of_salary=(item.price / (profile.monthly_income / 30))
            if profile and profile.monthly_income > 0 else 0,
        )
        entry = generate_narrative(ctx)
        digest_entries.append({
            "product_name": item.product_name,
            "price": item.price,
            "category": item.category,
            "narrative": entry,
            "created_at": item.created_at.isoformat() if item.created_at else "",
        })

    if profile and profile.monthly_income > 0:
        days_of_work = total_cost / (profile.monthly_income / 30)
        summary = (
            f"Your wish list has {len(items)} items totaling ${total_cost:.2f}. "
            f"That's equivalent to {days_of_work:.1f} days of work. "
            f"Review each item below and decide if you still want it."
        )
    else:
        summary = (
            f"Your wish list has {len(items)} items totaling ${total_cost:.2f}. "
            "Review each item below and decide if you still want it."
        )

    return {
        "summary": summary,
        "items": digest_entries,
        "total_cost": total_cost,
        "item_count": len(items),
    }


@router.post("/digest/review")
def mark_reviewed(db: Session = Depends(get_db)):
    """Mark all unreviewed wish list items as reviewed."""
    items = (
        db.query(WishListItem)
        .filter(WishListItem.reviewed == 0)
        .all()
    )
    for item in items:
        item.reviewed = 1
    db.commit()
    return {"status": "ok", "reviewed_count": len(items)}
