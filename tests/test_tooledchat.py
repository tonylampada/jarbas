"""Integration tests for the tooledchat module."""

import json
from jarbas import tooledchat

def test_slack_users():
    tooledchat.init()

    callback_events = []
    
    def callback(event_type, event_data):
        callback_events.append({"type": event_type, "data": event_data})
    
    query = "list 10 slack user names"
    messages = tooledchat.start_chat("helpful", query, cb=callback)

    assert messages, "No messages returned"
    assert len(messages) >= 3, f"Expected at least 3 messages in conversation, got {len(messages)}"
    
    assert messages[0]["role"] == "system", "First message should be system message"
    assert messages[1]["role"] == "user", "Second message should be user message"
    assert messages[1]["content"] == query, "User message should contain the query"
    assert messages[2]["role"] == "assistant", "Third message should be assistant message"
    assert "tool_calls" in messages[2], "Assistant should make a tool call"
    tool_calls = messages[2]["tool_calls"]
    slack_tool_call = None
    for tool_call in tool_calls:
        if (tool_call["type"] == "function" and 
            tool_call["function"]["name"] == "slack.slack_get_users"):
            slack_tool_call = tool_call
            break
    
    assert slack_tool_call, "No tool call for Slack users found"
    assert messages[3]["role"] == "tool", "Fourth message should be user message with tool results"
    assert messages[3]["content"].startswith("[{"), "Expected tool results message"
    tool_result = json.loads(messages[3]["content"])[0]["result"]
    
    if "text" in tool_result:
        nested_results = json.loads(tool_result["text"])
        tool_result = nested_results
    
    assert "ok" in tool_result, "Tool results should have 'ok' field"
    assert "members" in tool_result, "Tool results should have 'members' field"
    
    assert messages[-1]["role"] == "assistant", "Last message should be assistant message"
    assert "content" in messages[-1], "Assistant's final message should have content"
    assert messages[-1]["content"].strip(), "Assistant's final message should not be empty"
    
    final_content = messages[-1]["content"].lower()
    assert any(term in final_content for term in ["user", "member", "slack"]), "Final response should mention users"
    
    assert callback_events, "No callback events recorded"
    assert len(callback_events) >= 2, "Expected at least two callback events (tool call and tool result)"
    
    tool_call_event = next((e for e in callback_events if e["type"] == "tool_call"), None)
    assert tool_call_event, "No tool call event found"
    assert "tool" in tool_call_event["data"], "Tool call event should include tool name"
    assert "arguments" in tool_call_event["data"], "Tool call event should include arguments"
    
    tool_result_event = next((e for e in callback_events if e["type"] == "tool_result"), None)
    assert tool_result_event, "No tool result event found"
    assert "tool" in tool_result_event["data"], "Tool result event should include tool name"
    assert "result" in tool_result_event["data"], "Tool result event should include result data" 

def test_youtube():
    tooledchat.init()
    query = "summarize this video: https://www.youtube.com/watch?v=-qjE8JkIVoQ"
    messages = tooledchat.start_chat("helpful", query)
    assert any([t in messages[-1]["content"].lower() for t in ["lynx", "framework", "javascript", "tiktok"]]), "response should be about Lynx"
    