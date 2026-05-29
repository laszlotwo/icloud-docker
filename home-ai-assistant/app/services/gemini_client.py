import logging
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.config import settings
from app.services.tool_definitions import SYSTEM_PROMPT, TOOLS
from app.services.tool_handlers import dispatch_tool

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _build_tools(vault_key: bytes | None) -> list[types.Tool]:
    """Convert Anthropic-style tool definitions to Gemini function declarations."""
    tools = TOOLS if vault_key is not None else [t for t in TOOLS if t["name"] != "list_vault_titles"]
    declarations = []
    for t in tools:
        schema = t["input_schema"]
        kwargs = {"name": t["name"], "description": t["description"]}
        # Only attach parameters when the tool actually takes some
        if schema.get("properties"):
            kwargs["parameters_json_schema"] = schema
        declarations.append(types.FunctionDeclaration(**kwargs))
    return [types.Tool(function_declarations=declarations)]


def _build_config(vault_key: bytes | None) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=_build_tools(vault_key),
        temperature=0.7,
    )


def _to_contents(messages: list[dict]) -> list[types.Content]:
    """Convert stored {role, content(str)} messages into Gemini Content objects."""
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        text = m["content"] if isinstance(m["content"], str) else str(m["content"])
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    return contents


def _run_tool_calls(function_calls, db, vault_key) -> list[types.Part]:
    parts = []
    for fc in function_calls:
        logger.info("Tool call: %s(%s)", fc.name, dict(fc.args))
        result = dispatch_tool(fc.name, dict(fc.args), db, vault_key)
        parts.append(types.Part.from_function_response(name=fc.name, response={"result": result}))
    return parts


async def chat(messages: list[dict], db, vault_key: bytes | None = None) -> str:
    """Run the agentic tool-use loop with Gemini and return the final text."""
    client = _get_client()
    config = _build_config(vault_key)
    contents = _to_contents(messages)

    while True:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        candidate = response.candidates[0] if response.candidates else None
        parts = candidate.content.parts if candidate and candidate.content else []
        function_calls = [p.function_call for p in parts if p.function_call]

        if not function_calls:
            return response.text or ""

        contents.append(candidate.content)
        contents.append(types.Content(role="user", parts=_run_tool_calls(function_calls, db, vault_key)))


async def chat_stream(messages: list[dict], db, vault_key: bytes | None = None) -> AsyncIterator[str]:
    """Streaming version of the agentic loop. Yields text tokens."""
    client = _get_client()
    config = _build_config(vault_key)
    contents = _to_contents(messages)

    while True:
        function_calls = []
        model_parts = []

        stream = await client.aio.models.generate_content_stream(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        async for chunk in stream:
            candidate = chunk.candidates[0] if chunk.candidates else None
            if not candidate or not candidate.content:
                continue
            for part in candidate.content.parts or []:
                if part.text:
                    yield part.text
                    model_parts.append(part)
                if part.function_call:
                    function_calls.append(part.function_call)
                    model_parts.append(part)

        if not function_calls:
            break

        contents.append(types.Content(role="model", parts=model_parts))
        contents.append(types.Content(role="user", parts=_run_tool_calls(function_calls, db, vault_key)))
        yield "\n"
