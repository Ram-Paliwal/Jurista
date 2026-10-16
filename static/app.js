/**
 * Jurista — Frontend Application Controller
 * Pure Vanilla JavaScript implementation.
 * Handles isolated sessions, multilingual legal Q&A, PDF PyMuPDF extraction, and RAG grounding.
 */

(function () {
  "use strict";

  // State
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

  // DOM Elements
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

  // Sidebar Elements
  const dropzoneEl = document.getElementById("dropzone");
  const fileInputEl = document.getElementById("file-input");
  const uploadLoaderEl = document.getElementById("upload-loader");
  const dropzoneContentEl = dropzoneEl.querySelector(".dropzone-content");
  const docStatusBadgeEl = document.getElementById("doc-status-badge");
  const activeDocDetailsEl = document.getElementById("active-doc-details");
  const docFilenameEl = document.getElementById("doc-filename");
  const docPagesEl = document.getElementById("doc-pages");
  const docCharsEl = document.getElementById("doc-chars");
  const docChunksEl = document.getElementById("doc-chunks");
  const scannedWarningEl = document.getElementById("scanned-warning");
  const btnRemoveDocEl = document.getElementById("btn-remove-doc");
  const btnReExplainEl = document.getElementById("btn-re-explain");

  // Topic Chips
  const chipBtns = document.querySelectorAll(".chip-btn");

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
  }

  // -------------------------------------------------------------
  // Event Bindings
  // -------------------------------------------------------------
  function bindEvents() {
    // Chat Form Submit
    chatFormEl.addEventListener("submit", handleChatSubmit);

    // Textarea enter key submit (Shift+Enter for newline)
    userInputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatFormEl.dispatchEvent(new Event("submit"));
      }
    });

    userInputEl.addEventListener("input", autoResizeTextarea);

    // Language Change
    langSelectEl.addEventListener("change", handleLanguageChange);

    // New Session
    btnNewSessionEl.addEventListener("click", handleNewSession);

    // Multilingual Voice Input
    if (btnMicEl) {
      btnMicEl.addEventListener("click", toggleVoiceRecognition);
    }
    if (btnStopVoiceEl) {
      btnStopVoiceEl.addEventListener("click", stopVoiceRecognition);
    }

    // File Attachment & Drag/Drop
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

    // Remove active document
    btnRemoveDocEl.addEventListener("click", handleRemoveDocument);

    // Re-explain document button
    btnReExplainEl.addEventListener("click", () => {
      if (activeDocument) {
        sendMessage(`Please explain this legal document again with focus on deadlines and practical roadmap: ${activeDocument.filename}`);
      }
    });

    // Topic chips click
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

  // -------------------------------------------------------------
  // Auto-resize Textarea
  // -------------------------------------------------------------
  function autoResizeTextarea() {
    userInputEl.style.height = "auto";
    userInputEl.style.height = Math.min(userInputEl.scrollHeight, 140) + "px";
  }

  // -------------------------------------------------------------
  // Session Loader
  // -------------------------------------------------------------
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

  // -------------------------------------------------------------
  // Language Switching (Seamless, no context loss)
  // -------------------------------------------------------------
  async function handleLanguageChange(e) {
    const newLang = e.target.value;
    currentLanguage = newLang;
    localStorage.setItem("jurista_language", newLang);

    // Stop active voice session so next voice input uses updated language locale
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

  // -------------------------------------------------------------
  // New Session / Clear Context
  // -------------------------------------------------------------
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

    // Generate fresh session ID
    sessionId = "jurista-" + crypto.randomUUID();
    localStorage.setItem("jurista_session_id", sessionId);
    resetDocumentUI();

    // Reset Chat UI
    chatMessagesEl.innerHTML = `
      <div class="message-card message-jurista intro-message">
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
            <span class="message-time">Just now</span>
          </div>
          <div class="message-text">
            <p>New session started in <strong>${currentLanguage}</strong>.</p>
            <p>Ask any question regarding Indian law, court procedures, or upload a legal PDF for immediate grounded analysis.</p>
          </div>
        </div>
      </div>
    `;
  }

  // -------------------------------------------------------------
  // Document Upload
  // -------------------------------------------------------------
  function handleFileSelected(e) {
    if (e.target.files && e.target.files.length > 0) {
      uploadPdfFile(e.target.files[0]);
    }
  }

  async function uploadPdfFile(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF document (.pdf).");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      alert("File is too large. Maximum size is 15 MB.");
      return;
    }

    // Show upload state
    dropzoneContentEl.classList.add("hidden");
    uploadLoaderEl.classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);
    formData.append("language", currentLanguage);

    try {
      const res = await fetch("/api/upload-pdf", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.message || data.error || "Failed to process PDF.");
        resetDropzoneUI();
        return;
      }

      // Update UI with parsed doc
      renderActiveDocument({
        filename: data.filename,
        page_count: data.page_count,
        total_characters: data.total_characters,
        is_scanned: data.is_scanned,
        chunk_count: data.chunk_count
      });

      // Append upload message + explanation to chat
      appendUserMessage(`Uploaded PDF document: **${data.filename}** (${data.page_count} pages)`);
      appendAssistantMessage(data.explanation, "DOCUMENT_EXPLAIN", []);

      // Scroll to bottom
      scrollToBottom();
    } catch (err) {
      alert("Error uploading document: " + err.message);
    } finally {
      resetDropzoneUI();
      fileInputEl.value = "";
    }
  }

  function renderActiveDocument(doc) {
    activeDocument = doc;
    docStatusBadgeEl.textContent = "PDF Active";
    docStatusBadgeEl.className = "badge badge-success";

    docFilenameEl.textContent = doc.filename;
    docPagesEl.textContent = `${doc.page_count} Pages`;
    docCharsEl.textContent = `${doc.total_characters.toLocaleString()} Chars`;
    docChunksEl.textContent = `${doc.chunk_count || 0} Chunks`;

    if (doc.is_scanned) {
      scannedWarningEl.classList.remove("hidden");
    } else {
      scannedWarningEl.classList.add("hidden");
    }

    dropzoneEl.classList.add("hidden");
    activeDocDetailsEl.classList.remove("hidden");
  }

  function resetDocumentUI() {
    activeDocument = null;
    docStatusBadgeEl.textContent = "No PDF";
    docStatusBadgeEl.className = "badge badge-neutral";
    activeDocDetailsEl.classList.add("hidden");
    dropzoneEl.classList.remove("hidden");
    scannedWarningEl.classList.add("hidden");
  }

  function resetDropzoneUI() {
    uploadLoaderEl.classList.add("hidden");
    dropzoneContentEl.classList.remove("hidden");
  }

  function handleRemoveDocument() {
    if (confirm("Remove active document from this session?")) {
      resetDocumentUI();
      appendAssistantMessage("Active document removed from session context. You can continue asking general legal questions or upload another PDF.");
    }
  }

  // -------------------------------------------------------------
  // Chat Message Handling
  // -------------------------------------------------------------
  async function handleChatSubmit(e) {
    e.preventDefault();
    if (isProcessing) return;

    // Stop active speech recognition cleanly before sending
    if (isRecording) {
      stopVoiceRecognition();
    }

    const message = userInputEl.value.trim();
    if (!message) return;

    userInputEl.value = "";
    autoResizeTextarea();
    await sendMessage(message);
  }

  async function sendMessage(message) {
    isProcessing = true;
    btnSendEl.disabled = true;

    // Append User Message to UI
    appendUserMessage(message);

    // Show Typing Indicator
    const typingId = showTypingIndicator();
    scrollToBottom();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
          language: currentLanguage
        })
      });

      removeTypingIndicator(typingId);

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        appendAssistantMessage(`⚠️ **Error**: ${err.detail || "Failed to process request."}`);
        return;
      }

      const data = await res.json();
      appendAssistantMessage(data.response, data.intent, data.sources);
      scrollToBottom();
    } catch (err) {
      removeTypingIndicator(typingId);
      appendAssistantMessage(`⚠️ **Network Error**: Unable to reach Jurista backend (${err.message}).`);
    } finally {
      isProcessing = false;
      btnSendEl.disabled = false;
      userInputEl.focus();
    }
  }

  // -------------------------------------------------------------
  // Multilingual Voice Input (Web Speech API)
  // Supports English (en-IN), Hindi (hi-IN), and Marathi (mr-IN)
  // -------------------------------------------------------------
  function isSpeechRecognitionSupported() {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

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
      alert(
        "Voice input is not supported in this browser.\n\nPlease use Google Chrome, Microsoft Edge, or another browser with Web Speech API support."
      );
      return;
    }

    // Guard against duplicate active recognition sessions
    if (isRecording && recognition) {
      stopVoiceRecognition();
    }

    try {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      // Map current application language to recognition locale
      const activeLocale = LANGUAGE_LOCALES[currentLanguage] || "en-IN";
      recognition.lang = activeLocale;

      // Preserve any existing text the user already typed
      recognitionBaseText = userInputEl.value;

      recognition.onstart = () => {
        isRecording = true;
        btnMicEl.classList.add("recording");
        btnMicEl.title = "Listening... Click microphone or Stop button to finish";
        btnMicEl.setAttribute("aria-label", "Recording voice input, click to stop");
        
        voiceIndicatorEl.classList.remove("hidden");
        const langLabel = LANGUAGE_DISPLAY[currentLanguage] || currentLanguage;
        voiceStatusTextEl.textContent = `Listening in ${langLabel}... Speak now`;
      };

      recognition.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = 0; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            finalTranscript += item[0].transcript;
          } else {
            interimTranscript += item[0].transcript;
          }
        }

        const recognizedText = (finalTranscript + " " + interimTranscript).trim();
        if (recognizedText) {
          const prefix = recognitionBaseText.trim();
          userInputEl.value = prefix ? `${prefix} ${recognizedText}` : recognizedText;
          autoResizeTextarea();
        }
      };

      recognition.onerror = (event) => {
        console.warn("[Voice Recognition]", event.error);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          alert("Microphone permission was denied.\n\nPlease allow microphone access in your browser settings to speak your legal question.");
        } else if (event.error === "no-speech") {
          // Normal timeout when no speech is detected; silently reset without crashing
        } else if (event.error === "network") {
          alert("Network error occurred during speech recognition. Please check your internet connection.");
        } else if (event.error !== "aborted") {
          console.error("Speech recognition error:", event.error);
        }
        stopVoiceRecognition();
      };

      recognition.onend = () => {
        stopVoiceRecognition();
      };

      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      stopVoiceRecognition();
    }
  }

  function stopVoiceRecognition() {
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {
        // Safe ignore
      }
      recognition = null;
    }
    isRecording = false;
    if (btnMicEl) {
      btnMicEl.classList.remove("recording");
      btnMicEl.title = `Voice Input (${LANGUAGE_DISPLAY[currentLanguage] || currentLanguage})`;
      btnMicEl.setAttribute("aria-label", "Voice Input");
    }
    if (voiceIndicatorEl) {
      voiceIndicatorEl.classList.add("hidden");
    }
    userInputEl.focus();
  }

  // -------------------------------------------------------------
  // Message Rendering & Markdown Parser
  // -------------------------------------------------------------
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
          <span class="message-time">Just now</span>
        </div>
        <div class="message-text">${formatMarkdown(text)}</div>
      </div>
    `;
    chatMessagesEl.appendChild(card);
    scrollToBottom();
  }

  function appendAssistantMessage(text, intent, sources) {
    const card = document.createElement("div");
    card.className = "message-card message-jurista";

    let sourcesHtml = "";
    if (sources && sources.length > 0) {
      const pills = sources
        .map(
          (s) =>
            `<a class="source-pill-link" href="${s.official_url}" target="_blank" rel="noopener">
               📜 ${s.act} — ${s.section} &nearr;
             </a>`
        )
        .join("");
      sourcesHtml = `
        <div class="message-sources-box">
          <div class="sources-box-header">Verified Statutory Sources Cited:</div>
          <div class="sources-pills">${pills}</div>
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
          <span class="message-time">Just now</span>
        </div>
        <div class="message-text">${formatMarkdown(text)}</div>
        ${sourcesHtml}
      </div>
    `;

    chatMessagesEl.appendChild(card);
    scrollToBottom();
  }

  function showTypingIndicator() {
    const id = "typing-" + Date.now();
    const card = document.createElement("div");
    card.id = id;
    card.className = "message-card message-jurista";
    card.innerHTML = `
      <div class="message-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
          <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-header-row">
          <span class="sender-name">Jurista</span>
          <span class="message-time">Analyzing...</span>
        </div>
        <div class="message-text">
          <div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>
        </div>
      </div>
    `;
    chatMessagesEl.appendChild(card);
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function renderHistoryMessages(messages) {
    // Clear out except welcome card
    chatMessagesEl.innerHTML = "";
    messages.forEach((m) => {
      if (m.role === "user") {
        appendUserMessage(m.content);
      } else {
        appendAssistantMessage(m.content, m.route, m.sources);
      }
    });
    scrollToBottom();
  }

  function scrollToBottom() {
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  }

  // -------------------------------------------------------------
  // Lightweight, Safe Markdown Formatter
  // -------------------------------------------------------------
  function formatMarkdown(text) {
    if (!text) return "";

    // Escape HTML tags to prevent XSS
    let escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Code blocks
    escaped = escaped.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
    escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Headers
    escaped = escaped.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    escaped = escaped.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    escaped = escaped.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    // Bold & Italic
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    escaped = escaped.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Markdown Links [title](url)
    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 &nearr;</a>');

    // Bullet points
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
