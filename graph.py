"""
Jurista LangGraph Orchestration Pipeline
Coordinates intent classification, statutory + document retrieval,
and response generation with strict scope boundaries.
"""

from __future__ import annotations
import re
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

import prompts
from legal_db import search_legal_sources, format_legal_sources_for_prompt
from rag_engine import retrieve_document_chunks, format_document_chunks
from gemini_client import GeminiClient

class JuristaState(TypedDict):
    session_id: str
    language: str
    user_message: str
    intent: str
    is_out_of_scope: bool
    document_text: Optional[str]
    document_chunks: List[Dict[str, Any]]
    retrieved_doc_chunks: List[Dict[str, Any]]
    retrieved_legal_sources: List[Dict[str, Any]]
    conversation_context: str
    response_text: str


def check_needs_clarification(message: str) -> bool:
    """Detect if a user prompt is so brief or vague that essential facts are missing."""
    text = message.strip()
    words = text.split()
    if len(words) <= 3:
        # e.g., "notice received", "fraud happened", "police arrested", "eviction"
        vague_triggers = [
            "notice", "fir", "arrest", "fraud", "scam", "eviction", "cheque", "case",
            "divorce", "bail", "help me", "police problem", "court", "complaint"
        ]
        if any(vt in text.lower() for vt in vague_triggers):
            return True
    return False


def route_intent_node(state: JuristaState) -> Dict[str, Any]:
    """Classify user intent with zero-cost fast heuristic and fallback router."""
    user_msg = state.get("user_message", "").strip()
    lang = state.get("language", "English")

    # 1. Fast zero-cost out-of-scope check
    if GeminiClient.is_obviously_out_of_scope(user_msg):
        return {
            "intent": "OUT_OF_SCOPE",
            "is_out_of_scope": True,
            "response_text": prompts.build_prompt("OUT_OF_SCOPE", language=lang)
        }

    # 2. Check if a document is present and whether user explicitly asks to explain it
    has_doc = bool(state.get("document_chunks") or state.get("document_text"))
    lower_msg = user_msg.lower()

    explain_keywords = ["explain this document", "analyze this document", "what is this document", "explain pdf", "read this notice", "summarize document"]
    if has_doc and any(kw in lower_msg for kw in explain_keywords):
        return {
            "intent": "DOCUMENT_EXPLAIN",
            "is_out_of_scope": False
        }

    # 3. If there is an active document and user asks a question about it
    if has_doc and len(state.get("conversation_context", "")) > 10:
        # Follow-up context on existing document
        return {
            "intent": "DOCUMENT_FOLLOWUP",
            "is_out_of_scope": False
        }

    # 4. Check for critically missing information needing clarification
    if check_needs_clarification(user_msg):
        return {
            "intent": "NEEDS_CLARIFICATION",
            "is_out_of_scope": False
        }

    # 5. Default legal query
    return {
        "intent": "LEGAL_QUERY",
        "is_out_of_scope": False
    }


def retrieve_sources_node(state: JuristaState) -> Dict[str, Any]:
    """Retrieve document chunks and legal statutory sources separately."""
    user_msg = state.get("user_message", "")
    doc_chunks = state.get("document_chunks") or []

    # 1. Document chunk retrieval (if doc exists)
    retrieved_doc: List[Dict[str, Any]] = []
    if doc_chunks:
        retrieved_doc = retrieve_document_chunks(user_msg, doc_chunks, top_k=3)

    # 2. Curated statutory legal source retrieval
    retrieved_statutes = search_legal_sources(user_msg, top_k=3)

    return {
        "retrieved_doc_chunks": retrieved_doc,
        "retrieved_legal_sources": retrieved_statutes
    }


