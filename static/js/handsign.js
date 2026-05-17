/* ==========================================================================
   NeuroSense AI — Hand Sign Chat
   File: static/js/handsign.js

   Real-time behavior:
   - Camera starts automatically
   - /api/hand_predict runs continuously
   - Detected signs are appended after steady hold
   - Sentence Builder stays visible and synced
   - Live camera sentence preview stays synced
   - Clear / Space / Back / Send to AI work in real time
   ========================================================================== */

let vid = null;
let cvs = null;
let ctx2 = null;

let msgs = null;
let typing = null;

let sentBox = null;
let holdFill = null;

let cameraBuilder = null;
let liveSentPreview = null;
let liveWc = null;

let sentence = "";
let predInv = null;

let lastPred = null;
let holdCount = 0;

let isEditing = false;
let activeSpeakBtn = null;
let isSending = false;
let isPredicting = false;

const HOLD_REQUIRED = 3;
const PREDICT_INTERVAL_MS = 385;

/* ==========================================================================
   INIT
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  vid = document.getElementById("vid");
  cvs = document.getElementById("cvs");
  msgs = document.getElementById("msgs");
  typing = document.getElementById("typing");

  sentBox = document.getElementById("sentBox");
  holdFill = document.getElementById("holdFill");

  cameraBuilder = document.getElementById("cameraBuilder");
  liveSentPreview = document.getElementById("liveSentPreview");
  liveWc = document.getElementById("liveWc");

  if (cvs) {
    ctx2 = cvs.getContext("2d");
  }

  renderSentence(false);
  updateHold(0);
  initCam();
});

/* ==========================================================================
   TEXT TO SPEECH
   ========================================================================== */

function speak(text) {
  if (!("speechSynthesis" in window)) return;

  try {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(String(text || ""));
    utterance.rate = 0.88;
    utterance.pitch = 1;
    utterance.volume = 1;
    utterance.lang = "en-US";

    window.speechSynthesis.speak(utterance);
  } catch (error) {
    console.warn("Speech synthesis failed:", error);
  }
}

function speakBtn(btn) {
  if (!btn) return;

  const msg = btn.closest(".msg");
  if (!msg) return;

  const body = msg.querySelector(".msg-body");
  if (!body) return;

  const text = body.textContent.trim();

  if (activeSpeakBtn === btn && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    btn.classList.remove("speaking");
    activeSpeakBtn = null;
    return;
  }

  window.speechSynthesis.cancel();

  if (activeSpeakBtn) {
    activeSpeakBtn.classList.remove("speaking");
  }

  btn.classList.add("speaking");
  activeSpeakBtn = btn;

  speak(text);

  const checker = setInterval(() => {
    if (!window.speechSynthesis.speaking) {
      btn.classList.remove("speaking");
      activeSpeakBtn = null;
      clearInterval(checker);
    }
  }, 300);
}

/* ==========================================================================
   CAMERA STATUS
   ========================================================================== */

function setStatus(text, live = false, showBadge = false) {
  const statusText = document.getElementById("stext");
  const dot = document.getElementById("sdot");
  const badge = document.getElementById("handBadge");

  if (statusText) {
    statusText.textContent = text;
  }

  if (dot) {
    dot.classList.toggle("live", Boolean(live));
  }

  if (badge) {
    badge.classList.toggle("show", Boolean(showBadge));
  }
}

function updateHold(n) {
  const safeValue = clamp(Number(n || 0), 0, HOLD_REQUIRED);

  const holdN = document.getElementById("holdN");

  if (holdN) {
    holdN.textContent = safeValue;
  }

  if (holdFill) {
    holdFill.style.width = `${(safeValue / HOLD_REQUIRED) * 100}%`;
  }

  for (let i = 0; i < HOLD_REQUIRED; i++) {
    const segment = document.getElementById(`seg${i}`);

    if (segment) {
      segment.classList.toggle("on", i < safeValue);
    }
  }
}

