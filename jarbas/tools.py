from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCError
import anyio
from jarbas import configs
import fnmatch

tools = {}

async def init():
    """
    Initialize mcp_tools from config.yaml
    """
    # Load the configuration if not already loaded
    if configs._config is None:
        configs.init()
    
    # Get all MCP servers from the config
    mcp_servers = configs.get_mcp_servers()
    
    # Load tools from each server
    for server in mcp_servers:
        server_tools = await _load_tools(server["url"])
        
        # Add tools to the global tools dictionary with server name prefix
        # The ListToolsResult object contains a 'tools' attribute, not 'items'
        for tool in server_tools.tools:
            prefixed_name = f"{server['name']}.{tool.name}"
            tools[prefixed_name] = _tool_dict(tool)
    
    return tools

def _tool_dict(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        }
    }

def get_tools(*names):
    """
    Get tool definitions from in memory cache
    example:
    - tools = get_tools("slack.*", "youtube.*")
    - tools = get_tools("slack.get_slack_users", "youtube.*")
    """
    if not names:
        return tools
    result = []
    for pattern in names:
        if pattern.endswith(".*"):
            prefix = pattern[:-1]
            for tool_name, tool_def in tools.items():
                if tool_name.startswith(prefix):
                    result.append(tool_def)
        elif pattern in tools:
            result.append(tools[pattern])
    return result

async def call_tool(name, arguments):
    """
    Call a tool
    """
    if not tools:
        await init()
    
    if name not in tools:
        return {
            "type": "error",
            "code": -32601,
            "message": f"Tool not found: {name}"
        }
    
    # Extract server name from the prefixed tool name
    server_name = name.split('.')[0]
    tool_name = name[len(server_name) + 1:]  # +1 for the dot
    
    # Get the URL for the server
    mcp_servers = configs.get_mcp_servers()
    server_url = None
    for server in mcp_servers:
        if server["name"] == server_name:
            server_url = server["url"]
            break
    
    if not server_url:
        return {
            "type": "error",
            "code": -32601,
            "message": f"Server not found for tool: {name}"
        }
    
    # Connect to the server and call the tool
    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write, sampling_callback=None) as session:
            await session.initialize()
            result = await _call_tool_lowlevel(session, write, tool_name, arguments)
            return result

async def _load_tools(url):
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write, sampling_callback=None) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools

async def _call_tool_lowlevel(session, write, name, arguments):
    jsonrpc_request = JSONRPCRequest(
        jsonrpc = "2.0",
        id = session._request_id,
        method = "tools/call",
        params = {
            "name": name,
            "arguments": arguments
        }
    )
    await write.send(JSONRPCMessage(jsonrpc_request))
    response_stream, response_stream_reader = anyio.create_memory_object_stream[
        JSONRPCResponse | JSONRPCError
    ](1)
    session._response_streams[session._request_id] = response_stream
    response = await response_stream_reader.receive()
    session._request_id += 1
    if isinstance(response, JSONRPCError):
        return {
            "type": "error",
            "code": response.error.code,
            "message": response.error.message,
            "data": response.error.data
        }
    if 'toolResult' in response.result: # legacy server
        return response.result['toolResult']['content'][0]
    return response.result['content'][0]
