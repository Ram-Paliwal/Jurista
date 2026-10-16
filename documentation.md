# Jurista — AI Indian Legal Assistant & Document Explainer
## Comprehensive Technical Documentation

---

## 1. Executive Summary & Core Purpose

**Jurista** is an artificial intelligence-driven legal information and document analysis platform designed specifically for the **Indian legal framework**. It assists citizens, small business owners, consumers, and litigants by demystifying complex legal terminology, explaining legal documents (notices, petitions, contracts, complaints), and providing step-by-step procedural roadmaps grounded in verified Indian statutes.

### Key Objectives
* **Accessibility & Plain Language:** Translates dense legal notices and statutory provisions into simple, actionable explanations in English, Hindi, and Marathi.
* **Grounded Statutory Accuracy:** Eliminates hallucinations by integrating verified statutory sources from official repositories such as **India Code**, **eCourts**, and **NALSA**.
* **Allegation vs. Fact Distinction:** Enforces a critical legal-ethics rule: claims in an opposing legal notice or complaint are treated strictly as *allegations*, never established facts.
* **Zero-Cost Guardrails:** Employs ultra-fast heuristic pre-filtering to immediately reject non-legal queries without incurring LLM latency or API costs.
* **Resilient Multimodal Architecture:** Utilizes high-performance document extraction via **PyMuPDF**, persistent isolated SQLite session state, dynamic language switching without context loss, and an automatic multi-model failover pipeline across Google Gemini models.

---

## 2. High-Level System Architecture

```mermaid
flowchart TD
    User([User / Browser Client]) -->|HTTP / REST| FastAPI[FastAPI Backend - main.py]
    
    subgraph Client Layer [Frontend / Static]
        HTML[index.html - Accessible UI]
        CSS[style.css - Glassmorphism & Responsive Design]
        JS[app.js - State, Upload & Speech Engine]
    end
    
    subgraph Ingestion & Session Layer
        PDF[pdf_parser.py - PyMuPDF & Scanned Detection]
        SESS[(jurista_sessions.db - SQLite SessionStore)]
    end
    
    subgraph Intelligence & Retrieval Layer
        ORCH[graph.py - LangGraph State Orchestrator]
        FILTER[Heuristic Pre-filter - Scope Guardrail]
        STAT_DB[legal_db.py - Curated Indian Statutes]
        DOC_RAG[rag_engine.py - Local Document RAG]
        PROMPTS[prompts.py - Allegations & Multilingual Templates]
    end
    
    subgraph LLM Provider Layer
        CLIENT[gemini_client.py - GeminiClient Wrapper]
        M1[Primary: gemini-3.5-flash]
        M2[Fallback 1: gemini-3.5-flash-lite]
        M3[Fallback 2: gemini-3.6-flash]
        M4[Fallback 3: gemma-4-31b-it]
    end

    User <--> Client Layer
    Client Layer -->|POST /api/chat| FastAPI
    Client Layer -->|POST /api/upload-pdf| FastAPI
    
    FastAPI --> SESS
    FastAPI --> PDF
    FastAPI --> ORCH
    
    ORCH --> FILTER
    ORCH --> STAT_DB
    ORCH --> DOC_RAG
    ORCH --> PROMPTS
    ORCH --> CLIENT
    
    CLIENT --> M1
    M1 -.->|503 or 404 Failover| M2
    M2 -.->|Failover| M3
    M3 -.->|Failover| M4
```

---

## 3. Complete Directory & File Manifest

