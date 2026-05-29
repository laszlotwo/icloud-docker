from datetime import datetime

from sqlalchemy import DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VaultEntry(Base):
    __tablename__ = "vault_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))  # wifi/bank/website/other
    url: Mapped[str | None] = mapped_column(String(500))

    # Per-entry salt for key derivation
    salt: Mapped[bytes] = mapped_column(LargeBinary(16), nullable=False)

    # AES-256-GCM encrypted fields: nonce + ciphertext stored together
    username_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    password_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    notes_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
