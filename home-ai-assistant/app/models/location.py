from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ItemLocation(Base):
    __tablename__ = "item_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    room: Mapped[str | None] = mapped_column(String(50))
    container: Mapped[str | None] = mapped_column(String(200))
    tags: Mapped[str | None] = mapped_column(String(500))
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
