"""Integration tests for the llms module."""

import pytest
import asyncio
import json
from jarbas import llms, tools, configs


@pytest.fixture(scope="module", autouse=True)
def setup_configs():
    """Set up the configs before running tests."""
    configs.init()


def test_chat_basic():
    messages = [{"role": "user", "content": "Hello, what is your name?"}]
    provider, model = configs.get_default_model().split("/")
    response = llms.chat(provider=provider, model=model, messages=messages)

    assert response, "No response was returned"
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "content" in response, "Response should have content"
    assert response.get("role") == "assistant", "Response role should be 'assistant'"


def test_chat_with_tools():
    asyncio.run(tools.init())
    _tools = tools.get_tools("slack.*")
    assert _tools, "Tools were not loaded correctly. Make sure MCP servers are running."
    assert len(_tools) > 0, "No slack tools were found"
    messages = [
        {
            "role": "system", 
            "content": f"You are an assistant that has access to tools."
        },
        {
            "role": "user", 
            "content": f"list 10 slack users"
        }
    ]
    provider, model = configs.get_default_model().split("/")
    response = llms.chat(provider=provider, model=model, messages=messages, tools=_tools)
    
    assert response, "No response was returned"
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "tool_calls" in response, "Response should have tool_calls"
    assert isinstance(response["tool_calls"], list), "Tool calls should be a list"
    assert len(response["tool_calls"]) > 0, "There should be at least one tool call"
    tool_call = response["tool_calls"][0]
    assert "function" in tool_call, "Tool call should have a function"
    assert "name" in tool_call["function"], "Function should have a name"
    assert tool_call["function"]["name"] == "slack_get_users", f"Tool call should be slack_get_users, got {tool_call['function']['name']}"


def test_chat_with_multiple_turns():
    messages = [
        {"role": "user", "content": "Hello, what is your name?"},
        {"role": "assistant", "content": "I'm an AI assistant. You can call me Jarbas. How can I help you today?"},
        {"role": "user", "content": "What is the weather like?"}
    ]
    provider, model = configs.get_default_model().split("/")
    response = llms.chat(provider=provider, model=model, messages=messages)
    
    assert response, "No response was returned"
    assert isinstance(response, dict), "Response should be a dictionary"
    assert "content" in response, "Response should have content"
    assert response.get("role") == "assistant", "Response role should be 'assistant'"
    assert response["content"].strip() != "", "Response content should not be empty"


def test_chat_with_multiple_turns_using_tools():
    asyncio.run(tools.init())
    _tools = tools.get_tools("slack.*")
    assert _tools, "Tools were not loaded correctly. Make sure MCP servers are running."
    assert len(_tools) > 0, "No slack tools were found"
    tool_results = {
        "ok": True,
        "members": [
            {
                "id": "USLACKBOT",
                "name": "slackbot", 
                "deleted": False,
                "color": "757575"
            },
            {
                "id": "UL7FURTT5",
                "name": "John",
                "deleted": False,
                "color": "757575"
            }
        ],
        "cache_ts": 1741285071,
        "response_metadata": {
            "next_cursor": "xxxyyy="
        }
    }
    
    messages = [
        {
            "role": "system", 
            "content": f"You are an assistant that has access to tools."
        },
        {
            "role": "user", 
            "content": f"list 10 slack users"
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": "slack_get_users",
                    "arguments": {
                        "limit": 10
                    }
                },
                "id": "call_0",
                "type": "function"
            }]
        },
        {
            "role": "tool",
            "content": json.dumps(tool_results)
        }
    ]
    provider, model = configs.get_default_model().split("/")
    response = llms.chat(provider=provider, model=model, messages=messages, tools=_tools)
    
    assert response, "No response was returned"
