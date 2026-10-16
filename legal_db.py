"""
Jurista Indian Legal Knowledge Base & Source Retriever.

Architecture: Primary / Fallback
---------------------------------
1. PRIMARY — Indian Kanoon API (https://api.indiankanoon.org)
   Queries live case law and statutory text via INDIANKANOON_API_KEY from .env.
   Returns top-k results normalised to the same dict schema used by the
   hardcoded database so that no other module requires any changes.

2. FALLBACK — Curated hardcoded statutory database (BM25 keyword scoring)
   Used automatically when:
     • INDIANKANOON_API_KEY is absent or empty.
     • The Indian Kanoon API is unreachable (network error, timeout, 5xx).
     • The API returns an empty result set.
   Falls back silently — callers never observe any difference in return type.

Curated provisions are sourced from official Indian repositories:
India Code (indiacode.nic.in), eCourts (services.ecourts.gov.in), NALSA (nalsa.gov.in).
Never hallucinate section numbers or citations.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indian Kanoon API configuration
# ---------------------------------------------------------------------------
_INDIANKANOON_API_KEY: Optional[str] = os.environ.get("INDIANKANOON_API_KEY", "").strip() or None
_INDIANKANOON_SEARCH_URL = "https://api.indiankanoon.org/search/"
_API_TIMEOUT_SECONDS = 6  # keep latency acceptable; fallback on timeout

# ---------------------------------------------------------------------------
# BM25 relevance threshold — tune this value to tighten / relax filtering.
# Results with a score below this threshold are discarded rather than returned
# as low-quality matches.  Raise it to be more selective; lower it to surface
# more statutes at the cost of relevance.
# ---------------------------------------------------------------------------
MINIMUM_RELEVANCE_SCORE: int = 8

# ---------------------------------------------------------------------------
# Curated statutory database with official India Code references (FALLBACK)
# ---------------------------------------------------------------------------
LEGAL_STATUTES: List[Dict[str, Any]] = [
    {
        "id": "ni_act_138",
        "domain": "criminal",
        "act": "Negotiable Instruments Act, 1881",
        "section": "Section 138",
        "title": "Dishonour of Cheque for Insufficiency of Funds",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2189",
        "keywords": ["cheque bounce", "check bounce", "cheque", "dishonour", "insufficient funds", "138", "demand notice", "15 days", "bank return"],
        "summary": "When a cheque drawn for discharge of debt/liability is returned unpaid by bank due to insufficient funds, it is a criminal offence punishable with imprisonment up to 2 years or fine up to twice the cheque amount. A statutory demand notice must be dispatched within 30 days of receipt of cheque return memo giving the drawer 15 days to pay.",
        "procedure": "1. Collect bank return memo. 2. Send formal legal notice within 30 days via Registered Post. 3. Provide 15 days to pay. 4. If unpaid, file criminal complaint under Section 142 before Judicial Magistrate within 30 days from expiry of the 15-day notice period."
    },
    {
        "id": "ni_act_141",
        "domain": "criminal",
        "act": "Negotiable Instruments Act, 1881",
        "section": "Section 141",
        "title": "Offences by Companies",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2189",
        "keywords": ["cheque company", "director liability", "company cheque bounce", "director", "vicarious liability"],
        "summary": "If the person committing an offence under section 138 is a company, every person who at the time was in charge of and responsible to the company for the conduct of its business shall be deemed guilty, along with the company itself.",
        "procedure": "Notice and complaint must specifically aver the role and direct responsibility of the named directors."
    },
    {
        "id": "cpa_2019_deficiency",
        "domain": "consumer",
        "act": "Consumer Protection Act, 2019",
        "section": "Section 2(11) & Section 35",
        "title": "Deficiency in Goods or Services & Complaint Filing",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/15256",
        "keywords": ["consumer", "defective product", "refund", "warranty", "e-commerce", "airline cancellation", "medical negligence", "deficiency in service", "edaakhil"],
        "summary": "Protects consumers against deficiency in goods or services, unfair trade practices, and misleading advertisements. Consumers can file a complaint electronically via the e-Daakhil portal (edaakhil.nic.in).",
        "procedure": "District Consumer Commission entertains claims where consideration value does not exceed Rs. 50 Lakhs. Can be filed where the complainant resides. Limitation period is 2 years from date on which cause of action arose."
    },
    {
        "id": "bnss_173_fir",
        "domain": "procedure",
        "act": "Bharatiya Nagarik Suraksha Sanhita, 2023 / CrPC 154",
        "section": "BNSS Section 173 (CrPC Section 154)",
        "title": "Information in Cognizable Cases (FIR Registration)",
        "official_url": "https://www.indiacode.nic.in",
        "keywords": ["fir", "police complaint", "refuse fir", "cognizable", "police station", "zero fir", "online fir"],
        "summary": "Mandates police officers to register a First Information Report (FIR) for cognizable offences without unreasonable delay. Provides for Zero FIR (can be registered at any police station irrespective of jurisdiction) and e-FIR.",
        "procedure": "1. A free copy of the FIR must be provided to the informant immediately. 2. If the officer-in-charge refuses, send substance of information in writing by post to Superintendent of Police (SP) under BNSS Section 173(4). 3. If still unaddressed, file application before Judicial Magistrate under BNSS Section 175(3)."
    },
    {
        "id": "bnss_35_arrest",
        "domain": "procedure",
        "act": "Bharatiya Nagarik Suraksha Sanhita, 2023 / CrPC 41A",
        "section": "BNSS Section 35 (CrPC Section 41A)",
        "title": "Notice of Appearance Before Police Officer",
        "official_url": "https://www.indiacode.nic.in",
        "keywords": ["police notice", "41a", "arrest protection", "notice of appearance", "police questioning", "custody"],
        "summary": "For offences punishable with imprisonment up to 7 years, arrest is not automatic. The police officer must issue a formal Notice of Appearance directing the person to appear before them. Compliance with notice prevents arrest unless reasons are recorded in writing.",
        "procedure": "Always appear with counsel or record receipt. Take acknowledgment of attendance with date and time."
    },
    {
        "id": "bns_cheating_318",
        "domain": "criminal",
        "act": "Bharatiya Nyaya Sanhita, 2023 / IPC 420",
        "section": "BNS Section 318 (IPC Section 420)",
        "title": "Cheating and Dishonestly Inducing Delivery of Property",
        "official_url": "https://www.indiacode.nic.in",
        "keywords": ["fraud", "cheating", "scam", "financial fraud", "deceit", "420", "money taken", "fake promise"],
        "summary": "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property commits an offence punishable with imprisonment up to 7 years and fine.",
        "procedure": "File written complaint at local police station or Cyber Crime cell with transaction records, chat transcripts, and bank statements."
    },
    {
        "id": "it_act_66d",
        "domain": "cyber",
        "act": "Information Technology Act, 2000",
        "section": "Section 66D & 43",
        "title": "Cheating by Personation Using Computer Resource & Cyber Fraud",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/1999",
        "keywords": ["cyber crime", "online fraud", "upi fraud", "phishing", "identity theft", "credit card fraud", "cyber helpline", "1930"],
        "summary": "Punishes cheating by personating through any computer resource with imprisonment up to 3 years and fine up to 1 lakh. Section 43 covers civil compensation for unauthorized access and data theft.",
        "procedure": "Immediately call National Cyber Crime Helpline '1930' to freeze illicit bank transfers, and file formal complaint at https://cybercrime.gov.in within 24 hours."
    },
    {
        "id": "tpa_106_lease",
        "domain": "tenancy",
        "act": "Transfer of Property Act, 1882",
        "section": "Section 106 & Section 108",
        "title": "Duration of Leases & Notice to Terminate Tenancy",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2338",
        "keywords": ["tenant", "landlord", "eviction", "rent agreement", "security deposit", "notice period", "leave and license", "flat rent"],
        "summary": "Leases from month-to-month are terminable by 15 days' notice expiring with the end of a month of the tenancy. A landlord cannot evict a tenant by force or illegal disconnection of electricity/water without due process of law.",
        "procedure": "Notice must be in writing, signed, and delivered in person or by registered post. Unlawful eviction allows tenant to seek injunction from civil court or Rent Tribunal."
    },
    {
        "id": "pwdva_2005",
        "domain": "family",
        "act": "Protection of Women from Domestic Violence Act, 2005",
        "section": "Section 12, 18 & 19",
        "title": "Application to Magistrate, Protection Orders & Right to Reside",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2021",
        "keywords": ["domestic violence", "pwdva", "maintenance", "cruelty", "dowry", "shared household", "protection officer"],
        "summary": "Aggrieved woman can apply to Judicial Magistrate for protection orders (prohibiting acts of violence), residence orders (right to reside in shared household), monetary relief, and custody orders.",
        "procedure": "Approach Protection Officer, Service Provider, or Judicial Magistrate directly. National Women Helpline: 181. Free legal aid provided by DLSA."
    },
    {
        "id": "rera_2016_18",
        "domain": "property",
        "act": "Real Estate (Regulation and Development) Act, 2016",
        "section": "Section 18 & Section 31",
        "title": "Return of Amount and Compensation for Delayed Builder Possession",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2158",
        "keywords": ["builder delay", "rera", "flat possession", "builder refund", "homebuyer", "allotment"],
        "summary": "If builder fails to complete or give possession in accordance with terms of agreement for sale, allottee is entitled to refund of amount paid along with interest at prescribed rate, or monthly interest for every month of delay.",
        "procedure": "File complaint online before State RERA Authority under Section 31."
    },
    {
        "id": "rti_act_2005_6",
        "domain": "procedure",
        "act": "Right to Information Act, 2005",
        "section": "Section 6 & Section 7",
        "title": "Request for Obtaining Information & Time Limits",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2065",
        "keywords": ["rti", "right to information", "public authority", "government delay", "pio", "first appeal", "rtionline"],
        "summary": "A citizen can request information from any Public Authority in writing or via rtionline.gov.in. Information must be provided within 30 days (48 hours if life or liberty is involved).",
        "procedure": "If not received within 30 days, file First Appeal under Section 19(1) to First Appellate Authority within 30 days."
    },
    {
        "id": "nalsa_legal_aid_1987",
        "domain": "legal_aid",
        "act": "Legal Services Authorities Act, 1987",
        "section": "Section 12",
        "title": "Criteria for Giving Free Legal Services",
        "official_url": "https://nalsa.gov.in",
        "keywords": ["free legal aid", "nalsa", "dlsa", "slsa", "lawyer help", "cannot afford lawyer", "15100"],
        "summary": "Provides free, competent legal services to marginalized sections including women, children, members of SC/ST, victims of trafficking, disabled persons, industrial workmen, and persons in custody or below income thresholds.",
        "procedure": "Apply online at nalsa.gov.in, approach local District Legal Services Authority (DLSA) at district court, or call toll-free helpline 15100."
    },
    {
        "id": "ecourts_tracking",
        "domain": "procedure",
        "act": "eCourts Services & Case Tracking Framework",
        "section": "CNR Number Verification",
        "title": "Official Court Case Status Tracking",
        "official_url": "https://services.ecourts.gov.in",
        "keywords": ["ecourts", "cnr", "case status", "court hearing", "cause list", "case order"],
        "summary": "The eCourts Services portal (services.ecourts.gov.in) provides verified real-time case information using the 16-character alphanumeric Case Natural Record (CNR) number, Case Number, or Party Name.",
        "procedure": "Check official case status exclusively at https://services.ecourts.gov.in or via the official eCourts Services mobile app."
    }
]


# ---------------------------------------------------------------------------
# Indian Kanoon API — primary retrieval
# ---------------------------------------------------------------------------

def _normalise_indiankanoon_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single Indian Kanoon search result dict into the same schema
    used by the hardcoded LEGAL_STATUTES entries so that callers require
    zero changes.

    Indian Kanoon search result fields (typical):
        tid         -- document ID (integer)
        title       -- document title / case name
        headline    -- short text excerpt / holding
        doctype     -- "judgments" | "acts" | etc.
        publishdate -- date string
        court       -- court name (for judgments)
    """
    tid = str(doc.get("tid", ""))
    title = str(doc.get("title", "")).strip()
    headline = str(doc.get("headline", "")).strip()
    doctype = str(doc.get("doctype", "")).strip()
    court = str(doc.get("court", "")).strip()
    publish_date = str(doc.get("publishdate", "")).strip()

    # Build a sensible act/section label from available metadata.
    if doctype.lower() == "acts":
        act_label = title
        section_label = "Indian Kanoon -- Acts"
    else:
        act_label = court or "Indian Kanoon"
        section_label = publish_date or doctype or "Judgment"

    official_url = f"https://indiankanoon.org/doc/{tid}/" if tid else "https://indiankanoon.org/"

    return {
        "id": f"ik_{tid}",
        "act": act_label,
        "section": section_label,
        "title": title,
        "official_url": official_url,
        "keywords": [],          # live results; keywords not pre-indexed
        "domain": "general",      # Indian Kanoon results carry no domain metadata
        "summary": headline or title,
        "procedure": (
            f"Refer to the full document at {official_url} for complete "
            "procedural details and citations."
        ),
    }


