"""
Jurista Backend Server
FastAPI application providing endpoints for:
- Legal Q&A Chatbot (Scope-enforced, grounded in Indian law)
- PDF Legal Document Explainer (PyMuPDF with scanned/invalid handling)
- Local RAG Retrieval (Statutes + Document chunks)
- Persistent Session Context & Language Switching
"""

from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from session_store import SessionStore
from pdf_parser import extract_text_from_pdf
from rag_engine import chunk_document_text
from graph import process_jurista_turn
from legal_db import search_legal_sources, format_legal_sources_for_prompt
import prompts

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Jurista — AI Indian Legal Assistant",
    description="Accessible, grounded legal document analysis and information assistant.",
    version="2.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Request & Response Models
# -------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Client session UUID")
    message: str = Field(..., min_length=1, description="User question or legal prompt")
    language: Optional[str] = Field(default=None, description="Preferred language (English, Hindi, Marathi)")

class LanguageSwitchRequest(BaseModel):
    session_id: str = Field(..., description="Target session UUID")
    language: str = Field(..., description="English, Hindi, or Marathi")

class ClearSessionRequest(BaseModel):
    session_id: str


# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Health check and configuration status."""
    from gemini_client import GeminiClient
    client = GeminiClient()
    return {
        "status": "healthy",
        "service": "Jurista",
        "gemini_configured": client.is_configured(),
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    }


@app.get("/api/session/{session_id}")
def get_session_details(session_id: str):
    """Retrieve isolated session details, active document status, and chat history."""
    session = SessionStore.create_or_get_session(session_id)
    messages = SessionStore.get_messages(session_id)
    doc = session.get("document")

    doc_summary = None
    if doc:
        doc_summary = {
            "filename": doc.get("filename"),
            "page_count": doc.get("page_count"),
            "total_characters": doc.get("total_characters"),
            "is_scanned": doc.get("is_scanned"),
            "chunk_count": len(doc.get("chunks", []))
        }

    return {
        "session_id": session["session_id"],
        "language": session["language"],
        "document": doc_summary,
        "messages": messages
    }


@app.post("/api/session/language")
def update_language(req: LanguageSwitchRequest):
    """Switch language (English, Hindi, Marathi) seamlessly without losing context."""
    if req.language not in prompts.SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Choose from {prompts.SUPPORTED_LANGUAGES}")

    SessionStore.set_language(req.session_id, req.language)
    return {
        "success": True,
        "session_id": req.session_id,
        "language": req.language
    }