/* ==========================================================================
   CAMERA INIT
   ========================================================================== */

function initCam() {
  if (!vid || !cvs) {
    setStatus("Camera UI not found", false, false);
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setStatus("Camera not supported", false, false);

    addMsg(
      "assistant",
      "Your browser does not support camera access. Please use Chrome or Edge.",
      false
    );

    return;
  }

  navigator.mediaDevices
    .getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 720 },
        height: { ideal: 540 }
      },
      audio: false
    })
    .then((stream) => {
      vid.srcObject = stream;

      setStatus("Camera ready — show a sign", true, false);

      if (predInv) {
        clearInterval(predInv);
      }

      predInv = setInterval(predict, PREDICT_INTERVAL_MS);
    })
    .catch((error) => {
      console.error("Camera error:", error);

      setStatus("Camera error", false, false);

      addMsg(
        "assistant",
        "Camera permission was denied or unavailable. Please allow camera access and refresh this page.",
        false
      );
    });
}

/* ==========================================================================
   HAND PREDICTION
   ========================================================================== */

async function predict() {
  if (isPredicting) return;
  if (!vid || !cvs || !ctx2) return;
  if (!vid.srcObject || vid.videoWidth === 0 || vid.videoHeight === 0) return;

  isPredicting = true;

  try {
    cvs.width = vid.videoWidth;
    cvs.height = vid.videoHeight;

    ctx2.drawImage(vid, 0, 0, cvs.width, cvs.height);

    const response = await fetch("/api/hand_predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cache-Control": "no-cache"
      },
      body: JSON.stringify({
        image: cvs.toDataURL("image/jpeg", 0.8)
      })
    });

    const data = await response.json();

    if (data.no_model) {
      showNoModelOverlay(true);

      if (predInv) {
        clearInterval(predInv);
        predInv = null;
      }

      setStatus("No trained model found", false, false);
      return;
    }

    showNoModelOverlay(false);

    const predicted = sanitizePrediction(data.predicted);

    if (predicted) {
      handlePrediction(predicted, data);
    } else {
      resetPredictionState("Show a hand sign...");
    }

    if (data.sentence !== undefined && !isEditing) {
      sentence = normalizeSentence(data.sentence || "");
      renderSentence(false);
    }

  } catch (error) {
    console.warn("Prediction failed:", error);
    setStatus("Prediction failed", false, false);
  } finally {
    isPredicting = false;
  }
}

function handlePrediction(predicted, data) {
  const signVal = document.getElementById("signVal");

  if (signVal) {
    signVal.textContent = predicted;
  }

  setStatus(`Detected: ${predicted}`, true, true);

  if (predicted === lastPred) {
    holdCount += 1;
  } else {
    holdCount = 1;
    lastPred = predicted;
  }

  updateHold(holdCount);

  if (data.appended || holdCount >= HOLD_REQUIRED) {
    const nextSentence = data.sentence !== undefined
      ? data.sentence
      : appendWordToSentence(sentence, predicted);

    sentence = normalizeSentence(nextSentence);

    holdCount = 0;
    lastPred = null;

    updateHold(0);
    flashDetectedSign();

    if (!isEditing) {
      renderSentence(true);
    }
  }
}

function resetPredictionState(statusText) {
  const signVal = document.getElementById("signVal");

  if (signVal) {
    signVal.textContent = "—";
  }

  setStatus(statusText || "Show a hand sign...", false, false);

  holdCount = 0;
  lastPred = null;

  updateHold(0);
}

function flashDetectedSign() {
  const signVal = document.getElementById("signVal");

  if (!signVal) return;

  signVal.classList.add("flash");

  setTimeout(() => {
    signVal.classList.remove("flash");
  }, 380);
}

function showNoModelOverlay(show) {
  const noModel = document.getElementById("noModel");

  if (!noModel) return;

  noModel.classList.toggle("hidden", !show);
}