| File / Folder | Purpose | Key Responsibilities & Technologies |
| :--- | :--- | :--- |
| **`main.py`** | Application Entrypoint & REST API | FastAPI application, CORS middleware, API endpoint definitions, request validation, static file routing. |
| **`gemini_client.py`** | Google GenAI SDK Wrapper | Manages API communication, implements regex/keyword heuristic pre-check, and provides automatic model failovers. |
| **`graph.py`** | LangGraph Orchestration Pipeline | Implements `StateGraph` state-machine for intent routing (`LEGAL_QUERY`, `DOCUMENT_EXPLAIN`, `DOCUMENT_FOLLOWUP`, `OUT_OF_SCOPE`). |
| **`legal_db.py`** | Indian Statutory Knowledge Base | Curated catalog of major Indian statutes (NI Act, CPA 2019, BNSS 2023, BNS 2023, RERA, RTI, NALSA). |
| **`rag_engine.py`** | Local Document RAG Engine | Text chunking, tokenization, BM25-style lexical scoring, and page-tagged document retrieval. |
| **`pdf_parser.py`** | PDF Document Processor | PyMuPDF text extraction, character thresholds for scanned document detection, page/size safety limits. |
| **`session_store.py`** | SQLite Session State Store | Thread-safe database management for multi-turn conversations, active document attachments, and language settings. |
| **`prompts.py`** | Master Prompt Library | Master system instruction, statutory citation formatting, allegation caution rules, and multilingual templates. |
| **`jurista_sessions.db`** | SQLite Database File | Embedded storage containing `sessions` and `messages` tables. |
| **`test_system.py`** | End-to-End Test Suite | Automated verification testing 8 core workflows (health, filtering, Q&A, upload, follow-ups, language switch, scanned handling). |
| **`requirements.txt`** | Dependency Manifest | Pinned Python packages required to run the backend and testing tools. |
| **`run.bat`** | Windows One-Click Launcher | Automatically checks Python, verifies `.env`, opens the browser, and launches the server. |
| **`.env` / `.env.example`** | Environment Variables | Holds `GEMINI_API_KEY`, `GEMINI_MODEL`, `PORT`, and `HOST`. |
| **`static/index.html`** | Web Application Frontend | Modern, semantic, accessible HTML5 layout with legal notice viewer, chat stream, and disclaimer badges. |
| **`static/style.css`** | Design System & Styling | Modern CSS styling, glassmorphism, responsive flex/grid layouts, custom scrollbars, typography via Google Fonts. |
| **`static/app.js`** | Frontend Logic & State | Client UUID session management, Drag-and-Drop file uploads, markdown parsing, and Web Speech API synthesis. |

---

## 4. In-Depth Component Analysis

### 4.1. Fast Heuristic Pre-Filter (`gemini_client.py`)
To prevent unnecessary API latency and conserve token quotas, every query first passes through an instantaneous heuristic pre-check:
1. **Legal Whitelist Bypass:** If the query contains words like `law`, `court`, `act`, `section`, `cheque`, `fir`, `bail`, `rera`, `bns`, `bnss`, `police`, `advocate`, or their Hindi/Marathi equivalents (`कायदा`, `अदालत`, `तक्रार`), it immediately bypasses the filter and proceeds to legal analysis.
2. **Out-of-Scope Regex Matching:** Queries matching patterns for code generation (Python, Java, CSS), cooking recipes, sports fixtures, pure arithmetic, riddles, or weather forecasts are instantly flagged as `OUT_OF_SCOPE` with zero LLM API invocation.
3. **Graceful Polite Rejection:** Out-of-scope queries receive an immediate polite refusal in the active language informing the user that Jurista is dedicated solely to Indian legal information.

### 4.2. Multi-Model Resilient Fallback Engine (`gemini_client.py`)
To handle model deprecations (such as legacy Gemini 1.5/2.5 series) and transient high-demand spikes (HTTP 503 errors), the `GeminiClient` maintains an automated fallback chain:
* **Primary Target:** Configured via `GEMINI_MODEL` (defaults to `gemini-3.5-flash`).
* **Fallback Priority Queue:**
  1. `gemini-3.5-flash`
  2. `gemini-3.5-flash-lite`
  3. `gemini-3.6-flash`
  4. `gemma-4-31b-it`
* **Handling:** If a candidate returns a `503 UNAVAILABLE` or `404 NOT_FOUND`, the client logs the fallback and transparently queries the next active model in sequence without interrupting the user.

