# NeuroSense AI — A Multimodal Mental Health Assistant

> **Major Project | B.Tech CSE (Data Science & Artificial Intelligence) with IBM**
> SRM University Delhi-NCR | May 2026
> **Group 48** — Devashish Biswas (11022210072) · Prateek (11022210084) · Lakshay (11022210087)
> **Guide:** Mr. Anand Singh, Assistant Professor (CSE)

---

## What is NeuroSense AI?

NeuroSense AI is a **locally deployed, privacy-preserving, multimodal AI mental health assistant** built as a single Flask web application. It is the first open-source system to combine three simultaneous input modalities — typed text, live voice, and hand gestures — with real-time facial emotion recognition, all within one coherent therapeutic conversation interface.

The system does **not** diagnose, prescribe medication, or replace licensed professionals. It is a **first-response support tool** that makes mental wellness assistance accessible 24/7, at zero cost, in 44 languages, including 11 Indian languages — without requiring internet connectivity for core inference.

---

## The Core Problem It Solves

| Barrier | Scale |
|---|---|
| People with mental disorders globally | 970 million (WHO, 2023) |
| Indians receiving adequate treatment | < 10–12% |
| Psychiatrists per 100,000 people in India | ~1 (WHO recommendation: 3) |
| Cost of private therapy in India | ₹1,500–₹5,000 per session |
| Annual global lost productivity (untreated mental illness) | $1 trillion |
| Sign language users worldwide with zero AI mental health access | 70 million+ |

Existing platforms (Woebot, Wysa, Replika) are **entirely text-based**, cloud-dependent, and emotionally blind — they respond to what a user *says*, not how they *feel*. NeuroSense AI is engineered to also respond to how a person feels — as revealed through facial expressions, voice, and gestures.

---

## Five Core AI Components

### 1. Real-Time Facial Emotion Recognition
- **Library:** FER (Facial Emotion Recognition) with `mtcnn=True`
- **Face Detector:** MTCNN — 3-stage cascaded CNN (P-Net → R-Net → O-Net)
- **Classifier:** Deep CNN trained on FER-2013 (35,887 grayscale 48×48 images)
- **Emotions detected:** Happy, Sad, Angry, Fear, Disgust, Surprise, Neutral (7 classes)
- **Polling interval:** Every 1,600ms via JavaScript `setInterval`
- **Performance:** Overall F1-Score 88.6%; Happy class F1 = 0.95
- **Key mechanism:** Detected emotion stored in `session['sentiment']` and injected into every LLM system prompt dynamically

### 2. Empathic AI Conversation (LLM Backend)
- **Primary model:** LLaMA-3.3-70B-Versatile via **Groq Cloud API** (fast, scalable)
- **Local fallback:** Phi-3 Mini (3.8B parameters) via **Ollama** (offline, private)
- **Prompt architecture:** Dynamic system prompt construction embedding detected emotion + language + CBT/DBT guidelines
- **Average response time:** 1,400ms (Groq API), 9,100ms (local CPU-only)
- **Safety layer:** Pre-LLM content filter + post-LLM hallucination checker

### 3. Voice Chat (Speech-to-Text + Text-to-Speech)
- **STT:** Browser Web Speech API — 16+ locale codes, 95.2% accuracy (quiet environment)
- **TTS Primary:** gTTS (Google Text-to-Speech) — MP3 streaming
- **TTS Fallback:** pyttsx3 (fully offline)
- **Languages:** 44 languages with locale-mapped voice recognition

### 4. Hand Sign Chat (Gesture-Based Communication)
- **Landmark extraction:** MediaPipe Hands — 21 3D landmarks per hand
- **Feature vector:** 126 floats (21 × 3 coords × 2 hands; zeros if one hand absent)
- **Classifier:** RandomForestClassifier — 150 decision trees
- **Training:** 100 samples per sign word, trains in 2–10 seconds on CPU
- **Stability mechanism:** Hold-to-confirm — word appended only after 4 consecutive stable predictions (~1.4 seconds of hold time)
- **Accuracy:** 96.7% at 30-word vocabulary, 99.2% at 5-word vocabulary
- **Target users:** Speech-impaired and hearing-impaired individuals

