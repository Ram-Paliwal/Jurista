"""
Jurista Gemini Client Wrapper
Handles communication with Gemini Flash via the official `google-genai` SDK.
Features:
- Loads API key securely from .env
- Fast heuristic pre-check to reject non-legal queries without invoking the LLM
- Graceful error handling and retry mechanism
"""

from __future__ import annotations
import os
import re
from typing import Optional, List, Tuple
from dotenv import load_dotenv

# Load server-side environment variables from .env
load_dotenv()

# Obvious non-legal keywords and patterns for zero-latency, zero-cost rejection
OUT_OF_SCOPE_PATTERNS = [
    r"\b(write|generate|debug|code|script|function|program|class)\b.*(python|java|javascript|c\+\+|html|css|sql|rust|php)\b",
    r"\b(recipe|bake|cook|ingredients|calories|nutrition)\b",
    r"\b(who won|cricket match|football match|world cup|olympics|box office|movie review|song lyrics)\b",
    r"\b(calculate|integral|derivative|algebra|math problem)\b",
    r"^\s*([0-9\+\-\*\/\^\s\(\)\=\%]+)\s*$",
    r"\b(tell me a joke|tell a story|bedtime story|riddle|horoscope|astrology)\b",
    r"\b(weather in|temperature today|forecast)\b",
]

DEFAULT_FLASH_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
FALLBACK_MODELS = [
    DEFAULT_FLASH_MODEL,
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemma-4-31b-it"
]

class GeminiClient:
    """Wrapper around Google Gemini GenAI SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiClient] Initialization notice: {e}")

    def is_configured(self) -> bool:
        """Check if a valid API key is present."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    @staticmethod
    def is_obviously_out_of_scope(text: str) -> bool:
        """
        Fast heuristic pre-filter.
        Rejects obviously non-legal queries without incurring Gemini API latency or cost.
        """
        if not text or not text.strip():
            return False

        lower = text.strip().lower()

        # If it contains explicit legal terms, it's not out-of-scope
        legal_whitelists = [
            "law", "court", "act", "section", "police", "fir", "advocate", "lawyer",
            "notice", "judge", "bail", "crime", "tenant", "rent", "property", "cheque",
            "consumer", "complaint", "divorce", "custody", "agreement", "fine", "arrest",
            "statute", "rights", "petition", "order", "summons", "affidavit", "tribunal",
            "bns", "ipc", "bnss", "crpc", "cpc", "rera", "rti", "cyber", "fraud", "nalsa",
            "कायदे", "कायदा", "न्यायालय", "वकील", "तक्रार", "कानून", "अदालत", "धारा", "पुलिस"
        ]
        if any(term in lower for term in legal_whitelists):
            return False

        for pattern in OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, lower):
                return True

        return False

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Calls Gemini Flash model with graceful automatic fallback across available models.
        Returns generated text or clear user-facing error message.
        """
        if not self.is_configured():
            return (
                "⚠️ **Gemini API Key Required**\n\n"
                "Please add your `GEMINI_API_KEY` to the `.env` file in the project folder to enable live responses.\n\n"
                "Example in `.env`:\n"
                "```env\nGEMINI_API_KEY=AIzaSy...\n```\n\n"
                "*Meanwhile, statutory source retrieval and document parsing remain fully operational.*"
            )

        try:
            from google import genai
            from google.genai import types

            if not self._client:
                self._client = genai.Client(api_key=self.api_key)

            config = None
            if system_instruction:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,  # Low temperature for grounded legal information
                )

            # Build deduplicated priority candidate list
            requested_model = model or DEFAULT_FLASH_MODEL
            candidates = [requested_model]
            for m in FALLBACK_MODELS:
                if m not in candidates:
                    candidates.append(m)

            last_error = None
            for candidate in candidates:
                try:
                    response = self._client.models.generate_content(
                        model=candidate,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as model_err:
                    err_msg = str(model_err)
                    last_error = err_msg
                    print(f"[GeminiClient] Model '{candidate}' encountered issue: {err_msg[:120]}... Trying fallback.")
                    continue

            return f"⚠️ **Gemini Service Notice**: All candidate models temporarily unavailable. Last error: {last_error}"

        except Exception as exc:
            error_str = str(exc)
            print(f"[GeminiClient Error] {error_str}")
            if "API_KEY_INVALID" in error_str or "400" in error_str:
                return f"⚠️ **Gemini API Error**: Invalid or expired API key. Please check `GEMINI_API_KEY` in `.env`."
            elif "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                return f"⚠️ **Rate Limit**: Gemini API rate limit reached. Please wait a few seconds and try again."
            return f"⚠️ **Gemini Error**: {error_str}"

