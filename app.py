import streamlit as st
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)
from backend import init_backend, tools_schema, execute_tool

st.set_page_config(page_title="ParcelPilot Internal AI Agent", layout="wide", page_icon="📦")

# Inject Modern UI/UX CSS
st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Title Gradient */
    h1 {
        background: -webkit-linear-gradient(45deg, #6366F1, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 1.5rem;
    }
    
    /* Sleek Chat Messages */
    [data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        animation: fadeIn 0.4s ease-out;
    }
    
    /* Interactive Buttons */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        border: 1px solid rgba(99, 102, 241, 0.5);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(99, 102, 241, 0.4);
        border-color: #8B5CF6;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_data():
    init_backend()
    return True

st.title("ParcelPilot Internal AI Support Agent")

# Sidebar for config and state
with st.sidebar:
    st.header("Context Configuration")
    user_role = st.selectbox("Simulate Role", ["Internal Support Agent", "Customer"])
    if user_role == "Customer":
        account_context = st.text_input("Customer Account ID Context", value="ACC-001")
    else:
        account_context = "ALL"
        
    st.info("The agent will respect this context and the supplied documentation.")

load_data()

# Initialize Groq
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY in .env file. Please add it and restart.")
    st.stop()
    
client = Groq(api_key=api_key)

SYSTEM_PROMPT = """You are the ParcelPilot AI Support Agent.
Your job is to answer support queries quickly and reliably, and help investigate issues.

CRITICAL RULES:
1. You can search documents, lookup structured data, and take actions.
2. If you find conflicting rules, remember that Customer-specific agreements ALWAYS override general policies.
3. Current policies OVERRIDE deprecated policies. Pay attention to warnings about deprecated policies!
4. Do not assume all data is reliable. If a historical ticket contradicts a policy, follow the current policy or escalate.
5. You MUST act within your simulated role. If you are acting as a Customer, you can only lookup and discuss data belonging to their Account ID. If you are Internal Support, you can access everything.
6. Only use the provided tools to get information. DO NOT hallucinate policies.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "pending_tool_calls" not in st.session_state:
    st.session_state.pending_tool_calls = []

# Display chat history (exclude system and tool responses)
for msg in st.session_state.messages:
    if msg["role"] not in ["system", "tool"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg.get("display_content", msg["content"]))
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    st.caption(f"🔧 Used tool: {tc['function']['name']}")

# Handle Pending Action Confirmation
if st.session_state.pending_action:
    action = st.session_state.pending_action
    st.warning(f"**Action Required**: The agent wants to execute a state-changing action `{action['function']['name']}`.\n\nDetails: {action['function']['arguments']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Action", type="primary"):
            # Execute it
            args = json.loads(action['function']['arguments'])
            result = execute_tool(action['function']['name'], args)
            
            # Append tool response
            st.session_state.messages.append({
                "role": "tool",
                "tool_call_id": action["id"],
                "name": action['function']['name'],
                "content": result
            })
            # Also execute any other pending non-mutating tool calls from that same turn
            for tc in st.session_state.pending_tool_calls:
                if tc["id"] != action["id"]:
                    args = json.loads(tc["function"]["arguments"])
                    res = execute_tool(tc["function"]["name"], args)
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["function"]["name"],
                        "content": res
                    })
            
            st.session_state.pending_action = None
            st.session_state.pending_tool_calls = []
            st.rerun()
            
    with col2:
        if st.button("Cancel Action"):
            st.session_state.messages.append({
                "role": "tool",
                "tool_call_id": action["id"],
                "name": action['function']['name'],
                "content": "ERROR: User denied the action."
            })
            for tc in st.session_state.pending_tool_calls:
                if tc["id"] != action["id"]:
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["function"]["name"],
                        "content": "Cancelled due to associated action denial."
                    })
            
            st.session_state.pending_action = None
            st.session_state.pending_tool_calls = []
            st.rerun()
    st.stop() # Wait for user interaction


if prompt := st.chat_input("Ask a support question..."):
    # Enforce role context
    context_msg = f"[Context: User Role is {user_role}. "
    if account_context != "ALL":
        context_msg += f"Account scoped to {account_context}. ]\n"
    else:
        context_msg += "Full internal access. ]\n"
        
    full_prompt = context_msg + prompt
    st.session_state.messages.append({"role": "user", "content": full_prompt, "display_content": prompt})
    st.rerun()

# Only call LLM if the last message requires a response (user or tool)
if len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] in ["user", "tool"]:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Construct message list for Groq
            api_messages = []
            for m in st.session_state.messages:
                if m["role"] == "assistant" and "tool_calls" in m:
                    # Format properly for OpenAI/Groq
                    msg_dict = {"role": "assistant", "content": m.get("content")}
                    msg_dict["tool_calls"] = m["tool_calls"]
                    api_messages.append(msg_dict)
                elif m["role"] == "tool":
                    api_messages.append({"role": "tool", "tool_call_id": m.get("tool_call_id"), "content": m.get("content"), "name": m.get("name")})
                else:
                    # Strip out extra keys
                    api_messages.append({"role": m["role"], "content": m.get("content")})

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=api_messages,
                tools=tools_schema,
                tool_choice="auto"
            )
            
            resp_msg = response.choices[0].message
            
            if resp_msg.tool_calls:
                # We save the tool calls
                intercepted = False
                
                # Clean up representation for session state
                clean_tool_calls = [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}} for t in resp_msg.tool_calls]
                
                # Record assistant message with tool calls BEFORE executing
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resp_msg.content or "",
                    "tool_calls": clean_tool_calls
                })
                
                for tc in clean_tool_calls:
                    if tc["function"]["name"] == "take_action":
                        st.session_state.pending_action = tc
                        st.session_state.pending_tool_calls = clean_tool_calls
                        intercepted = True
                        break
                        
                if intercepted:
                    st.rerun()
                else:
                    # Execute non-mutating tools immediately
                    for tc in clean_tool_calls:
                        st.caption(f"🔧 Calling {tc['function']['name']}...")
                        args = json.loads(tc['function']['arguments'])
                        res = execute_tool(tc['function']['name'], args)
                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": tc['function']['name'],
                            "content": res
                        })
                    st.rerun() # Rerun to send tool outputs back to LLM
                    
            else:
                # Normal text response
                message_placeholder.markdown(resp_msg.content)
                st.session_state.messages.append({"role": "assistant", "content": resp_msg.content})