def generate_answer_node(state: JuristaState) -> Dict[str, Any]:
    """Assemble final prompt and generate grounded response via Gemini Flash."""
    intent = state.get("intent", "LEGAL_QUERY")
    lang = state.get("language", "English")
    user_msg = state.get("user_message", "")
    conv_context = state.get("conversation_context", "")

    # Format sources
    legal_sources_text = format_legal_sources_for_prompt(state.get("retrieved_legal_sources", []))
    doc_chunks_text = format_document_chunks(state.get("retrieved_doc_chunks", []))
    full_doc_text = state.get("document_text") or doc_chunks_text

    client = GeminiClient()

    if intent == "DOCUMENT_EXPLAIN":
        prompt = prompts.build_prompt(
            "DOCUMENT_EXPLAIN",
            language=lang,
            document_text=full_doc_text[:8000],  # Bound prompt length
            retrieved_sources=legal_sources_text,
            user_query=user_msg
        )
    elif intent == "DOCUMENT_FOLLOWUP":
        prompt = prompts.build_prompt(
            "DOCUMENT_FOLLOWUP",
            language=lang,
            document_context=doc_chunks_text,
            conversation_context=conv_context,
            retrieved_sources=legal_sources_text,
            user_query=user_msg
        )
    elif intent == "NEEDS_CLARIFICATION":
        prompt = prompts.build_prompt(
            "NEEDS_CLARIFICATION",
            language=lang,
            user_query=user_msg,
            conversation_context=conv_context
        )
    else:
        # Default: LEGAL_QUERY
        prompt = prompts.build_prompt(
            "LEGAL_QUERY",
            language=lang,
            user_query=user_msg,
            retrieved_sources=legal_sources_text,
            conversation_context=conv_context
        )

    # Call Gemini Flash
    generated = client.generate_content(
        prompt=prompt,
        system_instruction=prompts.SYSTEM_PROMPT
    )

    return {"response_text": generated}


def out_of_scope_node(state: JuristaState) -> Dict[str, Any]:
    """Zero-LLM rejection node for out-of-scope queries."""
    lang = state.get("language", "English")
    rejection = prompts.build_prompt("OUT_OF_SCOPE", language=lang)
    return {"response_text": rejection}


# Routing condition
def should_route_out_of_scope(state: JuristaState) -> str:
    if state.get("is_out_of_scope"):
        return "out_of_scope"
    return "retrieve"


# Build the StateGraph
workflow = StateGraph(JuristaState)

# Add Nodes
workflow.add_node("route_intent", route_intent_node)
workflow.add_node("retrieve_sources", retrieve_sources_node)
workflow.add_node("generate_answer", generate_answer_node)
workflow.add_node("out_of_scope", out_of_scope_node)

# Add Edges
workflow.add_edge(START, "route_intent")
workflow.add_conditional_edges(
    "route_intent",
    should_route_out_of_scope,
    {
        "out_of_scope": "out_of_scope",
        "retrieve": "retrieve_sources"
    }
)
workflow.add_edge("retrieve_sources", "generate_answer")
workflow.add_edge("generate_answer", END)
workflow.add_edge("out_of_scope", END)

# Compile the Graph
jurista_app = workflow.compile()


def process_jurista_turn(
    session_id: str,
    user_message: str,
    language: str = "English",
    document_text: Optional[str] = None,
    document_chunks: Optional[List[Dict[str, Any]]] = None,
    conversation_context: str = ""
) -> Dict[str, Any]:
    """Execute one turn through the compiled LangGraph pipeline."""
    initial_state: JuristaState = {
        "session_id": session_id,
        "language": language,
        "user_message": user_message,
        "intent": "LEGAL_QUERY",
        "is_out_of_scope": False,
        "document_text": document_text,
        "document_chunks": document_chunks or [],
        "retrieved_doc_chunks": [],
        "retrieved_legal_sources": [],
        "conversation_context": conversation_context,
        "response_text": ""
    }

    final_state = jurista_app.invoke(initial_state)
    return {
        "intent": final_state["intent"],
        "is_out_of_scope": final_state["is_out_of_scope"],
        "retrieved_doc_chunks": final_state["retrieved_doc_chunks"],
        "retrieved_legal_sources": final_state["retrieved_legal_sources"],
        "response": final_state["response_text"]
    }
