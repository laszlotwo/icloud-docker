import json
import uuid

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_vault_key
from app.models.reminder import ConversationHistory
from app.services.claude_client import chat_stream

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

MAX_HISTORY = 20  # messages to keep in context


class ChatRequest(BaseModel):
    message: str


def _get_or_create_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return session_id


@router.post("")
async def chat_endpoint(
    body: ChatRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    vault_key: bytes | None = Depends(get_vault_key),
):
    session_id = _get_or_create_session(request, response)

    # Load recent history
    history = (
        db.query(ConversationHistory)
        .filter(ConversationHistory.session_id == session_id)
        .order_by(ConversationHistory.created_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )
    history.reverse()

    messages = []
    for h in history:
        msg: dict = {"role": h.role, "content": h.content}
        messages.append(msg)
    messages.append({"role": "user", "content": body.message})

    # Save user message
    db.add(ConversationHistory(session_id=session_id, role="user", content=body.message))
    db.commit()

    collected_response = []

    async def generate():
        async for token in chat_stream(messages, db, vault_key):
            collected_response.append(token)
            yield f"data: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"

        full_response = "".join(collected_response)
        db.add(ConversationHistory(session_id=session_id, role="assistant", content=full_response))
        db.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
def get_history(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 50,
):
    session_id = request.cookies.get("session_id", "")
    history = (
        db.query(ConversationHistory)
        .filter(ConversationHistory.session_id == session_id)
        .order_by(ConversationHistory.created_at.asc())
        .limit(limit)
        .all()
    )
    return [{"role": h.role, "content": h.content, "created_at": h.created_at.isoformat()} for h in history]


@router.delete("/history")
def clear_history(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id", "")
    db.query(ConversationHistory).filter(ConversationHistory.session_id == session_id).delete()
    db.commit()
    return {"cleared": True}
