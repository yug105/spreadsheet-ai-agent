"""Tests for the LangChain <-> OpenAI message/tool glue used by the engine.

These cover the format conversions (no network calls) that let the custom
multi-turn loop drive the model through LangChain's ChatOpenAI + bind_tools.
"""

import json

import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("langchain_openai")

from langchain_core.messages import (  # noqa: E402
    AIMessage,
    convert_to_messages,
    convert_to_openai_messages,
)
from langchain_openai import ChatOpenAI  # noqa: E402

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_cell_data",
            "description": "Read a cell or range",
            "parameters": {
                "type": "object",
                "properties": {"range": {"type": "string"}},
                "required": ["range"],
            },
        },
    }
]


def test_bind_tools_accepts_openai_schema():
    llm = ChatOpenAI(model="anthropic/claude-3.5-sonnet", api_key="dummy")
    # Should not raise; binding is a pure, offline operation.
    assert llm.bind_tools(TOOLS) is not None


def test_convert_dicts_to_messages_handles_tool_turn():
    messages = [
        {"role": "system", "content": "you are a sheet agent"},
        {"role": "user", "content": "read A1"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_cell_data", "arguments": json.dumps({"range": "A1"})},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": json.dumps({"result": "42"})},
    ]
    converted = [type(m).__name__ for m in convert_to_messages(messages)]
    assert converted == ["SystemMessage", "HumanMessage", "AIMessage", "ToolMessage"]


def test_ai_message_converts_back_to_openai_tool_calls():
    ai = AIMessage(
        content="",
        tool_calls=[{"name": "get_cell_data", "args": {"range": "B2"}, "id": "call_2", "type": "tool_call"}],
    )
    openai_message = convert_to_openai_messages([ai])[0]
    tool_calls = openai_message.get("tool_calls") or []

    # This is exactly what the engine's _execute_tool_call reads.
    name = tool_calls[0].get("function", {}).get("name")
    args = tool_calls[0].get("function", {}).get("arguments")
    assert name == "get_cell_data"
    assert json.loads(args) == {"range": "B2"}
