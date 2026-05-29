import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_session_id, require_vault_key
from app.models.vault import VaultEntry
from app.schemas.vault import VaultEntryCreate, VaultEntryDecrypted, VaultEntrySummary, VaultUnlockRequest
from app.services.encryption import decrypt_field, derive_key, encrypt_field, generate_salt

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])


@router.post("/unlock")
def unlock_vault(body: VaultUnlockRequest, request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")

    # Verify the master password by deriving a test key (no stored hash needed,
    # we just store the key in memory and rely on decryption failure for wrong passwords)
    test_salt = b"\x00" * 16
    key = derive_key(body.master_password, test_salt)

    if not hasattr(request.app.state, "vault_sessions"):
        request.app.state.vault_sessions = {}

    request.app.state.vault_sessions[session_id] = {
        "key": body.master_password,  # store password, not derived key (key is per-entry)
        "unlocked_at": time.time(),
    }
    return {"unlocked": True}


@router.post("/lock")
def lock_vault(request: Request):
    session_id = request.cookies.get("session_id", "")
    vault_sessions: dict = getattr(request.app.state, "vault_sessions", {})
    vault_sessions.pop(session_id, None)
    return {"locked": True}


def _get_master_password(request: Request) -> str:
    from app.config import settings
    session_id = request.cookies.get("session_id", "")
    vault_sessions: dict = getattr(request.app.state, "vault_sessions", {})
    entry = vault_sessions.get(session_id)
    if not entry:
        raise HTTPException(status_code=403, detail="密码库已锁定，请先解锁")
    if time.time() - entry["unlocked_at"] > settings.VAULT_SESSION_TIMEOUT_MINUTES * 60:
        vault_sessions.pop(session_id, None)
        raise HTTPException(status_code=403, detail="密码库会话已超时，请重新解锁")
    return entry["key"]


@router.get("", response_model=list[VaultEntrySummary])
def list_vault_entries(
    request: Request,
    db: Session = Depends(get_db),
):
    _get_master_password(request)  # require unlock
    return db.query(VaultEntry).order_by(VaultEntry.created_at.desc()).all()


@router.post("", response_model=VaultEntrySummary)
def create_vault_entry(body: VaultEntryCreate, request: Request, db: Session = Depends(get_db)):
    master_password = _get_master_password(request)
    salt = generate_salt()
    key = derive_key(master_password, salt)

    entry = VaultEntry(
        title=body.title,
        category=body.category,
        url=body.url,
        salt=salt,
        username_encrypted=encrypt_field(body.username, key) if body.username else None,
        password_encrypted=encrypt_field(body.password, key),
        notes_encrypted=encrypt_field(body.notes, key) if body.notes else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=VaultEntryDecrypted)
def get_vault_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    master_password = _get_master_password(request)
    entry = db.get(VaultEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")

    key = derive_key(master_password, entry.salt)
    try:
        return VaultEntryDecrypted(
            id=entry.id,
            title=entry.title,
            category=entry.category,
            url=entry.url,
            username=decrypt_field(entry.username_encrypted, key) if entry.username_encrypted else None,
            password=decrypt_field(entry.password_encrypted, key),
            notes=decrypt_field(entry.notes_encrypted, key) if entry.notes_encrypted else None,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    except Exception:
        raise HTTPException(status_code=403, detail="解密失败，主密码可能不正确")


@router.put("/{entry_id}", response_model=VaultEntrySummary)
def update_vault_entry(entry_id: int, body: VaultEntryCreate, request: Request, db: Session = Depends(get_db)):
    master_password = _get_master_password(request)
    entry = db.get(VaultEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")

    salt = generate_salt()
    key = derive_key(master_password, salt)
    entry.title = body.title
    entry.category = body.category
    entry.url = body.url
    entry.salt = salt
    entry.username_encrypted = encrypt_field(body.username, key) if body.username else None
    entry.password_encrypted = encrypt_field(body.password, key)
    entry.notes_encrypted = encrypt_field(body.notes, key) if body.notes else None
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}")
def delete_vault_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    _get_master_password(request)
    entry = db.get(VaultEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(entry)
    db.commit()
    return {"deleted": True}
