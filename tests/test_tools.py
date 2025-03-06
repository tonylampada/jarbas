"""Integration tests for the tools module."""

import pytest
import asyncio
from jarbas import tools, configs
import fnmatch


@pytest.fixture(scope="module", autouse=True)
def setup_configs():
    """Set up the configs before running tests."""
    configs.init()


@pytest.mark.asyncio
async def test_init():
    """Test initializing tools from config."""
    # Make sure tools cache is empty
    tools.tools = {}
    
    # Initialize tools
    await tools.init()
    
    # Check that tools were loaded
    assert tools.tools, "Tools were not loaded"
    
    # Get the server configs to verify tools were loaded from all servers
    mcp_servers = configs.get_mcp_servers()
    servers_found = set()
    
    # Verify that tools from each server were loaded
    for tool_name in tools.tools:
        server_name = tool_name.split('.')[0]
        servers_found.add(server_name)
    
    # Check that at least one tool from each server was loaded
    for server in mcp_servers:
        assert server["name"] in servers_found, f"No tools found for server: {server['name']}"


@pytest.mark.asyncio
async def test_get_tools():
    """Test getting tools using patterns."""
    # Make sure init has been called
    if not tools.tools:
        await tools.init()
    
    # Test getting all tools for a specific service
    slack_tools = tools.get_tools("slack.*")
    assert slack_tools, "No slack tools found"
    for tool in slack_tools:
        assert tool["function"]["name"].startswith("slack_"), f"Non-slack tool in results: {tool}"
    
    # Test getting specific tool
    specific_tools = tools.get_tools("slack.slack_post_message")
    if specific_tools:  # Only assert if the tool exists
        assert len(specific_tools) == 1, "Expected exactly one tool"
        assert specific_tools[0]["function"]["name"] == "slack_post_message", "Expected tool not found"
    
    # Test getting multiple patterns
    multi_pattern_tools = tools.get_tools("slack.*", "youtube.*")
    assert multi_pattern_tools, "No tools found for multiple patterns"
    
    for tool in multi_pattern_tools:
        assert tool["function"]["name"].startswith(("slack_", "get_transcript")), f"Unexpected tool: {tool}"


@pytest.mark.asyncio
async def test_call_tool():
    if not tools.tools:
        await tools.init()
    
    result = await tools.call_tool("slack.slack_get_users", {"limit": 5})
    assert result is not None, "Tool call returned None"
    
    if isinstance(result, dict) and result.get("type") == "error":
        assert "code" in result, "Error response missing code"
        assert "message" in result, "Error response missing message" 