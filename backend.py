import os
import json
import pandas as pd
from typing import Dict, Any, List
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Global state
df_accounts = None
df_orders = None
df_tickets = None
collection = None

# Mock action log
action_log = []

def init_backend():
    global df_accounts, df_orders, df_tickets, collection
    
    # 1. Load Excel
    excel_path = "ParcelPilot_Assessment_Data.xlsx"
    try:
        df_accounts = pd.read_excel(excel_path, sheet_name="accounts")
        df_orders = pd.read_excel(excel_path, sheet_name="orders")
        df_tickets = pd.read_excel(excel_path, sheet_name="tickets")
    except Exception as e:
        print(f"Error loading Excel: {e}")
        # Create empty dataframes as fallback if sheet names differ
        df_accounts = pd.DataFrame()
        df_orders = pd.DataFrame()
        df_tickets = pd.DataFrame()

    # 2. Load PDFs into ChromaDB
    # Using DefaultEmbeddingFunction (all-MiniLM-L6-v2) for free local embeddings
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    chroma_client = chromadb.Client()
    # Delete if exists to avoid errors on reload
    try:
        chroma_client.delete_collection(name="parcelpilot_docs")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(
        name="parcelpilot_docs", 
        embedding_function=ef
    )
    
    pdfs = [
        "01_Support_Policy_v3_CURRENT.pdf",
        "02_Support_Policy_v2_DEPRECATED.pdf",
        "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
        "04_Product_Operations_Guide_and_Known_Issues.pdf",
        "05_Northstar_Logistics_Enterprise_Agreement.pdf",
        "06_LumenWorks_Service_Agreement.pdf"
    ]
    
    docs = []
    ids = []
    metadatas = []
    
    for pdf in pdfs:
        if not os.path.exists(pdf):
            continue
        reader = PdfReader(pdf)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        
        # Simple chunking (1500 chars)
        chunk_size = 1500
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            ids.append(f"{pdf}_chunk_{i}")
            is_deprecated = "DEPRECATED" in pdf
            metadatas.append({"source": pdf, "deprecated": is_deprecated})
            
    if docs:
        collection.add(
            documents=docs,
            metadatas=metadatas,
            ids=ids
        )

# Tool 1: Document Search
def document_search(query: str) -> str:
    """Searches policies, agreements, product documentation, SOPs."""
    if not collection:
        return "Database not initialized."
        
    results = collection.query(
        query_texts=[query],
        n_results=4
    )
    
    out = []
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        src = meta.get("source", "Unknown")
        dep = " (WARNING: DEPRECATED POLICY)" if meta.get("deprecated") else ""
        out.append(f"--- Source: {src}{dep} ---\n{doc}\n")
        
    return "\n".join(out)

# Tool 2: Structured Data Lookup
def structured_data_lookup(entity_type: str, entity_id: str) -> str:
    """
    Query or calculate information using the supplied account, order, and ticket data.
    entity_type must be one of: 'account', 'order', 'ticket'
    entity_id must be the specific ID (e.g., 'ORD-1001')
    """
    global df_accounts, df_orders, df_tickets
    
    entity_type = entity_type.lower()
    
    if entity_type == 'account':
        df = df_accounts
        if df is None or df.empty: return "No account data available."
        # Attempt to find by Account ID or Name
        # We will do a generic string search across the first few columns
        match = df.astype(str).apply(lambda row: row.astype(str).str.contains(entity_id, case=False).any(), axis=1)
        res = df[match]
        if res.empty:
            return f"No account found matching '{entity_id}'"
        return res.to_json(orient="records")
        
    elif entity_type == 'order':
        df = df_orders
        if df is None or df.empty: return "No order data available."
        match = df.astype(str).apply(lambda row: row.astype(str).str.contains(entity_id, case=False).any(), axis=1)
        res = df[match]
        if res.empty:
            return f"No order found matching '{entity_id}'"
        return res.to_json(orient="records")
        
    elif entity_type == 'ticket':
        df = df_tickets
        if df is None or df.empty: return "No ticket data available."
        match = df.astype(str).apply(lambda row: row.astype(str).str.contains(entity_id, case=False).any(), axis=1)
        res = df[match]
        if res.empty:
            return f"No ticket found matching '{entity_id}'"
        return res.to_json(orient="records")
        
    else:
        return f"Unknown entity_type '{entity_type}'. Must be account, order, or ticket."

# Tool 3: State-Changing Action
def take_action(action_type: str, details: str) -> str:
    """
    Perform a state-changing action (Creating an escalation, Updating a ticket, Creating a follow-up task).
    Requires explicit user confirmation before actually executing.
    action_type should be one of: 'escalate', 'update_ticket', 'create_task'
    """
    log_entry = {"action": action_type, "details": details}
    action_log.append(log_entry)
    return f"SUCCESS: Action '{action_type}' was executed with details: {details}"

# Tools schema for OpenAI
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "document_search",
            "description": "Search policies, agreements, product documentation, SOPs, and other supplied documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "structured_data_lookup",
            "description": "Query or calculate information using the supplied account, order, and ticket data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["account", "order", "ticket"],
                        "description": "The type of entity to look up."
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "The ID of the account, order, or ticket (e.g. ORD-1001, Northstar, etc)."
                    }
                },
                "required": ["entity_type", "entity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_action",
            "description": "Perform a state-changing action such as creating an escalation, updating a ticket, or creating a follow-up task. IMPORTANT: Calling this function will trigger a UI confirmation prompt. Only call this when you have gathered all necessary information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["escalate", "update_ticket", "create_task"],
                        "description": "The type of action to perform."
                    },
                    "details": {
                        "type": "string",
                        "description": "Detailed description of the action being taken, including reasons and specific IDs."
                    }
                },
                "required": ["action_type", "details"]
            }
        }
    }
]

# Helper to dispatch tools
def execute_tool(name: str, arguments: dict) -> str:
    if name == "document_search":
        return document_search(arguments.get("query", ""))
    elif name == "structured_data_lookup":
        return structured_data_lookup(arguments.get("entity_type", ""), arguments.get("entity_id", ""))
    elif name == "take_action":
        return take_action(arguments.get("action_type", ""), arguments.get("details", ""))
    else:
        return f"Error: Unknown function {name}"
