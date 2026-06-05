"""User profile settings endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import UserProfile
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    monthly_income: Optional[float] = None
    monthly_avg_spend: Optional[float] = None
    data_retention_days: Optional[int] = None
    llm_mode: Optional[str] = None  # "local" or "cloud"


class ProfileResponse(BaseModel):
    monthly_income: float = 0.0
    monthly_avg_spend: float = 0.0
    data_retention_days: int = 90
    llm_mode: str = "local"

    model_config = {"from_attributes": True}


def _get_or_create_profile(db: Session) -> UserProfile:
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(req: ProfileUpdateRequest, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    if req.monthly_income is not None:
        profile.monthly_income = req.monthly_income
    if req.monthly_avg_spend is not None:
        profile.monthly_avg_spend = req.monthly_avg_spend
    if req.data_retention_days is not None:
        profile.data_retention_days = req.data_retention_days
    if req.llm_mode is not None:
        profile.llm_mode = req.llm_mode
    profile.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(profile)
    return profile
