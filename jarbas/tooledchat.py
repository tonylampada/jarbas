from jarbas import configs, tools, llms
import asyncio
import json

provider = None
model = None
agent = None

def init():
    # read the configs, make sure tools and llms are ready
    # sets provider and model (from config) as globals, which can also be set from set_provider_and_model
    # same with agent
    global provider, model, agent
    
    # Initialize configs
    if configs._config is None:
        configs.init()
    
    # Initialize tools asynchronously
    asyncio.run(tools.init())
    
    # Set default provider and model
    default_model = configs.get_default_model()
    if default_model and "/" in default_model:
        provider, model = default_model.split("/")
    
    # Set default agent
    agent = configs.get_default_agent()

def _get_selected_agent(agent_name=None):
    """Get the selected agent configuration.
    
    Args:
        agent_name: The name of the agent to get. If None, uses the global agent.
        
    Returns:
        The agent configuration dictionary or None if not found.
    """
    global agent
    
    # If no agent_name provided, use the global agent
    if agent_name is None:
        if not agent:
            agent = configs.get_default_agent()
        agent_name = agent
    
    # Get all agents and find the selected one
    agents = configs.get_agents()
    selected_agent = next((a for a in agents if a["name"] == agent_name), None)
    
    return selected_agent

def _starter_messages(agent_name, text):
    """Create the initial messages for a chat session with an agent."""
    # Get agent configuration
    selected_agent = _get_selected_agent(agent_name)
    
    if not selected_agent:
        raise ValueError(f"Agent '{agent_name}' not found")
    
    # Create system and user messages
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
    """Process the tool result to handle different response formats."""
    # Handle nested structure when the result is in a text field and is a JSON string
    if isinstance(tool_result, dict) and "text" in tool_result and isinstance(tool_result["text"], str):
        try:
            nested_result = json.loads(tool_result["text"])
            return nested_result
        except json.JSONDecodeError:
            # If it's not valid JSON, return the original
            pass
    return tool_result

def chat(messages, cb=None):
    # chats with the llm, invoking tools as needed
    # returns a list of updatedmessages, containing the agent's response and the tool calls
    # cb is a callback function that is called on two events:
    # - when a tool call is made
    # - when a tool call returns a result (or error)
    global provider, model, agent
    
    if not provider or not model:
        # If provider and model not set, use default from config
        default_model = configs.get_default_model()
        if default_model and "/" in default_model:
            provider, model = default_model.split("/")
    
    # Get agent configuration for tools
    selected_agent = _get_selected_agent()
    
    # Get tools based on agent configuration
    agent_tools = None
    if selected_agent and selected_agent.get("enable_tools") and "tools" in selected_agent:
        agent_tools = tools.get_tools(*selected_agent["tools"])
    
    # Chat with the LLM
    response = llms.chat(provider=provider, model=model, messages=messages, tools=agent_tools)
    
    # Update messages with the response
    updated_messages = messages.copy()
    updated_messages.append(response)
    
    # Handle tool calls
    if "tool_calls" in response:
        for tool_call in response["tool_calls"]:
            if tool_call["type"] == "function":
                function_name = tool_call["function"]["name"]
                
                # Handle arguments - could be a string or already a dict
                function_args = tool_call["function"]["arguments"]
                if isinstance(function_args, str):
                    try:
                        function_args = json.loads(function_args)
                    except json.JSONDecodeError:
                        # If can't parse, use as is
                        pass
                
                # Form full tool name with namespace
                full_tool_name = None
                for pattern in selected_agent["tools"]:
                    if pattern.endswith(".*"):
                        prefix = pattern[:-1]
                        if function_name.startswith(prefix.split(".")[1]) and "." not in function_name:
                            full_tool_name = f"{prefix.split('.')[0]}.{function_name}"
                            break
                    elif pattern.split(".")[-1] == function_name:
                        full_tool_name = pattern
                        break
                
                if not full_tool_name:
                    # If no match found, try using function_name directly
                    # or prefix with the first available namespace
                    if "." in function_name:
                        full_tool_name = function_name
                    elif selected_agent["tools"] and "." in selected_agent["tools"][0]:
                        namespace = selected_agent["tools"][0].split(".")[0]
                        full_tool_name = f"{namespace}.{function_name}"
                    else:
                        full_tool_name = function_name
                
                # Notify about tool call if callback provided
                if cb:
                    cb("tool_call", {
                        "tool": full_tool_name,
                        "arguments": function_args
                    })
                
                # Call the tool
                tool_result = asyncio.run(tools.call_tool(full_tool_name, function_args))
                
                # Process tool result for better handling
                processed_result = _process_tool_result(tool_result)
                
                # Notify about tool result if callback provided
                if cb:
                    cb("tool_result", {
                        "tool": full_tool_name,
                        "result": processed_result
                    })
                
                # Add tool result to messages
                updated_messages.append({
                    "role": "tool",
                    "content": json.dumps(processed_result)
                })
                
                # Get response from LLM with tool results
                final_response = llms.chat(provider=provider, model=model, messages=updated_messages, tools=agent_tools)
                updated_messages.append(final_response)
    
    return updated_messages

