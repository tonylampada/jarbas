import ollama
from jarbas import configs

def chat(provider, model, messages, tools=None):
    """
    Chat with a model, possibly with tools.
    returns the next response from the model.
    Example:
    - messages = [{"role": "user", "content": "Hello, how are you?"}]
    - _tools = tools.get_tools("slack.*", "youtube.*")
    - response = chat(model="ollama-local/qwen2.5", messages=messages)
    - should return a chat response

    - messages = [{"role": "user", "content": "list 10 slack users"}]
    - _tools = tools.get_tools("slack.*", "youtube.*")
    - response = chat(model="ollama-local/qwen2.5", messages=messages, tools=_tools)
    - should return a response with a tool call
    """
    # If no messages were provided, use an empty list
    _provider = configs.get_llm_provider(provider)
    if _provider["type"] == "ollama":
        return _chat_ollama(_provider, model, messages, tools)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _chat_ollama(_provider, model, messages, tools=None):
    if configs._config is None:
        configs.init()
    base_url = _provider.get("url", "http://localhost:11434")
    client = ollama.Client(host=base_url)
    try:
        response = client.chat(
            model=model,
            messages=messages,
            tools=tools
        )
        message = response["message"]
        message_dict = {
            "role": message.role,
            "content": message.content,
        }
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                tool_call_dict = {
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    },
                    "id": tool_call.id if hasattr(tool_call, "id") else f"call_{len(tool_calls)}",
                    "type": "function"
                }
                tool_calls.append(tool_call_dict)
            message_dict["tool_calls"] = tool_calls
        return message_dict
    except Exception as e:
        # Log error and return a basic error response
        print(f"Error calling Ollama API: {e}")
        return {
            "role": "assistant",
            "content": f"I encountered an error: {str(e)}"
        }