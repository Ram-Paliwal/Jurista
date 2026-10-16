"""
Jurista Session Store
Persistent, isolated conversation context and document management.
Uses SQLite with thread-safe access to ensure strict session isolation.
Allows switching language (English, Hindi, Marathi) without losing history or document context.
"""

from __future__ import annotations
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).parent / "jurista_sessions.db"

def init_db():
    """Initialize SQLite tables for isolated session management."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'English',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                document_json TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                route TEXT,
                sources_json TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)")
        conn.commit()


# Initialize on import
init_db()


class SessionStore:
    """Thread-safe SQLite-backed session store."""

    @staticmethod
    def create_or_get_session(session_id: Optional[str] = None, default_lang: str = "English") -> Dict[str, Any]:
        """Fetch an existing session or initialize a new one with a unique UUID."""
        if not session_id or not session_id.strip():
            session_id = str(uuid.uuid4())

        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, language, created_at, updated_at, document_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                doc_data = json.loads(row[4]) if row[4] else None
                return {
                    "session_id": row[0],
                    "language": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "document": doc_data
                }
            else:
                cursor.execute(
                    "INSERT INTO sessions (session_id, language, created_at, updated_at, document_json) VALUES (?, ?, ?, ?, NULL)",
                    (session_id, default_lang, now, now)
                )
                conn.commit()
                return {
                    "session_id": session_id,
                    "language": default_lang,
                    "created_at": now,
                    "updated_at": now,
                    "document": None
                }

    @staticmethod
    def set_language(session_id: str, language: str) -> bool:
        """Update the session language without altering messages or document context."""
        if language not in ("English", "Hindi", "Marathi"):
            language = "English"

        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET language = ?, updated_at = ? WHERE session_id = ?", (language, now, session_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_language(session_id: str) -> str:
        """Retrieve the currently configured session language."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            return row[0] if row else "English"

    @staticmethod
    def save_document(session_id: str, document_data: Dict[str, Any]) -> None:
        """Associate an extracted legal document with the session."""
        now = time.time()
        doc_json = json.dumps(document_data)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET document_json = ?, updated_at = ? WHERE session_id = ?",
                (doc_json, now, session_id)
            )
            conn.commit()

    @staticmethod
    def get_document(session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the session's active document."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT document_json FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None

    @staticmethod
    def clear_document(session_id: str) -> None:
        """Remove document context from session."""
        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET document_json = NULL, updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()

    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        route: Optional[str] = None,
        sources: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to the isolated session history."""
        msg_id = str(uuid.uuid4())
        now = time.time()
        sources_json = json.dumps(sources) if sources else None

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (message_id, session_id, role, content, route, sources_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, route, sources_json, now)
            )
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()

        return {
            "message_id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "route": route,
            "sources": sources or [],
            "timestamp": now
        }

    @staticmethod
    def get_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve ordered message history for this session."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id, session_id, role, content, route, sources_json, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()

        messages = []
        for r in rows:
            messages.append({
                "message_id": r[0],
                "session_id": r[1],
                "role": r[2],
                "content": r[3],
                "route": r[4],
                "sources": json.loads(r[5]) if r[5] else [],
                "timestamp": r[6]
            })
        return messages

    @staticmethod
    def clear_messages(session_id: str) -> None:
        """Reset conversation messages for this session."""
        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()

    @staticmethod
    def get_conversation_context(session_id: str, max_turns: int = 4) -> str:
        """Format recent conversation turns for prompt context injection."""
        messages = SessionStore.get_messages(session_id)
        if not messages:
            return "No previous conversation context."

        recent = messages[- (max_turns * 2):]
        history_lines = []
        for m in recent:
            prefix = "User" if m["role"] == "user" else "Jurista"
            history_lines.append(f"{prefix}: {m['content']}")
        return "\n".join(history_lines)
