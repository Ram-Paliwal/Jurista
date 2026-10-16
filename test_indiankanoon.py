"""
test_indiankanoon.py — Quick diagnostic for Indian Kanoon API + legal_db.py
"""
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

import requests

# ── 1. Read key ──────────────────────────────────────────────────────────────
API_KEY = os.environ.get("INDIANKANOON_API_KEY", "").strip()
SEARCH_URL = "https://api.indiankanoon.org/search/"
QUERY = "cheque bounce section 138"

print("=" * 60)
print("  Indian Kanoon API + legal_db.py Diagnostic")
print("=" * 60)

# ── 2. Key presence check ─────────────────────────────────────────────────────
if API_KEY:
    print(f"\n[KEY]  ✅  INDIANKANOON_API_KEY is set  (length: {len(API_KEY)} chars)")
else:
    print("\n[KEY]  ❌  INDIANKANOON_API_KEY is NOT set (or empty) in .env")
    print("           → legal_db.py will use the BM25 fallback automatically.")

# ── 3. Raw API call ───────────────────────────────────────────────────────────
print(f"\n[API]  Querying: {SEARCH_URL!r}")
print(f"       formInput: {QUERY!r}")

if not API_KEY:
    print("[API]  ⚠️   Skipping live API call — no key present.")
else:
    try:
        t0 = time.perf_counter()
        resp = requests.post(
            SEARCH_URL,
            data={"formInput": QUERY, "pagenum": 0},
            headers={
                "Authorization": f"Token {API_KEY}",
                "Accept": "application/json",
            },
            timeout=6,
        )
        elapsed = (time.perf_counter() - t0) * 1000

        print(f"       HTTP {resp.status_code}  ({elapsed:.0f} ms)")

        if resp.ok:
            payload = resp.json()
            docs = payload.get("docs", [])
            print(f"\n[API]  ✅  Success — {len(docs)} document(s) returned")
            for i, doc in enumerate(docs[:3], 1):
                title = doc.get("title", "(no title)")
                tid   = doc.get("tid", "?")
                print(f"       [{i}] tid={tid}  |  {title[:70]}")
        else:
            print(f"\n[API]  ❌  Non-OK response ({resp.status_code})")
            print(f"           Body: {resp.text[:300]}")

    except requests.exceptions.Timeout:
        print("\n[API]  ❌  Request timed out after 6 s")
    except requests.exceptions.ConnectionError as exc:
        print(f"\n[API]  ❌  Connection error: {exc}")
    except Exception as exc:
        print(f"\n[API]  ❌  Unexpected error: {exc}")

# ── 4. search_legal_sources() with source detection ──────────────────────────
print("\n" + "-" * 60)
print("[LDB]  Calling legal_db.search_legal_sources('cheque bounce', 3)")

# Monkey-patch the private helpers to track which path was taken
import legal_db

_source_used = {"value": "unknown"}
_orig_ik  = legal_db._search_indiankanoon
_orig_bm25 = legal_db._search_local_bm25

def _tracked_ik(query, top_k):
    result = _orig_ik(query, top_k)
    if result is not None:
        _source_used["value"] = "🌐  Indian Kanoon API"
    return result

def _tracked_bm25(query, top_k):
    _source_used["value"] = "📚  Local BM25 (hardcoded fallback)"
    return _orig_bm25(query, top_k)

legal_db._search_indiankanoon = _tracked_ik
legal_db._search_local_bm25   = _tracked_bm25

results = legal_db.search_legal_sources("cheque bounce", 3)

print(f"\n[LDB]  Source used  →  {_source_used['value']}")
print(f"[LDB]  Results      →  {len(results)} item(s)")
for i, r in enumerate(results, 1):
    print(f"       [{i}] id={r['id']!r:30s}  act={r['act'][:50]!r}")

# ── 5. format_legal_sources_for_prompt() ─────────────────────────────────────
print("\n" + "-" * 60)
print("[FMT]  format_legal_sources_for_prompt() output (first 400 chars):")
formatted = legal_db.format_legal_sources_for_prompt(results)
print(formatted[:400])
if len(formatted) > 400:
    print("  ... (truncated)")

print("\n" + "=" * 60)
print("  Diagnostic complete.")
print("=" * 60)
