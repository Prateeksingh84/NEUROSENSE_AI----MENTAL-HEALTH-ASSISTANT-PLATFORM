/* ==========================================================================
   NeuroSense AI — Voice Chat
   UPDATED: Stops AI voice when changing mode / leaving page
   ========================================================================== */

let recognition = null;
let isListening = false;
let synth = window.speechSynthesis;
let activeAudioElements = [];

document.addEventListener("DOMContentLoaded", () => {
  initSpeechRecognition();
  initVoiceButtons();
  initVoiceCleanupEvents();
});

/* ==========================================================================
   SPEECH RECOGNITION
   ========================================================================== */

function initSpeechRecognition(){
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    toast("Speech recognition is not supported in this browser");
    return;
  }

  recognition = new SpeechRecognition();

  recognition.lang = document.body.dataset.lang || "en-IN";
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onstart = () => {
    isListening = true;
    setVoiceStatus("Listening...");
    document.body.classList.add("listening");
  };

  recognition.onresult = (event) => {
    let text = "";

    for(let i = event.resultIndex; i < event.results.length; i++){
      text += event.results[i][0].transcript;
    }

    const input = document.getElementById("voiceInput");

    if(input){
      input.value = text;
    }
  };

  recognition.onerror = (event) => {
    console.warn("Voice recognition error:", event.error);
    toast("Voice error: " + event.error);
    stopListening();
  };

  recognition.onend = () => {
    isListening = false;
    document.body.classList.remove("listening");
    setVoiceStatus("Ready");
  };
}

/* ==========================================================================
   BUTTON EVENTS
   ========================================================================== */

function initVoiceButtons(){
  const micBtn = document.getElementById("micBtn");
  const sendBtn = document.getElementById("voiceSendBtn");
  const stopBtn = document.getElementById("stopSpeechBtn");

  if(micBtn){
    micBtn.addEventListener("click", () => {
      if(isListening){
        stopListening();
      }else{
        startListening();
      }
    });
  }

  if(sendBtn){
    sendBtn.addEventListener("click", sendVoiceMessage);
  }

  if(stopBtn){
    stopBtn.addEventListener("click", stopAllVoiceAudio);
  }

  const voiceInput = document.getElementById("voiceInput");

  if(voiceInput){
    voiceInput.addEventListener("keydown", (e) => {
      if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        sendVoiceMessage();
      }
    });
  }
}

/* ==========================================================================
   START / STOP LISTENING
   ========================================================================== */

function startListening(){
  if(!recognition){
    toast("Speech recognition is not available");
    return;
  }

  try{
    stopSpeakingOnly();
    recognition.start();
  }catch(err){
    console.warn("Could not start recognition:", err);
  }
}

function stopListening(){
  try{
    if(recognition && isListening){
      recognition.stop();
    }
  }catch(err){
    console.warn("Could not stop recognition:", err);
  }

  isListening = false;
  document.body.classList.remove("listening");
  setVoiceStatus("Ready");
}

/* ==========================================================================
   SEND VOICE MESSAGE
   ========================================================================== */

async function sendVoiceMessage(){
  const input = document.getElementById("voiceInput");
  const text = input ? input.value.trim() : "";

  if(!text){
    toast("Please speak or type a message");
    return;
  }

  stopListening();

  appendMessage("user", text);

  if(input){
    input.value = "";
  }

  appendTyping();

  try{
    const res = await fetch("/api/voice_chat", {
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        message:text
      })
    });

    const data = await res.json();

    removeTyping();

    if(data.ok === false){
      toast(data.error || "Voice chat failed");
      return;
    }

    const reply = data.reply || "I am here with you.";

    appendMessage("assistant", reply);

    speak(reply);

  }catch(err){
    console.error(err);
    removeTyping();
    toast("Voice chat failed");
  }
}

/* ==========================================================================
   TEXT TO SPEECH
   ========================================================================== */

function speak(text){
  if(!text){
    return;
  }

  stopSpeakingOnly();

  if(!synth){
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);

  utterance.lang = document.body.dataset.lang || "en-IN";
  utterance.rate = 0.92;
  utterance.pitch = 1;
  utterance.volume = 1;

  utterance.onstart = () => {
    setVoiceStatus("AI speaking...");
  };

  utterance.onend = () => {
    setVoiceStatus("Ready");
  };

  utterance.onerror = () => {
    setVoiceStatus("Ready");
  };

  synth.speak(utterance);
}

function stopSpeakingOnly(){
  try{
    if(window.speechSynthesis){
      window.speechSynthesis.cancel();
    }
  }catch(err){
    console.warn("Speech synthesis stop error:", err);
  }
}