@app.post("/api/session/clear")
def clear_session(req: ClearSessionRequest):
    """Clear chat history and active document for this specific session."""
    SessionStore.clear_messages(req.session_id)
    SessionStore.clear_document(req.session_id)
    return {"success": True, "session_id": req.session_id, "message": "Session reset successfully."}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Main Legal Chatbot Endpoint.
    - Scope Enforcement: Fast rejection of unrelated queries without invoking main model.
    - Indian Law Grounding: Retrieves relevant statutory sources (India Code, eCourts, NALSA).
    - PDF Context: Answers follow-up questions using retrieved document chunks.
    - Multilingual: Responds in the active session language.
    """
    session_id = req.session_id or str(uuid.uuid4())
    session = SessionStore.create_or_get_session(session_id)

    # If language is explicitly passed, update it; otherwise preserve session language
    active_lang = req.language or session.get("language") or "English"
    if req.language:
        SessionStore.set_language(session_id, active_lang)

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Fetch persistent context for this session
    doc = SessionStore.get_document(session_id)
    doc_text = doc.get("full_text") if doc else None
    doc_chunks = doc.get("chunks") if doc else []
    conversation_context = SessionStore.get_conversation_context(session_id, max_turns=4)

    # 2. Record user query in history
    SessionStore.add_message(session_id=session_id, role="user", content=user_text)

    # 3. Execute LangGraph Pipeline
    pipeline_res = process_jurista_turn(
        session_id=session_id,
        user_message=user_text,
        language=active_lang,
        document_text=doc_text,
        document_chunks=doc_chunks,
        conversation_context=conversation_context
    )

    assistant_text = pipeline_res["response"]
    intent = pipeline_res["intent"]
    sources = pipeline_res.get("retrieved_legal_sources", [])

    # 4. Record assistant response in session history
    SessionStore.add_message(
        session_id=session_id,
        role="assistant",
        content=assistant_text,
        route=intent,
        sources=sources
    )

    return {
        "session_id": session_id,
        "language": active_lang,
        "intent": intent,
        "is_out_of_scope": pipeline_res.get("is_out_of_scope", False),
        "sources": sources,
        "retrieved_doc_chunks_count": len(pipeline_res.get("retrieved_doc_chunks", [])),
        "response": assistant_text
    }


@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None)
):
    """
    PDF Legal Document Explainer Endpoint.
    - Validates file format and size
    - Extracts text with PyMuPDF
    - Handles empty, invalid, oversized, and scanned image-only PDFs
    - Chunks document for local RAG
    - Immediately generates structured legal explanation in chosen language
    """
    target_session_id = session_id or str(uuid.uuid4())
    session = SessionStore.create_or_get_session(target_session_id)

    target_lang = language or session.get("language") or "English"
    if language:
        SessionStore.set_language(target_session_id, target_lang)

    # Validate filename
    filename = file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF (.pdf) files are supported for legal document analysis."
        )

    try:
        content_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(exc)}")

    # Extract text using PyMuPDF
    parse_result = extract_text_from_pdf(content_bytes, filename=filename)

    if not parse_result["success"]:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": parse_result["error"],
                "message": parse_result["message"]
            }
        )

    # Chunk the text for local RAG
    full_text = parse_result["full_text"]
    chunks = chunk_document_text(full_text)

    # Handle scanned document without selectable text
    if parse_result["is_scanned"]:
        explanation = (
            "⚠️ **Scanned or Image-Only Document Detected**\n\n"
            f"The uploaded document **{filename}** ({parse_result['page_count']} pages) appears to contain only scanned photos or images "
            f"without an embedded digital text layer (only {parse_result['total_characters']} characters could be extracted).\n\n"
            "**Recommended Action:**\n"
            "1. Run this PDF through an OCR scanner (e.g. Adobe Scan, Google Lens, or Google Drive 'Open with Docs').\n"
            "2. Upload the OCR-processed PDF, or paste the text directly into the chat.\n"
            "3. If this is an urgent court notice, check the hearing date or summons date physically printed on page 1."
        )
    else:
        # Generate full structured legal explanation
        pipeline_res = process_jurista_turn(
            session_id=target_session_id,
            user_message=f"Please analyze and explain this legal document: {filename}",
            language=target_lang,
            document_text=full_text,
            document_chunks=chunks,
            conversation_context=""
        )
        explanation = pipeline_res["response"]

    # Save to session store
    doc_payload = {
        "filename": filename,
        "page_count": parse_result["page_count"],
        "pages_processed": parse_result.get("pages_processed", parse_result["page_count"]),
        "total_characters": parse_result["total_characters"],
        "full_text": full_text,
        "is_scanned": parse_result["is_scanned"],
        "chunks": chunks
    }
    SessionStore.save_document(target_session_id, doc_payload)

    # Add message to history
    upload_notice = f"Uploaded PDF document: **{filename}** ({parse_result['page_count']} pages, {len(chunks)} chunks)."
    SessionStore.add_message(target_session_id, "user", upload_notice)
    SessionStore.add_message(target_session_id, "assistant", explanation, route="DOCUMENT_EXPLAIN")

    return {
        "success": True,
        "session_id": target_session_id,
        "filename": filename,
        "page_count": parse_result["page_count"],
        "total_characters": parse_result["total_characters"],
        "is_scanned": parse_result["is_scanned"],
        "chunk_count": len(chunks),
        "explanation": explanation,
        "message": parse_result["message"]
    }


# Serve static web interface
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=True)
