"""
Jurista Community Experiences & Evidence Vault Store
SQLite-backed persistence for public community incident reports and private session evidence vaults.
Strictly enforces separation between public community allegations and private user evidence.
"""

from __future__ import annotations
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).parent / "jurista_sessions.db"

def init_community_db():
    """Initialize SQLite tables for Community Experiences and Private Evidence Vault."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Community Reports Table (Public Citizen Experiences & Allegations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_reports (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                description TEXT NOT NULL,
                approx_location_name TEXT,
                latitude REAL,
                longitude REAL,
                incident_date TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                is_public INTEGER NOT NULL DEFAULT 1,
                author_session_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_public_status ON community_reports(is_public, status, created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_topic ON community_reports(topic)")

        # Private Evidence Vault Table (STRICTLY PRIVATE to a user's session)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_vault (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                item_type TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                approx_location TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vault_session ON evidence_vault(session_id, created_at DESC)")
        
        conn.commit()

        # Seed initial realistic public reports if table is completely empty
        cursor.execute("SELECT COUNT(*) FROM community_reports")
        count = cursor.fetchone()[0]
        if count == 0:
            seed_initial_community_reports(conn)


def seed_initial_community_reports(conn: sqlite3.Connection):
    """Seed a diverse set of initial public community reports across India with realistic approximate coordinates."""
    now = time.time()
    day = 86400
    
    seeds = [
        {
            "id": "rep-pune-001",
            "title": "Police Station Refusal to Register Zero FIR for Stolen Vehicle",
            "topic": "Police & FIR",
            "description": "Attempted to register an FIR for a two-wheeler stolen near Shivajinagar railway station. Duty officer insisted on writing a missing report instead of an FIR under BNSS Section 173 (CrPC 154). Escalated to ACP office with a written complaint receipt.",
            "approx_location_name": "Shivajinagar, Pune, Maharashtra",
            "latitude": 18.5314,
            "longitude": 73.8446,
            "incident_date": "2026-09-18",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-pune",
            "created_at": now - 28 * day,
            "updated_at": now - 28 * day
        },
        {
            "id": "rep-bengaluru-002",
            "title": "Builder Delay in Handover Without Occupancy Certificate (OC)",
            "topic": "RERA & Property",
            "description": "Real estate promoter in Whitefield delayed possession by 14 months past the RERA agreement deadline. Offered key possession on an indemnity bond without obtaining statutory OC. Multiple home buyers filing joint complaint under RERA Section 18 for interest refund.",
            "approx_location_name": "Whitefield, Bengaluru, Karnataka",
            "latitude": 12.9698,
            "longitude": 77.7500,
            "incident_date": "2026-09-24",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-blr",
            "created_at": now - 22 * day,
            "updated_at": now - 22 * day
        },
        {
            "id": "rep-delhi-003",
            "title": "E-Commerce Refusal to Refund Damaged Refrigerator",
            "topic": "Consumer Dispute",
            "description": "Delivered a damaged side-by-side refrigerator. Technician confirmed transit physical damage on day 1. E-commerce platform closed complaint stating 'beyond 48 hours policy'. Sent legal demand notice citing Consumer Protection Act 2019 deficiency in service and e-Daakhil filing notice.",
            "approx_location_name": "Connaught Place, New Delhi",
            "latitude": 28.6304,
            "longitude": 77.2177,
            "incident_date": "2026-10-02",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-delhi",
            "created_at": now - 14 * day,
            "updated_at": now - 14 * day
        },
        {
            "id": "rep-mumbai-004",
            "title": "Arbitrary Security Deposit Deduction Without Itemized Bills",
            "topic": "Tenant & Landlord",
            "description": "Vacated 2BHK flat in Andheri West after 3 years tenancy. Landlord withheld ₹60,000 security deposit claiming general repainting and deep cleaning charges despite regular wear-and-tear clauses in registered agreement. Initiating mediation through DLSA.",
            "approx_location_name": "Andheri West, Mumbai, Maharashtra",
            "latitude": 19.1363,
            "longitude": 72.8277,
            "incident_date": "2026-10-08",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-mumbai",
            "created_at": now - 8 * day,
            "updated_at": now - 8 * day
        },
        {
            "id": "rep-hyderabad-005",
            "title": "Online Task Investment Fraud via Instant Messaging Scam",
            "topic": "Cyber Fraud & Scams",
            "description": "Lured into a prepaid YouTube review commission scam that started with ₹500 payout and ended with ₹1.8 Lakh loss. Registered immediate complaint on National Cyber Crime Reporting Portal (1930 / cybercrime.gov.in) within 2 hours to freeze beneficiary account.",
            "approx_location_name": "HITEC City, Hyderabad, Telangana",
            "latitude": 17.4435,
            "longitude": 78.3772,
            "incident_date": "2026-10-12",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-hyd",
            "created_at": now - 4 * day,
            "updated_at": now - 4 * day
        },
        {
            "id": "rep-nolocation-006",
            "title": "National Bank Deducted Penalty on Minimum Balance During Salary Account Transition",
            "topic": "Consumer Dispute",
            "description": "Corporate salary account converted to regular savings account without prior statutory notice upon company resignation, followed by consecutive quarterly penalty charges. Submitted grievance to Banking Ombudsman under RBI Integrated Ombudsman Scheme.",
            "approx_location_name": None,
            "latitude": None,
            "longitude": None,
            "incident_date": "2026-10-10",
            "status": "published",
            "is_public": 1,
            "author_session_id": "system-seed-online",
            "created_at": now - 6 * day,
            "updated_at": now - 6 * day
        },
        {
            "id": "rep-private-draft-007",
            "title": "Private Draft - Cheque Bounce Section 138 Notice",
            "topic": "Cheque Dishonour",
            "description": "Private draft report not published to public feed.",
            "approx_location_name": "Pune, Maharashtra",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "incident_date": "2026-10-15",
            "status": "draft",
            "is_public": 0,
            "author_session_id": "system-seed-private",
            "created_at": now - 1 * day,
            "updated_at": now - 1 * day
        }
    ]

    cursor = conn.cursor()
    for s in seeds:
        cursor.execute("""
            INSERT OR REPLACE INTO community_reports 
            (id, title, topic, description, approx_location_name, latitude, longitude, incident_date, status, is_public, author_session_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["id"], s["title"], s["topic"], s["description"], s["approx_location_name"],
            s["latitude"], s["longitude"], s["incident_date"], s["status"], s["is_public"],
            s["author_session_id"], s["created_at"], s["updated_at"]
        ))
    conn.commit()


