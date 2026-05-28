from datetime import datetime

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    title: str
    description: str | None = None
    reminder_type: str
    trigger_spec: str


class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    reminder_type: str | None = None
    trigger_spec: str | None = None
    is_active: bool | None = None


class ReminderResponse(BaseModel):
    id: int
    title: str
    description: str | None
    reminder_type: str
    trigger_spec: str
    is_active: bool
    last_triggered_at: datetime | None
    next_trigger_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
