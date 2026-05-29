from google.genai import types

from app.services.gemini_client import _build_tools, _to_contents
from app.services.tool_definitions import TOOLS


def test_build_tools_returns_tool_list():
    tools = _build_tools(vault_key=b"key")
    assert len(tools) == 1
    assert isinstance(tools[0], types.Tool)
    # All tools (including vault) should be present when unlocked
    names = {fd.name for fd in tools[0].function_declarations}
    assert names == {t["name"] for t in TOOLS}


def test_build_tools_hides_vault_when_locked():
    tools = _build_tools(vault_key=None)
    names = {fd.name for fd in tools[0].function_declarations}
    assert "list_vault_titles" not in names


def test_no_param_tool_has_no_parameters():
    tools = _build_tools(vault_key=None)
    by_name = {fd.name: fd for fd in tools[0].function_declarations}
    # get_current_time has empty properties -> no parameters attached
    assert by_name["get_current_time"].parameters is None
    assert by_name["get_current_time"].parameters_json_schema is None


def test_param_tool_carries_schema():
    tools = _build_tools(vault_key=None)
    by_name = {fd.name: fd for fd in tools[0].function_declarations}
    assert by_name["add_expense"].parameters_json_schema is not None


def test_to_contents_maps_roles():
    contents = _to_contents([
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你"},
    ])
    assert contents[0].role == "user"
    assert contents[1].role == "model"
    assert contents[0].parts[0].text == "你好"
