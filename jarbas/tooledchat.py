from jarbas import configs, tools, llms
import asyncio
import json

provider = None
model = None
agent = None

def init():
    global provider, model, agent
    
    if configs._config is None:
        configs.init()
    asyncio.run(tools.init())
    default_model = configs.get_default_model()
    if default_model and "/" in default_model:
        provider, model = default_model.split("/")
    agent = configs.get_default_agent()

def _get_selected_agent(agent_name=None):
    global agent
    if agent_name is None:
        if not agent:
            agent = configs.get_default_agent()
        agent_name = agent
    agents = configs.get_agents()
    selected_agent = next((a for a in agents if a["name"] == agent_name), None)
    
    return selected_agent

def _starter_messages(agent_name, text):
    selected_agent = _get_selected_agent(agent_name)
    if not selected_agent:
        raise ValueError(f"Agent '{agent_name}' not found")
    messages = [
        {
            "role": "system",
            "content": selected_agent["system_content"]
        },
        {
            "role": "user",
            "content": text
        }
    ]
    
    return messages

def start_chat(agent_name, text, cb=None):
    # start a chat with the agent
    # example:
    # start_chat("helpful", "list 10 slack users")
    messages = _starter_messages(agent_name, text)
    return chat(messages, cb=cb)

def set_provider_and_model(new_provider, new_model):
    global provider, model
    provider = new_provider
    model = new_model

def set_agent(agent_name):
    global agent
    agent = agent_name

def _process_tool_result(tool_result):
    if isinstance(tool_result, dict) and "text" in tool_result and isinstance(tool_result["text"], str):
        try:
            nested_result = json.loads(tool_result["text"])
            return nested_result
        except json.JSONDecodeError:
            # If it's not valid JSON, return the original
            pass
    return tool_result


def _call_tools(tool_calls, cb=None):
    tool_results = []
    for tool_call in tool_calls:
        if tool_call["type"] == "function":
            function_name = tool_call["function"]["name"]
            function_args = tool_call["function"]["arguments"]
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except json.JSONDecodeError:
                    pass
            if cb:
                cb("tool_call", {
                    "tool": function_name,
                    "arguments": function_args
                })
            tool_result = asyncio.run(tools.call_tool(function_name, function_args))
            processed_result = _process_tool_result(tool_result)
            if cb:
                cb("tool_result", {
                    "tool": function_name,
                    "result": processed_result
                })
            tool_results.append({
                "tool": function_name,
                "result": processed_result,
            })
        else:
            raise ValueError(f"Unexpected tool call type: {tool_call['type']}")
    return tool_results


def chat(messages, cb=None):
    # chats with the llm, invoking tools as needed
    # returns a list of updatedmessages, containing the agent's response and the tool calls
    # cb is a callback function that is called on two events:
    # - when a tool call is made
    # - when a tool call returns a result (or error)
    global provider, model, agent
    
    if not provider or not model:
        default_model = configs.get_default_model()
        if default_model and "/" in default_model:
            provider, model = default_model.split("/")
    selected_agent = _get_selected_agent()
    agent_tools = None
    if selected_agent and selected_agent.get("enable_tools") and "tools" in selected_agent:
        agent_tools = tools.get_tools(*selected_agent["tools"])
    messages = messages.copy()
    response = llms.chat(provider=provider, model=model, messages=messages, tools=agent_tools)
    messages.append(response)
    while "tool_calls" in response:
        tools_responses = _call_tools(response["tool_calls"], cb=cb)
        messages.append({
            "role": "tool",
            "content": json.dumps(tools_responses)
        })
        response = llms.chat(provider=provider, model=model, messages=messages, tools=agent_tools)
        messages.append(response)
    return messages