def _search_indiankanoon(query: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
    """
    Call the Indian Kanoon Search API and return normalised results.

    Returns:
        A non-empty list of normalised dicts on success.
        None if the API key is missing, the call fails, or results are empty.
        Failures are logged at DEBUG level so production logs stay clean.
    """
    if not _INDIANKANOON_API_KEY:
        return None

    try:
        response = requests.post(
            _INDIANKANOON_SEARCH_URL,
            data={"formInput": query, "pagenum": 0},
            headers={
                "Authorization": f"Token {_INDIANKANOON_API_KEY}",
                "Accept": "application/json",
            },
            timeout=_API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.Timeout:
        logger.debug("Indian Kanoon API timed out for query %r -- using fallback.", query)
        return None
    except requests.exceptions.RequestException as exc:
        logger.debug("Indian Kanoon API request failed: %s -- using fallback.", exc)
        return None
    except ValueError:
        logger.debug("Indian Kanoon API returned non-JSON response -- using fallback.")
        return None

    docs: List[Dict[str, Any]] = payload.get("docs", [])
    if not docs:
        logger.debug("Indian Kanoon API returned empty results for query %r -- using fallback.", query)
        return None

    results = [_normalise_indiankanoon_doc(d) for d in docs[:top_k]]
    logger.debug("Indian Kanoon API returned %d result(s) for query %r.", len(results), query)
    return results


# ---------------------------------------------------------------------------
# BM25-style fallback -- local hardcoded database
# ---------------------------------------------------------------------------

# Keyword → domain mapping used by classify_query_domain.
# Each list entry is matched as a substring of the lowercased query so that
# multi-word phrases (e.g. "domestic violence") work without tokenisation.
_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "tenancy": [
        "tenant", "landlord", "rent", "eviction", "deposit",
        "security deposit", "lease", "flat rent", "notice period",
        "leave and license",
    ],
    "criminal": [
        "fir", "police", "arrest", "cheque", "fraud", "cheating",
        "bail", "complaint", "cognizable",
    ],
    "consumer": [
        "consumer", "refund", "warranty", "defective", "product",
        "service", "e-commerce", "airline", "medical negligence",
    ],
    "cyber": [
        "cyber", "online fraud", "upi", "phishing", "hacking",
        "credit card", "1930", "cybercrime",
    ],
    "property": [
        "builder", "rera", "possession", "flat", "homebuyer",
        "allotment", "apartment",
    ],
    "family": [
        "domestic violence", "divorce", "maintenance", "dowry",
        "cruelty", "custody", "wife", "husband",
    ],
    "procedure": [
        "rti", "information", "court", "fir", "magistrate",
        "case status", "cnr", "ecourts",
    ],
    "legal_aid": [
        "free lawyer", "legal aid", "nalsa", "dlsa",
        "cannot afford", "15100",
    ],
}

# Score threshold that lets a very high-confidence BM25 hit bypass the
# domain gate entirely (= MINIMUM_RELEVANCE_SCORE * 2).
_DOMAIN_OVERRIDE_SCORE: int = MINIMUM_RELEVANCE_SCORE * 2


def classify_query_domain(query: str) -> List[str]:
    """
    Classify a natural-language legal query into one or more domain labels.

    Iterates over ``_DOMAIN_KEYWORDS`` and checks whether any keyword for a
    domain appears as a substring of the lowercased query.  A query may match
    multiple domains; all matched domains are returned so that the caller can
    apply a union filter rather than forcing a single category.

    Args:
        query: The user's natural-language legal query.

    Returns:
        A list of matched domain strings (e.g. ``["criminal", "procedure"]``).
        Returns ``["general"]`` when no domain keyword matches, signalling that
        no domain filter should be applied.
    """
    q_lower = query.lower()
    matched: List[str] = [
        domain
        for domain, keywords in _DOMAIN_KEYWORDS.items()
        if any(kw in q_lower for kw in keywords)
    ]
    return matched if matched else ["general"]


def _search_local_bm25(
    query: str,
    top_k: int,
    min_score: int = MINIMUM_RELEVANCE_SCORE,
) -> List[Dict[str, Any]]:
    """
    Search the curated LEGAL_STATUTES using keyword and term overlap scoring,
    with an optional domain pre-filter derived from ``classify_query_domain``.

    Filtering logic
    ---------------
    1. Score every statute with the BM25-style keyword scorer.
    2. Discard any result whose score is below ``min_score``.
    3. Classify the query into matched domains via ``classify_query_domain``.
    4. If the query matches specific domains (not ``["general"]``):
       - Keep a result if its ``domain`` field is in the matched domains, OR
       - Keep it unconditionally if its score exceeds ``_DOMAIN_OVERRIDE_SCORE``
         (``MINIMUM_RELEVANCE_SCORE * 2``), treating very high BM25 confidence
         as a reliable signal that overrides the domain gate.
    5. If the query is ``["general"]`` (no domain matched), no domain filter
       is applied — only the score threshold governs inclusion.

    Args:
        query:     The user's natural-language legal query.
        top_k:     Maximum number of results to return.
        min_score: Per-call score floor; defaults to ``MINIMUM_RELEVANCE_SCORE``.
    """
    tokens = set(re.findall(r"\w+", query.lower()))
    scored_results = []

    for item in LEGAL_STATUTES:
        score = 0
        # Check explicit keywords
        for kw in item["keywords"]:
            kw_tokens = set(re.findall(r"\w+", kw.lower()))
            overlap = len(tokens.intersection(kw_tokens))
            if overlap > 0:
                score += overlap * 3
            if kw.lower() in query.lower():
                score += 8

        # Check act and section
        act_tokens = set(re.findall(r"\w+", item["act"].lower()))
        sec_tokens = set(re.findall(r"\w+", item["section"].lower()))
        score += len(tokens.intersection(act_tokens)) * 2
        score += len(tokens.intersection(sec_tokens)) * 4

        # Check summary tokens
        sum_tokens = set(re.findall(r"\w+", item["summary"].lower()))
        score += len(tokens.intersection(sum_tokens)) * 1

        if score >= min_score:  # discard anything below the relevance threshold
            scored_results.append((score, item))

    # --- Domain filtering ---------------------------------------------------
    matched_domains = classify_query_domain(query)
    if matched_domains != ["general"]:
        domain_set = set(matched_domains)
        scored_results = [
            (score, item)
            for score, item in scored_results
            if item["domain"] in domain_set          # domain matches, OR
            or score >= _DOMAIN_OVERRIDE_SCORE       # very high BM25 confidence
        ]
        logger.debug(
            "Domain filter applied: %s — %d result(s) remain.",
            matched_domains,
            len(scored_results),
        )

    # Sort descending by score; return empty list if nothing clears the bar
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_results[:top_k]]


