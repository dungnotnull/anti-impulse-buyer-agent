"""SQLAlchemy ORM models."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from backend.database import Base


def _utcnow_naive():
    """Return naive UTC datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SpendingEvent(Base):
    """Log of every purchase intercept event."""

    __tablename__ = "spending_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(512), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    category = Column(String(128), default="")
    url = Column(Text, default="")
    impulsivity_score = Column(Float, nullable=False, default=0.0)
    score_tier = Column(String(16), nullable=False, default="low")
    decision = Column(
        String(16), nullable=False, default="blocked"
    )  # blocked | proceeded | wishlisted
    narrative = Column(Text, default="")
    challenge_difficulty = Column(String(16), default="easy")
    challenge_passed = Column(Integer, default=0)  # 0=not attempted, 1=passed, -1=failed
    created_at = Column(DateTime, nullable=False, default=_utcnow_naive)


class WishListItem(Base):
    """Deferred purchase items the user 'wish-listed' instead of buying."""

    __tablename__ = "wish_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(512), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    category = Column(String(128), default="")
    url = Column(Text, default="")
    source_event_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow_naive)
    reviewed = Column(Integer, default=0)  # 0 = pending, 1 = reviewed


class EssentialItem(Base):
    """User-curated whitelist of allowable purchases."""

    __tablename__ = "essential_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(512), nullable=False)
    category = Column(String(128), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, nullable=False, default=_utcnow_naive)


class UserProfile(Base):
    """Single-user profile settings."""

    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monthly_income = Column(Float, default=0.0)
    monthly_avg_spend = Column(Float, default=0.0)
    data_retention_days = Column(Integer, default=90)
    llm_mode = Column(
        String(16), default="local"
    )  # "local" | "cloud" (opt-in)
    created_at = Column(DateTime, nullable=False, default=_utcnow_naive)
    updated_at = Column(
        DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive
    )
