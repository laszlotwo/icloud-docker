from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db


def get_session_id(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
    return session_id


def get_vault_key(request: Request) -> bytes | None:
    """Returns the in-memory vault key for this session, or None if vault is locked."""
    session_id = get_session_id(request)
    vault_sessions: dict = getattr(request.app.state, "vault_sessions", {})
    entry = vault_sessions.get(session_id)
    if entry is None:
        return None
    import time
    from app.config import settings
    if time.time() - entry["unlocked_at"] > settings.VAULT_SESSION_TIMEOUT_MINUTES * 60:
        vault_sessions.pop(session_id, None)
        return None
    return entry["key"]


def require_vault_key(
    request: Request,
    vault_key: bytes | None = Depends(get_vault_key),
) -> bytes:
    if vault_key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="密码库已锁定，请先解锁",
        )
    return vault_key
