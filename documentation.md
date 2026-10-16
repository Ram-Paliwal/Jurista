# Jurista — AI Indian Legal Assistant & Legal Document Explainer
## Comprehensive Technical Documentation

---

## 1. Project Overview

### 1.1 What Jurista Is and What It Does
**Jurista** is an open-source, artificial intelligence-powered legal assistant and document analysis platform engineered specifically for the **Indian legal framework**. Navigating India's legal system is fraught with challenges for ordinary citizens due to archaic statutory phrasing, procedural complexity, strict limitation periods, and the intimidating nature of formal legal notices.

Jurista bridges this gap by providing:
1. **Statutory Information & Guidance:** Plain-language, practical answers to common citizen legal problems (cheque dishonour, landlord-tenant disputes, consumer grievances, FIR registration refusals, cyber fraud, delayed builder possession, domestic violence, and free legal aid).
2. **Document Explainer (PDF Ingestion):** Automated parsing and structured explanation of uploaded legal notices, contracts, court summons, and police complaints using PyMuPDF. It identifies parties, dates, claimed financial amounts, explicit allegations, and statutory procedural roadmaps.
3. **Allegation vs. Fact Ethical Boundary:** Enforces a strict legal-ethical rule treating all assertions in user-uploaded documents and opposing notices as unilateral *allegations*, preventing unwarranted panic and maintaining objective neutrality.
4. **Interactive Community Experiences & Dispute Mapping:** A privacy-preserving crowd-sourced incident mapping module powered by Leaflet.js and OpenStreetMap (OSM) that allows citizens to view and report real-world consumer and legal disputes (e.g., e-commerce refund failures, illegal security deposit deductions, police station FIR refusals).
5. **Private Evidence Vault:** A strictly isolated, session-scoped digital repository where users can safely record private document notes, receipt references, and incident details without ever publishing them to the public map or feed.

### 1.2 Target Users
- **Everyday Citizens & Consumers:** Individuals confronting e-commerce disputes, unfair bank deductions, or deficient utility/travel services.
- **Tenants & Property Buyers:** Tenants facing wrongful eviction or deposit withholding, and homebuyers dealing with delayed possession under RERA.
- **Recipients of Legal Notices:** Individuals who receive intimidating demand notices (e.g., Section 138 Negotiable Instruments Act cheque dishonour notices) needing immediate clarity on statutory deadlines (e.g., the 15-day cure window).
- **Litigants & Complainants:** People seeking to understand police complaint procedures (Zero FIR, Section 173 BNSS / 154 CrPC) or how to check real-time court case statuses via eCourts CNR tracking.
- **Marginalized Litigants:** Individuals seeking free legal aid through the National Legal Services Authority (NALSA) and District Legal Services Authorities (DLSA) under Section 12 of the Legal Services Authorities Act, 1987.

### 1.3 Key Features List
- **Statutory Grounding:** Every legal claim is tied directly to verified statutes from official repositories (India Code, eCourts, NALSA).
- **Claim Confidence Label System:** Enforces categorization of assertions into `[STATUTE]`, `[AGREEMENT]`, `[PRINCIPLE]`, `[JURISDICTION-DEPENDENT]`, or `[UNVERIFIED]`.
- **Zero-Cost Heuristic Pre-Filter:** Sub-millisecond regex and keyword pre-screening that catches and politely rejects out-of-scope queries (coding, cooking, math, entertainment) with zero LLM API invocation and zero token cost.
- **Two-Path Domain-Aware Legal Retrieval:** Blends high-precision curated local BM25 statutory retrieval (Path A) with live Indian Kanoon API search (Path B).
- **In-Memory PDF Parsing & Scanned Detection:** High-speed PyMuPDF text extraction with automatic heuristic detection of image-only or scanned documents.
- **Multilingual Context Retention:** Full multi-turn conversation and document analysis across **English**, **Hindi (हिंदी)**, and **Marathi (मराठी)** with dynamic mid-conversation switching without loss of context.
- **Voice Accessibility:** Client-side speech-to-text recognition and text-to-speech audio synthesis powered by the browser Web Speech API across all three supported languages.
- **Privacy-Preserving Locality Picker:** Approximate locality geocoding via OpenStreetMap Nominatim with coordinate truncation (~11-meter precision) and zero GPS tracking requirements.
- **Session-Isolated Architecture:** Thread-safe SQLite persistence (`jurista_sessions.db`) maintaining client data privacy across multi-turn chats, document chunks, and private evidence vaults.

### 1.4 Tech Stack Summary
- **Backend Framework:** FastAPI (Python 3.10+) with Uvicorn ASGI server.
- **AI / LLM Orchestration:** LangGraph (`StateGraph`) state machine workflow; Google GenAI SDK (`google-genai`).
- **Primary AI Models:** Google Gemini 2.5 Flash / Gemini 3.5 Flash, with automated fallback to `gemini-3.5-flash-lite`, `gemini-3.6-flash`, and `gemma-4-31b-it`.
- **Legal Research API:** Indian Kanoon Search API (`api.indiankanoon.org`) as live primary source for general legal queries.
- **PDF Extraction Engine:** PyMuPDF (`fitz` / `pymupdf`).
- **Search & Retrieval:** Custom lexical BM25 engine with Unicode Devanagari and alphanumeric tokenization.
- **Database / State Persistence:** Embedded thread-safe SQLite3 database (`jurista_sessions.db`).
- **Frontend Layer:** Vanilla HTML5, modern CSS3 (Glassmorphism, custom design system, Outfit and Plus Jakarta Sans typography), and Vanilla JavaScript (ES6+).
- **Mapping & Geospatial:** Leaflet.js (v1.9.4), OpenStreetMap tile server, and Leaflet.markercluster (v1.5.3).
- **Audio & Accessibility:** Web Speech API (`SpeechRecognition` / `SpeechSynthesis`).

---

## 2. Architecture Overview

### 2.1 How All the Pieces Connect
The Jurista architecture separates presentation, API routing, orchestration, statutory retrieval, and language generation into distinct, decoupled layers:

1. **Client Interface:** Modern browser client serving HTML5, CSS3, and Vanilla JavaScript (`app.js`). Manages client session UUIDs in `localStorage`, drives the chat stream, handles drag-and-drop PDF uploads, manages voice capture, renders Leaflet maps, and interfaces with the REST API.
2. **REST API Gateway (`main.py`):** FastAPI endpoints handling CORS, Pydantic request/response validation, file streaming for PDF uploads, and dispatching queries to the session store and LangGraph workflow.
3. **Session & Persistence Layer (`session_store.py` & `community_store.py`):** Thread-safe SQLite database (`jurista_sessions.db`) holding `sessions`, `messages`, `community_reports`, and `evidence_vault` tables.
4. **Document Ingestion Layer (`pdf_parser.py` & `rag_engine.py`):** Validates raw PDF bytes, checks size/page limits, runs PyMuPDF text extraction, detects image-only scans, splits text into overlapping character chunks tagged with page numbers, and stores structured representations in SQLite.
5. **Orchestration Layer (`graph.py`):** A compiled LangGraph `StateGraph` that passes a shared `JuristaState` dictionary through sequential and conditional nodes: intent classification, statutory/document retrieval, prompt building, and LLM generation.
6. **Statutory Intelligence & RAG (`legal_db.py` & `rag_engine.py`):** Classifies queries into 8 distinct legal domains, computes BM25 relevance scores over 13 curated Indian statutes, queries the Indian Kanoon API for general live queries, and retrieves top document excerpts.
7. **Prompt Engine (`prompts.py`):** Injects master system instructions, citation formats, mandatory claim confidence labels, allegation guardrails, and language instructions into specialized prompt templates.
8. **LLM Client Wrapper (`gemini_client.py`):** Manages the Google GenAI SDK connection, enforces zero-cost out-of-scope regex filtering, configures low temperature (0.2) for legal precision, and manages automated fallback across model candidates.

### 2.2 Request Flow from Browser to Gemini and Back

#### Flow A: Legal Query / Chat Request (`POST /api/chat`)
1. User types or speaks a message in `index.html`.
2. `app.js` issues a `POST /api/chat` request with `session_id`, `message`, and `language`.
3. `main.py` creates or fetches the session from `SessionStore`, reads prior conversation turns (up to 4 turns), loads active document chunks (if any), and records the user's message.
4. `process_jurista_turn()` invokes the compiled LangGraph pipeline:
   - **Node 1 (`route_intent`):** Checks `GeminiClient.is_obviously_out_of_scope()`. If out-of-scope, immediately sets intent to `OUT_OF_SCOPE` and returns pre-translated rejection text without calling the LLM. Otherwise, checks for document explain, document follow-up, or vague prompts needing clarification.
   - **Conditional Edge (`should_route_out_of_scope`):** Diverts `OUT_OF_SCOPE` directly to the end; routes legal intents to `retrieve_sources`.
   - **Node 2 (`retrieve_sources`):** Runs `retrieve_document_chunks()` over uploaded PDF chunks (top 3) and `search_legal_sources()` over Indian statutes (top 1).
   - **Node 3 (`generate_answer`):** Selects template (`LEGAL_QUERY_PROMPT`, `DOCUMENT_FOLLOWUP_PROMPT`, etc.), injects language instruction, retrieved sources, and context via `build_prompt()`, and calls `GeminiClient.generate_content()`.
   - `GeminiClient` sends prompt with `SYSTEM_PROMPT` to Google Gemini (temperature 0.2). If primary model returns 503/404, it cycles through fallback models.
5. `main.py` normalizes retrieved sources to guarantee valid string fields, saves the assistant response in SQLite `messages`, and returns JSON to the browser.
6. `app.js` renders Markdown into HTML, displays verified authority citation chips, and updates conversation history.

#### Flow B: PDF Upload Request (`POST /api/upload-pdf`)
1. User drops a PDF into the dropzone.
2. `app.js` posts multipart form-data to `/api/upload-pdf`.
3. `main.py` validates file extension and reads binary bytes.
4. `extract_text_from_pdf()` checks magic `%PDF-` header, size (<15MB), page count (<50), extracts page-by-page text, and checks if total characters < 50 (`is_scanned: true`).
5. `chunk_document_text()` segments extracted text into 750-character chunks with 120-character overlap, preserving page boundaries.
6. If scanned, an OCR recommendation notice is generated. If digital, the LangGraph pipeline is invoked with intent `DOCUMENT_EXPLAIN` to generate a structured situation analysis.
7. Document metadata and chunks are saved to `jurista_sessions.db` under the active session.
8. The browser UI renders the active document badge, stats, and displays the structured breakdown in the chat window.

### 2.3 ASCII Pipeline Diagram

