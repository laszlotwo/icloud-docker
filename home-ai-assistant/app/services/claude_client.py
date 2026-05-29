import json
import logging
from typing import AsyncIterator

import anthropic

from app.config import settings
from app.services.tool_definitions import SYSTEM_PROMPT, TOOLS
from app.services.tool_handlers import dispatch_tool

logger = logging.getLogger(__name__)


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def chat(
    messages: list[dict],
    db,
    vault_key: bytes | None = None,
) -> str:
    """Run the agentic tool-use loop and return final text response."""
    client = _get_client()
    tools = TOOLS if vault_key is not None else [t for t in TOOLS if t["name"] != "list_vault_titles"]

    while True:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )

        if response.stop_reason == "end_turn":
            text_parts = [block.text for block in response.content if hasattr(block, "text")]
            return "".join(text_parts)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Tool call: %s(%s)", block.name, block.input)
                    result = dispatch_tool(block.name, block.input, db, vault_key)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
        else:
            # Unexpected stop reason
            text_parts = [block.text for block in response.content if hasattr(block, "text")]
            return "".join(text_parts) or "抱歉，发生了未知错误。"


async def chat_stream(
    messages: list[dict],
    db,
    vault_key: bytes | None = None,
) -> AsyncIterator[str]:
    """Streaming version: yields text tokens, handles tool_use internally."""
    client = _get_client()
    tools = TOOLS if vault_key is not None else [t for t in TOOLS if t["name"] != "list_vault_titles"]

    while True:
        full_text = ""
        tool_uses = []
        stop_reason = None

        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        ) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            full_text += event.delta.text
                            yield event.delta.text
            final_message = await stream.get_final_message()
            stop_reason = final_message.stop_reason
            for block in final_message.content:
                if block.type == "tool_use":
                    tool_uses.append(block)

        if stop_reason != "tool_use" or not tool_uses:
            break

        # Execute tools and continue
        tool_results = []
        for block in tool_uses:
            logger.info("Tool call: %s(%s)", block.name, block.input)
            result = dispatch_tool(block.name, block.input, db, vault_key)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages = messages + [
            {"role": "assistant", "content": [b.model_dump() for b in (
                [b for b in final_message.content]
            )]},
            {"role": "user", "content": tool_results},
        ]
        yield "\n"
