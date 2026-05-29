from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate
from app.services.scheduler import remove_reminder_job, schedule_reminder

router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderResponse])
def list_reminders(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(Reminder)
    if not include_inactive:
        query = query.filter(Reminder.is_active == True)  # noqa: E712
    return query.order_by(Reminder.next_trigger_at.asc().nullslast()).all()


@router.post("", response_model=ReminderResponse)
def create_reminder(body: ReminderCreate, db: Session = Depends(get_db)):
    reminder = Reminder(**body.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    try:
        schedule_reminder(reminder.id, reminder.title, reminder.reminder_type, reminder.trigger_spec)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"提醒格式错误: {e}")
    return reminder


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return reminder


@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(reminder_id: int, body: ReminderUpdate, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(reminder, field, value)
    db.commit()
    db.refresh(reminder)
    remove_reminder_job(reminder.id)
    if reminder.is_active:
        try:
            schedule_reminder(reminder.id, reminder.title, reminder.reminder_type, reminder.trigger_spec)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"提醒格式错误: {e}")
    return reminder


@router.post("/{reminder_id}/toggle", response_model=ReminderResponse)
def toggle_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    reminder.is_active = not reminder.is_active
    db.commit()
    remove_reminder_job(reminder.id)
    if reminder.is_active:
        schedule_reminder(reminder.id, reminder.title, reminder.reminder_type, reminder.trigger_spec)
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")
    remove_reminder_job(reminder.id)
    db.delete(reminder)
    db.commit()
    return {"deleted": True}