# Initialize on import
init_community_db()


class CommunityStore:
    """Thread-safe SQLite controller for Community Experiences."""

    @staticmethod
    def create_report(
        title: str,
        topic: str,
        description: str,
        approx_location_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        incident_date: Optional[str] = None,
        status: str = "published",
        is_public: bool = True,
        author_session_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """Create a new community report. Coordinates are rounded for privacy."""
        report_id = "rep-" + str(uuid.uuid4())[:8]
        now = time.time()
        
        # Approximate coordinate precision (4 decimals ~ 11m, 3 decimals ~ 110m)
        approx_lat = round(latitude, 4) if latitude is not None else None
        approx_lon = round(longitude, 4) if longitude is not None else None
        
        clean_status = "published" if status == "published" else "draft"
        clean_is_public = 1 if is_public else 0

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO community_reports 
                (id, title, topic, description, approx_location_name, latitude, longitude, incident_date, status, is_public, author_session_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, title.strip(), topic.strip(), description.strip(),
                approx_location_name.strip() if approx_location_name else None,
                approx_lat, approx_lon, incident_date, clean_status, clean_is_public,
                author_session_id, now, now
            ))
            conn.commit()

        return {
            "id": report_id,
            "title": title.strip(),
            "topic": topic.strip(),
            "description": description.strip(),
            "approx_location_name": approx_location_name,
            "latitude": approx_lat,
            "longitude": approx_lon,
            "incident_date": incident_date,
            "status": clean_status,
            "is_public": bool(clean_is_public),
            "created_at": now,
            "allegation_disclaimer": "User-submitted community experience/allegation. Not verified findings."
        }

    @staticmethod
    def get_public_reports(
        topic: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        has_location_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch public published community reports.
        STRICT SAFETY ENFORCEMENT: Only is_public=1 and status='published'.
        Private Evidence Vault entries or private drafts are strictly excluded.
        """
        query = """
            SELECT id, title, topic, description, approx_location_name, latitude, longitude, incident_date, created_at
            FROM community_reports
            WHERE is_public = 1 AND status = 'published'
        """
        params: List[Any] = []

        if topic and topic.strip() and topic.strip().lower() != "all":
            query += " AND LOWER(topic) = LOWER(?)"
            params.append(topic.strip())

        if has_location_only:
            query += " AND latitude IS NOT NULL AND longitude IS NOT NULL"

        if from_date and from_date.strip():
            query += " AND incident_date >= ?"
            params.append(from_date.strip())

        if to_date and to_date.strip():
            query += " AND incident_date <= ?"
            params.append(to_date.strip())

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(approx_location_name) LIKE ?)"
            params.extend([term, term, term])

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        reports = []
        for r in rows:
            reports.append({
                "id": r[0],
                "title": r[1],
                "topic": r[2],
                "description": r[3],
                "approx_location_name": r[4],
                "latitude": r[5],
                "longitude": r[6],
                "incident_date": r[7],
                "created_at": r[8],
                "is_public": True,
                "status": "published",
                "allegation_disclaimer": "User-submitted community experience/allegation. Not verified findings."
            })
        return reports

    @staticmethod
    def get_report_by_id(report_id: str, requester_session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a specific report if published public or owned by requester session."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, topic, description, approx_location_name, latitude, longitude, incident_date, status, is_public, author_session_id, created_at
                FROM community_reports WHERE id = ?
            """, (report_id,))
            r = cursor.fetchone()

        if not r:
            return None

        is_public = bool(r[9])
        status = r[8]
        author_session_id = r[10]

        # Safety check: if not public and not author, block access
        if not (is_public and status == "published") and author_session_id != requester_session_id:
            return None

        return {
            "id": r[0],
            "title": r[1],
            "topic": r[2],
            "description": r[3],
            "approx_location_name": r[4],
            "latitude": r[5],
            "longitude": r[6],
            "incident_date": r[7],
            "status": r[8],
            "is_public": is_public,
            "created_at": r[11],
            "allegation_disclaimer": "User-submitted community experience/allegation. Not verified findings."
        }