# ---------------------------------------------------------------------------
# Public API -- return signature unchanged; no other file needs modification
# ---------------------------------------------------------------------------

def search_legal_sources(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search Indian legal sources for the most relevant statutory references.

    Strategy (domain-aware, two-path):

    Path A — known domain (classify_query_domain returns something other than
    ``["general"]``):
      1. Local BM25 over curated LEGAL_STATUTES (preferred — corpus is curated
         and domain-tagged, so precision is high for matching entries).
      2. Indian Kanoon API as fallback if BM25 returns no results (handles
         queries that fall outside the hardcoded statute set).

    Path B — general / unclassified query (classify_query_domain → ``["general"]``):
      1. Indian Kanoon API (live, broad coverage).
      2. Local BM25 if the API is unavailable or returns nothing.

    Args:
        query:  The user's natural-language legal query.
        top_k:  Maximum number of results to return (default: 3).

    Returns:
        List of up to ``top_k`` dicts, each with keys:
        ``id``, ``act``, ``section``, ``title``, ``official_url``,
        ``keywords``, ``summary``, ``procedure``, ``domain``.
        Returns an empty list for blank queries.
    """
    if not query or not query.strip():
        return []

    matched_domains = classify_query_domain(query)

    if matched_domains != ["general"]:
        # ------------------------------------------------------------------
        # Path A: known domain — local BM25 only, no Indian Kanoon fallback.
        # Rationale: Indian Kanoon has no domain awareness; if our curated
        # corpus has no match for a known domain it signals a database gap,
        # not that IK will produce more relevant results.
        # ------------------------------------------------------------------
        bm25_results = _search_local_bm25(query, top_k)
        if bm25_results:
            logger.debug(
                "Domain-specific query %r: returning %d local BM25 result(s) "
                "(domains: %s).",
                query,
                len(bm25_results),
                matched_domains,
            )
            return bm25_results

        logger.debug(
            "Domain-specific query %r: local BM25 empty (domains: %s) — "
            "no Indian Kanoon fallback for known domains.",
            query,
            matched_domains,
        )
        return []

    else:
        # ------------------------------------------------------------------
        # Path B: general query — prefer Indian Kanoon, fall back to BM25
        # ------------------------------------------------------------------
        api_results = _search_indiankanoon(query, top_k)
        if api_results is not None:
            return api_results

        return _search_local_bm25(query, top_k)


def format_legal_sources_for_prompt(sources: List[Dict[str, Any]]) -> str:
    """Format retrieved legal provisions as authoritative grounding text for LLM prompts."""
    if not sources:
        return "No specific pre-indexed statute matched directly. Rely strictly on verified general Indian statutes and state when unverified."

    formatted_parts = []
    for s in sources:
        formatted_parts.append(
            f"* Source: [{s['act']} -- {s['section']}]\n"
            f"  Title: {s['title']}\n"
            f"  Official Portal: {s['official_url']}\n"
            f"  Statutory Rule: {s['summary']}\n"
            f"  Prescribed Legal Procedure: {s['procedure']}"
        )
    return "\n\n".join(formatted_parts)
