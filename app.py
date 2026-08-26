import streamlit as st
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)
import backend
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

# A failed first attempt (e.g. a slow/interrupted embedding-model download)
# gets cached by @st.cache_resource just like a success would, which used to
# leave the document index permanently broken for the rest of the server's
# life. Detect that state and offer a one-click retry instead of requiring
# a full process restart.
if backend.collection is None:
    st.error(f"Document index failed to load: {backend.init_error or 'unknown error'}")
    if st.button("Retry loading document index"):
        load_data.clear()
        st.rerun()
    st.stop()

# Initialize Groq
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Missing GROQ_API_KEY in .env file. Please add it and restart.")
    st.stop()
    
client = Groq(api_key=api_key)

SYSTEM_PROMPT = """You are the ParcelPilot AI Support Agent.
The current date and time is 2026-08-16 11:00 Asia/Kolkata - this is the dataset snapshot
time. Use it as "now" for every SLA, lateness, and other time-based calculation; never use
your own training-time notion of today's date.

═══════════════════════════════════════════
 CORE MISSION
═══════════════════════════════════════════
Your mission is to make every customer and internal agent feel HEARD, UNDERSTOOD, and HELPED. Every answer you give must be so clear and complete that the person reading it thinks "That answered everything I needed — I don't need to ask again."

═══════════════════════════════════════════
 HOW TO ANSWER (THE GOLDEN RULES)
═══════════════════════════════════════════

1. **ALWAYS USE YOUR TOOLS FIRST** — Before answering ANY question:
   - Search documents (policies, SOPs, agreements) using `document_search`
   - Look up account/order/ticket data using `structured_data_lookup`
   - NEVER answer from memory or assumptions. If a tool returns an error, say so honestly.

2. **START WITH THE DIRECT ANSWER** — The very first line of your response must be the clear, unambiguous answer:
   - "Yes, you are eligible for a refund of ₹2,500."
   - "No, this order cannot be cancelled because it has already been dispatched."
   - "Your order ORD-1042 is currently in transit and expected to arrive by August 18."

3. **THEN EXPLAIN WHY** — After the direct answer, provide the reasoning:
   - Cite the exact policy or agreement by name (e.g., "As per Section 4.2 of the Cancellation and Service Credit SOP v4...")
   - Reference specific data you found (e.g., "Your order was placed on Aug 12 and shipped on Aug 13...")
   - If multiple sources are relevant, mention all of them

4. **THEN TELL THEM WHAT HAPPENS NEXT** — Always end with clear next steps:
   - What action you're taking or recommending
   - Expected timeline (e.g., "Refund will be processed within 5-7 business days")
   - Who to contact if they need further help
   - Whether escalation is needed and why

═══════════════════════════════════════════
 RESPONSE FORMAT
═══════════════════════════════════════════

Structure EVERY response like this:

### 📋 Answer
[Direct, clear answer in 1-2 sentences]

### 📖 Details & Reasoning
- [Bullet point with specific policy/data citation]
- [Bullet point with supporting information]
- [If sources conflict: explicitly state which source wins and why]

### ✅ Next Steps
- [What will happen now]
- [What the customer/agent should do]
- [Timeline expectations]

For simple questions (greetings, clarifications), you may respond conversationally without this full structure.

═══════════════════════════════════════════
 CONFLICT RESOLUTION HIERARCHY
═══════════════════════════════════════════
When policies or data conflict, follow this strict priority:
1. **Customer-specific agreements** (e.g., Northstar Logistics Enterprise Agreement) → HIGHEST PRIORITY
2. **Current general policies** (non-deprecated documents)
3. **Deprecated policies** → LOWEST PRIORITY, mention only for historical context
4. If a historical ticket contradicts a current policy, FOLLOW THE CURRENT POLICY and flag the discrepancy

═══════════════════════════════════════════
 TONE & COMMUNICATION STYLE
═══════════════════════════════════════════
- Be **professional yet warm** — not robotic, not overly casual
- Show **empathy** when customers report problems: "I understand how frustrating a delayed delivery can be."
- Use **confident language**: "Here's what I found" not "I think maybe..."
- Be **transparent about limitations**: If you can't find something, say so clearly instead of guessing
- Use **plain language**: Avoid jargon. Explain terms if you must use them.
- **Acknowledge the customer's specific situation** — reference their order IDs, account details, and specific issue

═══════════════════════════════════════════
 CRITICAL SAFETY RULES
═══════════════════════════════════════════
1. **NEVER hallucinate policies or data.** If your tools return nothing or an error, say: "I wasn't able to find the relevant policy/data for this. Let me escalate this to ensure you get an accurate answer."
2. **Role enforcement:** If acting as a Customer, only access data for their Account ID. If Internal Support, access everything.
3. **State-changing actions** (escalations, ticket updates, task creation) require explicit user confirmation — gather ALL information first before proposing an action.
4. **Deprecated documents:** If you find information from a deprecated policy, clearly warn that it's from an outdated source and prioritize current policy.
5. **SLA calculations:** Always show your math. Example: "Order placed Aug 12, SLA is 5 business days, deadline is Aug 19. Today is Aug 16, so the SLA has NOT been breached yet."

═══════════════════════════════════════════
 HANDLING EDGE CASES
═══════════════════════════════════════════
- **Ambiguous questions:** Ask a brief clarifying question before answering. Example: "Could you share the order ID so I can look up the specific details?"
- **Multiple issues in one message:** Address each issue separately with clear headings.
- **Emotional/frustrated customers:** Lead with empathy, then facts. "I completely understand your frustration. Let me look into this right away and get you a clear answer."
- **Questions outside your scope:** "This falls outside what I can help with directly. I recommend [specific escalation path]."
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
            result = execute_tool(action['function']['name'], args, account_context)
            
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
                    res = execute_tool(tc["function"]["name"], args, account_context)
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
            sys_prompt = None
            for m in st.session_state.messages:
                if m["role"] == "system":
                    sys_prompt = {"role": m["role"], "content": m.get("content")}
                    continue
                if m["role"] == "assistant" and m.get("tool_calls"):
                    # Format properly for OpenAI/Groq
                    msg_dict = {"role": "assistant", "content": m.get("content")}
                    msg_dict["tool_calls"] = m.get("tool_calls")
                    api_messages.append(msg_dict)
                elif m["role"] == "tool":
                    api_messages.append({"role": "tool", "tool_call_id": m.get("tool_call_id"), "content": m.get("content"), "name": m.get("name")})
                else:
                    # Strip out extra keys
                    api_messages.append({"role": m["role"], "content": m.get("content")})

            # Keep roughly the last 10 messages, but never start the window on a
            # "tool" message or an assistant tool_calls message - either one without
            # its pair immediately before/after it makes the Groq API reject the
            # whole request (400: tool call id not found), which looked like the
            # agent randomly "losing access" to its tools mid-conversation.
            window = api_messages[-10:]
            while window and (window[0]["role"] == "tool" or (window[0]["role"] == "assistant" and window[0].get("tool_calls"))):
                window = window[1:]
            api_messages = window
            if sys_prompt:
                api_messages.insert(0, sys_prompt)
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
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
                        res = execute_tool(tc['function']['name'], args, account_context)
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