```
+──────────────────────────────────────────────────────────────────────────────+
|                                BROWSER CLIENT                                |
|  [Chat UI]   [PyMuPDF Dropzone]   [Leaflet Map & Feed]   [Evidence Vault]   |
+───────┬──────────────┬─────────────────────┬─────────────────────┬───────────+
        │ POST /chat   │ POST /upload-pdf    │ GET/POST /community │ /vault
        ▼              ▼                     ▼                     ▼
+──────────────────────────────────────────────────────────────────────────────+
|                           FASTAPI SERVER (main.py)                           |
+───────┬──────────────┬─────────────────────┬─────────────────────┬───────────+
        │              │                     │                     │
        │              ▼                     │                     │
        │      +───────────────────+         │                     │
        │      |   pdf_parser.py   |         │                     │
        │      | PyMuPDF / Scanned |         │                     │
        │      +─────────┬─────────+         │                     │
        │                ▼                   ▼                     ▼
        │      +───────────────────+  +────────────────────────────────────────+
        │      |   rag_engine.py   |  |   jurista_sessions.db (SQLite3)        |
        │      | Document Chunks   |  |  - sessions       - community_reports  |
        │      +─────────┬─────────+  |  - messages       - evidence_vault     |
        │                │            +────────────────────────────────────────+
        ▼                ▼                               ▲
+─────────────────────────────────────────────+          │
|          LANGGRAPH PIPELINE (graph.py)      |          │
|                                             |          │
|  +---------------------------------------+  |          │
|  | Node 1: route_intent                  |  |          │
|  | - Regex Out-of-Scope Pre-check        |  |          │
|  | - Document presence check             |  |          │
|  | - Vague message clarification check   |  |          │
|  +───────────────────┬───────────────────+  |          │
|                      │                      |          │
|         [Is Out Of Scope?]                  |          │
|         /               \                   |          │
|       YES                NO                 |          │
|       /                   \                 |          │
|      ▼                     ▼                |          │
| +──────────────+   +──────────────────────+ |          │
| | out_of_scope |   | retrieve_sources     | |          │
| | Zero-cost    |   | - Top 3 Doc Chunks   | |          │
| | rejection    |   | - Top 1 Legal Statute| |          │
| +──────┬───────+   +──────────┬───────────+ |          │
|        │                      ▼             |          │
|        │           +──────────────────────+ |          │
|        │           | generate_answer      | |          │
|        │           | - build_prompt()     | |          │
|        │           | - SYSTEM_PROMPT      | |          │
|        │           +──────────┬───────────+ |          │
|        │                      │             |          │
|        ▼                      ▼             |          │
|      [END]                  [END]           |          │
+───────────────────────────────┬─────────────+          │
                                │                        │
                                ▼                        │
                 +─────────────────────────────+         │
                 |   gemini_client.py          |         │
                 |   Google GenAI SDK          |         │
                 |   Primary: gemini-2.5/3.5   |         │
                 |   Fallback: lite/3.6/gemma  |         │
                 +──────────────┬──────────────+         │
                                │                        │
                                ▼                        │
                 +─────────────────────────────+         │
                 |   Google Gemini Flash API   |         │
                 +─────────────────────────────+         │
                                │                        │
                                +────────────────────────+
                                Store message & sources
```

---

## 3. Folder Structure

Every file in the Jurista repository and its one-line explanation:

```
Jurista/
├── .env                     # Local environment file storing Gemini API key, Indian Kanoon key, and server host/port
├── .env.example             # Template file documenting all configurable environment variables
├── .gitignore               # Git ignore file excluding virtual environments, databases, cache, and secrets
├── LICENSE                  # MIT Open Source License agreement
├── README.md                # Project README with overview, badges, quickstart, statutory coverage, and architecture
├── documentation.md         # Exhaustive, complete technical documentation of the entire Jurista system
├── requirements.txt         # Pinned Python package dependencies (FastAPI, PyMuPDF, google-genai, etc.)
├── run.bat                  # Windows one-click batch launcher to verify environment and launch Jurista in default browser
├── jurista_sessions.db      # Embedded SQLite database holding sessions, messages, community reports, and evidence vault
│
├── main.py                  # FastAPI REST server defining all endpoints, middleware, request schemas, and static mounts
├── graph.py                 # LangGraph orchestration state machine, defining nodes, intent routing, and turn execution
├── legal_db.py              # Curated 13-statute Indian legal database, domain classification, BM25 scorer, and Indian Kanoon API
├── rag_engine.py            # Local lexical RAG engine for chunking documents, BM25 retrieval, and prompt excerpt formatting
├── prompts.py               # Master prompt library with system instruction, confidence labels, allegations rule, and templates
├── gemini_client.py         # Google GenAI client wrapper with zero-cost heuristic regex pre-filter and multi-model failover
├── session_store.py         # Thread-safe SQLite controller for multi-turn sessions, chat history, and document payload caching
├── pdf_parser.py            # PyMuPDF PDF parser handling page extraction, size limits, and scanned/image-only document detection
├── community_store.py       # Thread-safe SQLite controller for public community incident reports and private session evidence vaults
│
├── static/
│   ├── index.html           # Accessible semantic HTML5 interface with tabs for Legal Assistant, Community Map, and Evidence Vault
│   ├── style.css            # Custom CSS3 stylesheet featuring dark-slate glassmorphism, responsive grids, and design tokens
│   └── app.js               # Frontend controller managing state, chat messaging, PDF uploads, Leaflet mapping, and voice APIs
│
└── tests/ (Automated Verification Scripts)
    ├── test_system.py       # 8-stage end-to-end automated test suite verifying health, filtering, Q&A, PDF, and language switching
    ├── test_community.py    # Verification test suite for community reports, Leaflet data contracts, and Evidence Vault isolation
    └── test_indiankanoon.py # Diagnostic script checking Indian Kanoon API keys, live endpoint latency, and fallback behavior
```

---

## 4. Each File in Detail

### 4.1 `main.py`
- **Purpose and Why It Exists:** Serves as the primary entrypoint and API gateway for the Jurista backend. Exposes REST endpoints to the frontend, coordinates database operations, runs document ingestion, and triggers the LangGraph turn execution.
- **How It Works:** Initializes the FastAPI application, mounts CORS middleware, mounts `/static` for static assets, and defines structured Pydantic models for request validation. Implements API endpoints for health status, session management, language switching, chat queries, PDF uploads, community report publishing, and private evidence vault operations.
- **Functions & Classes:**
  - `class ChatRequest(BaseModel)`: Validates chat payloads (`session_id`: Optional[str], `message`: str min length 1, `language`: Optional[str]).
  - `class LanguageSwitchRequest(BaseModel)`: Validates language changes (`session_id`: str, `language`: str).
  - `class ClearSessionRequest(BaseModel)`: Validates session clearing (`session_id`: str).
  - `class CommunityReportCreate(BaseModel)`: Validates public report submissions (`title`, `topic`, `description`, `approx_location_name`, `latitude`, `longitude`, `incident_date`, `is_public`, `session_id`). Includes `@field_validator` for latitude (-90 to 90) and longitude (-180 to 180), and `@model_validator(mode="after")` ensuring latitude and longitude are supplied as a pair.
  - `class VaultItemCreate(BaseModel)`: Validates private evidence vault items (`session_id`, `title`, `item_type`, `description`, `approx_location`).
  - `health_check() -> Dict[str, Any]`: Returns system health, service name, Gemini configuration status, and active model.
  - `get_session_details(session_id: str) -> Dict[str, Any]`: Fetches language, active document summary (page count, characters, scanned flag, chunks), and full message history.
  - `update_language(req: LanguageSwitchRequest) -> Dict[str, Any]`: Validates language against `prompts.SUPPORTED_LANGUAGES` and updates SQLite session state.
  - `clear_session(req: ClearSessionRequest) -> Dict[str, Any]`: Clears messages and active document for the session.
  - `chat_endpoint(req: ChatRequest) -> Dict[str, Any]`: Core chat handler. Pulls session history, fetches document context, records the user message, invokes `process_jurista_turn()`, normalizes returned sources (guaranteeing non-null string fields), logs assistant response, and returns the answer.
  - `upload_pdf(file: UploadFile, session_id: Optional[str], language: Optional[str]) -> Dict[str, Any]`: Handles multipart PDF upload. Validates `.pdf` extension, calls `extract_text_from_pdf()`, chunks text via `chunk_document_text()`, creates situation summary via `process_jurista_turn()`, and persists document payload in `SessionStore`.
  - `get_community_reports(...) -> Dict[str, Any]`: Queries published community reports with filtering by topic, search term, date range, and location toggle. Enforces server-side safety disclaimer.
  - `get_single_community_report(report_id: str, session_id: Optional[str]) -> Dict[str, Any]`: Fetches a single public report or private draft if owned by `session_id`.
  - `create_community_report(req: CommunityReportCreate) -> Dict[str, Any]`: Saves a new community experience report with rounded approximate coordinates.
  - `get_vault_items(session_id: str) -> Dict[str, Any]`: Retrieves private evidence records strictly filtered by caller `session_id`.
  - `add_vault_item(req: VaultItemCreate) -> Dict[str, Any]`: Creates a private vault item for the caller's session.
  - `delete_vault_item(item_id: str, session_id: str) -> Dict[str, Any]`: Deletes an evidence item if owned by `session_id`.
  - `serve_index() -> FileResponse`: Returns `static/index.html`.
- **Dependencies Imported:** `fastapi` (`FastAPI`, `UploadFile`, `File`, `Form`, `HTTPException`, `CORSMiddleware`, `StaticFiles`, `FileResponse`, `JSONResponse`), `pydantic` (`BaseModel`, `Field`, `field_validator`, `model_validator`), `dotenv` (`load_dotenv`), `session_store`, `pdf_parser`, `rag_engine`, `graph`, `legal_db`, `community_store`, `prompts`.
- **Important Constants:** `BASE_DIR = Path(__file__).resolve().parent`, `STATIC_DIR = BASE_DIR / "static"`.
- **Edge Cases & Behaviors:**
  - If `session_id` is omitted in `/api/chat`, a new UUID4 is minted automatically.
  - Normalizes every retrieved source dictionary so that optional fields default to empty strings, preventing frontend JavaScript `undefined` errors.
  - Coordinates in community reports are strictly validated: if either latitude or longitude is provided without the other, a 422 validation error is raised.

### 4.2 `graph.py`
- **Purpose and Why It Exists:** Coordinates the AI orchestration pipeline using LangGraph. Provides a deterministic, auditable state machine separating routing, retrieval, generation, and scope enforcement.
- **How It Works:** Defines `JuristaState` (a `TypedDict`), creates four nodes (`route_intent`, `retrieve_sources`, `generate_answer`, `out_of_scope`), and configures conditional routing using `should_route_out_of_scope`.
- **Functions & Classes:**
  - `class JuristaState(TypedDict)`: State container holding `session_id`, `language`, `user_message`, `intent`, `is_out_of_scope`, `document_text`, `document_chunks`, `retrieved_doc_chunks`, `retrieved_legal_sources`, `conversation_context`, and `response_text`.
  - `check_needs_clarification(message: str) -> bool`: Returns `True` if the user prompt is extremely brief (<= 3 words) and contains vague legal triggers (`notice`, `fir`, `arrest`, `fraud`, `scam`, `eviction`, `cheque`, `case`, `divorce`, `bail`, `help me`, `police problem`, `court`, `complaint`).
  - `route_intent_node(state: JuristaState) -> Dict[str, Any]`: First checks `GeminiClient.is_obviously_out_of_scope()`. If out-of-scope, immediately returns `OUT_OF_SCOPE` with pre-translated refusal. If document exists and message matches explain keywords, returns `DOCUMENT_EXPLAIN`. If document exists with active conversation, returns `DOCUMENT_FOLLOWUP`. If vague, returns `NEEDS_CLARIFICATION`. Defaults to `LEGAL_QUERY`.
  - `retrieve_sources_node(state: JuristaState) -> Dict[str, Any]`: Calls `retrieve_document_chunks(user_msg, doc_chunks, top_k=3)` if document chunks exist; calls `search_legal_sources(user_msg, top_k=1)` to retrieve the single most relevant statutory reference.
  - `generate_answer_node(state: JuristaState) -> Dict[str, Any]`: Selects appropriate prompt from `prompts.py`, bounds document text to 8,000 characters for prompt safety, formats sources, calls `GeminiClient.generate_content()`, and sets `response_text`.
  - `out_of_scope_node(state: JuristaState) -> Dict[str, Any]`: Formats and returns static polite refusal text in the active language without calling the LLM.
  - `should_route_out_of_scope(state: JuristaState) -> str`: Conditional edge returning `"out_of_scope"` or `"retrieve"`.
  - `process_jurista_turn(...) -> Dict[str, Any]`: Public execution function that initializes `JuristaState`, invokes the compiled graph (`jurista_app.invoke()`), and unpacks the final state into a response dictionary.
