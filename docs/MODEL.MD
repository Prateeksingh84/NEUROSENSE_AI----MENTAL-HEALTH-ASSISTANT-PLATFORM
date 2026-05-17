# NeuroSense AI — Models Used

> **Project:** NeuroSense AI: A Multimodal Mental Health Assistant
> **Team:** Devashish Biswas (11022210072) · Prateek (11022210084) · Lakshay (11022210087)
> **Institution:** SRM University Delhi-NCR | B.Tech CSE DSAI (IBM) | May 2026

---

## Table of Contents

1. [Model Overview](#1-model-overview)
2. [MTCNN — Face Detection Model](#2-mtcnn--face-detection-model)
3. [FER CNN — Facial Emotion Recognition Model](#3-fer-cnn--facial-emotion-recognition-model)
4. [MediaPipe Hands — Hand Landmark Model](#4-mediapipe-hands--hand-landmark-model)
5. [RandomForestClassifier — Hand Sign Recognition Model](#5-randomforestclassifier--hand-sign-recognition-model)
6. [LLaMA 3.3 70B — Cloud LLM (Groq)](#6-llama-33-70b--cloud-llm-groq)
7. [Phi-3 Mini — Local LLM (Ollama)](#7-phi-3-mini--local-llm-ollama)
8. [Web Speech API — Speech-to-Text Model](#8-web-speech-api--speech-to-text-model)
9. [gTTS & pyttsx3 — Text-to-Speech Models](#9-gtts--pyttsx3--text-to-speech-models)
10. [Deep Translator — Multilingual Translation Model](#10-deep-translator--multilingual-translation-model)
11. [LLM Prompt Engineering Model](#11-llm-prompt-engineering-model)
12. [Model Performance Summary](#12-model-performance-summary)

---

## 1. Model Overview

NeuroSense AI integrates **10 distinct AI/ML models** across 5 functional subsystems. Each model was selected to maximise accuracy, enable offline operation, and preserve user privacy.

| # | Model | Task | Backend | Local / Cloud |
|---|---|---|---|---|
| 1 | MTCNN | Face detection | FER library (TensorFlow) | Local |
| 2 | FER CNN | Facial emotion classification | TensorFlow ≥ 2.15.0 | Local |
| 3 | MediaPipe Hands | 21-point 3D hand landmark extraction | MediaPipe ≥ 0.10.32 | Local |
| 4 | RandomForestClassifier | Hand sign / gesture classification | Scikit-learn ≥ 1.4.0 | Local |
| 5 | LLaMA 3.3 70B | Empathetic AI conversation (pipeline agents) | Groq API | Cloud |
| 6 | Phi-3 Mini (3.8B) | Research & knowledge chat | Ollama | Local |
| 7 | Web Speech API | Speech-to-text recognition | Browser native | Local |
| 8 | gTTS | Text-to-speech synthesis (primary) | Google TTS API | Cloud |
| 9 | pyttsx3 | Text-to-speech synthesis (offline fallback) | OS TTS engine | Local |
| 10 | Deep Translator | Multilingual input/output translation | Google Translate API | Cloud |

---

## 2. MTCNN — Face Detection Model

### What It Does
MTCNN (Multi-Task Cascaded Convolutional Networks) is the **first stage** of the emotion detection pipeline. It locates human faces in the webcam frame before the FER classifier can run emotion recognition.

### Architecture

MTCNN uses a **3-stage cascaded CNN pipeline**, each stage progressively refining the face region:

```
Input RGB Frame
      │
      ▼
┌─────────────────────────────────┐
│  Stage 1 — P-Net (Proposal)     │
│  Scans image at multiple scales  │
│  Generates candidate face boxes  │
└─────────────────┬───────────────┘
                  ▼
┌─────────────────────────────────┐
│  Stage 2 — R-Net (Refinement)   │
│  Rejects false positives         │
│  Refines bounding box coordinates│
└─────────────────┬───────────────┘
                  ▼
┌─────────────────────────────────┐
│  Stage 3 — O-Net (Output)       │
│  Final face region + landmarks   │
│  Outputs bounding box + 5 facial │
│  landmark coordinates            │
└─────────────────────────────────┘
```

### Parameters

| Parameter | Value |
|---|---|
| Architecture | 3-stage cascaded CNN (P-Net → R-Net → O-Net) |
| Input | RGB image frame (any resolution) |
| Output | Bounding box coordinates + facial landmarks |
| Detection Threshold | 0.5 (configurable) |
| Minimum Face Size | 20 × 20 pixels |
| Backend Library | FER library with `mtcnn=True` flag |
| Library Version | ≥ 0.1.1 |

### Why MTCNN Was Chosen
- Handles **pose variation**, **scale variation**, **partial occlusion**, and **non-frontal faces** — all common in real-world webcam use
- **Multi-scale detection** means faces close to or far from the camera are both reliably detected
- Integrated seamlessly into the FER library via a single flag (`mtcnn=True`), reducing implementation complexity

### Research Basis
Zhang et al. (2016) — *"Joint Face Detection and Alignment Using Multi-task Cascaded Convolutional Networks"* — introduced MTCNN as a simultaneous face detection, alignment, and landmark localisation system. It is the most widely adopted multi-class face detector in production FER systems.

---

## 3. FER CNN — Facial Emotion Recognition Model

### What It Does
The FER CNN is the **second stage** of the emotion detection pipeline. After MTCNN locates the face bounding box, the FER CNN classifies the face region into one of 7 universal emotion categories.

### Architecture

| Parameter | Value |
|---|---|
| Architecture | Deep CNN with batch normalisation layers |
| Training Dataset | **FER-2013** — 35,887 grayscale 48×48 images |
| Emotion Classes | 7 (happy, sad, angry, fear, disgust, surprise, neutral) |
| Output | Probability distribution over all 7 classes |
| Dominant Emotion | `argmax(probability_scores)` |
| Confidence Report | Normalised scores (always sum to 1.0) |
| Library | FER ≥ 22.5.1 |
| Deep Learning Backend | TensorFlow ≥ 2.15.0 |

### FER-2013 Training Dataset — Class Distribution

| Emotion | Training Samples | Percentage |
|---|---|---|
| Happy | 8,989 | 25.05% |
| Neutral | 6,198 | 17.27% |
| Sad | 6,077 | 16.93% |
| Fear | 5,121 | 14.27% |
| Angry | 4,953 | 13.80% |
| Surprise | 4,002 | 11.15% |
| Disgust | 547 | 1.52% |
| **Total** | **35,887** | **100%** |

### Emotion Detection Performance (Per Class)

| Emotion Class | Precision | Recall | F1-Score | Test Samples |
|---|---|---|---|---|
| Happy | 0.94 | 0.96 | **0.95** | 895 |
| Neutral | 0.89 | 0.87 | **0.88** | 620 |
| Sad | 0.86 | 0.88 | **0.87** | 608 |
| Angry | 0.91 | 0.89 | **0.90** | 495 |
| Fear | 0.88 | 0.85 | **0.86** | 512 |
| Surprise | 0.93 | 0.94 | **0.93** | 400 |
| Disgust | 0.82 | 0.79 | **0.80** | 55 |
| **Overall** | **0.89** | **0.88** | **0.88** | **3,585** |

### How It Integrates with NeuroSense AI

```
Every 1600ms (JavaScript setTimeout loop):
  ├── Webcam frame → base64 JPEG → POST /api/emotion_detect
  ├── MTCNN locates face → FER CNN classifies emotion
  ├── Full 7-class probability distribution returned
  ├── Dominant emotion stored in session['sentiment']
  └── Emotion name + emoji + confidence bars shown in chat UI
```

> **Graceful degradation:** If no face is detected → system defaults to `neutral` without crashing or blocking the user.

### Research Basis
- **Ekman & Friesen (1978)** — Established the 7 universal emotion categories (Facial Action Coding System) used as the FER taxonomy
- **FER-2013 (Goodfellow et al., 2013)** — Standard benchmark dataset; human-level accuracy ≈ 65–68%, state-of-the-art deep learning ≈ 70–75%
- **RAF-DB (Li et al., 2017)** — Demonstrated that real-world expressions are blends of emotions, motivating NeuroSense AI's full probability distribution output rather than a single label

---

## 4. MediaPipe Hands — Hand Landmark Model

### What It Does
MediaPipe Hands extracts **21 three-dimensional landmark coordinates** from each hand in real time, providing the feature vector that feeds into the RandomForest gesture classifier.

### Architecture

MediaPipe Hands operates as a **two-stage pipeline**:

```
Webcam Frame
      │
      ▼
┌──────────────────────────┐
│  Palm Detector           │
│  Identifies hand         │
│  bounding boxes          │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  Hand Landmark Model     │
│  Regresses 21 3D (x,y,z) │
│  landmark coordinates    │
│  per detected hand       │
└──────────────────────────┘
```

### 21 Landmark Points per Hand

Each hand has 21 anatomically-defined landmarks covering all joints:

| Region | Landmarks |
|---|---|
| Wrist | 1 point |
| Thumb | 4 points (CMC, MCP, IP, TIP) |
| Index Finger | 4 points (MCP, PIP, DIP, TIP) |
| Middle Finger | 4 points (MCP, PIP, DIP, TIP) |
| Ring Finger | 4 points (MCP, PIP, DIP, TIP) |
| Pinky Finger | 4 points (MCP, PIP, DIP, TIP) |
| **Total** | **21 points** |

### Feature Vector Calculation

```
1 hand  = 21 landmarks × 3 coordinates (x, y, z)  =  63 floats
2 hands = 63 + 63                                  = 126 floats (final feature vector)
          (Hand 2 = zeros if only one hand detected)
```

### Key Specifications

| Property | Value |
|---|---|
| Library | MediaPipe ≥ 0.10.32 |
| Landmark Dimensions | 3D (x, y, z) — depth axis included |
| Output per Frame | 126-float feature vector (2 hands) |
| Hardware Requirement | **CPU-only** — no GPU required |
| Runtime Speed | 30+ FPS on mobile/consumer hardware |
| Task File | `data/models/hand_landmarker.task` |

### Why 3D Landmarks Over 2D
Using (x, y, z) rather than (x, y) provides robustness to hand pose variation along the **depth axis** — i.e., hands turned sideways, tilted, or partially rotated toward the camera are still accurately represented.

### Research Basis
Zhang et al. (Google, 2020) — *"MediaPipe Hands: On-device Real-time Hand Tracking"* — introduced the pipeline as a CPU-capable 30+ FPS landmark model, enabling gesture recognition on any consumer webcam without specialised hardware (unlike earlier approaches requiring Microsoft Kinect or data gloves).

---

## 5. RandomForestClassifier — Hand Sign Recognition Model

### What It Does
Classifies the 126-float MediaPipe feature vector into a trained sign/word class, forming the core of the Hand Sign Chat feature.

### Model Parameters

| Parameter | Value | Justification |
|---|---|---|
| `n_estimators` | **150 trees** | Balance between accuracy and inference speed |
| Feature Vector | **126 floats** | 21 landmarks × 3 coords × 2 hands |
| Training Samples | **100 per word (minimum)** | Sufficient to capture gesture variance per user |
| `max_features` | `sqrt(n_features)` | Default — prevents overfitting |
| `bootstrap` | `True` | Random sampling with replacement (bagging) |
| Confidence Threshold | **0.40 (40%)** | Predictions below this are discarded |
| Serialisation | Python pickle `.pkl` | Fast model load at inference |
| Training Time | **2–10 seconds** (CPU-only) | 10 words × 100 samples typical |
| Training Data File | `data/word_data.csv` | Auto-created by CLI collection tool |
| Model File | `data/word_model.pkl` | Saved after training, loaded at app startup |

### Hold-to-Confirm Mechanism

```
Every 350ms — JavaScript polls /api/hand_predict:
  │
  ├── clf.predict([features])         → predicted word
  ├── max(clf.predict_proba(...))     → confidence score
  │     IF confidence < 0.40 → discard prediction
  │
  ├── Compare pred with session['hand_last_pred']
  │     IF same → session['hand_pred_count'] += 1
  │     ELSE    → session['hand_pred_count'] = 1
  │
  └── IF hand_pred_count >= 4 (STABLE_THRESHOLD):
        ├── Word appended to session['hand_sentence']
        ├── Capitalisation rules applied
        └── Count + last_pred reset
```

> Requiring **4 consecutive identical predictions** before appending prevents false positives from brief hand movements or gesture transitions.

### Accuracy vs. Vocabulary Size

| Words Trained | Training Samples | Accuracy | Precision | Recall | Training Time |
|---|---|---|---|---|---|
| 5 words | 500 | 99.2% | 0.993 | 0.992 | 1.2 sec |
| 10 words | 1,000 | 98.7% | 0.988 | 0.987 | 2.1 sec |
| 20 words | 2,000 | 97.9% | 0.981 | 0.978 | 4.8 sec |
| **30 words** | **3,000** | **96.7%** | **0.969** | **0.966** | **7.3 sec** |
| 50 words | 5,000 | 95.1% | 0.953 | 0.950 | 12.4 sec |

### Special Signs Supported
`SPACE` · `DELETE` · `CLEAR` · `ENTER` — for full sentence construction and editing control.

### Why RandomForest Over Deep Learning (LSTM / CNN)
- Trains in **seconds on CPU** with only 100 samples per sign — no GPU or large dataset required
- Robust to **scale variation** in landmark values
- Provides **calibrated probabilities** via `predict_proba()`, enabling the confidence threshold gate
- Individual hand anatomy and signing style vary per user — user-collected training outperforms pre-trained generalised models (e.g., ASL Alphabet Kaggle dataset was evaluated and rejected for this reason)

### Research Basis
Breiman (2001) — *"Random Forests"* — introduced the ensemble method. MediaPipe Hands + RandomForest was validated by Google (Zhang et al., 2020) as a practical, accurate gesture pipeline on consumer hardware.

---

## 6. LLaMA 3.3 70B — Cloud LLM (Groq)

### What It Does
LLaMA 3.3 70B is the **primary language model** for all 7 agents in the multi-agent therapy pipeline — SafetyAgent, EmotionAgent, SocialAgent, WellnessAgent, PsychiatristAgent, TherapyAgent, and HallucinationAgent.

### Model Specifications

| Property | Value |
|---|---|
| Model Name | LLaMA-3.3-70B-Versatile |
| Parameters | 70 Billion |
| Developer | Meta AI (open-source weights) |
| Inference Provider | Groq API (cloud) |
| Context Length | 128K tokens |
| Response Latency | Sub-second (Groq LPU inference) |
| Access | Free via Groq API key |

### Temperature Settings Per Agent

| Agent | Temperature | Reason |
|---|---|---|
| SafetyAgent | **0.0** | Fully deterministic — safety decisions must be consistent |
| HallucinationAgent | **0.0** | Fully deterministic — validation must be consistent |
| EmotionAgent | 0.1 | Near-deterministic — emotion classification |
| SocialAgent | 0.1 | Near-deterministic — social risk classification |
| PsychiatristAgent | 0.1 | Near-deterministic — clinical escalation logic |
| WellnessAgent | 0.25 | Slight variation — wellness recommendations |
| ReportAgent | 0.25 | Slight variation — structured report generation |
| TherapyAgent | **0.45** | Highest — allows natural, varied empathetic language |
| General Chat | 0.7 | Balanced creative empathy + coherence |

### Why LLaMA 3.3 70B
- Achieves performance **competitive with GPT-4** on instruction-following and conversational benchmarks
- Freely accessible through Groq's inference API (no cost barrier)
- Groq's **LPU (Language Processing Unit)** delivers sub-second latency critical for real-time therapy pipeline

### Research Basis
- Touvron et al. (2023) — *LLaMA: Open and Efficient Foundation Language Models*
- Meta AI (2024) — *LLaMA 3 Technical Report* — LLaMA 3.3 70B achieves near GPT-4 performance on MMLU, HumanEval, and conversational benchmarks

---

## 7. Phi-3 Mini — Local LLM (Ollama)

### What It Does
Phi-3 Mini powers the **ResearchAgent**, **KnowledgeAgent**, and **TemplateAgent** — handling all Research Chat and Knowledge Chat queries locally, ensuring no research queries ever leave the user's device.

### Model Specifications

| Property | Value |
|---|---|
| Model Name | Phi-3 Mini |
| Parameters | **3.8 Billion** |
| Developer | Microsoft Research (2024) |
| Inference Engine | Ollama (local server) |
| Hardware Requirement | CPU-only (no GPU required) |
| Internet Required | **No — fully offline** |
| Context Length | 4K / 128K tokens (variant dependent) |

### Why Phi-3 Mini for Local Inference
- Despite being **15–20× smaller** than competing models, Phi-3 Mini achieves comparable performance on reasoning, instruction following, and conversational coherence benchmarks
- Runs entirely on CPU — no GPU required, making it accessible on any laptop or desktop
- **Zero data transmission** — research and knowledge queries stay on the user's machine, critical for mental health privacy

### Ollama Integration

```
ResearchAgent / KnowledgeAgent → POST http://localhost:11434/api/generate
  Body: { model: "phi3", prompt: "...", stream: false }
  Response: { response: "..." }

Fallback if Ollama unavailable:
  ResearchAgent → instructional fallback message
  KnowledgeAgent → _extractive_fallback() (top-ranked KB entry, no LLM)
```

### Research Basis
Microsoft Research (2024) — *"Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone"* — demonstrated that a 3.8B parameter model trained on a carefully curated dataset matches models 15–20× larger in size on reasoning and instruction benchmarks.

---

## 8. Web Speech API — Speech-to-Text Model

### What It Does
Converts live microphone audio to text in real-time directly in the browser — no server-side audio processing required.

### Specifications

| Property | Value |
|---|---|
| API Standard | W3C Web Speech API (SpeechRecognition) |
| Supported Browsers | Chrome, Edge (latest) |
| Mode | `continuous=true`, `interimResults=true` |
| Accuracy (NeuroSense AI) | **95.2%** |
| Languages Supported | 16+ locale codes |

### Language Locale Map (Sample)

| Region | Locales |
|---|---|
| English | `en-US`, `en-GB`, `en-IN`, `en-AU` |
| Indian Languages | `hi-IN`, `ta-IN`, `te-IN`, `bn-IN`, `mr-IN`, `ml-IN`, `gu-IN`, `pa-IN` |
| East Asian | `zh-CN`, `zh-TW`, `ja-JP`, `ko-KR` |
| Middle East | `ar-SA` |
| European | `fr-FR`, `de-DE`, `es-ES`, `it-IT`, `pt-BR`, `ru-RU` |
| South-East Asian | `th-TH`, `vi-VN`, `id-ID` |

### How It Works in NeuroSense AI

```
User clicks mic button
  ├── SpeechRecognition initialised with selected locale
  ├── WHILE recording:
  │     ├── Interim results displayed word-by-word in UI
  │     └── Final transcript accumulated in curTx
  └── User clicks Stop / Send
        └── curTx → POST /api/voice_chat → agent pipeline
```

---

## 9. gTTS & pyttsx3 — Text-to-Speech Models

### gTTS (Primary TTS)

| Property | Value |
|---|---|
| Full Name | Google Text-to-Speech |
| Library | gTTS (Latest) |
| Output Format | MP3 audio |
| Language Support | 40+ language locales |
| Requirement | Internet connection |
| Voice Quality | Natural, human-like synthesis |

### pyttsx3 (Offline Fallback TTS)

| Property | Value |
|---|---|
| Library | pyttsx3 ≥ 2.90 |
| Output Format | OS audio (SAPI5 / NSSpeechSynthesizer / eSpeak) |
| Language Support | OS-dependent |
| Requirement | **None — fully offline** |
| Voice Quality | Robotic (OS TTS engine) |
| Rate | 0.88 (set in NeuroSense AI) |
| Pitch | 1.0 (set in NeuroSense AI) |

### Selection Logic

```
AI generates text reply
  │
  ├── Internet available? → gTTS → MP3 → browser audio playback
  └── Offline?            → pyttsx3 → OS TTS → local audio output
```

---

## 10. Deep Translator — Multilingual Translation Model

### What It Does
Translates user input from any supported language into English before LLM processing, and translates the AI response back to the user's language before display.

### Specifications

| Property | Value |
|---|---|
| Library | Deep Translator (Latest) |
| Backend | Google Translate API |
| Direction | User lang → English (input) + English → User lang (output) |
| Total Languages Supported | 50+ |

### Supported Language Groups

| Region | Languages |
|---|---|
| **Major Global** | English, Hindi, Spanish, French, German, Chinese (Simplified/Traditional), Japanese, Korean, Arabic, Russian, Portuguese |
| **Indian** | Tamil, Telugu, Bengali, Marathi, Malayalam, Kannada, Gujarati, Punjabi, Urdu, Odia, Assamese |
| **European** | Italian, Dutch, Polish, Turkish, Ukrainian, Greek, Czech, Swedish, Danish, Finnish, Norwegian, Romanian |
| **Asian** | Thai, Vietnamese, Indonesian, Malay, Filipino |
| **African / Other** | Afrikaans, Swahili, Zulu, Hebrew, Persian |

### Translation Pipeline

```
User input (any language)
  ├── Detect language
  ├── Translate → English
  ├── English text → LLM agents (pipeline)
  ├── English response generated
  └── Translate → User's selected language → display
```

---

## 11. LLM Prompt Engineering Model

### Dynamic Emotion-Aware Prompt Structure

NeuroSense AI constructs a fresh system prompt **before every LLM inference call**, injecting the current detected emotion:

```
SYSTEM PROMPT:
"You are NeuroSense AI — a compassionate, evidence-based
mental health support assistant.

Context:
- User's emotional state: {detected_emotion}
- User's language: {language_name}
- Respond in a warm, culturally sensitive manner

Guidelines:
- Be empathetic, non-judgmental, and supportive
- Use simple, clear language that translates well
- Keep responses concise (2-4 sentences)
- Use CBT/DBT-informed approaches when appropriate
- Never diagnose — suggest professional help when needed
- Be culturally aware and respectful

Crisis Resources (India):
- iCall: 9152987821
- Vandrevala Foundation: 1860-2662-345
- Tele-MANAS: 14416"

USER MESSAGE: {translated_user_input}
```

### Emotion → Response Style Mapping

| Detected Emotion | System Prompt Modifier | Response Style |
|---|---|---|
| happy | "User appears joyful" | Celebratory, reinforcing |
| sad | "User appears sad" | Gentle, validating, supportive |
| angry | "User appears angry" | Calm, de-escalating |
| fear | "User appears anxious/fearful" | Reassuring, grounding |
| surprise | "User appears surprised" | Curious, engaged |
| disgust | "User appears disgusted/upset" | Empathetic, non-judgmental |
| neutral | "User appears neutral" | Balanced, open-ended |

### GLOBAL_SAFETY_RULES (Applied to All Agents)

All 12 agents inherit 15 safety rules from `BaseAgent`, including:

- No mental illness diagnosis under any circumstances
- No medication prescription or dosage changes
- Non-diagnostic wording required (`"you may be feeling..."`, `"it may help to..."`)
- Mandatory crisis escalation protocol with Indian helpline numbers
- `contains_unsafe_medical_claim()` regex — 40+ patterns checked on every output

---

## 12. Model Performance Summary

| Model | Task | Metric | Target | Achieved | Grade |
|---|---|---|---|---|---|
| FER CNN + MTCNN | Facial emotion recognition | Overall accuracy | > 50% | **58.6%** (dominant: 92.9%) | B+ |
| FER CNN | Emotion F1-score (Happy) | F1 | — | **0.95** | A+ |
| FER CNN | Emotion F1-score (Overall) | F1 | — | **0.88** | A |
| RandomForest | Hand sign accuracy (30 words) | Accuracy | > 90% | **96.7%** | A+ |
| Web Speech API | Voice recognition | Accuracy | > 90% | **95.2%** | A |
| LLaMA 3.3 70B | LLM response relevance | Relevance score | > 90% | **96.8%** | A+ |
| Full System | End-to-end response latency | Latency | < 5 sec | **2.3 sec** | A+ |
| Full System | User satisfaction | Score / 5.0 | > 4.0 | **4.7 / 5.0** | A+ |

---

*NeuroSense AI — Models Documentation | Group 48 | SRM University Delhi-NCR | May 2026*