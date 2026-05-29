import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import stt, tts
from app.services.ai import chat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["voice"])

# WebSocket connection manager for broadcasting reminder notifications
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws) if hasattr(self.active, "discard") else (
            self.active.remove(ws) if ws in self.active else None
        )

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.active:
                self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    audio_chunks: list[bytes] = []
    session_messages: list[dict] = []

    try:
        while True:
            data = await websocket.receive()

            if "text" in data:
                msg = json.loads(data["text"])
                msg_type = msg.get("type")

                if msg_type == "start_recording":
                    audio_chunks = []

                elif msg_type == "end_recording":
                    if not audio_chunks:
                        await websocket.send_text(json.dumps({"type": "error", "message": "未录到音频"}))
                        continue

                    audio_bytes = b"".join(audio_chunks)
                    await websocket.send_text(json.dumps({"type": "processing", "step": "stt"}))

                    try:
                        transcript = await stt.transcribe(audio_bytes)
                    except Exception as e:
                        logger.exception("STT error")
                        await websocket.send_text(json.dumps({"type": "error", "message": f"语音识别失败: {e}"}))
                        continue

                    await websocket.send_text(json.dumps({"type": "transcript", "text": transcript}, ensure_ascii=False))

                    if not transcript.strip():
                        await websocket.send_text(json.dumps({"type": "error", "message": "未能识别语音内容"}))
                        continue

                    await websocket.send_text(json.dumps({"type": "processing", "step": "llm"}))
                    session_messages.append({"role": "user", "content": transcript})

                    try:
                        response_text = await chat(session_messages, db)
                    except Exception as e:
                        logger.exception("Claude error")
                        await websocket.send_text(json.dumps({"type": "error", "message": f"AI回复失败: {e}"}))
                        continue

                    session_messages.append({"role": "assistant", "content": response_text})
                    await websocket.send_text(json.dumps({"type": "response", "text": response_text}, ensure_ascii=False))

                    await websocket.send_text(json.dumps({"type": "processing", "step": "tts"}))
                    try:
                        audio_data = await tts.synthesize(response_text)
                    except Exception as e:
                        logger.exception("TTS error")
                        await websocket.send_text(json.dumps({"type": "error", "message": f"语音合成失败: {e}"}))
                        continue

                    await websocket.send_text(json.dumps({"type": "audio_start"}))
                    chunk_size = 4096
                    for i in range(0, len(audio_data), chunk_size):
                        await websocket.send_bytes(audio_data[i:i + chunk_size])
                    await websocket.send_text(json.dumps({"type": "audio_end"}))

            elif "bytes" in data:
                audio_chunks.append(data["bytes"])

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        logger.exception("Voice WebSocket error")
        manager.disconnect(websocket)
