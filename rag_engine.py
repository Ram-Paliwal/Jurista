"""
Jurista RAG Engine
Lightweight, local retrieval-augmented generation engine.
Performs document chunking, lexical ranking, and keeps document retrieval
strictly separated from legal statutory retrieval.
"""

from __future__ import annotations
import math
import re
from typing import List, Dict, Any

DEFAULT_CHUNK_SIZE = 750
DEFAULT_CHUNK_OVERLAP = 120

def clean_text_for_tokens(text: str) -> List[str]:
    """Tokenize and normalize text for simple lexical retrieval."""
    return re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]{2,}\b", text.lower())


def chunk_document_text(
    full_text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Split document text into structured overlapping chunks, preserving paragraph structure.
    Extracts page markers (e.g. '--- [Page X] ---') if present.
    """
    if not full_text or not full_text.strip():
        return []

    # Identify page segments if present
    page_sections = re.split(r"(--- \[Page \d+\] ---)", full_text)
    
    sections = []
    current_page = "1"
    
    idx = 0
    while idx < len(page_sections):
        part = page_sections[idx]
        page_match = re.match(r"--- \[Page (\d+)\] ---", part.strip())
        if page_match:
            current_page = page_match.group(1)
            idx += 1
            if idx < len(page_sections):
                sections.append((current_page, page_sections[idx]))
                idx += 1
        else:
            if part.strip():
                sections.append((current_page, part))
            idx += 1

    if not sections:
        sections = [("1", full_text)]

    chunks: List[Dict[str, Any]] = []
    chunk_id = 1

    for page_num, section_text in sections:
        # Split into natural paragraphs
        paragraphs = [p.strip() for p in section_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [section_text.strip()]

        current_buffer = ""
        for para in paragraphs:
            if len(current_buffer) + len(para) + 2 <= chunk_size:
                if current_buffer:
                    current_buffer += "\n\n" + para
                else:
                    current_buffer = para
            else:
                if current_buffer:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "text": current_buffer,
                        "tokens": clean_text_for_tokens(current_buffer)
                    })
                    chunk_id += 1
                    # Keep overlap from the end of current buffer
                    overlap_text = current_buffer[-chunk_overlap:] if len(current_buffer) > chunk_overlap else ""
                    current_buffer = (overlap_text + "\n" + para).strip()
                else:
                    # Para itself is larger than chunk_size, slice by sentences
                    sentences = re.split(r"(?<=[.!?।])\s+", para)
                    sent_buffer = ""
                    for sent in sentences:
                        if len(sent_buffer) + len(sent) + 1 <= chunk_size:
                            sent_buffer = (sent_buffer + " " + sent).strip()
                        else:
                            if sent_buffer:
                                chunks.append({
                                    "chunk_id": chunk_id,
                                    "page": page_num,
                                    "text": sent_buffer,
                                    "tokens": clean_text_for_tokens(sent_buffer)
                                })
                                chunk_id += 1
                            sent_buffer = sent
                    if sent_buffer:
                        current_buffer = sent_buffer

        if current_buffer:
            chunks.append({
                "chunk_id": chunk_id,
                "page": page_num,
                "text": current_buffer,
                "tokens": clean_text_for_tokens(current_buffer)
            })
            chunk_id += 1

    return chunks


def retrieve_document_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Lexical BM25-style relevance ranking over document chunks.
    Ensures that document retrieval is completely transparent, fast, and local.
    """
    if not chunks:
        return []

    if not query or not query.strip():
        # Return first top_k chunks as overview
        return chunks[:top_k]

    query_tokens = clean_text_for_tokens(query)
    if not query_tokens:
        return chunks[:top_k]

    total_chunks = len(chunks)
    # Calculate document frequency (DF) for query tokens
    df: Dict[str, int] = {}
    for t in query_tokens:
        df[t] = sum(1 for c in chunks if t in c["tokens"])

    scored: List[tuple[float, Dict[str, Any]]] = []
    avg_dl = sum(len(c["tokens"]) for c in chunks) / max(total_chunks, 1)
    k1 = 1.5
    b = 0.75

    for c in chunks:
        doc_tokens = c["tokens"]
        doc_len = len(doc_tokens)
        score = 0.0

        for t in query_tokens:
            if t in doc_tokens:
                f = doc_tokens.count(t)
                doc_freq = df.get(t, 0)
                # BM25 IDF
                idf = math.log(1.0 + (total_chunks - doc_freq + 0.5) / (doc_freq + 0.5))
                # BM25 TF
                denom = f + k1 * (1.0 - b + b * (doc_len / (avg_dl or 1.0)))
                tf = (f * (k1 + 1.0)) / denom
                score += idf * tf

        # If exact phrase or query snippet appears in chunk text, give a boost
        if query.lower() in c["text"].lower():
            score += 5.0

        if score > 0:
            scored.append((score, c))

    if not scored:
        # Fallback to the leading chunks so context is not blank
        return chunks[:top_k]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def format_document_chunks(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved document chunks for prompt injection."""
    if not chunks:
        return "No specific document uploaded or no relevant document chunks retrieved."

    formatted = []
    for c in chunks:
        formatted.append(
            f"[Document Excerpt — Page {c.get('page', 'Unknown')}, Chunk #{c.get('chunk_id', 1)}]:\n"
            f'"{c.get("text", "").strip()}"'
        )
    return "\n\n".join(formatted)
