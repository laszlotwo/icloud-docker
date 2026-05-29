import io
import logging

import edge_tts

from app.config import settings

logger = logging.getLogger(__name__)


async def synthesize(text: str, voice: str | None = None) -> bytes:
    """Generate Chinese TTS audio, returns MP3 bytes."""
    voice = voice or settings.TTS_VOICE
    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()