function stopSpeaking(){
  stopAllVoiceAudio();
}

/* ==========================================================================
   STOP EVERYTHING WHEN CHANGING MODE / LEAVING PAGE
   ========================================================================== */

function stopAllVoiceAudio(){
  try{
    // Stop browser text-to-speech
    if(window.speechSynthesis){
      window.speechSynthesis.cancel();
    }

    // Stop speech recognition mic
    if(recognition && isListening){
      recognition.stop();
    }

    isListening = false;

    // Stop any HTML audio element
    document.querySelectorAll("audio").forEach((audio) => {
      try{
        audio.pause();
        audio.currentTime = 0;
      }catch(err){}
    });

    // Stop tracked audio elements
    activeAudioElements.forEach((audio) => {
      try{
        audio.pause();
        audio.currentTime = 0;
      }catch(err){}
    });

    activeAudioElements = [];

    document.body.classList.remove("listening");

    setVoiceStatus("Ready");

  }catch(err){
    console.warn("Voice cleanup error:", err);
  }
}

function initVoiceCleanupEvents(){

  // Page close / refresh / route change
  window.addEventListener("beforeunload", () => {
    stopAllVoiceAudio();
  });

  // Browser back/forward cache handling
  window.addEventListener("pagehide", () => {
    stopAllVoiceAudio();
  });

  // When tab is hidden
  document.addEventListener("visibilitychange", () => {
    if(document.hidden){
      stopAllVoiceAudio();
    }
  });

  // Stop voice when clicking navigation/mode links
  document.addEventListener("click", function(e){
    const link = e.target.closest("a");

    if(!link){
      return;
    }

    const href = link.getAttribute("href") || "";

    const shouldStop =
      href.includes("/normal_chat") ||
      href.includes("/voice_chat") ||
      href.includes("/hand_chat") ||
      href.includes("/mode") ||
      href.includes("/dashboard") ||
      href.includes("/logout") ||
      href.includes("/auth") ||
      href.includes("/profile") ||
      href.includes("/settings");

    if(shouldStop){
      stopAllVoiceAudio();
    }
  });

  // Stop voice when submitting logout/change-mode forms
  document.addEventListener("submit", function(){
    stopAllVoiceAudio();
  });
}

/* ==========================================================================
   MESSAGE UI
   ========================================================================== */

function appendMessage(role,text){
  const box = document.getElementById("messages");

  if(!box){
    return;
  }

  const div = document.createElement("div");

  div.className = "message " + (
    role === "user" ? "user" : "assistant"
  );

  div.innerHTML = `
    <div class="msg-avatar">
      ${role === "user" ? "U" : "AI"}
    </div>

    <div>
      <div class="msg-bubble">
        ${escapeHtml(text)}
      </div>

      <div class="msg-time">
        ${new Date().toLocaleTimeString([], {
          hour:"2-digit",
          minute:"2-digit"
        })}
      </div>
    </div>
  `;

  box.appendChild(div);

  box.scrollTop = box.scrollHeight;
}

function appendTyping(){
  const box = document.getElementById("messages");

  if(!box){
    return;
  }

  removeTyping();

  const div = document.createElement("div");

  div.className = "message assistant";
  div.id = "typingBubble";

  div.innerHTML = `
    <div class="msg-avatar">
      AI
    </div>

    <div class="msg-bubble">
      <div class="typing">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;

  box.appendChild(div);

  box.scrollTop = box.scrollHeight;
}

function removeTyping(){
  const typing = document.getElementById("typingBubble");

  if(typing){
    typing.remove();
  }
}

/* ==========================================================================
   STATUS HELPERS
   ========================================================================== */

function setVoiceStatus(text){
  const el = document.getElementById("voiceStatus");

  if(el){
    el.textContent = text;
  }
}

function escapeHtml(text){
  return String(text)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;");
}

/* ==========================================================================
   TOAST
   ========================================================================== */

function toast(message){
  const t = document.createElement("div");

  t.className = "toast";
  t.textContent = message;

  document.body.appendChild(t);

  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transform = "translateY(12px)";
    t.style.transition = ".25s";

    setTimeout(() => {
      t.remove();
    }, 300);

  }, 3000);
}

/* ==========================================================================
   MAKE FUNCTION GLOBAL FOR HTML onclick=""
   ========================================================================== */

window.stopAllVoiceAudio = stopAllVoiceAudio;
window.stopSpeaking = stopSpeaking;
window.stopListening = stopListening;