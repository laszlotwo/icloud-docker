from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import ItemLocation
from app.schemas.location import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(room: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ItemLocation)
    if room:
        query = query.filter(ItemLocation.room == room)
    return query.order_by(ItemLocation.item_name).all()


@router.get("/search", response_model=list[LocationResponse])
def search_locations(q: str, db: Session = Depends(get_db)):
    like_q = f"%{q}%"
    return db.query(ItemLocation).filter(
        (ItemLocation.item_name.like(like_q)) |
        (ItemLocation.location.like(like_q)) |
        (ItemLocation.description.like(like_q))
    ).all()


@router.post("", response_model=LocationResponse)
def create_location(body: LocationCreate, db: Session = Depends(get_db)):
    location = ItemLocation(**body.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(ItemLocation, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="记录不存在")
    return loc


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, body: LocationUpdate, db: Session = Depends(get_db)):
    loc = db.get(ItemLocation, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(loc, field, value)
    db.commit()
    db.refresh(loc)
    return loc


@router.post("/{location_id}/confirm", response_model=LocationResponse)
def confirm_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(ItemLocation, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="记录不存在")
    loc.last_confirmed_at = datetime.now()
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(ItemLocation, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(loc)
    db.commit()
    return {"deleted": True}
