"""Essential items CRUD endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import EssentialItem
from backend.schemas.schemas import (
    EssentialItemCreate,
    EssentialItemResponse,
    EssentialItemUpdate,
)

router = APIRouter(prefix="/api/essentials", tags=["essentials"])


@router.get("", response_model=List[EssentialItemResponse])
def list_essentials(db: Session = Depends(get_db)):
    items = db.query(EssentialItem).order_by(EssentialItem.name).all()
    return items


@router.post("", response_model=EssentialItemResponse)
def create_essential(item: EssentialItemCreate, db: Session = Depends(get_db)):
    db_item = EssentialItem(name=item.name, category=item.category, notes=item.notes)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=EssentialItemResponse)
def update_essential(
    item_id: int, update: EssentialItemUpdate, db: Session = Depends(get_db)
):
    db_item = db.query(EssentialItem).filter(EssentialItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Essential item not found")
    if update.name is not None:
        db_item.name = update.name
    if update.category is not None:
        db_item.category = update.category
    if update.notes is not None:
        db_item.notes = update.notes
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_essential(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(EssentialItem).filter(EssentialItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Essential item not found")
    db.delete(db_item)
    db.commit()
    return {"status": "deleted", "id": item_id}