function sanitizePrediction(value) {
  const predicted = String(value || "").trim();

  if (!predicted) return "";
  if (predicted === "—") return "";
  if (predicted.toLowerCase() === "none") return "";
  if (predicted.toLowerCase() === "unknown") return "";

  return predicted;
}

/* ==========================================================================
   SENTENCE BUILDER
   ========================================================================== */

function renderSentence(pulse = false) {
  const cleanSentence = normalizeSentence(sentence);

  syncLiveSentence(cleanSentence, pulse);

  if (!sentBox) return;

  if (cleanSentence) {
    sentBox.textContent = cleanSentence;
    sentBox.classList.remove("empty");

    if (pulse) {
      sentBox.classList.add("appended");

      setTimeout(() => {
        sentBox.classList.remove("appended");
      }, 460);
    }
  } else {
    sentBox.textContent = "Start signing to build your sentence...";
    sentBox.classList.add("empty");
  }

  updateWordCount(cleanSentence);
}

function syncLiveSentence(cleanSentence, pulse = false) {
  const text = normalizeSentence(cleanSentence);
  const words = countWords(text);

  if (liveSentPreview) {
    liveSentPreview.textContent = text || "Start signing to build your sentence...";
    liveSentPreview.classList.toggle("empty", !text);
  }

  if (liveWc) {
    liveWc.textContent = words;
  }

  if (cameraBuilder && pulse) {
    cameraBuilder.classList.add("appended");

    setTimeout(() => {
      cameraBuilder.classList.remove("appended");
    }, 460);
  }
}

function updateWordCount(value) {
  const wc = document.getElementById("wc");

  if (!wc) return;

  wc.textContent = countWords(value);
}

function onBxFocus() {
  isEditing = true;

  if (!sentBox) return;

  if (sentBox.classList.contains("empty")) {
    sentBox.textContent = sentence || "";
    sentBox.classList.remove("empty");
  }
}

function onBxBlur() {
  isEditing = false;

  if (!sentBox) return;

  sentence = normalizeSentence(sentBox.textContent || "");

  syncLiveSentence(sentence, false);

  if (!sentence) {
    renderSentence(false);
  } else {
    sentBox.textContent = sentence;
    sentBox.classList.remove("empty");
    updateWordCount(sentence);
  }
}

function onBxInput() {
  if (!sentBox) return;

  sentence = normalizeSentence(sentBox.textContent || "");

  updateWordCount(sentence);
  syncLiveSentence(sentence, false);

  if (sentence) {
    sentBox.classList.remove("empty");
  }
}

async function clearSentence() {
  try {
    await fetch("/api/hand_reset", {
      method: "POST",
      headers: {
        "Accept": "application/json"
      }
    });
  } catch (error) {
    console.warn("Reset request failed:", error);
  }

  sentence = "";
  holdCount = 0;
  lastPred = null;

  updateHold(0);
  renderSentence(false);

  toast("Sentence cleared");
}

function addSpace() {
  sentence = `${normalizeSentence(sentence)} `;

  if (sentBox && isEditing) {
    sentBox.textContent = sentence;
  }

  renderSentence(false);

  fetch("/api/hand_reset", {
    method: "POST",
    headers: {
      "Accept": "application/json"
    }
  }).catch(() => {});
}

function bkspWord() {
  const words = normalizeSentence(sentence).split(/\s+/).filter(Boolean);

  words.pop();

  sentence = words.join(" ");

  if (sentBox && isEditing) {
    sentBox.textContent = sentence;
  }

  renderSentence(false);
}

function appendWordToSentence(currentSentence, word) {
  const cleanWord = sanitizePrediction(word);

  if (!cleanWord) {
    return normalizeSentence(currentSentence);
  }

  return normalizeSentence(`${currentSentence || ""} ${cleanWord}`);
}

/* ==========================================================================
   SEND TO AI
   ========================================================================== */