- **Dependencies Imported:** `langgraph.graph` (`StateGraph`, `START`, `END`), `prompts`, `legal_db`, `rag_engine`, `gemini_client`.
- **Important Constants:** Graph structure with compiled runner `jurista_app`.
- **Edge Cases & Behaviors:**
  - When a query is out-of-scope, the execution flow short-circuits completely past retrieval and LLM generation directly to `END`, resulting in zero API latency and zero cost.
  - Restricts legal statute retrieval to `top_k=1` to prevent prompt dilution and citation conflicts.

### 4.3 `legal_db.py`
- **Purpose and Why It Exists:** Serves as the authoritative knowledge base of verified Indian statutory provisions and provides a hybrid, domain-aware retrieval mechanism integrating local BM25 and the Indian Kanoon API.
- **How It Works:** Maintains a curated database of 13 major Indian statutes with official India Code URLs, section numbers, titles, keywords, summaries, procedures, and domain tags. Implements domain classification via `classify_query_domain()`, a weighted lexical BM25 scorer (`_search_local_bm25()`), and an Indian Kanoon live API search (`_search_indiankanoon()`).
- **Functions & Classes:**
  - `_normalise_indiankanoon_doc(doc: Dict[str, Any]) -> Dict[str, Any]`: Maps raw Indian Kanoon search results (`tid`, `title`, `headline`, `doctype`, `court`, `publishdate`) to the standard `LEGAL_STATUTES` schema (`id`, `act`, `section`, `title`, `official_url`, `summary`, `procedure`, `domain`).
  - `_search_indiankanoon(query: str, top_k: int) -> Optional[List[Dict[str, Any]]]`: Queries `https://api.indiankanoon.org/search/` via HTTP POST with `formInput` and bearer token. Returns normalized documents or `None` on timeout, error, or missing key.
  - `classify_query_domain(query: str) -> List[str]`: Matches query substrings against `_DOMAIN_KEYWORDS` across 8 legal domains. Returns a list of matched domains, or `["general"]` if none match.
  - `_search_local_bm25(query: str, top_k: int, min_score: int = MINIMUM_RELEVANCE_SCORE) -> List[Dict[str, Any]]`: Scores each statute based on keyword overlap (weight 3), exact keyword substring match (+8), act token overlap (*2), section token overlap (*4), and summary token overlap (*1). Filters out results below `MINIMUM_RELEVANCE_SCORE` (8). If query is domain-specific, keeps items whose domain matches or whose score exceeds `_DOMAIN_OVERRIDE_SCORE` (16).
  - `search_legal_sources(query: str, top_k: int = 3) -> List[Dict[str, Any]]`: Public retrieval function implementing the Two-Path strategy. Path A (known domain): local BM25 only (no Indian Kanoon fallback). Path B (general query): Indian Kanoon API first, falling back to local BM25.
  - `format_legal_sources_for_prompt(sources: List[Dict[str, Any]]) -> str`: Formats retrieved provisions into bulleted markdown text containing Act name, Section, Title, Official Portal URL, Statutory Rule, and Prescribed Legal Procedure.
- **Dependencies Imported:** `requests`, `dotenv`, `logging`, `re`, `os`.
- **Important Constants:**
  - `_INDIANKANOON_API_KEY`: Read from `INDIANKANOON_API_KEY` environment variable.
  - `_INDIANKANOON_SEARCH_URL = "https://api.indiankanoon.org/search/"`
  - `_API_TIMEOUT_SECONDS = 6`
  - `MINIMUM_RELEVANCE_SCORE = 8`: Relevance floor for BM25 results.
  - `_DOMAIN_OVERRIDE_SCORE = 16`: Score threshold allowing exceptionally high BM25 matches to bypass domain gating.
  - `LEGAL_STATUTES`: List of 13 curated Indian statute definitions.
  - `_DOMAIN_KEYWORDS`: Dictionary mapping 8 domains (`tenancy`, `criminal`, `consumer`, `cyber`, `property`, `family`, `procedure`, `legal_aid`) to representative keywords.
- **Edge Cases & Behaviors:**
  - Returns `[]` immediately for blank or whitespace-only queries.
  - In Path A (known domain), if BM25 produces no match, it returns an empty list rather than falling back to Indian Kanoon, because Indian Kanoon lacks domain metadata and would surface irrelevant results.

### 4.4 `rag_engine.py`
- **Purpose and Why It Exists:** Provides local document chunking and BM25 retrieval for user-uploaded legal PDFs, maintaining strict separation between private document text and statutory legal databases.
- **How It Works:** Tokenizes text with support for Devanagari Unicode characters, segments documents into overlapping chunks while preserving page numbers and paragraph boundaries, and computes BM25 relevance scores for user queries against document chunks.
- **Functions & Classes:**
  - `clean_text_for_tokens(text: str) -> List[str]`: Uses regex `\b[a-zA-Z0-9_\u0900-\u097F]{2,}\b` to extract tokens of length 2 or greater, supporting Hindi and Marathi Devanagari text.
  - `chunk_document_text(full_text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP, source_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`: Parses page boundary markers (`--- [Page X] ---`), splits text into natural paragraphs (`\n\n`), and packs paragraphs into chunks up to `chunk_size` (750 chars). If a paragraph exceeds `chunk_size`, it slices by sentence boundaries (`(?<=[.!?।])\s+`, including the Devanagari danda `।`). Appends overlapping tail text (120 chars) to consecutive chunks.
  - `retrieve_document_chunks(query: str, chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]`: Implements classic BM25 scoring with parameters $k_1 = 1.5$ and $b = 0.75$. Calculates document frequencies across chunks, computes IDF and TF scores, and applies a $+5.0$ score boost if the query string appears as an exact substring. If no chunks match, returns the first `top_k` chunks as general overview context.
  - `format_document_chunks(chunks: List[Dict[str, Any]]) -> str`: Formats retrieved document chunks into tagged prompt excerpts with page number, chunk ID, optional statutory metadata, and quoted excerpt text.
- **Dependencies Imported:** `math`, `re`, `typing`.
- **Important Constants:** `DEFAULT_CHUNK_SIZE = 750`, `DEFAULT_CHUNK_OVERLAP = 120`.
- **Edge Cases & Behaviors:**
  - Preserves source metadata (`act`, `section`, `official_url`) inside chunks when provided, allowing vector or lexical retrievers to maintain citation provenance.
  - Gracefully falls back to the leading chunks if a query contains no overlapping tokens, ensuring the LLM always receives document context during Q&A.

### 4.5 `prompts.py`
- **Purpose and Why It Exists:** Serves as the centralized prompt engineering library for Jurista. Encapsulates legal ethical guardrails, Indian legal citation standards, mandatory claim confidence labeling, allegation protection rules, and multilingual formatting.
- **How It Works:** Defines prompt templates with interpolation variables and provides `build_prompt()` which dynamically injects language directives and normalizes argument aliases.
- **Functions & Classes:**
  - `get_language_instruction(lang: str = "English", language: str | None = None) -> str`: Generates strict language directives instructing Gemini to respond exclusively in English, Hindi, or Marathi, while preserving statutory section numbers and legal citations accurately.
  - `build_prompt(prompt_type: str, lang: str = "English", language: str | None = None, **kwargs: Any) -> str`: Assembles prompt templates using `string.Formatter`, injects language instructions, normalizes query aliases (`user_query`, `user_question`, `user_message`), and safely defaults missing interpolation fields to empty strings to avoid `KeyError` exceptions.
- **Constants & Templates:**
  - `SUPPORTED_LANGUAGES = ("English", "Hindi", "Marathi")`
  - `SYSTEM_PROMPT`: Injected into every Gemini API call. Enforces strict scope (Indian law only), authoritative grounding (India Code, Indian Kanoon, NALSA, eCourts), mandatory claim confidence labels (`[STATUTE]`, `[AGREEMENT]`, `[PRINCIPLE]`, `[JURISDICTION-DEPENDENT]`, `[UNVERIFIED]`), jurisdiction gap warnings, the Allegations Rule for documents, and citizen legal aid information (NALSA 15100).
  - `LEGAL_QUERY_PROMPT`: Directs Gemini to write natural, flowing sentences with inline statutory citations, plain-English state variation notices, and a strict 5-part structure: `## Situation`, `## Your Legal Position`, `## What You Should Do` (`**Right Away:**`, `**This Week:**`, `**If the Problem Is Not Resolved:**`), `## What to Keep as Evidence`, and `## Important Limitations`.
  - `DOCUMENT_EXPLAIN_PROMPT`: Specialized for legal notice and document analysis. Enforces a 7-section structure: `What This Document Is`, `Claims & Allegations`, `Dates, Amounts & Stated Deadlines`, `Relevant Legal Provisions`, `Red Flags & Potential Irregularities`, `Practical Next Steps`, and `Legal Representation & Free Aid`.
  - `DOCUMENT_FOLLOWUP_PROMPT`: Handles iterative multi-turn Q&A on previously analyzed documents.
  - `NEEDS_CLARIFICATION_PROMPT`: Formulates at most 3 concise questions when crucial facts (dates, document type, jurisdiction) are missing.
  - `OUT_OF_SCOPE_RESPONSE`: Dictionary providing immediate polite rejection messages pre-translated into English, Hindi, and Marathi.
  - `UNCERTAINTY_ADDENDUM`: Standard addendum stating when specific provisions could not be verified from official records.
  - `PROMPT_MAP`: Dictionary mapping intent keys to prompt templates.
- **Edge Cases & Behaviors:**
  - `build_prompt("OUT_OF_SCOPE", language=...)` bypasses template formatting and returns the static localized rejection string directly.

### 4.6 `gemini_client.py`
- **Purpose and Why It Exists:** Wraps the official Google GenAI SDK (`google-genai`). Implements instant heuristic regex filtering to reject non-legal queries with zero latency, configures low-temperature generation, and provides automated multi-model failover.
- **How It Works:** Loads API keys from `.env`, initializes `genai.Client`, runs regex pre-checks against `OUT_OF_SCOPE_PATTERNS`, and cycles through candidate models if transient HTTP 503 or 404 errors occur.
- **Functions & Classes:**
  - `class GeminiClient`:
    - `__init__(api_key: Optional[str] = None)`: Initializes client instance; reads `GEMINI_API_KEY` from environment.
    - `is_configured() -> bool`: Returns `True` if `GEMINI_API_KEY` is set, non-empty, and does not start with `"your_"`.
    - `is_obviously_out_of_scope(text: str) -> bool`: Static pre-check. First checks a comprehensive whitelist of legal terms (in English, Hindi, and Marathi, e.g., `law`, `court`, `act`, `fir`, `bail`, `कायदा`, `अदालत`, `तक्रार`). If whitelisted, returns `False`. Next tests against `OUT_OF_SCOPE_PATTERNS` (code generation, recipes, sports scores, pure arithmetic, jokes, weather). Returns `True` if any pattern matches.
    - `generate_content(prompt: str, system_instruction: Optional[str] = None, model: Optional[str] = None) -> str`: Calls Gemini with `temperature=0.2`. Sequentially attempts models from `FALLBACK_MODELS`. If a candidate throws an exception, logs the error and tries the next candidate. Returns clean generated text or actionable error messages.
