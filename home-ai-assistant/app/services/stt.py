import asyncio
import io
import logging
import subprocess
import tempfile
import os
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)
_model: "WhisperModel | None" = None


def _get_model() -> "WhisperModel":
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper model: %s", settings.WHISPER_MODEL)
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _model


def _convert_to_wav(audio_bytes: bytes) -> bytes:
    """Convert any audio format to 16kHz mono WAV using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".webm", ".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_in_path, "-ar", "16000", "-ac", "1", tmp_out_path],
            capture_output=True,
            check=True,
        )
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def _transcribe_sync(audio_bytes: bytes) -> str:
    wav_bytes = _convert_to_wav(audio_bytes)
    model = _get_model()
    segments, _ = model.transcribe(
        io.BytesIO(wav_bytes),
        language="zh",
        beam_size=3,
        vad_filter=True,
    )
    return "".join(s.text for s in segments).strip()


async def transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to Chinese text. Runs in threadpool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_bytes)