### 4.3. Document Ingestion & PyMuPDF Parsing (`pdf_parser.py`)
Legal documents in India frequently include scanned orders, poorly aligned summons, or large petitions:
* **Size & Page Guardrails:** Rejects files exceeding `15 MB` or `50 pages` to protect memory and runtime limits.
* **Extraction Engine:** Uses `pymupdf` (Fitz) to iterate over document pages, inserting structural delimiters (`--- [Page X] ---`) to track source page numbers for all extracted clauses.
* **Scanned PDF Heuristic:** If a multi-page document yields fewer than 50 total textual characters, it is classified with `is_scanned: true`. Rather than failing silently, Jurista generates a structured explanation highlighting that the file appears to be a scanned image and provides practical instructions on how the user can proceed (such as converting via OCR).

### 4.4. Local Document RAG Engine (`rag_engine.py`)
* **Chunking Strategy:** Splits documents into overlapping segments (`750 characters` per chunk, with `120 characters` overlap) while respecting paragraph and sentence boundaries.
* **Lexical Retrieval:** Normalizes queries and chunks across alphanumeric and Devanagari Unicode scripts (`\u0900-\u097F`). Computes term frequency scores normalized by chunk length to return the top 3-4 most relevant segments.
* **Context Isolation:** Document chunks are kept strictly segregated from statutory sources in the prompt, preventing confusion between private contractual terms and general statutory law.

### 4.5. Curated Indian Statutory Knowledge Base (`legal_db.py`)
Jurista maintains a verified statutory repository that covers frequently encountered citizen legal issues:
* **Negotiable Instruments Act, 1881:**
  * *Section 138:* Dishonour of cheques for insufficiency of funds, mandatory 30-day notice rule, 15-day cure window, and 1-month filing limitation under Section 142.
  * *Section 141:* Vicarious liability of company directors.
* **Consumer Protection Act, 2019:**
  * *Section 2(11) & Section 35:* Deficiency in goods and services, e-Daakhil filing, pecuniary jurisdiction (District Commissions up to ₹50 Lakhs), 2-year limitation.
* **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) & CrPC:**
  * *BNSS Section 173 (CrPC 154):* Registration of cognizable offences, Zero FIR, free copy entitlement, appeals to SP under 173(4), and Section 175(3) magistrate applications.
  * *BNSS Section 35 (CrPC 41A):* Mandatory Notice of Appearance for offences punishable by under 7 years imprisonment.
* **Bharatiya Nyaya Sanhita, 2023 (BNS) & IPC:**
  * *BNS Section 303 (IPC 379):* Theft definitions and statutory penalties.
  * *BNS Section 318 (IPC 420):* Cheating and dishonestly inducing delivery of property.
* **Real Estate (Regulation and Development) Act, 2016 (RERA):**
  * *Sections 18 & 31:* Delayed possession, interest remedies, and filing complaints before the Real Estate Regulatory Authority.
* **Right to Information Act, 2005 (RTI):**
  * *Sections 6 & 7:* Application filing, ₹10 fee, 30-day response deadline (48 hours if life and liberty are at stake), first and second appeals.
* **Legal Services Authorities Act, 1987 (NALSA):**
  * *Section 12:* Entitlement to free legal aid for women, children, SC/ST, custody undertrials, and low-income individuals via DLSA/SLSA (Helpline: 15100).

### 4.6. Multi-Turn Session Store (`session_store.py`)
State is maintained in an embedded, thread-safe SQLite database (`jurista_sessions.db`):
* **`sessions` Table:** Stores `session_id` (UUID), active `language` (English, Hindi, Marathi), timestamps, and serialized `document_json` (containing full text, page count, and chunk index).
* **`messages` Table:** Stores individual turn messages, message role (`user` or `assistant`), route classification, cited sources, and timestamps.
* **Dynamic Language Switching:** When a user switches languages (via the dropdown in the UI), `SessionStore.set_language()` updates the session preference without clearing document chunks or prior message history. Future responses seamlessly adapt to the newly chosen language while retaining context.