- **Dependencies Imported:** `google.genai` (`Client`, `types`), `dotenv` (`load_dotenv`), `re`, `os`.
- **Important Constants:**
  - `OUT_OF_SCOPE_PATTERNS`: Regex patterns for coding, recipes, sports, arithmetic, jokes, and weather.
  - `DEFAULT_FLASH_MODEL`: Defaults to `os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")`.
  - `FALLBACK_MODELS = [DEFAULT_FLASH_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemma-4-31b-it"]`.
- **Edge Cases & Behaviors:**
  - If no API key is configured, returns a clear markdown message explaining how to add `GEMINI_API_KEY` to `.env`, while document parsing and statutory retrieval remain functional.
  - Catches `RESOURCE_EXHAUSTED` (HTTP 429) and returns a user-friendly rate-limit warning.

### 4.7 `session_store.py`
- **Purpose and Why It Exists:** Provides thread-safe, persistent storage for multi-turn conversations, active document attachments, and session settings using an embedded SQLite database.
- **How It Works:** Connects to `jurista_sessions.db` using context managers, creates tables on import, and performs CRUD operations for sessions and messages.
- **Functions & Classes:**
  - `init_db()`: Creates `sessions` and `messages` tables and builds index `idx_messages_session(session_id, timestamp)`.
  - `class SessionStore`:
    - `create_or_get_session(session_id: Optional[str] = None, default_lang: str = "English") -> Dict[str, Any]`: Retrieves existing session or inserts a new one with a UUID4.
    - `set_language(session_id: str, language: str) -> bool`: Updates session language in place without touching messages or documents.
    - `get_language(session_id: str) -> str`: Fetches active session language.
    - `save_document(session_id: str, document_data: Dict[str, Any]) -> None`: Serializes document metadata, text, and chunks into JSON and updates `document_json` column.
    - `get_document(session_id: str) -> Optional[Dict[str, Any]]`: Deserializes and returns active document JSON.
    - `clear_document(session_id: str) -> None`: Sets `document_json = NULL`.
    - `add_message(session_id: str, role: str, content: str, route: Optional[str] = None, sources: Optional[List[Any]] = None) -> Dict[str, Any]`: Inserts message record with UUID, role, content, route, sources JSON, and timestamp.
    - `get_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]`: Returns chronologically ordered message history.
    - `clear_messages(session_id: str) -> None`: Deletes all messages for a session.
    - `get_conversation_context(session_id: str, max_turns: int = 4) -> str`: Formats up to `max_turns * 2` recent messages as `"User: ...\nJurista: ..."` for prompt injection.
- **Dependencies Imported:** `sqlite3`, `json`, `time`, `uuid`, `pathlib`.
- **Important Constants:** `DB_PATH = Path(__file__).parent / "jurista_sessions.db"`.
- **Edge Cases & Behaviors:**
  - Enforces `FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE`.
  - Language switching preserves message history and document chunks completely, enabling seamless multilingual follow-ups.

### 4.8 `pdf_parser.py`
- **Purpose and Why It Exists:** Extracts digital text and page-by-page structure from PDF legal documents using PyMuPDF. Detects scanned, image-only, oversized, and corrupted files.
- **How It Works:** Inspects byte streams, validates the `%PDF-` header, opens the document in memory via `pymupdf.open()`, iterates over pages up to `MAX_PAGE_LIMIT`, strips null bytes, inserts page delimiters, and evaluates whether the character count falls below `MIN_TEXT_CHARS_FOR_DIGITAL`.
- **Functions & Classes:**
  - `class PDFParseException(Exception)`: Custom exception for parsing errors.
  - `extract_text_from_pdf(file_bytes: bytes, filename: str = "document.pdf", max_pages: int = MAX_PAGE_LIMIT) -> Dict[str, Any]`: Core parser. Returns dictionary containing `success`, `filename`, `page_count`, `pages_processed`, `total_characters`, `full_text`, `pages` list, `is_scanned`, `message`, and `error`.
- **Dependencies Imported:** `pymupdf`, `io`, `typing`.
- **Important Constants:**
  - `MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024` (15 MB limit)
  - `MAX_PAGE_LIMIT = 50` (50 pages limit)
  - `MIN_TEXT_CHARS_FOR_DIGITAL = 50` (scanned document character threshold)
- **Edge Cases & Behaviors:**
  - Rejects empty byte arrays (`EMPTY_FILE`), files > 15MB (`FILE_TOO_LARGE`), and non-PDF headers (`INVALID_PDF_FORMAT`).
  - If extracted characters across all pages < 50, flags `is_scanned = True` and returns a helpful notice recommending OCR scanning rather than failing silently.

### 4.9 `community_store.py`
- **Purpose and Why It Exists:** Manages public community experience reports and private session evidence vaults in SQLite, strictly separating public citizen allegations from confidential user evidence records.
- **How It Works:** Connects to `jurista_sessions.db`, creates `community_reports` and `evidence_vault` tables, seeds initial realistic public reports on first run, rounds geographical coordinates to 4 decimal places for privacy, and provides filtering and CRUD methods.
- **Functions & Classes:**
  - `init_community_db()`: Initializes tables and indexes; seeds initial reports if empty.
  - `seed_initial_community_reports(conn: sqlite3.Connection)`: Seeds 7 realistic dispute records across major Indian cities (Pune, Bengaluru, Delhi, Mumbai, Hyderabad, unmapped, and draft).
  - `class CommunityStore`:
    - `create_report(...) -> Dict[str, Any]`: Creates a public or draft report. Rounds latitude and longitude to 4 decimal places (~11 meters).
    - `get_public_reports(...) -> List[Dict[str, Any]]`: Queries published reports (`is_public = 1` and `status = 'published'`). Filters by topic, search substring, date range, and mapped-only flag. Strictly excludes private evidence vault items.
    - `get_report_by_id(report_id: str, requester_session_id: Optional[str] = None) -> Optional[Dict[str, Any]]`: Returns report details if published or if requester matches `author_session_id`.
  - `class EvidenceVaultStore`:
    - `create_vault_item(...) -> Dict[str, Any]`: Saves private evidence item (`item_type`: Notice, Receipt, Recording, Chat Log, Agreement) locked to `session_id`.
    - `get_vault_items(session_id: str) -> List[Dict[str, Any]]`: Fetches vault items strictly matching `session_id`.
    - `delete_vault_item(session_id: str, item_id: str) -> bool`: Deletes vault item if owned by `session_id`.
- **Dependencies Imported:** `sqlite3`, `json`, `time`, `uuid`, `pathlib`.
- **Important Constants:** `DB_PATH = Path(__file__).parent / "jurista_sessions.db"`.
- **Edge Cases & Behaviors:**
  - Privacy guarantee: Evidence vault records have no database linkage to community reports and are never queried or displayed on the public map or feed.
  - Public reports include a mandatory `allegation_disclaimer` stating they represent citizen allegations, not judicial findings.

### 4.10 `static/app.js`
- **Purpose and Why It Exists:** Frontend application controller written in Vanilla JavaScript. Drives chat interaction, PDF drag-and-drop uploads, Leaflet mapping with marker clustering, community feed filtering, location picking, voice input/output, and markdown rendering.
- **How It Works:** Encapsulated in an IIFE (`(function () { ... })()`). Manages state in memory and `localStorage`, binds DOM events, communicates with the backend via `fetch()`, initializes Leaflet maps, and manages the Web Speech API.
- **Key Functions:**
  - `init()`: Reads stored session and language, loads session history, binds events, sets up tabs, and initializes sub-modules.
  - `setupNavigationTabs()`: Toggles between Legal Assistant (`#view-chat`), Community Map (`#view-community`), and Evidence Vault (`#view-vault`).
  - `handleChatSubmit(e)` / `sendMessage(text)`: Posts user messages to `/api/chat`, manages loading spinner card, renders Markdown response, and adds citation chips.
  - `uploadPdfFile(file)`: Sends multipart PDF upload to `/api/upload-pdf`, manages loader UI, updates active document card, and renders explanation.
  - `toggleVoiceRecognition()` / `startVoiceRecognition()` / `stopVoiceRecognition()`: Uses browser `webkitSpeechRecognition` / `SpeechRecognition` configured with language locales (`en-IN`, `hi-IN`, `mr-IN`) for voice transcription into the chat textarea.
  - `playTextToSpeech(text, btnElement)`: Strips markdown formatting and uses browser `SpeechSynthesis` to read legal answers aloud in the active language.
  - `initCommunityMap()`: Initializes Leaflet map with OpenStreetMap tiles, creates a `L.markerClusterGroup`, and plots report pins with custom colored SVG markers.
  - `loadCommunityReports()` / `applyCommunityFilters()`: Fetches `/api/community/reports` and updates map markers and feed cards synchronously.
  - `openCreateReportModal()` / `initPickerMap()`: Opens report modal and interactive mini-map for approximate locality selection.
  - `loadVaultItems()` / `handleAddVaultSubmit()` / `deleteVaultItem()`: Manages private evidence vault records via `/api/vault/items`.
  - `renderMarkdown(text)`: Converts headers, code blocks, bold/italic markup, lists, and external links into clean semantic HTML.
- **Dependencies:** Leaflet.js, Leaflet.markercluster (loaded via CDN in `index.html`).

### 4.11 `static/index.html`
- **Purpose and Why It Exists:** Single-page semantic HTML5 user interface for Jurista.
- **Structure:**
  - Top header with brand icon, navigation tabs (`Legal Assistant & PDF`, `Community Map & Feed`, `Evidence Vault`), scope disclaimer badge, language dropdown, and New Session button.
  - **View 1 (`#view-chat`):** Split layout with left sidebar (active document status, upload dropzone, official Indian sources links) and right chat panel (message history, prompt chips, textarea, voice mic button, send button).
  - **View 2 (`#view-community`):** Community toolbar (search bar, topic filter, date filter, mapped-only checkbox, layout switchers: Split, Map, Feed) and workspace (synchronized feed card list and Leaflet map container).
  - **View 3 (`#view-vault`):** Private evidence vault table, add item button, and privacy shield notices.
  - Modals: Create Report modal with mini locality picker map, Report Details modal with statutory roadmaps, and Add Vault Item modal.

### 4.12 `static/style.css`
- **Purpose and Why It Exists:** Defines the complete visual design system for Jurista.
- **Design Specifications:**
  - Dark-slate theme using curated CSS custom properties: `--bg-app: #090D16`, `--bg-sidebar: #0E1626`, `--bg-surface: #141E33`, `--primary: #2563EB`, `--accent-cyan: #06B6D4`.
  - Typography: Google Fonts **Outfit** for headings and **Plus Jakarta Sans** for body and interface elements.
  - Glassmorphism: `backdrop-filter: blur(12px)` on cards and headers.
  - Responsive layout: Dynamic flex/grid rules adapting cleanly to desktop, tablet, and mobile screens.

