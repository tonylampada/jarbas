from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCError
import anyio

tools = {}

async def init():
    """
    Initialize mcp_tools from config.yaml
    """
    # uses _load_tools
    pass

def get_tools(*names):
    """
    Get tool definitions from in memory cache
    example:
    - tools = get_tools("slack.*", "youtube.*")
    - tools = get_tools("slack.get_slack_users", "youtube.*")
    """
    pass

async def call_tool(name, arguments):
    """
    Call a tool
    """
    # uses _call_tool_lowlevel
    pass


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
