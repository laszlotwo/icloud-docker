from datetime import datetime

from pydantic import BaseModel


class LocationCreate(BaseModel):
    item_name: str
    location: str
    description: str | None = None
    room: str | None = None
    container: str | None = None
    tags: str | None = None


class LocationUpdate(BaseModel):
    item_name: str | None = None
    location: str | None = None
    description: str | None = None
    room: str | None = None
    container: str | None = None
    tags: str | None = None


class LocationResponse(BaseModel):
    id: int
    item_name: str
    location: str
    description: str | None
    room: str | None
    container: str | None
    tags: str | None
    last_confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
