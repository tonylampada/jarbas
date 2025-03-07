from jarbas import tooledchat
import sys
import json

def print_tool_activity(event_type, event_data):
    """Display tool call and result information during chat."""
    if event_type == "tool_call":
        tool = event_data["tool"]
        args = event_data["arguments"]
        print(f"\n🔧 Calling tool: {tool}")
        print(f"   Arguments: {json.dumps(args, indent=2)[:100]}{'...' if len(json.dumps(args)) > 100 else ''}")
        print("   Working...", end="", flush=True)
    elif event_type == "tool_result":
        print(" Done ✓")
        result_preview = str(event_data["result"])
        # Limit the preview to a reasonable length
        if len(result_preview) > 200:
            result_preview = result_preview[:200] + "..."
        print(f"   Result preview: {result_preview}")

def display_assistant_response(message):
    """Display only the assistant's response."""
    if message["role"] != "assistant":
        return
        
    print(f"\n🤖 Assistant: ", end="")
    if "content" in message and message["content"]:
        print(f"{message['content']}")
    elif "tool_calls" in message:
        # We don't need to print anything here as the tool calls will be displayed by the callback
        print("(using tools to process your request...)")
    else:
        print("No response")

def display_help():
    """Display help information."""
    print("\n--- Jarbas CLI Help ---")
    print("Commands:")
    print("  /help        - Show this help message")
    print("  /quit        - Exit the chat")
    print("  /exit        - Same as /quit")
    print("  /agent NAME  - Switch to a different agent (e.g., /agent helpful)")
    print("  /reset       - Reset the conversation history")
    print("\nUsage Tips:")
    print("  - The system maintains conversation context across messages")
    print("  - When tools are used, you'll see real-time updates on tool execution")
    print("  - Press Ctrl+C to interrupt long responses")
    print("---------------------")

def handle_command(user_input, conversation):
    """Handle slash commands.
    
    Args:
        user_input: The user input string
        conversation: The current conversation history
        
    Returns:
        tuple: (was_command, should_exit, updated_conversation)
            was_command: True if the input was a command
            should_exit: True if the program should exit
            updated_conversation: The potentially modified conversation history
    """
    if not user_input:
        return True, False, conversation
        
    if user_input.lower() == "/quit" or user_input.lower() == "/exit":
        print("Goodbye! 👋")
        return True, True, conversation
            
    if user_input.lower() == "/help":
        display_help()
        return True, False, conversation
            
    if user_input.lower().startswith("/agent "):
        agent_name = user_input[7:].strip()
        try:
            tooledchat.set_agent(agent_name)
            print(f"Switched to agent: {agent_name}")
            # Reset conversation when switching agents
            return True, False, []
        except ValueError as e:
            print(f"Error: {e}")
            return True, False, conversation
            
    if user_input.lower() == "/reset":
        print("Conversation reset.")
        return True, False, []
    
    # Not a command
    return False, False, conversation

def main():
    """Main CLI chat loop."""
    # Initialize the chat module
    tooledchat.init()
    
    print("\nWelcome to Jarbas CLI")
    print("Type /help for available commands, or just start chatting!")
    print(f"Using agent: {tooledchat.agent}")
    
    # Keep track of conversation history
    conversation = []
    
    # Chat loop
    while True:
        try:
            # Get user input
            print("\n> ", end="")
            user_input = input().strip()
            
            # Handle special commands
            was_command, should_exit, conversation = handle_command(user_input, conversation)
            if was_command:
                if should_exit:
                    break
                continue
            
            if not conversation:
                messages = tooledchat.start_chat(tooledchat.agent, user_input, cb=print_tool_activity)
            else:
                conversation.append({"role": "user", "content": user_input})
                messages = tooledchat.chat(conversation, cb=print_tool_activity)
            conversation = messages
            display_assistant_response(messages[-1])
                
        except KeyboardInterrupt:
            print("\nChat interrupted. Type /quit to exit or continue chatting.")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()