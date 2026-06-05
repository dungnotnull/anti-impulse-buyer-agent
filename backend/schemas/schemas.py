"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Intercept ───

class InterceptRequest(BaseModel):
    product_name: str = Field(..., max_length=512)
    price: float = Field(..., ge=0)
    category: str = Field(default="", max_length=128)
    url: str = Field(default="")
    page_title: str = Field(default="", max_length=1024)
    timestamp: Optional[datetime] = None


class InterceptResponse(BaseModel):
    impulsivity_score: float
    score_tier: str  # low | medium | high
    narrative: str
    challenge_difficulty: str  # easy | medium | hard
    similar_owned_count: int = 0
    dark_pattern_warnings: list[str] = []


# ─── Events ───

class EventLogRequest(BaseModel):
    product_name: str = Field(..., max_length=512)
    price: float = Field(..., ge=0)
    category: str = Field(default="", max_length=128)
    url: str = Field(default="")
    impulsivity_score: float = 0.0
    score_tier: str = "low"
    decision: str = "blocked"  # blocked | proceeded | wishlisted
    narrative: str = ""
    challenge_difficulty: str = "easy"
    challenge_passed: int = 0


class EventLogResponse(BaseModel):
    id: int
    created_at: datetime


# ─── Essential Items ───

class EssentialItemCreate(BaseModel):
    name: str = Field(..., max_length=512)
    category: str = Field(default="", max_length=128)
    notes: str = Field(default="")


class EssentialItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class EssentialItemResponse(BaseModel):
    id: int
    name: str
    category: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Wish List ───

class WishListResponse(BaseModel):
    id: int
    product_name: str
    price: float
    category: str
    url: str
    created_at: datetime
    reviewed: int

    model_config = {"from_attributes": True}


# ─── Spending Summary ───

class SpendingSummaryResponse(BaseModel):
    total_blocked: int = 0
    total_proceeded: int = 0
    total_wishlisted: int = 0
    money_saved: float = 0.0
    recent_events: list = []
    current_streak_days: int = 0
