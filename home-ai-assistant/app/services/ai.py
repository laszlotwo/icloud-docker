"""AI provider facade. Dispatches to Gemini or Claude based on settings.AI_PROVIDER."""
from typing import AsyncIterator

from app.config import settings


def _use_gemini() -> bool:
    return settings.AI_PROVIDER.lower() == "gemini"


async def chat(messages: list[dict], db, vault_key: bytes | None = None) -> str:
    if _use_gemini():
        from app.services import gemini_client
        return await gemini_client.chat(messages, db, vault_key)
    from app.services import claude_client
    return await claude_client.chat(messages, db, vault_key)


async def chat_stream(messages: list[dict], db, vault_key: bytes | None = None) -> AsyncIterator[str]:
    if _use_gemini():
        from app.services import gemini_client
        async for token in gemini_client.chat_stream(messages, db, vault_key):
            yield token
    else:
        from app.services import claude_client
        async for token in claude_client.chat_stream(messages, db, vault_key):
            yield token