### 4.13 `.env.example`
- **Purpose and Why It Exists:** Documents required and optional environment variables for deployment.
- **Contents:**
  - `GEMINI_API_KEY`: Google AI Studio API key.
  - `GEMINI_MODEL`: Model identifier (defaults to `gemini-2.5-flash` or `gemini-3.5-flash`).
  - `INDIANKANOON_API_KEY`: Optional API key for live case law search via `api.indiankanoon.org`.
  - `PORT`: Server port (default 8000).
  - `HOST`: Server bind address (default 127.0.0.1).

### 4.14 `requirements.txt`
- **Purpose and Why It Exists:** Specifies pinned Python dependencies:
  - `fastapi>=0.110.0`
  - `uvicorn>=0.28.0`
  - `python-dotenv>=1.0.0`
  - `pydantic>=2.6.0`
  - `google-genai>=0.1.1`
  - `pymupdf>=1.24.0`
  - `python-multipart>=0.0.9`
  - `requests>=2.31.0`

### 4.15 `test_system.py`, `test_community.py`, `test_indiankanoon.py`
- **`test_system.py`:** Automated end-to-end test suite testing 8 critical workflows: health check, scope pre-filter rejection, statutory Q&A retrieval, in-memory PDF creation & upload, document follow-up context retention, language switching, Devanagari output generation, and scanned PDF detection.
- **`test_community.py`:** Verifies community report creation, coordinate validation, public feed retrieval, allegation safety notices, and private evidence vault isolation.
- **`test_indiankanoon.py`:** Validates Indian Kanoon API key presence, sends a diagnostic query to `api.indiankanoon.org/search/`, measures network latency, and monkey-patches `legal_db.py` to confirm Path A vs. Path B routing.

---

## 5. The RAG Pipeline

```
USER QUERY / UPLOADED DOCUMENT
              │
              ├─────────────────────────────────────────┐
              ▼                                         ▼
   [Document Ingestion]                        [Query Retrieval]
              │                                         │
              ▼                                         ▼
  chunk_document_text()                        classify_query_domain()
  - 750 char chunks                            - Match _DOMAIN_KEYWORDS
  - 120 char overlap                           - Returns domain or ["general"]
  - Sentence slicing (Devanagari danda)                 │
  - Page markers preserved                              ▼
              │                               +───────────────────+
              ▼                               | Path A or Path B? |
  [SQLite document_json]                      +─────────┬─────────+
              │                                         │
              ▼                       ┌─────────────────┴─────────────────┐
  retrieve_document_chunks()          ▼ (Known Domain: Path A)            ▼ (General: Path B)
  - BM25 Lexical Ranking      _search_local_bm25()                _search_indiankanoon()
  - k1=1.5, b=0.75            - Score >= 8                        - Live API Search
  - Substring boost (+5.0)    - Domain gate (override at 16)      - Normalized schema
  - Top 3 chunks returned     - Top 1 statute returned            - Fallback to BM25
              │                               │                                   │
              └───────────────────────┬───────┴───────────────────────────────────┘
                                      ▼
                             build_prompt()
                             - Injects top 3 document chunks
                             - Injects top 1 legal statute
                             - Injects mandatory confidence labels
```

### 5.1 How Document Chunking Works (`chunk_document_text`)
Located in `rag_engine.py`, `chunk_document_text()` processes raw legal text through a four-stage pipeline:
1. **Page Marker Extraction:** Detects structural markers inserted during PDF parsing (`--- [Page X] ---`) using regex `r"(--- \[Page \d+\] ---)"`. Associates every text block with its physical source page number.
2. **Paragraph Boundary Preservation:** Splits text by double newlines (`\n\n`) to preserve legal clause structures rather than arbitrarily cutting across sentences.
3. **Sentence Boundary Slicing for Oversized Paragraphs:** If an individual paragraph exceeds `chunk_size` (750 characters), it is sliced using a sentence regex:
   ```python
   re.split(r"(?<=[.!?।])\s+", para)
   ```
   Notice the inclusion of `।` (the Devanagari danda / purna viram), guaranteeing that Hindi and Marathi legal clauses are split cleanly at natural grammatical terminators.
4. **Sliding Overlap Window:** Each chunk appends the final 120 characters (`chunk_overlap`) of the preceding buffer to the beginning of the next chunk. Every chunk dictionary stores `chunk_id`, `page`, raw `text`, and pre-computed lexical `tokens`. Provenance metadata (`act`, `section`, `official_url`) is attached when present.

### 5.2 How BM25 Document Retrieval Works (`retrieve_document_chunks`)
Located in `rag_engine.py`, `retrieve_document_chunks()` performs transparent, fast, local relevance ranking over active document chunks:
1. **Tokenization:** Cleans the user query using `clean_text_for_tokens()`:
   ```python
   re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]{2,}\b", text.lower())
   ```
   Matches alphanumeric terms and Devanagari Unicode characters (`\u0900-\u097F`).
2. **Document Frequency (DF):** Calculates token frequency across all chunks in the active document.
3. **BM25 Scoring Formula:** Evaluates each chunk using standard BM25 weighting:
   $$\text{Score} = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{f(t, D) \cdot (k_1 + 1)}{f(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avg\_dl}}\right)}$$
   - $k_1 = 1.5$ (term frequency saturation parameter)
   - $b = 0.75$ (length normalization parameter)
   - $\text{IDF}(t) = \ln\left(1.0 + \frac{N - \text{DF}(t) + 0.5}{\text{DF}(t) + 0.5}\right)$
4. **Exact Substring Boost:** If the complete query string appears verbatim inside a chunk's text, an additional $+5.0$ bonus is added to prioritize direct textual matches.
5. **Fallback:** If no chunk yields a score $> 0$, the retriever returns the first `top_k` (3) chunks to guarantee that prompt context is never left empty.

### 5.3 How Legal Statute Retrieval Works (`search_legal_sources`)
Located in `legal_db.py`, `search_legal_sources()` executes statutory retrieval using a Two-Path architecture:
- Queries are first classified by domain via `classify_query_domain(query)`.
- **Path A (Known Domain):** Queries matching specific domains (e.g., criminal, consumer, tenancy) are routed exclusively to `_search_local_bm25()`.
- **Path B (General Query):** Queries matching no specific domain (`["general"]`) are routed to the live Indian Kanoon API (`_search_indiankanoon()`), falling back to local BM25 if the API is unreachable.

### 5.4 Domain Classification System (`classify_query_domain`)
The domain classifier iterates over `_DOMAIN_KEYWORDS` in `legal_db.py`. Each keyword is checked as a substring of the lowercased query. The 8 recognized domains are:
- `tenancy`: `tenant`, `landlord`, `rent`, `eviction`, `deposit`, `security deposit`, `lease`, `flat rent`, `notice period`, `leave and license`
- `criminal`: `fir`, `police`, `arrest`, `cheque`, `fraud`, `cheating`, `bail`, `complaint`, `cognizable`
- `consumer`: `consumer`, `refund`, `warranty`, `defective`, `product`, `service`, `e-commerce`, `airline`, `medical negligence`
- `cyber`: `cyber`, `online fraud`, `upi`, `phishing`, `hacking`, `credit card`, `1930`, `cybercrime`
- `property`: `builder`, `rera`, `possession`, `flat`, `homebuyer`, `allotment`, `apartment`
- `family`: `domestic violence`, `divorce`, `maintenance`, `dowry`, `cruelty`, `custody`, `wife`, `husband`
- `procedure`: `rti`, `information`, `court`, `fir`, `magistrate`, `case status`, `cnr`, `ecourts`
- `legal_aid`: `free lawyer`, `legal aid`, `nalsa`, `dlsa`, `cannot afford`, `15100`

If one or more keywords match, a list of matched domains is returned. If no keywords match, it returns `["general"]`.

### 5.5 How `top_k=1` Decision Was Made and Why
In `graph.py` (line 104), statutory retrieval is deliberately configured to:
```python
retrieved_statutes = search_legal_sources(user_msg, top_k=1)
```
**Rationale:**
1. **Precision Over Recall:** In legal Q&A, presenting two different statutes where one is only tangentially relevant (e.g., pairing Section 138 of the Negotiable Instruments Act with Section 420 of the IPC) frequently leads the LLM to blend procedural requirements, causing confusion about statutory deadlines (e.g., confusing the 15-day cheque notice cure period with general criminal procedure).
2. **Preventing Prompt Dilution:** Grounding the LLM in the single highest-scoring, domain-verified statute focuses the model on generating a concrete, step-by-step procedural roadmap for that specific legal remedy.
3. **Verified Primary Authority:** The single top statute returned by BM25 has already cleared `MINIMUM_RELEVANCE_SCORE = 8` and domain gating, providing sufficient authoritative grounding for the turn.

### 5.6 How Indian Kanoon API Integrates as Path B Only
The Indian Kanoon Search API (`https://api.indiankanoon.org/search/`) provides access to millions of Indian court judgments and central acts. However, it is integrated strictly as **Path B (general queries only)**:
- **Why Not Path A?** Indian Kanoon's search results carry no domain tags. For a specific query like "landlord withheld my security deposit", if our curated database has no matching statute, querying Indian Kanoon often returns high-level Supreme Court leasehold property tax appeals rather than residential tenancy principles. Returning no statute for a known domain signals a curated database gap, allowing the LLM to rely on general legal principles labeled `[PRINCIPLE]` rather than citing an irrelevant high court judgment.
- **Why Path B?** For broad or general queries that do not match the 8 curated domains, Indian Kanoon provides live coverage of Indian jurisprudence, with results normalized to the standard `LEGAL_STATUTES` dictionary schema.

---

## 6. The LangGraph Pipeline

### 6.1 State Schema (`JuristaState`)
Defined in `graph.py`, the state object flows through all nodes:

```python
class JuristaState(TypedDict):
    session_id: str                      # Unique client UUID
    language: str                        # "English", "Hindi", or "Marathi"
    user_message: str                    # Current turn input text
    intent: str                          # Intent classification label
    is_out_of_scope: bool                # Guardrail rejection flag
    document_text: Optional[str]         # Full raw text of active PDF
    document_chunks: List[Dict[str, Any]]# All indexed chunks of active PDF
    retrieved_doc_chunks: List[Dict[str, Any]] # Top 3 BM25 document chunks
    retrieved_legal_sources: List[Dict[str, Any]] # Top 1 statutory provision
    conversation_context: str            # Formatted recent conversation turns
    response_text: str                   # Final generated answer text
```

### 6.2 All Nodes Explained
1. **`route_intent_node`**:
   - Executes fast heuristic pre-screening via `GeminiClient.is_obviously_out_of_scope()`. If matched, sets `intent = "OUT_OF_SCOPE"` and loads pre-translated refusal text.
   - If not out-of-scope, inspects document state and conversation length to classify intent into `DOCUMENT_EXPLAIN`, `DOCUMENT_FOLLOWUP`, `NEEDS_CLARIFICATION`, or `LEGAL_QUERY`.
2. **`retrieve_sources_node`**:
   - Invokes `retrieve_document_chunks()` over uploaded PDF chunks (top 3).
   - Invokes `search_legal_sources()` over the statutory knowledge base (top 1).
3. **`generate_answer_node`**:
   - Formats retrieved document chunks and legal statutes into markdown grounding blocks.
   - Assembles the prompt via `prompts.build_prompt()`.
   - Dispatches the prompt and `SYSTEM_PROMPT` to `GeminiClient.generate_content()`.
4. **`out_of_scope_node`**:
   - Rejection sink for out-of-scope queries. Returns the localized polite refusal text directly without calling the LLM.

