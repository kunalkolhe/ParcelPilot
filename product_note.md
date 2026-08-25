# Product Note: ParcelPilot AI Support Agent

## Addressed Problem
For this assessment, I chose to implement a system that can handle both the Customer-Facing and Internal Support use cases, relying on a simulated "Context Configuration" toggle in the UI. 

However, to address **Problem 2: Trust and Reliability**, I explicitly designed the system to surface metadata about the reliability of sources. The document ingestion pipeline tags the deprecated policy (v2) with a `deprecated: true` flag. The system prompt then aggressively instructs the agent to discard deprecated policies in favor of current ones, and to prioritize customer-specific agreements over general policies. The LLM is forced to cite its sources and reason through conflicting information before responding or taking action.

## Future Development Ideas
If I were continuing to work on this product, I would build:
1. **Hardcoded Data-Layer RBAC**: Right now, the LLM is trusted to filter data based on the context prompt. In production, the `structured_data_lookup` tool should verify the requested `entity_id` against the active session's allowed accounts *before* returning data.
2. **Proactive Issue Detection (Problem 1)**: I would implement a CRON job that periodically runs clustering algorithms on incoming tickets to flag spikes in specific issue types, automatically opening a "Master Ticket" and summarizing the trend for the operations team.
3. **Citations in UI**: Enhance the Streamlit chat to provide clickable source citations so users can view the exact PDF snippet the agent used.

## What Was Intentionally Left Out
- **Authentication**: I used a simple dropdown to simulate the user's role and account context rather than building a full login flow.
- **Persistent Database**: I used an in-memory ChromaDB and loaded Excel files directly via Pandas rather than setting up PostgreSQL/Pinecone, as this makes the submission easy to run locally.

## Success Metric
**Resolution Rate without Human Handoff (Deflection Rate)**: To judge if this product is useful, I would track the percentage of customer inquiries that are successfully resolved by the AI (ending in a closed ticket or satisfied customer) without requiring an escalation to the human support team. An increase in this metric directly translates to reduced operations costs and faster resolution times for customers.
