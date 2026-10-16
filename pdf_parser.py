"""
Jurista PDF Parser Module
Robust text extraction and validation for Indian legal documents using PyMuPDF.
Handles empty, invalid, oversized, and image-only scanned PDFs gracefully.
"""

from __future__ import annotations
import io
from typing import Dict, Any, List
import pymupdf  # official recommended import

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MAX_PAGE_LIMIT = 50                     # 50 page limit for legal petitions / notices
MIN_TEXT_CHARS_FOR_DIGITAL = 50         # threshold to identify scanned PDFs

class PDFParseException(Exception):
    """Custom exception for controlled PDF parsing feedback."""
    pass


def extract_text_from_pdf(
    file_bytes: bytes,
    filename: str = "document.pdf",
    max_pages: int = MAX_PAGE_LIMIT
) -> Dict[str, Any]:
    """
    Extracts text and page-by-page metadata from PDF bytes.
    
    Returns a dict with:
        - success: bool
        - filename: str
        - page_count: int
        - total_characters: int
        - full_text: str
        - pages: List[Dict[str, Any]] (page_num, text, char_count)
        - is_scanned: bool
        - message: str
        - error: str | None
    """
    if not file_bytes:
        return {
            "success": False,
            "filename": filename,
            "page_count": 0,
            "total_characters": 0,
            "full_text": "",
            "pages": [],
            "is_scanned": False,
            "message": "The uploaded file is empty (0 bytes).",
            "error": "EMPTY_FILE"
        }

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return {
            "success": False,
            "filename": filename,
            "page_count": 0,
            "total_characters": 0,
            "full_text": "",
            "pages": [],
            "is_scanned": False,
            "message": f"The file size ({size_mb:.1f} MB) exceeds the maximum allowed limit of 15 MB.",
            "error": "FILE_TOO_LARGE"
        }

    # Verify PDF magic header (%PDF-)
    if not file_bytes.startswith(b"%PDF-"):
        return {
            "success": False,
            "filename": filename,
            "page_count": 0,
            "total_characters": 0,
            "full_text": "",
            "pages": [],
            "is_scanned": False,
            "message": "The uploaded file is not a valid PDF document or is corrupted.",
            "error": "INVALID_PDF_FORMAT"
        }

    try:
        # Open PDF from in-memory stream using PyMuPDF
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        return {
            "success": False,
            "filename": filename,
            "page_count": 0,
            "total_characters": 0,
            "full_text": "",
            "pages": [],
            "is_scanned": False,
            "message": f"Failed to open or decode PDF document: {str(exc)}",
            "error": "PDF_DECODE_ERROR"
        }

    try:
        total_pages = len(doc)
        if total_pages == 0:
            return {
                "success": False,
                "filename": filename,
                "page_count": 0,
                "total_characters": 0,
                "full_text": "",
                "pages": [],
                "is_scanned": False,
                "message": "The PDF document contains 0 pages.",
                "error": "EMPTY_DOCUMENT"
            }

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        pages_to_process = min(total_pages, max_pages)

        for page_idx in range(pages_to_process):
            page = doc[page_idx]
            page_text = page.get_text("text") or ""
            # Basic text clean-up: remove null bytes and excessive whitespace
            clean_text = page_text.replace("\x00", "").strip()
            
            pages_data.append({
                "page_num": page_idx + 1,
                "text": clean_text,
                "char_count": len(clean_text)
            })
            if clean_text:
                full_text_parts.append(f"--- [Page {page_idx + 1}] ---\n{clean_text}")

        combined_text = "\n\n".join(full_text_parts).strip()
        total_chars = len(combined_text)

        # Check for scanned image-only PDF
        is_scanned = total_chars < MIN_TEXT_CHARS_FOR_DIGITAL
        
        notice_message = "Document text successfully extracted."
        if is_scanned:
            notice_message = (
                "Notice: This PDF appears to be a scanned image or photographed document with little to no selectable text "
                f"({total_chars} characters extracted). For accurate legal analysis, please upload a text-searchable (OCR'd) PDF "
                "or paste the relevant notice text directly."
            )
        elif total_pages > max_pages:
            notice_message = (
                f"Document text extracted for the first {max_pages} of {total_pages} pages to preserve performance."
            )

        return {
            "success": True,
            "filename": filename,
            "page_count": total_pages,
            "pages_processed": pages_to_process,
            "total_characters": total_chars,
            "full_text": combined_text,
            "pages": pages_data,
            "is_scanned": is_scanned,
            "message": notice_message,
            "error": None
        }

    finally:
        try:
            doc.close()
        except Exception:
            pass