### 4.7. Orchestration & StateGraph (`graph.py`)
Uses the LangGraph `StateGraph` pattern to execute the turn pipeline:
```
[START]
   │
   ▼
route_intent_node ──(OUT_OF_SCOPE)──────► [END]
   │
   ├──(CLARIFICATION_NEEDED)───────────► clarification_node ──────► [END]
   │
   ├──(DOCUMENT_EXPLAIN)───────────────► document_explain_node ──► [END]
   │
   ├──(DOCUMENT_FOLLOWUP)──────────────► document_followup_node ─► [END]
   │
   └──(LEGAL_QUERY)────────────────────► legal_qa_node ──────────► [END]
```

### 4.8. Frontend Architecture & Design System (`static/`)
Built with semantic HTML5, Vanilla CSS, and modular Vanilla JavaScript:
* **Visual Styling:** Sleek dark-mode aesthetic utilizing rich slate-indigo backgrounds, glassmorphism (`backdrop-filter: blur(12px)`), smooth CSS transitions, and Google Fonts (**Outfit** for headings and **Plus Jakarta Sans** for body copy).
* **Document Inspector Sidebar:** Dedicated drawer displaying uploaded file status, total pages, character counts, chunk density, and scanned warnings.
* **Statutory Citation Badges:** Live citations are rendered as interactive, pill-shaped tags linking directly to official statutory resources (e.g., India Code).
* **Text-to-Speech Accessibility:** Integrated with the browser's native **Web Speech API** to allow citizens to listen to legal explanations read aloud in English, Hindi, or Marathi.

---

## 5. REST API Specification

### 5.1. Health Check
* **Endpoint:** `GET /api/health`
* **Purpose:** Verify server responsiveness, Gemini API key configuration, and active model.
* **Response Sample:**
```json
{
  "status": "healthy",
  "service": "Jurista",
  "gemini_configured": true,
  "model": "gemini-3.5-flash"
}
```

### 5.2. Get Session Details
* **Endpoint:** `GET /api/session/{session_id}`
* **Purpose:** Retrieve active session state, current language, active document metadata, and chat history.
* **Response Sample:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "language": "English",
  "document": {
    "filename": "Legal_Demand_Notice.pdf",
    "page_count": 2,
    "total_characters": 1840,
    "is_scanned": false,
    "chunk_count": 3
  },
  "messages": [
    {"role": "user", "content": "What is the notice about?"},
    {"role": "assistant", "content": "The notice alleges...", "route": "DOCUMENT_FOLLOWUP"}
  ]
}
```

### 5.3. Switch Session Language
* **Endpoint:** `POST /api/session/language`
* **Request Body:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "language": "Hindi"
}
```
* **Response Sample:**
```json
{
  "success": true,
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "language": "Hindi"
}
```

### 5.4. Clear Session
* **Endpoint:** `POST /api/session/clear`
* **Request Body:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

