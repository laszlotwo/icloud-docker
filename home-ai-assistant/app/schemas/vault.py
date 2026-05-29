from datetime import datetime

from pydantic import BaseModel


class VaultEntryCreate(BaseModel):
    title: str
    category: str | None = None
    url: str | None = None
    username: str | None = None
    password: str
    notes: str | None = None


class VaultEntryUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    url: str | None = None
    username: str | None = None
    password: str | None = None
    notes: str | None = None


class VaultEntryDecrypted(BaseModel):
    id: int
    title: str
    category: str | None
    url: str | None
    username: str | None
    password: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class VaultEntrySummary(BaseModel):
    id: int
    title: str
    category: str | None
    url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VaultUnlockRequest(BaseModel):
    master_password: str
