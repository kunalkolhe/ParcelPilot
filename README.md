# ParcelPilot AI Support Agent 📦

An intelligent, multi-agent Retrieval-Augmented Generation (RAG) support system built for the ParcelPilot AI Engineer assessment. 

This application serves as a dynamic customer service and internal operations assistant. It securely bridges unstructured policy documents (PDFs) and structured operational data (Excel) to resolve complex support queries, all while strictly adhering to user role permissions.

##  Key Features

* **Intelligent Document Retrieval**: Uses a local **ChromaDB** vector store and `sentence-transformers` embeddings to semantically search and reason over complex, occasionally conflicting company policies.
* **Structured Data Execution**: Integrates with Python's **Pandas** to perform live lookups and calculations against historical customer account, order, and ticket data.
* **Context-Aware Access Control**: A simulated UI sidebar allows the user to switch between a restrictive "Customer" view and a privileged "Internal Support Agent" view. The AI strictly respects these boundaries.
* **Human-in-the-Loop Safeguards**: If the AI attempts to execute a state-changing action (e.g., issuing a refund or creating a ticket), the Streamlit event loop is hard-paused. A UI warning forces explicit human authorization before the mutation proceeds.
* **Zero-Cost Lightning Inference**: Powered by the open-source `openai/gpt-oss-120b` model running on **Groq's** LPU inference engine for near-instantaneous reasoning and function calling.

##  Tech Stack

* **Frontend:** Streamlit (Python)
* **LLM Engine:** Groq API (`openai/gpt-oss-120b`)
* **Vector Database:** ChromaDB
* **Embeddings:** `all-MiniLM-L6-v2` (SentenceTransformers)
* **Data Processing:** Pandas, PyPDF

## ⚙️ Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/kunalkolhe/ParcelPilot.git
cd ParcelPilot
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure Environment Variables**
Rename `.env.example` to `.env` and add your Groq API Key:
```env
GROQ_API_KEY="your_groq_api_key_here"
```

**4. Run the Application**
```bash
streamlit run app.py
```
The application will be accessible at `http://localhost:8502`.

## 📁 Repository Structure
* `app.py`: The main Streamlit frontend interface, UI logic, and LLM chat loop.
* `backend.py`: The backend engine responsible for data ingestion, Pandas lookups, ChromaDB vector search, and tool schema definitions.
* `architecture_note.md`: Explanation of agent and tool design.
* `product_note.md`: Product decisions and future roadmap.
* `ai_tool_usage.md`: Documentation of AI pair-programming usage during development.