### 5.5. Send Legal Message
* **Endpoint:** `POST /api/chat`
* **Request Body:**
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "I received a cheque bounce notice for Rs. 50,000. What is my deadline to pay?",
  "language": "English"
}
```
* **Response Sample:**
```json
{
  "response": "Under Section 138 of the Negotiable Instruments Act, 1881...",
  "intent": "LEGAL_QUERY",
  "is_out_of_scope": false,
  "sources": [
    {
      "id": "ni_act_138",
      "act": "Negotiable Instruments Act, 1881",
      "section": "Section 138",
      "title": "Dishonour of Cheque for Insufficiency of Funds",
      "official_url": "https://www.indiacode.nic.in/handle/123456789/2189"
    }
  ],
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "language": "English"
}
```

### 5.6. Upload Legal PDF
* **Endpoint:** `POST /api/upload-pdf`
* **Content-Type:** `multipart/form-data`
* **Parameters:**
  * `file`: Binary PDF document
  * `session_id`: Client UUID string
  * `language`: Optional language string (e.g., `English`)
* **Response Sample:**
```json
{
  "success": true,
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "filename": "Demand_Notice.pdf",
  "page_count": 1,
  "total_characters": 750,
  "is_scanned": false,
  "chunk_count": 1,
  "explanation": "🔍 **Situation Summary**\nThe uploaded document is a legal demand notice issued by Advocate...",
  "message": "PDF analyzed successfully with 1 pages."
}
```

---

## 6. End-to-End Test Suite (`test_system.py`)

Jurista includes an automated verification script that executes 8 full lifecycle tests against the running system:

1. **Test 1: Health Check:** Validates that the FastAPI backend is operational and `gemini_configured` is true.
2. **Test 2: Heuristic Scope Filter:** Sends a Python scraping prompt; asserts `is_out_of_scope == True` without invoking the LLM.
3. **Test 3: Statutory Legal Q&A:** Queries Section 138 NI Act rights; verifies that statutory citations are retrieved and cited.
4. **Test 4: PDF Generation & Extraction:** Generates an in-memory legal demand notice via PyMuPDF, uploads it via multipart form, and verifies page chunking and automated situation summary generation.
5. **Test 5: Context Retention Follow-up:** Asks a follow-up question referencing the uploaded notice ("Who is the sender?"); verifies that the response accurately identifies the parties and claimed amounts.
6. **Test 6: In-Flight Language Switching:** Changes the active session language to Hindi via `/api/session/language`; verifies that the uploaded document and message history remain intact.
7. **Test 7: Multilingual Response Generation:** Asks a follow-up question in Hindi; verifies that the system responds accurately in Devanagari Hindi while preserving statutory terms.
8. **Test 8: Scanned PDF Graceful Handling:** Generates an image-only/blank PDF; verifies that `is_scanned == True` is returned with appropriate guidance.

To run the verification test suite:
```bash
python test_system.py
```

---

## 7. Installation, Setup & Local Execution Guide

### 7.1. Prerequisites
* **Operating System:** Windows 10/11, macOS, or Linux.
* **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14.
* **Google Gemini API Key:** Obtainable from [Google AI Studio](https://aistudio.google.com/).

### 7.2. Setup Instructions

1. **Clone or Navigate to the Workspace Directory:**
   ```cmd
   cd /d "e:\Jurista"
   ```

2. **Configure Environment Variables:**
   Copy `.env.example` to `.env` if not already present:
   ```cmd
   copy .env.example .env
   ```
   Open `.env` and set your API key:
   ```env
   GEMINI_API_KEY=AIzaSy...YourKeyHere...
   GEMINI_MODEL=gemini-3.5-flash
   PORT=8000
   HOST=127.0.0.1
   ```

3. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Launch the Application:**
   * **Option A (One-Click Windows Launcher):**
     Double-click `run.bat` or run:
     ```cmd
     run.bat
     ```
   * **Option B (Direct Python Command):**
     ```cmd
     python main.py
     ```

5. **Access the Web Interface:**
   Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

---

## 8. Ethical Guardrails, Compliance & Disclaimers

### 8.1. Bar Council of India Compliance
Under the Advocates Act, 1961 and the Bar Council of India Rules, legal solicitation and automated provision of legal representation are strictly regulated. Jurista adheres to the following principles:
* **Legal Information vs. Legal Advice:** Jurista explicitly identifies itself as an informational guide and research assistant. It does not create an attorney-client relationship.
* **Persistent Disclaimers:** Every generated output carries prominent notices stating that legal situations vary by jurisdiction and that users should consult a qualified advocate or their local Legal Services Authority (DLSA/SLSA).

### 8.2. Allegation Protection
Legal demand notices, FIR complaints, and eviction notices represent unilateral claims by opposing parties. Jurista's prompts are explicitly instructed to:
* Avoid accepting statements in user-uploaded documents as proven facts.
* Use neutral, cautious language (e.g., *"The notice claims..."*, *"The document alleges..."*).
* Prevent unwarranted alarm or panic by clarifying that notices are preliminary claims requiring an objective legal response.

### 8.3. Citizen Rights & Free Legal Aid
Jurista proactively informs eligible citizens (such as economically weaker sections, women, children, and undertrial prisoners) about their statutory entitlement to free legal aid under Section 12 of the Legal Services Authorities Act, 1987, referencing the national **NALSA helpline: 15100**.

---

*Documentation maintained for the Jurista Project. Built for accuracy, accessibility, and transparency under the laws of India.*
