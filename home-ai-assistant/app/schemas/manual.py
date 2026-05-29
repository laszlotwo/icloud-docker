from datetime import datetime

from pydantic import BaseModel


class ManualCreate(BaseModel):
    name: str
    brand: str | None = None
    model_number: str | None = None
    category: str | None = None
    content: str
    tags: str | None = None


class ManualUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    model_number: str | None = None
    category: str | None = None
    content: str | None = None
    tags: str | None = None


class ManualResponse(BaseModel):
    id: int
    name: str
    brand: str | None
    model_number: str | None
    category: str | None
    content: str
    tags: str | None
    file_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManualSummary(BaseModel):
    id: int
    name: str
    brand: str | None
    category: str | None
    tags: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
