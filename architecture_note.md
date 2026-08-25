# Architecture Note: ParcelPilot AI Support Agent

## Overview
The solution is a Streamlit-based web application that serves as a chat interface, powered by an OpenAI-driven reasoning agent. It connects to two distinct data retrieval systems (a vector database for documents and a pandas-based structured data query engine) and provides a safety-gated action execution tool.

## Agent Design
- **Core Reasoning Engine:** We utilize Groq's `openai/gpt-oss-120b` with Function Calling (Tools) for blazingly fast inference at zero cost.
- **Context Injection:** The system prompt enforces strict rules regarding source reliability (e.g., customer agreements override policies, current overrides deprecated). It also establishes the user's role (Internal Support vs. Customer).
- **Execution Loop:** When the LLM decides to call a tool, the application intercepts the response. Non-mutating tools (`document_search`, `structured_data_lookup`) are executed immediately and their results are fed back into the LLM context. Mutating tools (`take_action`) trigger a hard pause in the UI, requiring explicit human confirmation before the loop continues.

## Tool Design
The agent is equipped with exactly three tools, mapped directly to the assessment requirements:
1. **`document_search(query)`:** Uses an in-memory ChromaDB vector store. PDFs are parsed using `pypdf`, chunked, and embedded locally using `all-MiniLM-L6-v2` (SentenceTransformers) via Chroma's DefaultEmbeddingFunction. Crucially, metadata (like `deprecated = true`) is injected at indexing time so the LLM knows when to distrust a source.
2. **`structured_data_lookup(entity_type, entity_id)`:** Uses `pandas` to query the provided Excel file. It performs flexible text-matching across rows in the relevant sheets (Accounts, Orders, Tickets) and returns structured JSON strings.
3. **`take_action(action_type, details)`:** A mock function that simulates state changes. The application layer wraps this tool to enforce the "Confirmation Before Actions" requirement.

## Access Control and Data Privacy
Access control is implemented by injecting the `user_role` and `account_context` directly into the LLM's system instructions and conversation context for every turn. If the user is simulated as "Customer ACC-001", the LLM is instructed to refuse inquiries regarding other accounts. In a production environment, this context would be securely derived from a session token (JWT) rather than a UI dropdown, and the `structured_data_lookup` tool would enforce row-level security before data ever reaches the LLM.
