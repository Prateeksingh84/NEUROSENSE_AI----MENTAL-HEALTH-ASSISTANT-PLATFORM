# NeuroSense AI — Objectives of the Project

> **Project:** NeuroSense AI: A Multimodal Mental Health Assistant
> **Team:** Devashish Biswas (11022210072) · Prateek (11022210084) · Lakshay (11022210087)
> **Institution:** SRM University Delhi-NCR | B.Tech CSE DSAI (IBM) | May 2026

---

## Overview

The NeuroSense AI project has been developed around **six major goals**, each formulated with precise technical specifications. Together they form a unified system that bridges emotional intelligence with computational intelligence for accessible, privacy-preserving mental health support.

---

## Objective 1 — Real-Time Facial Emotion Recognition

Continuously monitor the user's emotional state via webcam throughout every active chat session, injecting the detected emotion directly into all LLM inference prompts.

- **Polling interval:** JavaScript `setTimeout` loop fires every **1600 milliseconds**
- **Detection pipeline:** FER algorithm combined with **MTCNN** (Multi-task Cascaded Convolutional Networks) for face localisation and emotion classification
- **Emotion categories:** 7 Ekman universal emotions — `happy`, `sad`, `angry`, `fear`, `disgust`, `surprise`, `neutral`
- **Session storage:** Detected emotion stored in `session['sentiment']` (Flask session variable) for consumption by the LLM inference layer
- **UI feedback:** Emotion name, corresponding emoji, and confidence score bars rendered live inside the chat GUI
- **Graceful degradation:** Face not found / insufficient lighting / partial obstruction → defaults to `neutral` without crashing

---

## Objective 2 — Empathetic AI Conversational Backend

Build a dual-model AI backend capable of running entirely offline while also supporting a high-speed cloud model, with every response grounded in therapeutic frameworks and real-time emotional context.

- **Local model:** Deploy **Phi-3 Mini (3.8B parameters)** via Ollama — zero internet connectivity required during inference
- **Cloud model:** **LLaMA 3.3 70B** via Groq API as an alternative, switchable via single configuration change
- **Emotion-aware prompting:** System prompt is dynamically constructed from the detected emotion before every new LLM inference call
- **Safety filtering:** Custom content safety filter screens every user input for harmful language *before* it reaches the LLM
- **Therapeutic grounding:** Responses target empathy, clinical grounding in **CBT / DBT** frameworks, and contextual awareness of the user's emotional state
- **Temperature setting:** Maintained at `0.7` — balancing creative empathetic language with response coherence

---

## Objective 3 — Hand Sign Recognition and Accessibility

Design a complete two-phase sign language pipeline accessible to users with speech or hearing impairments, with no dependency on pre-existing sign language datasets.

- **Phase 1 — Data Collection & Training (CLI-based):**
  - MediaPipe Hands extracts **21 3D landmark coordinates per hand** → 63 features per hand → **126 total features per two-hand frame**
  - **RandomForestClassifier (150 decision trees)** trained on user-collected gesture samples (typically 100 samples per sign class)
  - Vocabulary Management supports word removal and automatic model re-training for expansion

- **Phase 2 — Real-Time Web Inference:**
  - **Hold-to-confirm mechanism:** Requires **4 consecutive identical high-confidence predictions** before a word is appended — prevents false positives
  - Confidence threshold: predictions below `0.40` are discarded
  - Special signs supported: `SPACE`, `DELETE`, `CLEAR`, `ENTER` for full sentence construction control

- **Current performance:** 96.7% accuracy across 30 trained sign classes

---

## Objective 4 — Voice Chat Mode

Enable fully hands-free interaction with NeuroSense AI in multiple languages using browser-native speech input and server-side speech output.

- **Speech-to-Text:** Web Speech API `SpeechRecognition` for continuous, real-time browser speech-to-text conversion
- **Multilingual support:** 16+ language locale codes mapped — `en-US`, `hi-IN`, `ta-IN`, `te-IN`, `ar-SA`, `zh-CN`, and more
- **Text-to-Speech:** `pyttsx3` / `gTTS` integration on the server side producing MP3 audio responses
- **UI controls:** Microphone on/off toggle with waveform visualisation confirming recording status
- **Live transcript:** Real-time word-by-word transcript displayed while the user is speaking
- **Performance:** 95.2% speech recognition accuracy

---

## Objective 5 — Wellness Dashboard

Provide a comprehensive set of evidence-backed self-care tools, wellbeing tracking, and crisis resources — extending NeuroSense AI beyond conversation into active mental wellness support.

- **Mood trend visualisation:** Session emotion history charted using **Chart.js** for longitudinal self-awareness
- **Breathing exercises:**
  - Box Breathing (4s inhale → 4s hold → 4s exhale → 4s hold) with animated interactive timer
  - 4-7-8 Breathing technique guide with timer
- **Grounding technique:** 5-4-3-2-1 sensory grounding method for acute anxiety management
- **CBT-inspired activities:** Gratitude journaling, habit tracking, and a community affirmations wall
- **Crisis helplines** — displayed prominently throughout the application:

  | Helpline | Number |
  |---|---|
  | Tele-MANAS | 14416 |
  | KIRAN | 1800-599-0019 |
  | iCall (TISS) | 9152987821 |
  | Vandrevala Foundation | 1860-2662-345 |
  | AASRA | 022-27546669 |

---

## Objective 6 — Security and Ethical AI

Ensure that every layer of NeuroSense AI — from authentication to inference — upholds user privacy, data security, and responsible AI principles.

- **Session protection:** Flask session guard redirects all unauthenticated chat requests to the login page before any data is processed
- **Pre-LLM content censorship:** Custom-built prohibited words database screens all inputs before they reach the language model
- **PII non-storage policy:** Personally Identifiable Information is not retained beyond the active session duration
- **Local-only inference:** All model inference — emotion detection, language model calls (via Ollama), and gesture recognition — runs exclusively on the user's local machine; no personal health data transmitted to third-party servers
- **Clinical disclaimer:** An explicit disclaimer is displayed throughout the application reminding users that NeuroSense AI is a supportive tool and **not a substitute for professional mental health care**

---

## Objective Summary Table

| # | Objective | Key Technology | Measured Outcome |
|---|---|---|---|
| 1 | Real-Time Facial Emotion Recognition | FER + MTCNN + OpenCV | 58.6% FER accuracy (dominant: 92.9%) |
| 2 | Empathetic AI Conversational Backend | Phi-3 Mini (Ollama) / LLaMA 3.3 70B (Groq) | Satisfaction score: 4.7 / 5.0 |
| 3 | Hand Sign Recognition & Accessibility | MediaPipe + RandomForest (150 trees) | 96.7% accuracy, 30 sign classes |
| 4 | Voice Chat Mode | Web Speech API + pyttsx3 / gTTS | 95.2% speech recognition accuracy |
| 5 | Wellness Dashboard | Chart.js + CBT tools + crisis helplines | Comprehensive wellbeing support |
| 6 | Security & Ethical AI | Flask sessions + RLS + local inference | Zero third-party health data exposure |

---

*NeuroSense AI — Objectives of the Project | Group 48 | SRM University Delhi-NCR | May 2026*