async function sendSentence() {
  if (isSending) return;

  const text = isEditing
    ? normalizeSentence(sentBox?.textContent || "")
    : normalizeSentence(sentence || "");

  if (!text || text === "Start signing to build your sentence...") {
    addMsg(
      "assistant",
      "👋 Please sign something first. Hold each sign steady for it to register.",
      false
    );

    return;
  }

  isSending = true;

  addMsg("user", text, false);

  if (typing) {
    typing.classList.add("show");
  }

  if (msgs) {
    msgs.scrollTop = msgs.scrollHeight;
  }

  try {
    const response = await fetch("/api/hand_enter", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cache-Control": "no-cache"
      },
      body: JSON.stringify({
        sentence: text
      })
    });

    const data = await response.json();

    if (typing) {
      typing.classList.remove("show");
    }

    if (!response.ok || data.ok === false || data.success === false) {
      throw new Error(data.error || "Could not send sentence.");
    }

    addMsg(
      "assistant",
      data.reply || data.response || "I understand. I am here to support you.",
      true
    );

    sentence = "";
    holdCount = 0;
    lastPred = null;

    updateHold(0);
    renderSentence(false);

    fetch("/api/hand_reset", {
      method: "POST",
      headers: {
        "Accept": "application/json"
      }
    }).catch(() => {});

  } catch (error) {
    console.error("Send sentence failed:", error);

    if (typing) {
      typing.classList.remove("show");
    }

    addMsg(
      "assistant",
      error.message || "Sorry, there was an error while sending your sentence. Please try again.",
      false
    );
  } finally {
    isSending = false;
  }
}

/* ==========================================================================
   MESSAGES
   ========================================================================== */

function addMsg(role, content, autoSpeak = false) {
  if (!msgs) return;

  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const time = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });

  const speakButton =
    role === "assistant"
      ? `<button class="spkbtn" onclick="speakBtn(this)">🔊</button>`
      : "";

  div.innerHTML = `
    <div class="msg-body">${escapeHtml(content)}</div>
    <div class="msg-meta">
      ${speakButton}
      <span>${time}</span>
    </div>
  `;

  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;

  if (autoSpeak) {
    speak(content);

    const button = div.querySelector(".spkbtn");

    if (button) {
      button.classList.add("speaking");
      activeSpeakBtn = button;

      const checker = setInterval(() => {
        if (!window.speechSynthesis.speaking) {
          button.classList.remove("speaking");
          activeSpeakBtn = null;
          clearInterval(checker);
        }
      }, 300);
    }
  }
}

/* ==========================================================================
   HELPERS
   ========================================================================== */

function normalizeSentence(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function countWords(value) {
  const clean = normalizeSentence(value);

  if (!clean) return 0;

  return clean.split(/\s+/).filter(Boolean).length;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function escapeHtml(text) {
  return String(text || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(message) {
  const oldToast = document.querySelector(".toast");

  if (oldToast) {
    oldToast.remove();
  }

  const toastElement = document.createElement("div");
  toastElement.className = "toast";
  toastElement.textContent = message;

  document.body.appendChild(toastElement);

  setTimeout(() => {
    toastElement.style.opacity = "0";
    toastElement.style.transform = "translateY(10px)";
    toastElement.style.transition = ".25s ease";

    setTimeout(() => {
      toastElement.remove();
    }, 260);
  }, 3000);
}

/* ==========================================================================
   CLEANUP
   ========================================================================== */

window.addEventListener("beforeunload", () => {
  if (predInv) {
    clearInterval(predInv);
    predInv = null;
  }

  if (vid && vid.srcObject) {
    const tracks = vid.srcObject.getTracks();

    tracks.forEach((track) => {
      track.stop();
    });
  }

  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
});

/* ==========================================================================
   GLOBALS FOR INLINE HTML HANDLERS
   ========================================================================== */

window.speakBtn = speakBtn;

window.onBxFocus = onBxFocus;
window.onBxBlur = onBxBlur;
window.onBxInput = onBxInput;

window.clearSentence = clearSentence;
window.addSpace = addSpace;
window.bkspWord = bkspWord;
window.sendSentence = sendSentence;