### 5. Mental Wellbeing Support Tools (Wellness Dashboard)
- Mood tracking + emotion frequency visualization (Chart.js)
- Box breathing (4-4-4-4 cycle) + 4-7-8 breathing animations
- CBT thought records + DBT TIPP skill
- Gratitude journaling + habit tracker
- 5-4-3-2-1 grounding exercise
- Crisis toolkit with Indian helplines: **Tele-MANAS (14416)**, **KIRAN (1800-599-0019)**, **iCall (9152987821)**, **Vandrevala Foundation (1860-2662-345)**

---

## System Performance Summary

| Metric | Result | Target | Status |
|---|---|---|---|
| Emotion Detection (Overall F1) | 88.6% | > 85% | ✅ PASS |
| Hand Sign Accuracy (30-word vocab) | 96.7% | > 90% | ✅ PASS |
| Voice Recognition (quiet, English) | 95.2% | > 90% | ✅ PASS |
| LLM Response Relevance (human eval) | 96.8% | > 90% | ✅ PASS |
| End-to-End Latency (Groq mode) | ~2.3 sec | < 5 sec | ✅ PASS |
| System RAM Usage (full runtime) | ~3.5 GB | < 6 GB | ✅ PASS |
| Content Filter Accuracy | 100% | 100% | ✅ PASS |
| Session Security (unauth block) | 100% | 100% | ✅ PASS |
| User Satisfaction (UAT, 30 users) | 4.7 / 5.0 | > 4.0 | ✅ PASS |
| Language Support | 44 languages | > 10 | ✅ PASS |
| All Test Cases (TC-01 to TC-20) | 20 / 20 | 20 / 20 | ✅ PASS |
| **Overall System Score** | **9.1 / 10** | > 8.0 | ✅ PASS |

---

## Technology Stack at a Glance

| Layer | Technology | Version |
|---|---|---|
| Backend Framework | Flask | ≥ 3.0.0 |
| Primary LLM | LLaMA-3.3-70B via Groq | Latest |
| Local LLM | Phi-3 Mini via Ollama | Latest |
| Emotion Detection | FER + MTCNN + OpenCV | ≥ 22.5.1 |
| Hand Tracking | MediaPipe | ≥ 0.10.32 |
| Gesture Classifier | Scikit-learn RandomForest | ≥ 1.4.0 |
| Deep Learning Backend | TensorFlow | ≥ 2.15.0 |
| Image Processing | OpenCV + NumPy | ≥ 4.9.0 / 1.26.0 |
| TTS | gTTS (primary) + pyttsx3 (fallback) | Latest |
| STT | Web Speech API (browser native) | — |
| Translation | deep-translator (Google) | Latest |
| Database / Auth | Supabase (PostgreSQL + RLS + Auth) | Latest |
| Frontend Charts | Chart.js | 4.4.1 |
| Frontend Fonts | Google Fonts (Outfit, DM Sans, JetBrains Mono) | — |
| Data Serialization | CSV + Pickle | Built-in |
| Language | Python | 3.11 recommended |
| OS (Recommended) | Ubuntu 22.04 LTS | — |
| Browser | Chrome / Edge (Web Speech API support) | Latest |

---

## Project Directory Structure

