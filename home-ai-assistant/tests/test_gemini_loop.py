"""Mock-based test of the Gemini agentic loop (no live API key needed)."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


def _part(text=None, function_call=None):
    return SimpleNamespace(text=text, function_call=function_call)


def _response(parts, text=""):
    candidate = SimpleNamespace(content=SimpleNamespace(parts=parts))
    return SimpleNamespace(candidates=[candidate], text=text)


@pytest.mark.asyncio
async def test_chat_executes_tool_then_returns_text():
    from app.services import gemini_client

    fc = SimpleNamespace(name="get_current_time", args={})
    # First response asks for a tool call; second returns final text.
    responses = [
        _response([_part(function_call=fc)]),
        _response([_part(text="现在是下午3点。")], text="现在是下午3点。"),
    ]

    fake_models = SimpleNamespace(generate_content=AsyncMock(side_effect=responses))
    fake_client = SimpleNamespace(aio=SimpleNamespace(models=fake_models))

    captured = {}

    def fake_dispatch(name, args, db, vault_key):
        captured["name"] = name
        return {"time": "15:00"}

    with patch.object(gemini_client, "_get_client", return_value=fake_client), \
         patch.object(gemini_client, "dispatch_tool", side_effect=fake_dispatch):
        result = await gemini_client.chat([{"role": "user", "content": "现在几点"}], db=None)

    assert captured["name"] == "get_current_time"
    assert result == "现在是下午3点。"
    assert fake_models.generate_content.await_count == 2
