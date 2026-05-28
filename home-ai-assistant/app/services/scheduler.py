import asyncio
import logging
from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_ws_broadcast_fn = None  # injected at startup


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        jobstores = {"default": SQLAlchemyJobStore(url=settings.DATABASE_URL)}
        _scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Shanghai")
    return _scheduler


def set_broadcast_fn(fn):
    global _ws_broadcast_fn
    _ws_broadcast_fn = fn


async def _fire_reminder(reminder_id: int, title: str):
    logger.info("Reminder fired: id=%d title=%s", reminder_id, title)
    if _ws_broadcast_fn:
        await _ws_broadcast_fn({
            "type": "reminder_triggered",
            "id": reminder_id,
            "title": title,
            "timestamp": datetime.now().isoformat(),
        })

    from app.database import SessionLocal
    from app.models.reminder import Reminder

    db = SessionLocal()
    try:
        reminder = db.get(Reminder, reminder_id)
        if reminder:
            reminder.last_triggered_at = datetime.now()
            db.commit()
    finally:
        db.close()


def schedule_reminder(reminder_id: int, title: str, reminder_type: str, trigger_spec: str):
    scheduler = get_scheduler()
    job_id = f"reminder_{reminder_id}"

    if reminder_type == "once":
        trigger_dt = datetime.fromisoformat(trigger_spec)
        scheduler.add_job(
            _fire_reminder,
            "date",
            run_date=trigger_dt,
            args=[reminder_id, title],
            id=job_id,
            replace_existing=True,
        )
    elif reminder_type == "daily":
        time_part = trigger_spec  # "HH:MM"
        hour, minute = time_part.split(":")
        scheduler.add_job(
            _fire_reminder,
            "cron",
            hour=int(hour),
            minute=int(minute),
            args=[reminder_id, title],
            id=job_id,
            replace_existing=True,
        )
    elif reminder_type == "weekly":
        # trigger_spec format: "Mon,Wed,Fri HH:MM"
        days_part, time_part = trigger_spec.split(" ")
        hour, minute = time_part.split(":")
        scheduler.add_job(
            _fire_reminder,
            "cron",
            day_of_week=days_part,
            hour=int(hour),
            minute=int(minute),
            args=[reminder_id, title],
            id=job_id,
            replace_existing=True,
        )
    elif reminder_type == "cron":
        from apscheduler.triggers.cron import CronTrigger
        scheduler.add_job(
            _fire_reminder,
            CronTrigger.from_crontab(trigger_spec),
            args=[reminder_id, title],
            id=job_id,
            replace_existing=True,
        )


def remove_reminder_job(reminder_id: int):
    scheduler = get_scheduler()
    job_id = f"reminder_{reminder_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def restore_reminder_jobs():
    from app.database import SessionLocal
    from app.models.reminder import Reminder

    db = SessionLocal()
    try:
        reminders = db.query(Reminder).filter(Reminder.is_active == True).all()  # noqa: E712
        for r in reminders:
            try:
                schedule_reminder(r.id, r.title, r.reminder_type, r.trigger_spec)
            except Exception as e:
                logger.warning("Failed to restore reminder %d: %s", r.id, e)
    finally:
        db.close()