```
neurosense_ai/
│
├── app.py                        ← Main Flask application (all routes + API)
├── hs_module.py                  ← Hand sign training CLI + inference engine
├── generate_report.py            ← PDF/CSV report generator
├── requirements.txt              ← All pip dependencies
│
├── agents/                       ← Multi-agent AI pipeline
│   ├── base_agent.py             ← Shared Groq LLM caller + safety rules
│   ├── orchestrator.py           ← run_safe_therapy_pipeline()
│   ├── safety_agent.py           ← Crisis + risk classification
│   ├── emotion_agent.py          ← Emotional state synthesis
│   ├── social_agent.py           ← Social wellbeing analysis
│   ├── therapy_agent.py          ← CBT/DBT response generation
│   ├── wellness_agent.py         ← 5 wellness recommendations
│   ├── psychiatrist_agent.py     ← Professional referral guidance
│   ├── hallucination_agent.py    ← Response safety validation
│   ├── research_agent.py         ← Ollama-based mental health education
│   ├── template_agent.py         ← Research Chat template selection
│   ├── scope_guard_agent.py      ← Knowledge Chat scope enforcement
│   ├── knowledge_agent.py        ← Grounded KB answer generation
│   └── report_agent.py           ← Assessment + Solution report data
│
├── utils/
│   ├── supabase_client.py        ← Supabase public + service role clients
│   ├── supabase_user_management.py ← Profile, usage, avatar management
│   ├── wellbeing_utils.py        ← Check-in scoring + risk calculation
│   ├── professional_help.py      ← External referral guidance
│   ├── knowledge_store.py        ← Knowledge Chat history (local JSON)
│   ├── template_store.py         ← Template CRUD (local + Supabase)
│   ├── ollama_client.py          ← Local Ollama client wrapper
│   └── translation_helpers.py   ← Translation utilities
│
├── sql/
│   ├── supabase_schema.sql       ← Core 9-table schema
│   ├── supabase_enhanced_user_management.sql ← Enhanced profile + usage
│   ├── supabase_rls.sql          ← All Row Level Security policies
│   ├── wellbeing_checkins.sql    ← Check-in table
│   ├── knowledge_chat.sql        ← KB chat history table
│   ├── mental_health_templates.sql ← Template library table
│   └── professional_help.sql     ← Referral log table
│
├── templates/                    ← Jinja2 HTML templates
│   ├── index.html                ← Landing page
│   ├── login.html                ← Auth / registration
│   ├── mode_select.html          ← Mode selection + wellbeing check-in
│   ├── normal_chat.html          ← Text Chat with emotion sidebar
│   ├── voice_chat.html           ← Voice Chat with waveform
│   ├── hand_chat.html            ← Sign Language Chat
│   ├── dashboard.html            ← Insights dashboard
│   ├── analytics.html            ← Analytics charts
│   ├── session_history.html      ← Full session history viewer
│   ├── best_practices.html       ← CBT/DBT exercises
│   ├── support.html              ← Crisis support page
│   ├── research_chat.html        ← Ollama-powered research Q&A
│   ├── knowledge_chat.html       ← Grounded mental-health KB chat
│   ├── templates.html            ← Template library
│   ├── reports.html              ← Report download hub
│   ├── assessment_report.html    ← Mental Wellness Assessment
│   ├── solution_report.html      ← Personalized Wellness Plan
│   ├── profile.html              ← User profile management
│   ├── settings.html             ← User settings
│   └── admin_dashboard.html      ← Admin-only analytics
│
├── static/
│   ├── css/                      ← Per-page stylesheets
│   ├── js/                       ← Per-page JavaScript modules
│   └── uploads/avatars/          ← User avatar storage
│
├── data/                         ← Auto-created at runtime
│   ├── word_data.csv             ← Hand sign training data
│   ├── word_model.pkl            ← Trained RandomForest model
│   ├── research_chat_history.json ← Research Chat history (local)
│   └── knowledge_chat_history.json ← Knowledge Chat history (local)
│
├── knowledge/                    ← Approved mental-health knowledge base
│   └── retriever.py              ← KB retrieval (vector/keyword)
│
├── models/
│   └── hand_landmarker.task      ← MediaPipe task model
│
└── neurosense_data.json          ← Local session + emotion + report store
```

---

## Quick Start

```bash
# 1. Clone and enter project
git clone <repo-url> && cd neurosense_ai

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (.env file)
GROQ_API_KEY=gsk_xxxxxxxxxxxx
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SECRET_KEY=your-flask-secret-key
ADMIN_EMAILS=your@email.com

# 5. Run the application
python app.py
# → Select 1 for Web App → visit http://localhost:5000

# 6. (Optional) Train hand signs
python app.py
# → Select 2 for Hand Sign Training CLI
```

---

## UN Sustainable Development Goals Alignment

| SDG | Goal | NeuroSense AI Contribution |
|---|---|---|
| SDG 3 | Good Health and Well-being | 24/7 mental wellness support at zero cost |
| SDG 4 | Quality Education | Mental health education via dashboard resources |
| SDG 10 | Reduced Inequalities | Sign language support, offline capability, 44 languages |
| SDG 17 | Partnerships for Goals | Open-source model enabling institutional deployment |

---

## Key Academic Contributions

- First open-source multimodal mental health chatbot combining Text + Voice + Gesture simultaneously
- Novel real-time **emotion injection architecture** — live facial emotion embedded into every LLM prompt
- **Hold-to-confirm gesture stabilization** — practical engineering solution to false-positive sign recognition
- 44-language round-trip translation pipeline with LLM integration
- Complete offline capability protecting sensitive mental health data from cloud exposure
- Multi-agent pipeline design with GLOBAL_SAFETY_RULES preventing diagnosis/prescription claims
- Reproducible custom gesture vocabulary training CLI (non-technical users, < 30 minutes)