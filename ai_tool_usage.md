# AI Tool Usage

For this assessment, I used an advanced AI Pair Programmer (Google Deepmind's Antigravity system, paired with Gemini). 

How it was used:
- **Architectural Brainstorming:** Used the AI to determine the best approach for the local vector store (choosing ChromaDB) and structuring the application state loop in Streamlit.
- **Code Generation & Boilerplate:** Used the AI to rapidly write the `backend.py` data ingestion pipeline, implement the Streamlit chat loop, and write the custom CSS to modernise the UI.
- **Debugging & Iteration:** When encountering API limitations (e.g., OpenAI rate limits, Groq model deprecations), the AI was used to quickly adapt the `app.py` script to use alternative free-tier model providers and dynamically look up compatible models.
- **Mocking Tools:** The AI formulated the schema for the `take_action`, `document_search`, and `structured_data_lookup` tools to match the Groq/OpenAI tool-calling specification.