### 6.3 Routing Logic and Conditional Edges
The workflow graph is structured as:
```
[START] ──► route_intent ──► {should_route_out_of_scope}
                                 │
                 ┌───────────────┴───────────────┐
                 ▼ (is_out_of_scope == True)     ▼ (is_out_of_scope == False)
           out_of_scope                  retrieve_sources
                 │                               │
                 ▼                               ▼
               [END]                      generate_answer
                                                 │
                                                 ▼
                                               [END]
```

### 6.4 How Intents Are Classified
Intent classification follows a strict waterfall:
1. **`OUT_OF_SCOPE`:** Triggered if regex pattern matches non-legal topics (code, cooking, math, sports, weather) and contains no whitelisted legal keywords.
2. **`DOCUMENT_EXPLAIN`:** Triggered if document text/chunks exist AND the user's message contains phrases like `"explain this document"`, `"analyze this document"`, or `"read this notice"`.
3. **`DOCUMENT_FOLLOWUP`:** Triggered if document text/chunks exist AND prior conversation history exceeds 10 characters.
4. **`NEEDS_CLARIFICATION`:** Triggered if `check_needs_clarification()` detects that the query has 3 words or fewer and contains vague triggers (`notice`, `fir`, `arrest`, `fraud`, etc.).
5. **`LEGAL_QUERY`:** Default category for all general legal questions.

---

## 7. The Prompt System

### 7.1 `SYSTEM_PROMPT` — Full Explanation of Every Instruction Block
The `SYSTEM_PROMPT` is injected into every Gemini generation call and establishes strict operational boundaries:
- **Role Identity:** Defines Jurista as an objective AI legal information assistant specialized in Indian law, clarifying that it provides legal *information*, not formal legal advice.
- **Strict Scope Guardrail:** Mandates immediate polite refusal for non-Indian or non-legal topics.
- **Authoritative Sources:** Grounds all legal assertions in India Code, Indian Kanoon, NALSA, and eCourts. Enforces standard citation format `[Act Name, Year — Section X]`. Forbids hallucinating section numbers, deadlines, or penalty amounts.
- **Claim Confidence Labels (Mandatory):** Requires every legal assertion to be labeled:
  - `[STATUTE]`: Directly grounded in a named Act and Section.
  - `[AGREEMENT]`: Dependent on contractual or tenancy terms.
  - `[PRINCIPLE]`: General legal doctrine without specific single-section codification.
  - `[JURISDICTION-DEPENDENT]`: Subject to state or local variation.
  - `[UNVERIFIED]`: Provisions that could not be verified from official records.
- **Jurisdiction Gaps:** Requires flagging state-dependent rules (e.g., rent control, police manuals) with `[JURISDICTION-DEPENDENT]` whenever state or city is unspecified.
- **Allegations Rule:** Mandates treating claims in opposing notices or complaints as unilateral *allegations*, using neutral phrasing ("The notice alleges...", "The complainant claims...").
- **Citizen Rights & Free Legal Aid:** Directs eligible citizens to free legal aid under Section 12 of the Legal Services Authorities Act, 1987 via the national NALSA helpline: **15100**.

### 7.2 `LEGAL_QUERY_PROMPT` — Structure and Writing Rules
Configured for natural prose rather than rigid prefix blocks:
1. **Writing Rules:**
   - Write in flowing, empathetic sentences as an advisor speaking plainly to a non-lawyer.
   - Weave statutes naturally inline: *"Under the Consumer Protection Act, 2019 (Section 35), you may file..."*.
   - Mention state variations and agreement dependencies naturally within sentences.
   - Do NOT prefix lines with bracketed labels; place them as subtle inline footnotes if needed (e.g., $^1$[Transfer of Property Act, 1882 — Section 108]).
2. **Exact Five-Section Structure:**
   - `## Situation`: One short paragraph (2–4 sentences) summarizing the problem empathetically.
   - `## Your Legal Position`: 2–3 paragraphs explaining applicable Indian law, rights, entitlements, and statutory nuances.
   - `## What You Should Do`: A concrete numbered action plan organized under three sub-headings:
     - `**Right Away:**` (Immediate steps today)
     - `**This Week:**` (Follow-up actions or authorities to approach)
     - `**If the Problem Is Not Resolved:**` (Escalation to commissions, courts, or DLSA)
   - `## What to Keep as Evidence`: Concrete bulleted list of documents, receipts, screenshots, and logs to preserve.
   - `## Important Limitations`: Plain-language limitations paragraph highlighting state variations, contract dependencies, and NALSA helpline (15100).

### 7.3 `DOCUMENT_EXPLAIN_PROMPT`
Used when a user uploads a PDF. Mandates a 7-section structured analysis:
1. `📄 What This Document Is`: Document type, issuing authority/sender, recipient, core subject.
2. `⚠️ Claims & Allegations (What They Are Stating)`: Bullet points highlighting that claims are allegations, not established facts.
3. `📅 Dates, Amounts & Stated Deadlines`: Key dates, financial demands, stated response deadlines.
4. `⚖️ Relevant Legal Provisions`: Statutory provisions cited or applicable under Indian law.
5. `🚩 Red Flags & Potential Irregularities`: Procedural flaws, missing signatures, jurisdictional defects, or exaggerated threats.
6. `✅ Practical Next Steps (Your Roadmap)`: Immediate steps, weekly actions, evidence to safeguard.
7. `🚨 Legal Representation & Free Aid`: Guidance on advocate response and NALSA/DLSA aid (15100).

### 7.4 `DOCUMENT_FOLLOWUP_PROMPT`
Focuses on answering follow-up queries using the combination of active document excerpts, prior conversation history, and statutory provisions. Differentiates between what the document alleges versus what Indian law requires.

### 7.5 `NEEDS_CLARIFICATION_PROMPT`
Triggered on ultra-short vague queries. Acknowledges the general topic in one sentence, asks at most 3 concise clarifying questions (e.g., state/city, document type, dates), and reassures the user that a step-by-step roadmap will follow.

### 7.6 How `build_prompt()` Works
Defined in `prompts.py`, `build_prompt()` provides bulletproof template formatting:
- Accepts `prompt_type`, `language`, and dynamic `kwargs`.
- Fetches language instruction via `get_language_instruction()`.
- Maps parameter aliases (`user_query`, `user_question`, `user_message`) to prevent parameter mismatch bugs.
- Uses Python's `string.Formatter().parse()` to detect all format keys in the template, filling any missing keys with empty strings to guarantee that formatting never raises a `KeyError`.

### 7.7 Claim Confidence Label System Explanation
The label system prevents overconfident AI advice:
- `[STATUTE]`: Used when a right or procedure is codified in an official central Act.
- `[AGREEMENT]`: Used when an outcome depends entirely on private contract clauses (e.g., notice periods in leave-and-license agreements).
- `[PRINCIPLE]`: Used for established legal doctrines (e.g., principles of natural justice, fair wear-and-tear).
- `[JURISDICTION-DEPENDENT]`: Used for matters governed by state amendments (e.g., Maharashtra Rent Control Act vs. Delhi Rent Control Act).
- `[UNVERIFIED]`: Used when specific sections cannot be corroborated against official India Code text.

---

## 8. Legal Database

### 8.1 All 13 Curated Statutes Listed with Domain Tags

| ID | Domain | Act | Section | Title | Official Portal URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ni_act_138` | `criminal` | Negotiable Instruments Act, 1881 | Section 138 | Dishonour of Cheque for Insufficiency of Funds | [India Code](https://www.indiacode.nic.in/handle/123456789/2189) |
| `ni_act_141` | `criminal` | Negotiable Instruments Act, 1881 | Section 141 | Offences by Companies (Director Liability) | [India Code](https://www.indiacode.nic.in/handle/123456789/2189) |
| `cpa_2019_deficiency` | `consumer` | Consumer Protection Act, 2019 | Section 2(11) & Section 35 | Deficiency in Goods/Services & e-Daakhil Filing | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) |
| `bnss_173_fir` | `procedure` | Bharatiya Nagarik Suraksha Sanhita, 2023 | BNSS § 173 (CrPC 154) | Information in Cognizable Cases (FIR Registration & Zero FIR) | [India Code](https://www.indiacode.nic.in) |
| `bnss_35_arrest` | `procedure` | Bharatiya Nagarik Suraksha Sanhita, 2023 | BNSS § 35 (CrPC 41A) | Notice of Appearance Before Police Officer | [India Code](https://www.indiacode.nic.in) |
| `bns_cheating_318` | `criminal` | Bharatiya Nyaya Sanhita, 2023 | BNS § 318 (IPC 420) | Cheating and Dishonestly Inducing Delivery of Property | [India Code](https://www.indiacode.nic.in) |
| `it_act_66d` | `cyber` | Information Technology Act, 2000 | Section 66D & 43 | Cheating by Personation Using Computer Resource & Cyber Fraud | [India Code](https://www.indiacode.nic.in/handle/123456789/1999) |
| `tpa_106_lease` | `tenancy` | Transfer of Property Act, 1882 | Section 106 & 108 | Duration of Leases & Notice to Terminate Tenancy | [India Code](https://www.indiacode.nic.in/handle/123456789/2338) |
| `pwdva_2005` | `family` | Protection of Women from Domestic Violence Act, 2005 | Section 12, 18 & 19 | Application to Magistrate, Protection Orders & Right to Reside | [India Code](https://www.indiacode.nic.in/handle/123456789/2021) |
| `rera_2016_18` | `property` | Real Estate (Regulation and Dev.) Act, 2016 | Section 18 & 31 | Return of Amount & Compensation for Delayed Possession | [India Code](https://www.indiacode.nic.in/handle/123456789/2158) |
| `rti_act_2005_6` | `procedure` | Right to Information Act, 2005 | Section 6 & 7 | Request for Obtaining Information & Time Limits (30 Days / 48 Hrs) | [India Code](https://www.indiacode.nic.in/handle/123456789/2065) |
| `nalsa_legal_aid_1987`| `legal_aid` | Legal Services Authorities Act, 1987 | Section 12 | Criteria for Giving Free Legal Services (Helpline 15100) | [NALSA](https://nalsa.gov.in) |
| `ecourts_tracking` | `procedure` | eCourts Services Framework | CNR Verification | Official Court Case Status Tracking | [eCourts](https://services.ecourts.gov.in) |

### 8.2 Domain Classification System and `_DOMAIN_KEYWORDS`
The keyword mappings in `legal_db.py` cover 8 critical citizen legal domains:
- Tenancy, Criminal, Consumer, Cyber, Property, Family, Procedure, Legal Aid.
- Matching checks substring membership, allowing multi-word phrases like `"domestic violence"` or `"security deposit"` to match without complex stemming.

### 8.3 BM25 Scoring Explained
In `_search_local_bm25()`:
- Tokens are extracted via regex `\w+`.
- Scoring weights:
  - Keyword token overlap: $\text{count} \times 3$
  - Verbatim keyword substring match in query: $+8$
  - Act title token overlap: $\text{count} \times 2$
  - Section title token overlap: $\text{count} \times 4$
  - Summary token overlap: $\text{count} \times 1$
- Any item scoring below `min_score` (default 8) is discarded.

### 8.4 `MINIMUM_RELEVANCE_SCORE` and Why It Is 8
`MINIMUM_RELEVANCE_SCORE: int = 8`.
**Reasoning:**
- A score of 8 requires either:
  1. An exact match of a key legal term (e.g., `"cheque bounce"`, `"zero fir"`, `"41a"` awards $+8$ immediately).
  2. Multiple overlapping tokens across Section and Act titles (e.g., matching `"Section"` and `"138"` gives $2 \times 4 = 8$).
- Setting the threshold to 8 eliminates false-positive noise from incidental words (like `"notice"`, `"court"`, or `"delay"`) matching every statute in the database.

### 8.5 Path A vs. Path B Retrieval Strategy and the Reasoning
- **Path A (Known Domain):** If `classify_query_domain(query)` returns one of the 8 recognized domains, search is restricted strictly to local BM25 over `LEGAL_STATUTES`. If no statute clears the score floor, an empty list is returned. Indian Kanoon is not queried because it lacks domain metadata and would surface irrelevant case law.
- **Path B (General Query):** If the query has no domain keyword (`["general"]`), Indian Kanoon is queried first for live case law coverage. If unavailable or empty, it falls back to local BM25.

---

## 9. Session Management

### 9.1 SQLite Schema (`sessions` and `messages` tables)
Defined in `session_store.py`:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'English',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    document_json TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    route TEXT,
    sources_json TEXT,
    timestamp REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
```

