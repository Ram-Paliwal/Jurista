/**
 * Jurista — Frontend Application Controller
 * Pure Vanilla JavaScript implementation.
 * Integrates:
 * - Legal Q&A Chatbot with Scope Enforcement & Indian Statutory Grounding
 * - PDF Document Explainer (PyMuPDF)
 * - Multilingual Voice Recognition (Web Speech API) & Speech Synthesis
 * - Community Experiences Interactive Map (Leaflet.js + OSM tiles + MarkerCluster)
 * - Synchronized Community Feed & Filtering (Topic, Date, Search, Location)
 * - Safe Approximate Location Picker for Citizen Reports
 * - Strictly Isolated Private Evidence Vault
 */

(function () {
  "use strict";

  // -------------------------------------------------------------
  // Application State
  // -------------------------------------------------------------
  let sessionId = localStorage.getItem("jurista_session_id");
  if (!sessionId) {
    sessionId = "jurista-" + crypto.randomUUID();
    localStorage.setItem("jurista_session_id", sessionId);
  }

  let currentLanguage = localStorage.getItem("jurista_language") || "English";
  let activeDocument = null;
  let isProcessing = false;

  // Web Speech API Configuration & State
  const LANGUAGE_LOCALES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Marathi": "mr-IN"
  };

  const LANGUAGE_DISPLAY = {
    "English": "English (en-IN)",
    "Hindi": "Hindi (हिंदी, hi-IN)",
    "Marathi": "Marathi (मराठी, mr-IN)"
  };

  let recognition = null;
  let isRecording = false;
  let recognitionBaseText = "";

  // Community Map & Reports State
  let communityMap = null;
  let markersClusterGroup = null;
  let reportMarkersMap = new Map(); // report_id -> { marker, report }
  let allCommunityReports = [];
  let filteredCommunityReports = [];
  let activeReportId = null;
  let communityLayoutMode = "split"; // 'split', 'map', 'feed'

  // Location Picker State
  let pickerMap = null;
  let pickerMarker = null;
  let selectedPickerLat = null;
  let selectedPickerLon = null;

  // -------------------------------------------------------------
  // DOM Elements
  // -------------------------------------------------------------
  // Navigation Tabs
  const navBtnChat = document.getElementById("nav-btn-chat");
  const navBtnCommunity = document.getElementById("nav-btn-community");
  const navBtnVault = document.getElementById("nav-btn-vault");
  const viewChat = document.getElementById("view-chat");
  const viewCommunity = document.getElementById("view-community");
  const viewVault = document.getElementById("view-vault");

  // Chat Elements
  const chatMessagesEl = document.getElementById("chat-messages");
  const chatFormEl = document.getElementById("chat-form");
  const userInputEl = document.getElementById("user-input");
  const btnSendEl = document.getElementById("btn-send");
  const btnAttachEl = document.getElementById("btn-attach");
  const btnMicEl = document.getElementById("btn-mic");
  const voiceIndicatorEl = document.getElementById("voice-indicator");
  const voiceStatusTextEl = document.getElementById("voice-status-text");
  const btnStopVoiceEl = document.getElementById("btn-stop-voice");
  const langSelectEl = document.getElementById("lang-select");
  const btnNewSessionEl = document.getElementById("btn-new-session");

  // PDF Sidebar Elements
  const dropzoneEl = document.getElementById("dropzone");
  const fileInputEl = document.getElementById("file-input");
  const uploadLoaderEl = document.getElementById("upload-loader");
  const docStatusBadgeEl = document.getElementById("doc-status-badge");
  const activeDocDetailsEl = document.getElementById("active-doc-details");
  const docFilenameEl = document.getElementById("doc-filename");
  const docPagesEl = document.getElementById("doc-pages");
  const docCharsEl = document.getElementById("doc-chars");
  const docChunksEl = document.getElementById("doc-chunks");
  const scannedWarningEl = document.getElementById("scanned-warning");
  const btnRemoveDocEl = document.getElementById("btn-remove-doc");
  const btnReExplainEl = document.getElementById("btn-re-explain");
  const chipBtns = document.querySelectorAll(".chip-btn");

  // Community Feed & Map Elements
  const communityWorkspaceEl = document.getElementById("community-workspace");
  const communitySearchInput = document.getElementById("community-search");
  const communityTopicFilter = document.getElementById("community-topic-filter");
  const communityDateFilter = document.getElementById("community-date-filter");
  const communityHasLocationToggle = document.getElementById("community-has-location-toggle");
  const btnViewSplit = document.getElementById("btn-view-split");
  const btnViewMap = document.getElementById("btn-view-map");
  const btnViewFeed = document.getElementById("btn-view-feed");
  const btnRefreshReports = document.getElementById("btn-refresh-reports");
  const feedCountBadge = document.getElementById("feed-count-badge");
  const communityReportsList = document.getElementById("community-reports-list");
  const communityEmptyState = document.getElementById("community-empty-state");
  const btnClearFilters = document.getElementById("btn-clear-filters");
  const mapLoadingEl = document.getElementById("map-loading");
  const mapErrorNoticeEl = document.getElementById("map-error-notice");
  const btnRetryMap = document.getElementById("btn-retry-map");
  const btnCenterIndia = document.getElementById("btn-center-india");
  const mapActiveReportBanner = document.getElementById("map-active-report-banner");
  const activeBannerTopic = document.getElementById("active-banner-topic");
  const activeBannerTitle = document.getElementById("active-banner-title");
  const activeBannerLocation = document.getElementById("active-banner-location");
  const btnActiveBannerView = document.getElementById("btn-active-banner-view");
  const btnActiveBannerClose = document.getElementById("btn-active-banner-close");

  // Create Report Modal Elements
  const btnOpenCreateReport = document.getElementById("btn-open-create-report");
  const modalCreateReport = document.getElementById("modal-create-report");
  const btnCloseCreateModal = document.getElementById("btn-close-create-modal");
  const btnCancelCreateReport = document.getElementById("btn-cancel-create-report");
  const formCreateReport = document.getElementById("form-create-report");
  const inputReportTitle = document.getElementById("input-report-title");
  const selectReportTopic = document.getElementById("select-report-topic");
  const inputIncidentDate = document.getElementById("input-incident-date");
  const inputReportDesc = document.getElementById("input-report-desc");
  const chkIncludeLocation = document.getElementById("chk-include-location");
  const locationPickerPanel = document.getElementById("location-picker-panel");
  const inputLocalitySearch = document.getElementById("input-locality-search");
  const btnSearchLocality = document.getElementById("btn-search-locality");
  const localitySearchResults = document.getElementById("locality-search-results");
  const inputApproxLocationName = document.getElementById("input-approx-location-name");
  const badgeSelectedCoords = document.getElementById("badge-selected-coords");
  const btnRemoveLocation = document.getElementById("btn-remove-location");
  const chkIsPublic = document.getElementById("chk-is-public");
  const chkIntegrityConfirm = document.getElementById("chk-integrity-confirm");

  // Report Detail Modal Elements
  const modalReportDetail = document.getElementById("modal-report-detail");
  const btnCloseDetailModal = document.getElementById("btn-close-detail-modal");
  const modalDetailTitle = document.getElementById("modal-detail-title");
  const detailTopicBadge = document.getElementById("detail-topic-badge");
  const detailLocationText = document.getElementById("detail-location-text");
  const detailDateText = document.getElementById("detail-date-text");
  const detailNarrativeContent = document.getElementById("detail-narrative-content");
  const detailRoadmapContent = document.getElementById("detail-roadmap-content");
  const btnDetailShowMap = document.getElementById("btn-detail-show-map");
  const btnDetailAskAi = document.getElementById("btn-detail-ask-ai");

  // Evidence Vault Elements
  const vaultItemsList = document.getElementById("vault-items-list");
  const vaultEmptyState = document.getElementById("vault-empty-state");
  const btnOpenAddVault = document.getElementById("btn-open-add-vault");
  const btnEmptyAddVault = document.getElementById("btn-empty-add-vault");
  const modalAddVault = document.getElementById("modal-add-vault");
  const btnCloseVaultModal = document.getElementById("btn-close-vault-modal");
  const btnCancelVault = document.getElementById("btn-cancel-vault");
  const formAddVault = document.getElementById("form-add-vault");
  const inputVaultTitle = document.getElementById("input-vault-title");
  const selectVaultType = document.getElementById("select-vault-type");
  const inputVaultDesc = document.getElementById("input-vault-desc");
  const inputVaultLoc = document.getElementById("input-vault-loc");

  // -------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------
  function init() {
    langSelectEl.value = currentLanguage;
    if (btnMicEl) {
      btnMicEl.title = `Voice Input (${LANGUAGE_DISPLAY[currentLanguage] || currentLanguage})`;
    }
    loadSession();
    bindEvents();
    autoResizeTextarea();
    setupNavigationTabs();
    setupCommunityFeedAndMap();
    setupCreateReportModal();
    setupReportDetailModal();
    setupEvidenceVault();
  }

  // -------------------------------------------------------------
  // Navigation Tabs Switcher
  // -------------------------------------------------------------
  function setupNavigationTabs() {
    const tabs = [
      { btn: navBtnChat, view: viewChat, id: "chat" },
      { btn: navBtnCommunity, view: viewCommunity, id: "community" },
      { btn: navBtnVault, view: viewVault, id: "vault" }
    ];

    tabs.forEach(({ btn, view, id }) => {
      btn.addEventListener("click", () => {
        tabs.forEach(t => {
          t.btn.classList.remove("active");
          t.view.classList.add("hidden");
        });
        btn.classList.add("active");
        view.classList.remove("hidden");

        if (id === "community") {
          setTimeout(() => {
            if (!communityMap) {
              initCommunityMap();
            } else {
              communityMap.invalidateSize();
            }
          }, 100);
          if (allCommunityReports.length === 0) {
            loadCommunityReports();
          }
        } else if (id === "vault") {
          loadVaultItems();
        }
      });
    });
  }

  // -------------------------------------------------------------
  // Event Bindings for Chat & PDF (Preserved unchanged)
  // -------------------------------------------------------------
  function bindEvents() {
    chatFormEl.addEventListener("submit", handleChatSubmit);

    userInputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatFormEl.dispatchEvent(new Event("submit"));
      }
    });

    userInputEl.addEventListener("input", autoResizeTextarea);
    langSelectEl.addEventListener("change", handleLanguageChange);
    btnNewSessionEl.addEventListener("click", handleNewSession);

    if (btnMicEl) {
      btnMicEl.addEventListener("click", toggleVoiceRecognition);
    }
    if (btnStopVoiceEl) {
      btnStopVoiceEl.addEventListener("click", stopVoiceRecognition);
    }

    btnAttachEl.addEventListener("click", () => fileInputEl.click());
    dropzoneEl.addEventListener("click", (e) => {
      if (e.target !== fileInputEl) fileInputEl.click();
    });

    fileInputEl.addEventListener("change", handleFileSelected);

    dropzoneEl.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzoneEl.classList.add("dragover");
    });

    dropzoneEl.addEventListener("dragleave", () => {
      dropzoneEl.classList.remove("dragover");
    });

    dropzoneEl.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzoneEl.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadPdfFile(e.dataTransfer.files[0]);
      }
    });

    btnRemoveDocEl.addEventListener("click", handleRemoveDocument);

    btnReExplainEl.addEventListener("click", () => {
      if (activeDocument) {
        sendMessage(`Please explain this legal document again with focus on deadlines and practical roadmap: ${activeDocument.filename}`);
      }
    });

    chipBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const query = btn.getAttribute("data-query");
        if (query) {
          userInputEl.value = query;
          autoResizeTextarea();
          userInputEl.focus();
        }
      });
    });
  }

  function autoResizeTextarea() {
    userInputEl.style.height = "auto";
    userInputEl.style.height = Math.min(userInputEl.scrollHeight, 140) + "px";
  }

  async function loadSession() {
    try {
      const res = await fetch(`/api/session/${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.language) {
        currentLanguage = data.language;
        langSelectEl.value = currentLanguage;
      }

      if (data.document) {
        renderActiveDocument(data.document);
      } else {
        resetDocumentUI();
      }

      if (data.messages && data.messages.length > 0) {
        renderHistoryMessages(data.messages);
      }
    } catch (err) {
      console.warn("Could not load session history:", err);
    }
  }

  async function handleLanguageChange(e) {
    const newLang = e.target.value;
    currentLanguage = newLang;
    localStorage.setItem("jurista_language", newLang);

    if (isRecording) {
      stopVoiceRecognition();
    }
    if (btnMicEl) {
      btnMicEl.title = `Voice Input (${LANGUAGE_DISPLAY[currentLanguage] || currentLanguage})`;
    }

    try {
      await fetch("/api/session/language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, language: newLang })
      });

      appendAssistantMessage(
        `Language switched to **${newLang}**. All subsequent answers and document explanations will be delivered in ${newLang}.`
      );
    } catch (err) {
      console.error("Language switch error:", err);
    }
  }

  async function handleNewSession() {
    if (!confirm("Are you sure you want to start a new session? This will clear current chat history and document context.")) {
      return;
    }

    stopVoiceRecognition();

    try {
      await fetch("/api/session/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (e) {
      // ignore
    }

    sessionId = "jurista-" + crypto.randomUUID();
    localStorage.setItem("jurista_session_id", sessionId);

    chatMessagesEl.innerHTML = "";
    resetDocumentUI();
    activeDocument = null;

    appendAssistantMessage(
      "A new session has started. Previous conversation history and active documents have been reset. How may I assist you with Indian law today?"
    );
  }

  function handleFileSelected(e) {
    if (e.target.files && e.target.files.length > 0) {
      uploadPdfFile(e.target.files[0]);
    }
  }

  async function uploadPdfFile(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a valid PDF legal document (.pdf).");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      alert("File size exceeds 15 MB limit. Please upload a smaller document.");
      return;
    }

    uploadLoaderEl.classList.remove("hidden");
    const dropContent = dropzoneEl.querySelector(".dropzone-content");
    if (dropContent) dropContent.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);
    formData.append("language", currentLanguage);

    appendUserMessage(`Uploaded document: **${escapeHtml(file.name)}** (${(file.size / 1024).toFixed(1)} KB)`);
    const loadingCard = appendLoadingMessage("Extracting text via PyMuPDF & generating structured explanation...");

    try {
      const res = await fetch("/api/upload-pdf", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      removeMessageCard(loadingCard);

      if (!res.ok || !data.success) {
        appendAssistantMessage(`❌ **Document Analysis Failed:** ${data.message || data.detail || "Unable to parse PDF."}`);
        resetDocumentUI();
        return;
      }

      renderActiveDocument({
        filename: data.filename,
        page_count: data.page_count,
        total_characters: data.total_characters,
        is_scanned: data.is_scanned,
        chunk_count: data.chunk_count
      });

      appendAssistantMessage(data.explanation, {
        route: "DOCUMENT_EXPLAIN",
        sources: []
      });

    } catch (err) {
      removeMessageCard(loadingCard);
      appendAssistantMessage(`❌ **Upload Error:** Failed to communicate with server: ${err.message}`);
      resetDocumentUI();
    } finally {
      uploadLoaderEl.classList.add("hidden");
      if (dropContent) dropContent.classList.remove("hidden");
      fileInputEl.value = "";
    }
  }

  function renderActiveDocument(doc) {
    activeDocument = doc;
    docFilenameEl.textContent = doc.filename;
    docPagesEl.textContent = `${doc.page_count} Pages`;
    docCharsEl.textContent = `${doc.total_characters.toLocaleString()} Chars`;
    docChunksEl.textContent = `${doc.chunk_count} RAG Chunks`;

    docStatusBadgeEl.textContent = "Active PDF";
    docStatusBadgeEl.className = "badge badge-primary";

    if (doc.is_scanned) {
      scannedWarningEl.classList.remove("hidden");
    } else {
      scannedWarningEl.classList.add("hidden");
    }

    activeDocDetailsEl.classList.remove("hidden");
    dropzoneEl.classList.add("has-active-doc");
  }

  function resetDocumentUI() {
    activeDocument = null;
    docStatusBadgeEl.textContent = "No PDF";
    docStatusBadgeEl.className = "badge badge-neutral";
    activeDocDetailsEl.classList.add("hidden");
    scannedWarningEl.classList.add("hidden");
    dropzoneEl.classList.remove("has-active-doc");
  }

  async function handleRemoveDocument() {
    if (!confirm("Remove the active PDF document from this session?")) return;
    try {
      await fetch("/api/session/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      resetDocumentUI();
      appendAssistantMessage("Active document removed. You can upload a new PDF anytime.");
    } catch (err) {
      console.error(err);
    }
  }

  function handleChatSubmit(e) {
    e.preventDefault();
    if (isProcessing) return;

    const message = userInputEl.value.trim();
    if (!message) return;

    userInputEl.value = "";
    autoResizeTextarea();
    sendMessage(message);
  }

  async function sendMessage(text) {
    if (isProcessing) return;
    isProcessing = true;
    btnSendEl.disabled = true;

    appendUserMessage(text);
    const loadingCard = appendLoadingMessage("Analyzing statutory sources and drafting grounded response...");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          language: currentLanguage
        })
      });

      const data = await res.json();
      removeMessageCard(loadingCard);

      if (!res.ok) {
        appendAssistantMessage(`⚠️ **Error:** ${data.detail || "Server failed to process query."}`);
        return;
      }

      appendAssistantMessage(data.response, {
        intent: data.intent,
        sources: data.sources || [],
        is_out_of_scope: data.is_out_of_scope
      });

    } catch (err) {
      removeMessageCard(loadingCard);
      appendAssistantMessage(`⚠️ **Network Error:** Could not contact Jurista server. Please ensure the backend is running.`);
    } finally {
      isProcessing = false;
      btnSendEl.disabled = false;
      userInputEl.focus();
    }
  }

  function appendUserMessage(text) {
    const card = document.createElement("div");
    card.className = "message-card message-user";
    card.innerHTML = `
      <div class="message-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-header-row">
          <span class="sender-name">You</span>
          <span class="message-time">${getCurrentTime()}</span>
        </div>
        <div class="message-text">
          <p>${escapeHtml(text)}</p>
        </div>
      </div>
    `;
    chatMessagesEl.appendChild(card);
    scrollToBottom();
  }

  function appendAssistantMessage(markdownText, meta = {}) {
    const card = document.createElement("div");
    card.className = "message-card message-jurista";

    let sourcesHtml = "";
    if (meta.sources && meta.sources.length > 0) {
      sourcesHtml = `
        <div class="sources-pill-box">
          <span class="sources-pill-label">Verified Authorities:</span>
          <div class="sources-pills-list">
            ${meta.sources.map(s => `
              <a href="${s.url}" target="_blank" rel="noopener" class="source-citation-chip" title="${escapeHtml(s.key_takeaway || s.title)}">
                <span>§ ${escapeHtml(s.section)} (${escapeHtml(s.act)})</span>
                <span class="chip-arrow">&nearr;</span>
              </a>
            `).join("")}
          </div>
        </div>
      `;
    }

    let outOfScopeNotice = "";
    if (meta.is_out_of_scope) {
      outOfScopeNotice = `
        <div class="scope-rejection-banner">
          <span class="scope-tag">Out of Scope Filter</span>
          <span>Zero-cost prefilter redirected this request to protect legal scope boundaries.</span>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="message-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
          <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
          <path d="M7 21h10"/>
          <path d="M12 3v18"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-header-row">
          <span class="sender-name">Jurista</span>
          <div class="message-actions-row">
            <span class="message-time">${getCurrentTime()}</span>
            <button class="btn-tts" title="Listen to answer (Speech playback)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
              </svg>
            </button>
          </div>
        </div>
        ${outOfScopeNotice}
        <div class="message-text">
          ${renderMarkdown(markdownText)}
        </div>
        ${sourcesHtml}
      </div>
    `;

    const ttsBtn = card.querySelector(".btn-tts");
    if (ttsBtn) {
      ttsBtn.addEventListener("click", () => playTextToSpeech(markdownText, ttsBtn));
    }

    chatMessagesEl.appendChild(card);
    scrollToBottom();
  }

  function appendLoadingMessage(label) {
    const card = document.createElement("div");
    card.className = "message-card message-jurista loading-card";
    card.innerHTML = `
      <div class="message-avatar">
        <div class="spinner-small"></div>
      </div>
      <div class="message-body">
        <div class="message-text">
          <p class="loading-label">${escapeHtml(label)}</p>
        </div>
      </div>
    `;
    chatMessagesEl.appendChild(card);
    scrollToBottom();
    return card;
  }

  function removeMessageCard(card) {
    if (card && card.parentNode) {
      card.parentNode.removeChild(card);
    }
  }

  function renderHistoryMessages(messages) {
    messages.forEach(m => {
      if (m.role === "user") {
        appendUserMessage(m.content);
      } else {
        appendAssistantMessage(m.content, {
          route: m.route,
          sources: m.sources || []
        });
      }
    });
  }

  function playTextToSpeech(text, btnElement) {
    if (!("speechSynthesis" in window)) {
      alert("Text-to-speech audio playback is not supported by your browser.");
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      btnElement.classList.remove("speaking");
      return;
    }

    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#+\s/g, "")
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = LANGUAGE_LOCALES[currentLanguage] || "en-IN";
    utterance.rate = 1.0;

    btnElement.classList.add("speaking");

    utterance.onend = () => btnElement.classList.remove("speaking");
    utterance.onerror = () => btnElement.classList.remove("speaking");

    window.speechSynthesis.speak(utterance);
  }

  // Multilingual Web Speech API (Voice Recognition)
  function toggleVoiceRecognition() {
    if (isRecording) {
      stopVoiceRecognition();
    } else {
      startVoiceRecognition();
    }
  }

  function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    try {
      recognition = new SpeechRecognition();
    } catch (e) {
      alert("Unable to initialize speech recognition: " + e.message);
      return;
    }

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = LANGUAGE_LOCALES[currentLanguage] || "en-IN";

    recognitionBaseText = userInputEl.value;

    recognition.onstart = () => {
      isRecording = true;
      voiceIndicatorEl.classList.remove("hidden");
      voiceStatusTextEl.textContent = `Listening in ${LANGUAGE_DISPLAY[currentLanguage] || currentLanguage}... Speak now`;
      btnMicEl.classList.add("recording");
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const separator = recognitionBaseText && !recognitionBaseText.endsWith(" ") ? " " : "";
      if (finalTranscript) {
        recognitionBaseText = (recognitionBaseText + separator + finalTranscript).trim();
      }

      userInputEl.value = (recognitionBaseText + (interimTranscript ? " " + interimTranscript : "")).trimStart();
      autoResizeTextarea();
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopVoiceRecognition();
    };

    recognition.onend = () => {
      stopVoiceRecognition();
    };

    try {
      recognition.start();
    } catch (e) {
      console.warn("Speech start failed:", e);
      stopVoiceRecognition();
    }
  }

  function stopVoiceRecognition() {
    isRecording = false;
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {}
      recognition = null;
    }
    if (voiceIndicatorEl) voiceIndicatorEl.classList.add("hidden");
    if (btnMicEl) btnMicEl.classList.remove("recording");
  }

  function scrollToBottom() {
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  }

  function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // -------------------------------------------------------------
  // Community Map & Reports Controller
  // -------------------------------------------------------------
  function setupCommunityFeedAndMap() {
    // Toolbar Filters
    communitySearchInput.addEventListener("input", debounce(applyCommunityFilters, 250));
    communityTopicFilter.addEventListener("change", applyCommunityFilters);
    communityDateFilter.addEventListener("change", applyCommunityFilters);
    communityHasLocationToggle.addEventListener("change", applyCommunityFilters);

    btnClearFilters.addEventListener("click", () => {
      communitySearchInput.value = "";
      communityTopicFilter.value = "All";
      communityDateFilter.value = "all";
      communityHasLocationToggle.checked = false;
      applyCommunityFilters();
    });

    btnRefreshReports.addEventListener("click", () => {
      loadCommunityReports();
    });

    // View Mode Switches
    btnViewSplit.addEventListener("click", () => setLayoutMode("split"));
    btnViewMap.addEventListener("click", () => setLayoutMode("map"));
    btnViewFeed.addEventListener("click", () => setLayoutMode("feed"));

    // Retry map button
    if (btnRetryMap) {
      btnRetryMap.addEventListener("click", () => {
        mapErrorNoticeEl.classList.add("hidden");
        initCommunityMap();
      });
    }

    // Center India / Fit all markers
    if (btnCenterIndia) {
      btnCenterIndia.addEventListener("click", fitAllMarkers);
    }

    // Active Banner dismissal & view
    if (btnActiveBannerClose) {
      btnActiveBannerClose.addEventListener("click", () => {
        mapActiveReportBanner.classList.add("hidden");
        clearActiveReportHighlight();
      });
    }

    if (btnActiveBannerView) {
      btnActiveBannerView.addEventListener("click", () => {
        if (activeReportId) {
          openReportDetailModal(activeReportId);
        }
      });
    }
  }

  function setLayoutMode(mode) {
    communityLayoutMode = mode;
    btnViewSplit.classList.toggle("active", mode === "split");
    btnViewMap.classList.toggle("active", mode === "map");
    btnViewFeed.classList.toggle("active", mode === "feed");

    communityWorkspaceEl.className = `community-workspace layout-${mode}`;

    if (mode !== "feed" && communityMap) {
      setTimeout(() => communityMap.invalidateSize(), 150);
    }
  }

  function initCommunityMap() {
    if (typeof L === "undefined") {
      console.warn("Leaflet library not loaded");
      mapErrorNoticeEl.classList.remove("hidden");
      return;
    }

    if (communityMap) return;

    try {
      // Default centered on India with reasonable zoom
      communityMap = L.map("community-map", {
        center: [21.5937, 78.9629],
        zoom: 5,
        minZoom: 3,
        maxZoom: 18,
        zoomControl: true
      });

      const tileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
      });

      tileLayer.on("tileerror", function () {
        mapErrorNoticeEl.classList.remove("hidden");
      });

      tileLayer.on("load", function () {
        mapErrorNoticeEl.classList.add("hidden");
      });

      tileLayer.addTo(communityMap);

      // Marker Cluster Group
      if (typeof L.markerClusterGroup !== "undefined") {
        markersClusterGroup = L.markerClusterGroup({
          showCoverageOnHover: false,
          maxClusterRadius: 40,
          spiderfyOnMaxZoom: true,
          iconCreateFunction: function (cluster) {
            const count = cluster.getChildCount();
            let c = "small";
            if (count > 5) c = "medium";
            if (count > 15) c = "large";
            return L.divIcon({
              html: `<div><span>${count}</span></div>`,
              className: `marker-cluster marker-cluster-${c}`,
              iconSize: L.point(40, 40)
            });
          }
        });
        communityMap.addLayer(markersClusterGroup);
      }

      loadCommunityReports();

    } catch (err) {
      console.error("Map initialization failed:", err);
      mapErrorNoticeEl.classList.remove("hidden");
    }
  }

  async function loadCommunityReports() {
    mapLoadingEl.classList.remove("hidden");
    feedCountBadge.textContent = "Loading community reports...";

    try {
      const res = await fetch("/api/community/reports");
      const data = await res.json();

      if (res.ok && data.success) {
        allCommunityReports = data.reports || [];
        applyCommunityFilters();
      } else {
        feedCountBadge.textContent = "Failed to load reports.";
      }
    } catch (err) {
      console.error("Error loading community reports:", err);
      feedCountBadge.textContent = "Error loading reports.";
    } finally {
      mapLoadingEl.classList.add("hidden");
    }
  }

  function applyCommunityFilters() {
    const searchVal = communitySearchInput.value.trim().toLowerCase();
    const topicVal = communityTopicFilter.value;
    const dateVal = communityDateFilter.value;
    const hasLocationOnly = communityHasLocationToggle.checked;

    const now = Date.now();

    filteredCommunityReports = allCommunityReports.filter(report => {
      // Topic filter
      if (topicVal && topicVal !== "All" && report.topic.toLowerCase() !== topicVal.toLowerCase()) {
        return false;
      }

      // Location filter
      if (hasLocationOnly && (report.latitude == null || report.longitude == null)) {
        return false;
      }

      // Date filter
      if (dateVal && dateVal !== "all" && report.incident_date) {
        const days = parseInt(dateVal, 10);
        const reportDate = new Date(report.incident_date).getTime();
        const diffDays = (now - reportDate) / (1000 * 60 * 60 * 24);
        if (diffDays > days) return false;
      }

      // Search keyword filter
      if (searchVal) {
        const text = `${report.title} ${report.description} ${report.approx_location_name || ""}`.toLowerCase();
        if (!text.includes(searchVal)) return false;
      }

      return true;
    });

    renderCommunityFeed(filteredCommunityReports);
    renderMapMarkers(filteredCommunityReports);
  }

  function renderCommunityFeed(reports) {
    communityReportsList.innerHTML = "";

    const mappedCount = reports.filter(r => r.latitude != null && r.longitude != null).length;
    feedCountBadge.textContent = `Showing ${reports.length} report${reports.length === 1 ? "" : "s"} (${mappedCount} on map)`;

    if (reports.length === 0) {
      communityEmptyState.classList.remove("hidden");
      return;
    }
    communityEmptyState.classList.add("hidden");

    reports.forEach(report => {
      const card = document.createElement("div");
      card.className = "report-card";
      card.id = `report-card-${report.id}`;
      if (activeReportId === report.id) card.classList.add("active-card");

      const hasCoords = report.latitude != null && report.longitude != null;
      const locDisplay = report.approx_location_name ? `📍 ${escapeHtml(report.approx_location_name)}` : "No map location attached";
      const dateDisplay = report.incident_date ? `📅 ${escapeHtml(report.incident_date)}` : "Date not specified";

      card.innerHTML = `
        <div class="report-card-header">
          <span class="badge badge-topic">${escapeHtml(report.topic)}</span>
          <span class="badge badge-allegation">Allegation</span>
        </div>
        <h4 class="report-card-title">${escapeHtml(report.title)}</h4>
        <div class="report-card-meta">
          <span class="report-card-meta-item">${locDisplay}</span>
          <span class="report-card-meta-item">${dateDisplay}</span>
        </div>
        <p class="report-card-snippet">${escapeHtml(report.description)}</p>
        <div class="report-card-actions">
          ${hasCoords ? `
            <button class="btn btn-secondary btn-xs btn-show-on-map" data-report-id="${report.id}" title="Center and highlight on map">
              📍 View on Map
            </button>
          ` : `
            <span class="stat-tag">Online / Unmapped</span>
          `}
          <button class="btn btn-link btn-xs btn-open-detail" data-report-id="${report.id}">
            Read Full Experience &rarr;
          </button>
        </div>
      `;

      // Click card to highlight and center
      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-open-detail")) {
          openReportDetailModal(report.id);
          return;
        }
        selectReport(report.id, true);
      });

      const btnShowMap = card.querySelector(".btn-show-on-map");
      if (btnShowMap) {
        btnShowMap.addEventListener("click", (e) => {
          e.stopPropagation();
          selectReport(report.id, true);
          if (communityLayoutMode === "feed") {
            setLayoutMode("split");
          }
        });
      }

      communityReportsList.appendChild(card);
    });
  }

  function renderMapMarkers(reports) {
    if (!communityMap || !markersClusterGroup) return;

    markersClusterGroup.clearLayers();
    reportMarkersMap.clear();

    const boundsPoints = [];

    reports.forEach(report => {
      if (report.latitude == null || report.longitude == null) return;

      const lat = parseFloat(report.latitude);
      const lon = parseFloat(report.longitude);
      if (isNaN(lat) || isNaN(lon)) return;

      boundsPoints.push([lat, lon]);

      // Create Custom Pin Icon
      const pinIcon = L.divIcon({
        className: "custom-leaflet-pin-wrapper",
        html: `
          <div class="custom-leaflet-pin" id="pin-${report.id}">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
              <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
              <path d="M7 21h10"/>
              <path d="M12 3v18"/>
            </svg>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });

      const marker = L.marker([lat, lon], { icon: pinIcon });

      // Popup Content
      const snippet = report.description.length > 140 ? report.description.slice(0, 140) + "..." : report.description;
      const popupHtml = `
        <div class="map-popup-card">
          <div class="map-popup-header">
            <span class="badge-topic">${escapeHtml(report.topic)}</span>
            <span class="map-popup-disclaimer">Allegation</span>
          </div>
          <h4 class="map-popup-title">${escapeHtml(report.title)}</h4>
          <div class="map-popup-meta">
            <span>📍 ${escapeHtml(report.approx_location_name || "Approximate locality")}</span>
            ${report.incident_date ? `<span>📅 ${escapeHtml(report.incident_date)}</span>` : ""}
          </div>
          <p class="map-popup-snippet">${escapeHtml(snippet)}</p>
          <button class="btn btn-primary btn-xs btn-full mt-2 btn-popup-full" data-report-id="${report.id}">
            Open Full Report
          </button>
        </div>
      `;

      marker.bindPopup(popupHtml, { maxWidth: 300 });

      marker.on("click", () => {
        selectReport(report.id, false);
      });

      marker.on("popupopen", (e) => {
        const popupEl = e.popup.getElement();
        if (popupEl) {
          const btn = popupEl.querySelector(".btn-popup-full");
          if (btn) {
            btn.addEventListener("click", () => openReportDetailModal(report.id));
          }
        }
      });

      markersClusterGroup.addLayer(marker);
      reportMarkersMap.set(report.id, { marker, report });
    });

    if (boundsPoints.length > 0 && communityMap) {
      // Don't auto-reset zoom aggressively if user is focused on a report
      if (!activeReportId) {
        communityMap.fitBounds(boundsPoints, { padding: [40, 40], maxZoom: 13 });
      }
    }
  }

  function selectReport(reportId, zoomTo = true) {
    activeReportId = reportId;

    // Highlight card in feed
    document.querySelectorAll(".report-card").forEach(c => c.classList.remove("active-card"));
    const activeCard = document.getElementById(`report-card-${reportId}`);
    if (activeCard) {
      activeCard.classList.add("active-card");
      activeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // Highlight pin and center map if coords exist
    const item = reportMarkersMap.get(reportId);
    if (item && communityMap) {
      const { marker, report } = item;

      // Unhighlight previous pins
      document.querySelectorAll(".custom-leaflet-pin").forEach(p => p.classList.remove("pin-active"));
      const pinEl = document.getElementById(`pin-${reportId}`);
      if (pinEl) pinEl.classList.add("pin-active");

      // Update Floating Banner
      activeBannerTopic.textContent = report.topic;
      activeBannerTitle.textContent = report.title;
      activeBannerLocation.textContent = `📍 ${report.approx_location_name || "Approximate locality"}`;
      mapActiveReportBanner.classList.remove("hidden");

      if (zoomTo) {
        const latLng = marker.getLatLng();
        if (markersClusterGroup) {
          markersClusterGroup.zoomToShowLayer(marker, () => {
            marker.openPopup();
          });
        } else {
          communityMap.flyTo(latLng, 14, { duration: 0.8 });
          marker.openPopup();
        }
      }
    } else {
      mapActiveReportBanner.classList.add("hidden");
    }
  }

  function clearActiveReportHighlight() {
    activeReportId = null;
    document.querySelectorAll(".report-card").forEach(c => c.classList.remove("active-card"));
    document.querySelectorAll(".custom-leaflet-pin").forEach(p => p.classList.remove("pin-active"));
  }

  function fitAllMarkers() {
    if (!communityMap || !markersClusterGroup) return;
    const bounds = markersClusterGroup.getBounds();
    if (bounds.isValid()) {
      communityMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
    } else {
      communityMap.setView([21.5937, 78.9629], 5);
    }
  }

  // -------------------------------------------------------------
  // Create Community Report Modal & Location Picker
  // -------------------------------------------------------------
  function setupCreateReportModal() {
    btnOpenCreateReport.addEventListener("click", () => {
      openCreateReportModal();
    });

    btnCloseCreateModal.addEventListener("click", () => {
      closeCreateReportModal();
    });

    btnCancelCreateReport.addEventListener("click", () => {
      closeCreateReportModal();
    });

    // Toggle location attachment
    chkIncludeLocation.addEventListener("change", (e) => {
      if (e.target.checked) {
        locationPickerPanel.classList.remove("hidden");
        initPickerMap();
      } else {
        locationPickerPanel.classList.add("hidden");
        clearPickerLocation();
      }
    });

    // Locality search
    btnSearchLocality.addEventListener("click", searchLocalityViaNominatim);
    inputLocalitySearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        searchLocalityViaNominatim();
      }
    });

    btnRemoveLocation.addEventListener("click", () => {
      clearPickerLocation();
    });

    // Form submission
    formCreateReport.addEventListener("submit", handleCreateReportSubmit);
  }

  function openCreateReportModal() {
    formCreateReport.reset();
    chkIsPublic.checked = true;
    chkIntegrityConfirm.checked = false;
    chkIncludeLocation.checked = false;
    locationPickerPanel.classList.add("hidden");
    clearPickerLocation();

    modalCreateReport.classList.remove("hidden");
  }

  function closeCreateReportModal() {
    modalCreateReport.classList.add("hidden");
  }

  function initPickerMap() {
    setTimeout(() => {
      if (typeof L === "undefined") return;

      if (!pickerMap) {
        pickerMap = L.map("location-picker-map", {
          center: [20.5937, 78.9629],
          zoom: 4,
          zoomControl: true
        });

        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 18,
          attribution: '&copy; OpenStreetMap'
        }).addTo(pickerMap);

        // Click on map to place pin
        pickerMap.on("click", (e) => {
          setPickerCoordinates(e.latlng.lat, e.latlng.lng, true);
        });
      } else {
        pickerMap.invalidateSize();
      }
    }, 150);
  }

  function setPickerCoordinates(lat, lon, reverseGeocode = false) {
    selectedPickerLat = parseFloat(lat.toFixed(4));
    selectedPickerLon = parseFloat(lon.toFixed(4));

    badgeSelectedCoords.textContent = `Lat: ${selectedPickerLat}, Lng: ${selectedPickerLon}`;
    badgeSelectedCoords.className = "stat-tag font-medium text-emerald";

    if (!pickerMarker && pickerMap) {
      pickerMarker = L.marker([selectedPickerLat, selectedPickerLon], {
        draggable: true
      }).addTo(pickerMap);

      pickerMarker.on("dragend", (e) => {
        const pos = e.target.getLatLng();
        setPickerCoordinates(pos.lat, pos.lng, true);
      });
    } else if (pickerMarker) {
      pickerMarker.setLatLng([selectedPickerLat, selectedPickerLon]);
    }

    if (pickerMap) {
      pickerMap.panTo([selectedPickerLat, selectedPickerLon]);
    }

    if (reverseGeocode && (!inputApproxLocationName.value || inputApproxLocationName.value.trim() === "")) {
      reverseGeocodeCoordinates(selectedPickerLat, selectedPickerLon);
    }
  }

  function clearPickerLocation() {
    selectedPickerLat = null;
    selectedPickerLon = null;
    badgeSelectedCoords.textContent = "No pin selected";
    badgeSelectedCoords.className = "stat-tag";
    inputApproxLocationName.value = "";
    if (pickerMarker && pickerMap) {
      pickerMap.removeLayer(pickerMarker);
      pickerMarker = null;
    }
  }

  async function searchLocalityViaNominatim() {
    const query = inputLocalitySearch.value.trim();
    if (!query) return;

    btnSearchLocality.disabled = true;
    localitySearchResults.classList.remove("hidden");
    localitySearchResults.innerHTML = `<div class="locality-search-item">Searching Indian localities...</div>`;

    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=5`;
      const res = await fetch(url, {
        headers: { "Accept-Language": "en" }
      });
      const results = await res.json();

      if (!results || results.length === 0) {
        localitySearchResults.innerHTML = `<div class="locality-search-item text-muted">No localities found. Try a broader city or district name.</div>`;
        return;
      }

      localitySearchResults.innerHTML = "";
      results.forEach(item => {
        const el = document.createElement("div");
        el.className = "locality-search-item";
        el.textContent = item.display_name;
        el.addEventListener("click", () => {
          const lat = parseFloat(item.lat);
          const lon = parseFloat(item.lon);
          // Format short locality name
          const parts = item.display_name.split(",").map(p => p.trim());
          const shortName = parts.slice(0, 3).join(", ");
          inputApproxLocationName.value = shortName;

          setPickerCoordinates(lat, lon, false);
          if (pickerMap) pickerMap.setView([lat, lon], 12);

          localitySearchResults.classList.add("hidden");
        });
        localitySearchResults.appendChild(el);
      });

    } catch (err) {
      console.warn("Nominatim search error:", err);
      localitySearchResults.innerHTML = `<div class="locality-search-item text-amber">Search service unavailable. You can click directly on the map to set location.</div>`;
    } finally {
      btnSearchLocality.disabled = false;
    }
  }

  async function reverseGeocodeCoordinates(lat, lon) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14`;
      const res = await fetch(url);
      const data = await res.json();
      if (data && data.address) {
        const addr = data.address;
        const nameParts = [addr.suburb || addr.neighbourhood || addr.city_district || addr.town || addr.city, addr.state];
        const formatted = nameParts.filter(Boolean).join(", ");
        if (formatted) inputApproxLocationName.value = formatted;
      }
    } catch (e) {
      // ignore reverse geocode failures
    }
  }

  async function handleCreateReportSubmit(e) {
    e.preventDefault();

    const title = inputReportTitle.value.trim();
    const topic = selectReportTopic.value;
    const desc = inputReportDesc.value.trim();
    const date = inputIncidentDate.value || null;
    const isPublic = chkIsPublic.checked;

    if (!title || !topic || !desc) {
      alert("Please fill in the required title, category, and narrative fields.");
      return;
    }

    if (!chkIntegrityConfirm.checked) {
      alert("Please check the integrity notice confirming this is a genuine user experience.");
      return;
    }

    const payload = {
      title: title,
      topic: topic,
      description: desc,
      approx_location_name: inputApproxLocationName.value.trim() || null,
      latitude: chkIncludeLocation.checked && selectedPickerLat != null ? selectedPickerLat : null,
      longitude: chkIncludeLocation.checked && selectedPickerLon != null ? selectedPickerLon : null,
      incident_date: date,
      is_public: isPublic,
      session_id: sessionId
    };

    const submitBtn = formCreateReport.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.textContent = "Publishing...";

    try {
      const res = await fetch("/api/community/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert("Failed to submit report: " + (data.detail || data.message || "Unknown error"));
        return;
      }

      closeCreateReportModal();
      await loadCommunityReports();

      // Focus on newly created report
      if (data.report && data.report.id) {
        setTimeout(() => selectReport(data.report.id, true), 300);
      }

      alert("Your experience report has been published to the community feed.");

    } catch (err) {
      alert("Network error: Could not submit report.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Publish Experience</span>`;
    }
  }

  // -------------------------------------------------------------
  // Report Detail Modal & Statutory Guidance
  // -------------------------------------------------------------
  function setupReportDetailModal() {
    btnCloseDetailModal.addEventListener("click", () => {
      modalReportDetail.classList.add("hidden");
    });

    btnDetailShowMap.addEventListener("click", () => {
      if (activeReportId) {
        modalReportDetail.classList.add("hidden");
        selectReport(activeReportId, true);
        if (communityLayoutMode === "feed") setLayoutMode("split");
      }
    });

    btnDetailAskAi.addEventListener("click", () => {
      const report = allCommunityReports.find(r => r.id === activeReportId);
      if (!report) return;

      modalReportDetail.classList.add("hidden");
      // Switch to Chat Tab
      navBtnChat.click();

      const consultationPrompt = `I am reviewing a community report regarding **${report.topic}**: "${report.title}".\n\nWhat are the citizen's legal rights, procedural deadlines, and recommended statutory actions under Indian law?`;
      userInputEl.value = consultationPrompt;
      autoResizeTextarea();
      sendMessage(consultationPrompt);
    });
  }

  function openReportDetailModal(reportId) {
    const report = allCommunityReports.find(r => r.id === reportId);
    if (!report) return;

    activeReportId = reportId;
    modalDetailTitle.textContent = report.title;
    detailTopicBadge.textContent = report.topic;
    detailLocationText.textContent = report.approx_location_name ? `📍 ${report.approx_location_name}` : "No approximate location attached";
    detailDateText.textContent = report.incident_date ? `📅 ${report.incident_date}` : "Date not specified";
    detailNarrativeContent.textContent = report.description;

    // Enable or disable "Show on Map" button
    if (report.latitude != null && report.longitude != null) {
      btnDetailShowMap.disabled = false;
      btnDetailShowMap.classList.remove("hidden");
    } else {
      btnDetailShowMap.disabled = true;
      btnDetailShowMap.classList.add("hidden");
    }

    // Render Statutory Roadmap based on Topic
    detailRoadmapContent.innerHTML = getStatutoryRoadmapForTopic(report.topic);

    modalReportDetail.classList.remove("hidden");
  }

  function getStatutoryRoadmapForTopic(topic) {
    switch (topic) {
      case "Consumer Dispute":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Statute:</strong> Consumer Protection Act, 2019 (Sections 2(11) & 35) covering deficiency of goods/services.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Online Filing Portal:</strong> File complaint online via <strong>e-Daakhil</strong> (edaakhil.nic.in) with digital payment of nominal fee.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Pecuniary Jurisdiction:</strong> District Commission entertains claims up to ₹50 Lakhs; State Commission up to ₹2 Crores.</div></div>
        `;
      case "Police & FIR":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Zero FIR Mandate:</strong> BNSS 2023 Section 173 (CrPC 154) requires mandatory registration of Zero FIR regardless of police jurisdiction.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Procedure on Refusal:</strong> Send written substance of complaint via registered post to Superintendent of Police (SP / DCP) under BNSS S. 173(4).</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Magisterial Remedy:</strong> File application under BNSS S. 175(3) (CrPC 156(3)) requesting Magistrate direction for investigation.</div></div>
        `;
      case "Tenant & Landlord":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Notice Period:</strong> Transfer of Property Act, 1882 (Section 106) mandates minimum 15 days written termination notice for residential month-to-month leases.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Essential Services:</strong> Landlords are strictly prohibited from disconnecting electricity or water to enforce eviction without court order.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Deposit Dispute:</strong> File for pre-litigation conciliation through District Legal Services Authority (DLSA / NALSA 15100).</div></div>
        `;
      case "RERA & Property":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Delay Penalty & Interest:</strong> Real Estate (Regulation & Development) Act (RERA) Section 18 mandates builder pay monthly interest for delayed possession.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Complaint Filing:</strong> File online complaint under Section 31 before the State Real Estate Regulatory Authority (e.g. MahaRERA, UP-RERA, K-RERA).</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Occupancy Certificate:</strong> Never accept key possession on an indemnity bond without a verified statutory OC issued by municipal corporation.</div></div>
        `;
      case "Cheque Dishonour":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Statutory Notice:</strong> Negotiable Instruments Act, 1881 Section 138 requires serving legal demand notice within 30 days of bank return memo.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>15-Day Cure Period:</strong> Drawer has 15 days from notice receipt to pay the dishonoured amount.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Limitation:</strong> Criminal complaint must be filed before the Judicial Magistrate within 30 days following the 15-day cure window.</div></div>
        `;
      case "Cyber Fraud & Scams":
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Immediate Golden Hour:</strong> Dial national cyber helpline <strong>1930</strong> or register immediately at <strong>cybercrime.gov.in</strong> to freeze beneficiary funds.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Bank Intimation:</strong> Send formal written letter & email to your bank's nodal officer within 72 hours for zero-liability fraud protection under RBI circulars.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Evidence:</strong> Preserve transaction UTR numbers, SMS logs, WhatsApp chats, and phishing URLs in your private Evidence Vault.</div></div>
        `;
      default:
        return `
          <div class="roadmap-step-item"><span class="roadmap-step-num">1.</span> <div><strong>Statutory Rights:</strong> Verified against India Code and constitutional remedies under Article 226/32.</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">2.</span> <div><strong>Free Legal Aid:</strong> Eligible citizens (women, children, custody, low income) are entitled to free legal aid through NALSA / DLSA (Toll-Free 15100).</div></div>
          <div class="roadmap-step-item"><span class="roadmap-step-num">3.</span> <div><strong>Consultation:</strong> Ask Jurista AI in the chat tab for specific document review or step-by-step statutory roadmaps.</div></div>
        `;
    }
  }

  // -------------------------------------------------------------
  // Private Evidence Vault Controller
  // -------------------------------------------------------------
  function setupEvidenceVault() {
    btnOpenAddVault.addEventListener("click", () => {
      formAddVault.reset();
      modalAddVault.classList.remove("hidden");
    });

    btnEmptyAddVault.addEventListener("click", () => {
      formAddVault.reset();
      modalAddVault.classList.remove("hidden");
    });

    btnCloseVaultModal.addEventListener("click", () => {
      modalAddVault.classList.add("hidden");
    });

    btnCancelVault.addEventListener("click", () => {
      modalAddVault.classList.add("hidden");
    });

    formAddVault.addEventListener("submit", handleAddVaultSubmit);
  }

  async function loadVaultItems() {
    try {
      const res = await fetch(`/api/vault/items?session_id=${sessionId}`);
      const data = await res.json();

      if (res.ok && data.success) {
        renderVaultItems(data.items || []);
      }
    } catch (err) {
      console.warn("Error loading vault items:", err);
    }
  }

  function renderVaultItems(items) {
    vaultItemsList.innerHTML = "";

    if (items.length === 0) {
      vaultEmptyState.classList.remove("hidden");
      return;
    }
    vaultEmptyState.classList.add("hidden");

    items.forEach(item => {
      const card = document.createElement("div");
      card.className = "vault-card";
      const dateStr = new Date(item.created_at * 1000).toLocaleDateString();

      card.innerHTML = `
        <div class="vault-card-header">
          <span class="vault-type-badge">${escapeHtml(item.item_type)}</span>
          <button class="btn-icon-subtle btn-delete-vault" data-id="${item.id}" title="Delete Record">&times;</button>
        </div>
        <h4 class="vault-card-title">${escapeHtml(item.title)}</h4>
        ${item.description ? `<p class="vault-card-notes">${escapeHtml(item.description)}</p>` : ""}
        ${item.approx_location ? `<div class="report-card-meta"><span class="report-card-meta-item">📍 ${escapeHtml(item.approx_location)} (Confidential)</span></div>` : ""}
        <div class="vault-card-footer">
          <span>🔒 Private Record</span>
          <span>Added: ${dateStr}</span>
        </div>
      `;

      const deleteBtn = card.querySelector(".btn-delete-vault");
      deleteBtn.addEventListener("click", () => deleteVaultItem(item.id));

      vaultItemsList.appendChild(card);
    });
  }

  async function handleAddVaultSubmit(e) {
    e.preventDefault();

    const title = inputVaultTitle.value.trim();
    const itemType = selectVaultType.value;
    const desc = inputVaultDesc.value.trim();
    const loc = inputVaultLoc.value.trim();

    if (!title || !itemType) return;

    try {
      const res = await fetch("/api/vault/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          title: title,
          item_type: itemType,
          description: desc || null,
          approx_location: loc || null
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        modalAddVault.classList.add("hidden");
        loadVaultItems();
      } else {
        alert("Failed to save vault item.");
      }
    } catch (err) {
      alert("Network error: Could not save vault item.");
    }
  }

  async function deleteVaultItem(itemId) {
    if (!confirm("Are you sure you want to remove this private record from your Evidence Vault?")) return;

    try {
      const res = await fetch(`/api/vault/items/${itemId}?session_id=${sessionId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        loadVaultItems();
      }
    } catch (err) {
      console.error(err);
    }
  }

  // -------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------
  function debounce(fn, ms) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderMarkdown(text) {
    if (!text) return "";

    let escaped = escapeHtml(text);

    escaped = escaped.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
    escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

    escaped = escaped.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    escaped = escaped.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    escaped = escaped.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    escaped = escaped.replace(/\*(.*?)\*/g, "<em>$1</em>");

    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 &nearr;</a>');

    const lines = escaped.split("\n");
    let inList = false;
    const processedLines = [];

    for (let line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("• ")) {
        if (!inList) {
          processedLines.push("<ul>");
          inList = true;
        }
        processedLines.push(`<li>${trimmed.substring(2)}</li>`);
      } else {
        if (inList) {
          processedLines.push("</ul>");
          inList = false;
        }
        if (trimmed.length > 0 && !trimmed.startsWith("<h") && !trimmed.startsWith("<pre")) {
          processedLines.push(`<p>${line}</p>`);
        } else {
          processedLines.push(line);
        }
      }
    }
    if (inList) processedLines.push("</ul>");

    return processedLines.join("\n");
  }

  // Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", init);
})();
