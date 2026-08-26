# ParcelPilot AI Demo Video Script

## 1. Introduction (0:00 - 0:30)
* **Visual**: Screen recording showing the ParcelPilot Streamlit UI on the main chat screen.
* **Speaker**: 
  > "Hi, I'm excited to present my submission for the ParcelPilot AI Engineer assessment. 
  > 
  > Today, we're looking at the **ParcelPilot AI Support Agent**. Put simply, this is a fully functional, AI-powered chatbot designed to resolve complex customer support queries automatically and safely.
  > 
  > What we built is a unified system that connects to two very different data sources: unstructured PDF company policies (like SLAs and contracts) and structured operational data (like account details, live orders, and support tickets). 
  > 
  > Depending on whether you are acting as an internal support agent or a customer, the AI can read policies, look up specific live order data, and even propose actions like escalating a ticket—all while keeping data completely isolated and secure with strict access controls."

## 2. Walkthrough of the Architecture & UI (0:30 - 1:00)
* **Visual**: Briefly show the sidebar where the "Context Configuration" toggle is located.
* **Speaker**: 
  > "Let's take a quick look at the interface. On the left, we have our Context Configuration sidebar. This allows us to simulate our user's role—switching between an Internal Support Agent who has full access, and a Customer who is restricted to their specific Account ID. 
  > 
  > The intelligence behind the agent is powered by Groq's fast LPU engine using the `gpt-oss-120b` model, connected to a local ChromaDB vector store for our policies, and Pandas for our structured account, order, and ticket data."

## 3. Demonstrating RAG & Conflict Resolution (1:00 - 1:45)
* **Visual**: Type a question that requires policy lookup. (e.g., *What is the cancellation SLA?*)
* **Speaker**: 
  > "First, let's see how it handles unstructured data. I'll ask it about the cancellation policy. 
  > 
  > Behind the scenes, the model queries the ChromaDB vector store. You'll notice it correctly prioritizes the *current* version of our Support Policy over the deprecated one, effectively solving the Trust and Reliability problem mentioned in the assessment."

## 4. Demonstrating Structured Data & Access Control (1:45 - 2:30)
* **Visual**: Set the role to "Customer" and the Account ID to "ACC-001". Ask the agent: *What is the status of my recent order?*
* **Speaker**: 
  > "Now, let's demonstrate the structured data tools and access control. I'm simulating a Customer with Account ID 'ACC-001'. When I ask about my order, the agent triggers the `structured_data_lookup` tool. 
  > 
  > Crucially, this access control is enforced at the *data layer*. The tool receives the context and strictly filters the backend Pandas dataframe, so the LLM cannot physically access data belonging to any other account."

## 5. Demonstrating Human-in-the-Loop Safeguards (2:30 - 3:00)
* **Visual**: Ask the agent to perform an action. (e.g., *Please escalate my late order.*)
* **Speaker**: 
  > "Finally, let's look at safety. If the agent decides a state-changing action is necessary—like escalating a ticket or issuing a refund—it calls the `take_action` tool.
  > 
  > Instead of executing immediately, the Streamlit UI hard-pauses, surfacing a warning block. The human user must explicitly click 'Confirm Action' before the operation is completed, providing a critical human-in-the-loop safeguard."

## 6. Conclusion (3:00 - 3:15)
* **Visual**: Show the successful confirmation message in the chat.
* **Speaker**: 
  > "That covers the core functionality of the ParcelPilot Support Agent! It successfully integrates unstructured policy search, structured data lookup, strict access controls, and human-in-the-loop safety checks. Thank you for watching!"