### 9.2 How Session Isolation Works
- Every client session is identified by a unique UUID4 (`jurista-` + UUIDv4), generated client-side and saved in browser `localStorage`.
- All database queries filter strictly by `WHERE session_id = ?`.
- No cross-talk or shared state exists between sessions. Multiple users querying simultaneously maintain completely private message histories, document contexts, and evidence vaults.

### 9.3 How Document Context Is Stored and Retrieved
- When a PDF is uploaded, `extract_text_from_pdf()` extracts the text, and `chunk_document_text()` splits it into structured chunks.
- The entire document payload (filename, page count, total characters, full text, scanned flag, chunks) is serialized to JSON and stored in the `document_json` column of the `sessions` table.
- On subsequent turns, `SessionStore.get_document(session_id)` deserializes this JSON, making chunks immediately available for BM25 retrieval without re-reading the PDF file.

### 9.4 How Conversation Context Is Built for Prompts
- `SessionStore.get_conversation_context(session_id, max_turns=4)` fetches the most recent message records ordered by timestamp.
- Selects the last `max_turns * 2` messages (up to 8 individual messages representing 4 complete user-assistant turns).
- Formats them into a clean dialogue string:
  ```
  User: I received a cheque bounce notice for Rs. 50,000.
  Jurista: Under Section 138 of the Negotiable Instruments Act...
  ```
- This string is interpolated into the `{conversation_context}` variable of prompt templates.

---

## 10. API Endpoints

### 10.1 `GET /api/health`
- **Method:** `GET`
- **Path:** `/api/health`
- **Request Body:** None
- **Response Shape:**
  ```json
  {
    "status": "healthy",
    "service": "Jurista",
    "gemini_configured": true,
    "model": "gemini-3.5-flash"
  }
  ```
- **What It Does:** Verifies server responsiveness, checks if `GEMINI_API_KEY` is configured, and reports active model.

### 10.2 `GET /api/session/{session_id}`
- **Method:** `GET`
- **Path:** `/api/session/{session_id}`
- **Path Parameters:** `session_id` (str)
- **Response Shape:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "language": "English",
    "document": {
      "filename": "Demand_Notice.pdf",
      "page_count": 2,
      "total_characters": 1840,
      "is_scanned": false,
      "chunk_count": 3
    },
    "messages": [
      {
        "message_id": "msg-123",
        "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "role": "user",
        "content": "What is the notice deadline?",
        "route": null,
        "sources": [],
        "timestamp": 1729000000.0
      }
    ]
  }
  ```
- **What It Does:** Retrieves session configuration, active document metadata, and message history.

### 10.3 `POST /api/session/language`
- **Method:** `POST`
- **Path:** `/api/session/language`
- **Request Body:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "language": "Hindi"
  }
  ```
- **Response Shape:**
  ```json
  {
    "success": true,
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "language": "Hindi"
  }
  ```
- **What It Does:** Updates session language to English, Hindi, or Marathi without clearing chat history or documents.

### 10.4 `POST /api/session/clear`
- **Method:** `POST`
- **Path:** `/api/session/clear`
- **Request Body:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```
- **Response Shape:**
  ```json
  {
    "success": true,
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "message": "Session reset successfully."
  }
  ```
- **What It Does:** Clears all messages and active document attachments for the session.

### 10.5 `POST /api/chat`
- **Method:** `POST`
- **Path:** `/api/chat`
- **Request Body:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "message": "I received a cheque bounce notice for Rs. 50,000. What is my deadline to pay?",
    "language": "English"
  }
  ```
