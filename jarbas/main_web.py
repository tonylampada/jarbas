import streamlit as st
from jarbas import tooledchat
import json
import traceback

def display_tool_activity(tool_name, arguments, result=None):
    """Display tool call and result information in the UI."""
    with st.chat_message("assistant", avatar="🔧"):
        st.write(f"Calling tool: **{tool_name}**")
        with st.expander("Arguments"):
            st.json(arguments)
        
        if result is not None:
            st.write("✅ Tool execution complete")
            with st.expander("Result preview"):
                if isinstance(result, dict) or isinstance(result, list):
                    st.json(result)
                else:
                    st.write(str(result)[:1000] + "..." if len(str(result)) > 1000 else str(result))

def print_tool_activity(event_type, event_data):
    """Callback for tool activity that works with Streamlit."""
    if event_type == "tool_call":
        tool = event_data["tool"]
        args = event_data["arguments"]
        # Store tool call info in session state to display it
        st.session_state.current_tool = {
            "name": tool,
            "args": args
        }
        # Display the tool call immediately
        display_tool_activity(tool, args)
        
    elif event_type == "tool_result":
        # Complete the tool call display with the result
        if "current_tool" in st.session_state:
            display_tool_activity(
                st.session_state.current_tool["name"], 
                st.session_state.current_tool["args"],
                event_data["result"]
            )
            # Clear the current tool
            st.session_state.current_tool = None

def handle_command(command):
    """Handle slash commands."""
    if command.lower() == "/reset":
        st.session_state.messages = []
        st.session_state.conversation = []
        st.success("Conversation reset.")
        return True
    
    if command.lower().startswith("/agent "):
        agent_name = command[7:].strip()
        try:
            tooledchat.set_agent(agent_name)
            st.session_state.messages = []
            st.session_state.conversation = []
            st.success(f"Switched to agent: {agent_name}")
            return True
        except ValueError as e:
            st.error(f"Error: {e}")
            return True
    
    if command.lower() == "/help":
        st.info("""
        ## Jarbas Commands:
        - **/help** - Show this help message
        - **/reset** - Reset the conversation history
        - **/agent NAME** - Switch to a different agent
        
        ## Usage Tips:
        - The system maintains conversation context across messages
        - When tools are used, you'll see real-time updates on tool execution
        """)
        return True
    
    # Not a recognized command
    return False

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
        
    if "current_tool" not in st.session_state:
        st.session_state.current_tool = None
        
    if "processing" not in st.session_state:
        st.session_state.processing = False

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Jarbas Web",
        page_icon="🤖",
        layout="wide"
    )

    # Initialize tooledchat if needed
    if not hasattr(st.session_state, "tooledchat_initialized"):
        tooledchat.init()
        st.session_state.tooledchat_initialized = True
    
    # Initialize session state
    init_session_state()
    
    # App header
    st.title("Jarbas Web 🤖")
    st.caption(f"Using agent: **{tooledchat.agent}**")
    
    # Display command help in sidebar
    with st.sidebar:
        st.markdown("## Commands")
        st.markdown("- **/help** - Show help message")
        st.markdown("- **/reset** - Reset conversation")
        st.markdown("- **/agent NAME** - Switch agent")
        
        # Display available agents
        try:
            agents = tooledchat._get_selected_agent()
            if agents:
                st.markdown("## Current Agent")
                st.json({
                    "name": agents["name"],
                    "description": agents.get("description", "No description")
                }, expanded=False)
        except:
            pass
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                if "content" in message and message["content"]:
                    st.write(message["content"])
    
    # Display processing indicator if needed
    if st.session_state.processing:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                st.empty()
    
    # Chat input
    if prompt := st.chat_input("Type a message...", disabled=st.session_state.processing):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
        
        # Check if it's a command
        if prompt.startswith("/"):
            if handle_command(prompt):
                # If it was a valid command, don't process further
                st.rerun()
        
        # Set processing state
        st.session_state.processing = True
        st.rerun()

    # Process the message if in processing state
    if st.session_state.processing and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        try:
            prompt = st.session_state.messages[-1]["content"]
            
            # Process the message with Jarbas
            if not st.session_state.conversation:
                messages = tooledchat.start_chat(tooledchat.agent, prompt, cb=print_tool_activity)
            else:
                st.session_state.conversation.append({"role": "user", "content": prompt})
                messages = tooledchat.chat(st.session_state.conversation, cb=print_tool_activity)
            
            st.session_state.conversation = messages
            
            # Display the assistant's response
            assistant_message = messages[-1]
            if assistant_message["role"] == "assistant":
                st.session_state.messages.append(assistant_message)
                with st.chat_message("assistant", avatar="🤖"):
                    if "content" in assistant_message and assistant_message["content"]:
                        st.write(assistant_message["content"])
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
        finally:
            # Clear processing state
            st.session_state.processing = False
            st.rerun()

if __name__ == "__main__":
    main() 