class EvidenceVaultStore:
    """Thread-safe SQLite controller for Private Evidence Vault items."""

    @staticmethod
    def create_vault_item(
        session_id: str,
        title: str,
        item_type: str,
        description: Optional[str] = None,
        file_path: Optional[str] = None,
        approx_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store a private evidence document/note strictly locked to user's session."""
        item_id = "vlt-" + str(uuid.uuid4())[:8]
        now = time.time()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evidence_vault
                (id, session_id, title, item_type, description, file_path, approx_location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, session_id, title.strip(), item_type.strip(),
                description.strip() if description else None,
                file_path, approx_location, now, now
            ))
            conn.commit()

        return {
            "id": item_id,
            "session_id": session_id,
            "title": title.strip(),
            "item_type": item_type.strip(),
            "description": description,
            "file_path": file_path,
            "approx_location": approx_location,
            "created_at": now,
            "is_private": True
        }

    @staticmethod
    def get_vault_items(session_id: str) -> List[Dict[str, Any]]:
        """Fetch private evidence items strictly belonging to the given session."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, title, item_type, description, file_path, approx_location, created_at
                FROM evidence_vault WHERE session_id = ? ORDER BY created_at DESC
            """, (session_id,))
            rows = cursor.fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "session_id": r[1],
                "title": r[2],
                "item_type": r[3],
                "description": r[4],
                "file_path": r[5],
                "approx_location": r[6],
                "created_at": r[7],
                "is_private": True
            })
        return items

    @staticmethod
    def delete_vault_item(session_id: str, item_id: str) -> bool:
        """Delete an evidence vault item if owned by session."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM evidence_vault WHERE id = ? AND session_id = ?", (item_id, session_id))
            conn.commit()
            return cursor.rowcount > 0