- **Response Shape:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "language": "English",
    "intent": "LEGAL_QUERY",
    "is_out_of_scope": false,
    "sources": [
      {
        "id": "ni_act_138",
        "act": "Negotiable Instruments Act, 1881",
        "section": "Section 138",
        "title": "Dishonour of Cheque for Insufficiency of Funds",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2189",
        "summary": "When a cheque drawn for discharge of debt..."
      }
    ],
    "retrieved_doc_chunks_count": 0,
    "response": "## Situation\n\nYou received a statutory demand notice..."
  }
  ```
- **What It Does:** Primary legal Q&A endpoint. Runs scope pre-filter, intent routing, document/statutory retrieval, and Gemini response generation.

### 10.6 `POST /api/upload-pdf`
- **Method:** `POST`
- **Path:** `/api/upload-pdf`
- **Content-Type:** `multipart/form-data`
- **Form Parameters:**
  - `file`: Binary PDF file (`.pdf`)
  - `session_id`: Client UUID string (optional)
  - `language`: Preferred language string (optional)
- **Response Shape:**
  ```json
  {
    "success": true,
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "filename": "Demand_Notice.pdf",
    "page_count": 2,
    "total_characters": 1840,
    "is_scanned": false,
    "chunk_count": 3,
    "explanation": "📄 **What This Document Is**\n- Document Type: Legal Notice...",
    "message": "PDF analyzed successfully with 2 pages."
  }
  ```
- **What It Does:** Extracts text via PyMuPDF, checks for scanned images, segments text into overlapping chunks, generates an immediate structured analysis, and stores document state.

### 10.7 `GET /api/community/reports`
- **Method:** `GET`
- **Path:** `/api/community/reports`
- **Query Parameters:** `topic` (str), `search` (str), `from_date` (YYYY-MM-DD), `to_date` (YYYY-MM-DD), `has_location_only` (bool), `limit` (int, default 100)
- **Response Shape:**
  ```json
  {
    "success": true,
    "count": 5,
    "allegation_notice": "Community reports reflect user-submitted experiences and allegations...",
    "reports": [
      {
        "id": "rep-pune-001",
        "title": "Police Station Refusal to Register Zero FIR",
        "topic": "Police & FIR",
        "description": "Attempted to register an FIR for a stolen two-wheeler...",
        "approx_location_name": "Shivajinagar, Pune, Maharashtra",
        "latitude": 18.5314,
        "longitude": 73.8446,
        "incident_date": "2026-09-18",
        "created_at": 1729000000.0,
        "is_public": true,
        "status": "published",
        "allegation_disclaimer": "User-submitted community experience/allegation. Not verified findings."
      }
    ]
  }
  ```
- **What It Does:** Fetches public published community experience reports for the interactive map and feed.

### 10.8 `GET /api/community/reports/{report_id}`
- **Method:** `GET`
- **Path:** `/api/community/reports/{report_id}`
- **Path Parameters:** `report_id` (str)
- **Query Parameters:** `session_id` (str, optional)
- **Response Shape:** Returns full details of the single report if published or owned by `session_id`.
- **What It Does:** Returns full report details for display in the report details modal.

### 10.9 `POST /api/community/reports`
- **Method:** `POST`
- **Path:** `/api/community/reports`
- **Request Body:**
  ```json
  {
    "title": "E-Commerce Refusal to Replace Defective Electronics",
    "topic": "Consumer Dispute",
    "description": "Purchased a television that failed within 10 days...",
    "approx_location_name": "Indiranagar, Bengaluru, Karnataka",
    "latitude": 12.9784,
    "longitude": 77.6408,
    "incident_date": "2026-10-14",
    "is_public": true,
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```
- **Response Shape:**
  ```json
  {
    "success": true,
    "report": { ... },
    "message": "Experience report submitted successfully."
  }
  ```
- **What It Does:** Validates coordinates, rounds them to 4 decimals, and creates a public or draft community experience report.

### 10.10 `GET /api/vault/items`
- **Method:** `GET`
- **Path:** `/api/vault/items?session_id=...`
- **Query Parameters:** `session_id` (str, required)
- **Response Shape:**
  ```json
  {
    "success": true,
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "count": 2,
    "items": [
      {
        "id": "vlt-84f9b2c1",
        "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "title": "Cheque Return Memo Copy",
        "item_type": "Notice",
        "description": "Bank return memo showing funds insufficient remark",
        "approx_location": "SBI Pune Main Branch",
        "created_at": 1729000000.0,
        "is_private": true
      }
    ]
  }
  ```
- **What It Does:** Retrieves private evidence items strictly isolated to the caller's session.

### 10.11 `POST /api/vault/items`
- **Method:** `POST`
- **Path:** `/api/vault/items`
- **Request Body:**
  ```json
  {
    "session_id": "jurista-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "title": "Cheque Return Memo Copy",
    "item_type": "Notice",
    "description": "Bank return memo showing funds insufficient remark",
    "approx_location": "SBI Pune Main Branch"
  }
  ```
- **Response Shape:**
  ```json
  {
    "success": true,
    "item": { ... },
    "message": "Evidence item saved to your private vault."
  }
  ```
- **What It Does:** Saves a confidential document reference or private record note to the session's private vault.

### 10.12 `DELETE /api/vault/items/{item_id}`
- **Method:** `DELETE`
- **Path:** `/api/vault/items/{item_id}?session_id=...`
- **Path Parameters:** `item_id` (str)
- **Query Parameters:** `session_id` (str, required)
- **Response Shape:**
  ```json
  {
    "success": true,
    "message": "Vault item removed."
  }
  ```
- **What It Does:** Deletes a private vault item after verifying that it belongs to the caller's `session_id`.

---

## 11. Frontend (`app.js`)

### 11.1 Application State Variables
- `sessionId`: Client UUID string (persisted in `localStorage.getItem("jurista_session_id")`).
- `currentLanguage`: Active language string (`"English"`, `"Hindi"`, or `"Marathi"`).
- `activeDocument`: Object storing metadata of currently attached PDF (`filename`, `page_count`, `total_characters`, `is_scanned`, `chunk_count`).
- `isProcessing`: Boolean preventing duplicate prompt submissions while awaiting server response.
- `communityMap`: Leaflet map instance for community dispute visualization.
- `markersClusterGroup`: Leaflet `markerClusterGroup` managing grouped map pins.
- `reportMarkersMap`: `Map<string, {marker, report}>` linking report IDs to map markers.
- `allCommunityReports`: Array storing raw public reports fetched from backend.
- `filteredCommunityReports`: Array storing reports currently passing active filter criteria.
- `activeReportId`: ID of currently inspected or highlighted report card.
- `communityLayoutMode`: Active layout mode (`"split"`, `"map"`, or `"feed"`).
- `pickerMap` / `pickerMarker`: Mini Leaflet map and draggable pin for locality selection.
- `selectedPickerLat` / `selectedPickerLon`: Temporary coordinates selected in the location picker.
- `recognition` / `isRecording` / `recognitionBaseText`: Web Speech recognition state variables.

### 11.2 Major Functions Explained
- `init()`: Reads stored preferences, binds all UI events, checks initial session details, and sets up tabs.
- `setupNavigationTabs()`: Manages switching between `#view-chat`, `#view-community`, and `#view-vault`, triggering map invalidation when switching to community view.
- `handleChatSubmit()` / `sendMessage()`: Gathers message text, displays user card, renders loading card, calls `/api/chat`, and renders assistant markdown and citation chips.
- `uploadPdfFile(file)`: Validates file type and size (<15MB), creates `FormData`, calls `/api/upload-pdf`, and renders structured explanation.
- `initCommunityMap()`: Initializes Leaflet map centered on India `[21.5937, 78.9629]`, loads OpenStreetMap tiles, and attaches click listeners.
- `loadCommunityReports()` / `applyCommunityFilters()`: Queries `/api/community/reports` with active filters, renders feed cards in `#community-reports-list`, and rebuilds map markers in `markersClusterGroup`.
- `selectReport(reportId, shouldFlyTo)`: Synchronizes feed and map; centers map on report pin (`flyTo`), opens popup, and scrolls feed to highlight the card.
- `initPickerMap()` / `handlePickerMapClick()`: Powers the location picker modal, updating the draggable marker and reverse-geocoding coordinates.
- `toggleVoiceRecognition()` / `startVoiceRecognition()` / `stopVoiceRecognition()`: Interacts with the browser's `SpeechRecognition` API, appending spoken words into the chat textarea in real time.
- `playTextToSpeech(text, btnElement)`: Strips markdown symbols and synthesizes spoken audio using `SpeechSynthesisUtterance`.
- `renderMarkdown(text)`: Converts raw markdown into safe HTML headings, code blocks, lists, bold/italic text, and external links with `target="_blank"`.

### 11.3 Chat Flow
1. User enters text or clicks a topic chip.
2. `appendUserMessage()` writes message to DOM and scrolls to bottom.
3. `appendLoadingMessage()` shows animated pulse card.
4. Server processes turn and returns response text, route intent, and verified authority sources.
5. `appendAssistantMessage()` replaces loading card with formatted markdown, adds clickable citation chips, and adds a Text-to-Speech audio button.

### 11.4 PDF Upload Flow
1. User drags a file into `#dropzone` or clicks to browse.
2. `uploadPdfFile()` validates that the file has a `.pdf` extension and is under 15 MB.
3. Shows upload progress spinner.
4. On success, `renderActiveDocument()` displays active PDF badge, page count, character count, and chunk density in the sidebar.
5. Displays structured explanation in chat stream.

### 11.5 Community Map and Reports Flow
1. Reports are fetched from `/api/community/reports` and plotted on the Leaflet map.
2. Clicking a cluster expands nearby pins.
3. Clicking a marker centers the map, opens a popup with topic badge, incident date, and excerpt, and highlights the corresponding card in the feed.
4. Clicking "Ask Jurista AI about this issue" in the report detail modal automatically pre-fills the chat input with a consultation prompt and switches to the Chat tab.

### 11.6 Evidence Vault Flow
1. Users view private records in a secure tabular layout.
2. Users can create confidential records for notices, receipts, agreements, or chat logs.
3. Records are persisted in `evidence_vault` and isolated strictly to the user's session UUID.
4. Vault records are never shown on the public map or shared in community feeds.

### 11.7 Voice Recognition
- Uses `window.SpeechRecognition` or `window.webkitSpeechRecognition`.
- Sets locale dynamically based on `currentLanguage`: `en-IN` (English), `hi-IN` (Hindi), or `mr-IN` (Marathi).
- Supports continuous real-time interim results, streaming recognized words directly into the textarea.

### 11.8 Markdown Renderer (`renderMarkdown`)
- First escapes HTML special characters (`&`, `<`, `>`, `"`, `'`) to prevent XSS.
- Replaces code blocks (`` `code` `` and ```` ```pre``` ````).
- Replaces Markdown headers (`###`, `##`, `#`).
- Replaces bold (`**`) and italic (`*`) markup.
- Converts markdown links `[text](url)` to `<a href="url" target="_blank" rel="noopener">text &nearr;</a>`.
- Parses unordered lists (`- `, `* `, `• `), wrapping items in `<ul><li>...</li></ul>`.

---

## 12. Known Design Decisions

### 12.1 Why `top_k=1` for Statute Retrieval
In `graph.py` line 104, statutory retrieval is set to `top_k=1`. In legal informational systems, providing a single, highly accurate statutory reference yields substantially better LLM outputs than supplying 3 or 4 marginally relevant statutes. Citing multiple provisions often leads the LLM to conflate procedural timelines (e.g., mixing civil suit limitation periods with 15-day cheque bounce notice cure windows).

### 12.2 Why Indian Kanoon Is Path B Only for Domain Queries
The Indian Kanoon API index contains millions of court opinions across appellate jurisdictions. However, its search endpoint does not support structured domain filtering. When a user asks a domain-specific question (e.g., regarding tenant deposit refunds), if the curated database lacks a match, querying Indian Kanoon often returns irrelevant corporate tax lease judgments. Therefore, Path A queries (known domains) rely exclusively on the curated local database, while Path B (general/unclassified queries) uses Indian Kanoon for broad coverage.

### 12.3 Why BM25 Not Vector Embeddings
1. **Verifiable Precision:** Legal statutes depend on exact section numbers, Act titles, and specific statutory phrases (e.g., `"Section 138"`, `"Zero FIR"`, `"41A Notice"`). Lexical BM25 matches these exact tokens with 100% fidelity, whereas dense vector embeddings often exhibit semantic drift (e.g., confusing bail applications with anticipatory bail).
2. **Zero Heavy Dependencies:** Eliminates dependencies on multi-gigabyte neural embedding models (e.g., PyTorch, HuggingFace Transformers, ChromaDB, FAISS), allowing Jurista to start instantly and run efficiently in constrained environments.
3. **Multilingual Lexical Support:** Custom tokenization supports Devanagari Unicode scripts directly, matching statutory terms across languages.

### 12.4 Why SQLite Not a Hosted Database
1. **Local Privacy:** Legal documents, demand notices, and private evidence records remain entirely on the user's local machine or private server instance.
2. **Zero Configuration:** Runs out of the box with zero external database configuration, connection strings, or cloud database fees.
3. **Thread Safety & ACID Compliance:** Python's standard `sqlite3` module with connection context managers provides thread-safe, ACID-compliant persistence for multi-turn sessions and evidence records.

### 12.5 Why LangGraph for Orchestration
1. **Deterministic State Machine:** LangGraph provides an explicit `StateGraph` that clearly defines transitions between routing, retrieval, generation, and scope rejection.
2. **Auditable Edge Conditions:** Conditional routing (`should_route_out_of_scope`) makes guardrail enforcement auditable and deterministic, guaranteeing that out-of-scope prompts never touch the LLM.
3. **State Transparency:** The shared `JuristaState` dictionary maintains full inspection visibility across every turn of the pipeline.

---

## 13. Setup & Running

### 13.1 Prerequisites
- **Operating System:** Linux, macOS, or Windows 10/11.
- **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Google Gemini API Key:** Obtainable free from [Google AI Studio](https://aistudio.google.com/).
- **Optional Indian Kanoon API Key:** For live case law search, obtainable from [Indian Kanoon API](https://api.indiankanoon.org/).

### 13.2 Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/jurista.git
   cd jurista
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 13.3 `.env` Configuration
Copy `.env.example` to create `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure variables:
```env
# Google Gemini API Key (Required)
GEMINI_API_KEY=AIzaSyYourActualKeyHere

# Model identifier (Optional, defaults to gemini-2.5-flash or gemini-3.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Indian Kanoon API Key (Optional)
# If omitted, legal_db.py automatically uses the curated BM25 statutory database
INDIANKANOON_API_KEY=

# Server settings
PORT=8000
HOST=127.0.0.1
```

### 13.4 How to Run the Server

#### Option A: Windows One-Click Launcher
Double-click `run.bat` or run from command prompt:
```cmd
run.bat
```
*(Verifies Python environment, checks `.env`, installs dependencies if missing, starts Uvicorn, and automatically opens `http://127.0.0.1:8000` in your default browser.)*

#### Option B: Manual Command Line Execution
```bash
python main.py
```
Or directly with Uvicorn:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The web application will be live at: **`http://127.0.0.1:8000/`**

### 13.5 How to Run Tests
Jurista includes three specialized verification test suites:

1. **End-to-End System Test Suite:**
   ```bash
   python test_system.py
   ```
   *Verifies health check, out-of-scope regex filter, statutory Q&A retrieval, in-memory PDF creation & upload, document follow-ups, language switching, Devanagari generation, and scanned document detection.*

2. **Community Experiences & Map Test Suite:**
   ```bash
   python test_community.py
   ```
   *Verifies report creation, coordinate validation, public feed retrieval, allegation safety notices, and private evidence vault isolation.*

3. **Indian Kanoon Diagnostic Test:**
   ```bash
   python test_indiankanoon.py
   ```
   *Tests API key presence, sends a diagnostic query to `api.indiankanoon.org`, measures latency, and confirms Path A vs. Path B fallback routing.*

---

## 14. Known Limitations & Future Improvements

### 14.1 Local Database Has 13 Curated Statutes
- **Limitation:** The curated database in `legal_db.py` contains 13 foundational central statutory provisions. While these cover high-frequency citizen issues, they do not encompass specialized statutory areas (such as Admiralty law, Patent oppositions, Insolvency & Bankruptcy Code, or Military Court procedures).
- **Future Improvement:** Expand the curated catalog to 100+ high-frequency central acts and rules, organized by modular domain JSON catalogs.

### 14.2 No Vector Embeddings Yet
- **Limitation:** The RAG pipeline relies strictly on lexical BM25 token matching. While highly effective for matching section numbers and exact terminology, it may struggle with queries that describe legal concepts using purely non-legal colloquial language without keyword overlap.
- **Future Improvement:** Introduce a hybrid retrieval architecture combining local BM25 scoring with lightweight, on-device vector embeddings (e.g., `all-MiniLM-L6-v2` via ONNX runtime) for dual lexical-semantic search.

### 14.3 State-Specific Law Gaps
- **Limitation:** Many civil and police subjects in India are governed by state-specific enactments (e.g., the *Maharashtra Rent Control Act, 1999* vs. the *Delhi Rent Control Act, 1958*, or state-specific Police Regulations). The system currently addresses this by flagging such issues with `[JURISDICTION-DEPENDENT]` and providing general guidance.
- **Future Improvement:** Introduce a state-selection dropdown allowing users to specify their state/union territory, activating state-specific statutory rule overrides.

### 14.4 Optical Character Recognition (OCR) for Scanned PDFs
- **Limitation:** Scanned or image-only documents currently trigger an alert advising users to run external OCR or paste text directly.
- **Future Improvement:** Integrate on-device OCR using Tesseract or PyMuPDF's built-in OCR capabilities (`page.get_textpage_ocr()`) to automatically extract selectable text from image-only court orders and notices.

### 14.5 Progressive Web App (PWA) Offline Support
- **Limitation:** The application requires internet connectivity to query Google Gemini and Leaflet tile servers.
- **Future Improvement:** Package Jurista as an installable PWA with offline caching of statutory texts and offline emergency legal contact directories.

---

*Documentation maintained for the Jurista Project. Built for accuracy, accessibility, and transparency under the laws of India.*
