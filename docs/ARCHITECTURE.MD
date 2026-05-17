# NeuroSense AI — System Architecture Documentation

> **Project:** NeuroSense AI: A Multimodal Mental Health Assistant
> **Team:** Devashish Biswas (11022210072) · Prateek (11022210084) · Lakshay (11022210087)
> **Institution:** SRM University Delhi-NCR | B.Tech CSE DSAI (IBM) | May 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Agentic AI Architecture](#4-agentic-ai-architecture)
   - 4.1 [Design Principles](#41-design-principles)
   - 4.2 [Agent Inventory](#42-agent-inventory)
   - 4.3 [BaseAgent Foundation](#43-baseagent-foundation)
   - 4.4 [Orchestrator Pipeline](#44-orchestrator-pipeline)
5. [Individual Agent Specifications](#5-individual-agent-specifications)
6. [Supabase Database Architecture](#6-supabase-database-architecture)
   - 6.1 [Client Initialisation](#61-client-initialisation)
   - 6.2 [Database Schema — 13 Tables](#62-database-schema--13-tables)
   - 6.3 [Row Level Security](#63-row-level-security)
   - 6.4 [Authentication Architecture](#64-authentication-architecture)
7. [Persistence Architecture](#7-persistence-architecture)
8. [Module Interaction Matrix](#8-module-interaction-matrix)
9. [AI Model Architecture](#9-ai-model-architecture)
10. [Security Architecture](#10-security-architecture)

---

## 1. System Overview

NeuroSense AI is a locally deployed, Flask-based multimodal mental health assistant integrating five AI subsystems into a single web application:

| Subsystem | Technology | Accuracy |
|---|---|---|
| Facial Emotion Recognition | FER + MTCNN + OpenCV | 58.6% (dominant: 92.9%) |
| Empathic AI Conversation | Phi-3 Mini (Ollama) / LLaMA-3.3-70B (Groq) | — |
| Speech-to-Text / Text-to-Speech | Web Speech API + pyttsx3 + gTTS | 95.2% |
| Sign Language Recognition | MediaPipe + RandomForest (150 trees) | 96.7% (30 classes) |
| Mental Wellbeing Tools | Mood tracking, CBT tasks, breathing, journaling | Satisfaction: 4.7/5 |

**Core design constraint:** All inference (language models, emotion detection, gesture recognition) runs locally. No personal health data is transmitted to third-party servers.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
│  HTML5 + CSS3 + Vanilla JS                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Text UI  │ │ Voice UI │ │ Sign UI  │ │ Research/KB UI   │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│       │            │            │                 │             │
│  Web Speech API  Canvas      MediaPipe       Chart.js 4.4.1    │
│  SpeechSynthesis  JPEG b64   landmarks                          │
└───────┼────────────┼────────────┼─────────────────┼─────────────┘
        │            │            │                 │
        └────────────┴────────────┴─────────────────┘
                               │
                    HTTP REST API (Flask)
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                     BACKEND LAYER                                │
│                      Flask ≥ 3.0.0                               │
│                               │                                  │
│   ┌───────────────────────────┼─────────────────────────────┐   │
│   │         AGENT LAYER       │                             │   │
│   │                           ▼                             │   │
│   │  ┌─────────────────────────────────────────────────┐   │   │
│   │  │        run_safe_therapy_pipeline()               │   │   │
│   │  │  SafetyAgent → EmotionAgent → SocialAgent →     │   │   │
│   │  │  WellnessAgent → PsychiatristAgent →            │   │   │
│   │  │  TherapyAgent → HallucinationAgent              │   │   │
│   │  └──────────────────────┬──────────────────────────┘   │   │
│   │                         │                               │   │
│   │  ┌──────────────────────┴──────────────────────────┐   │   │
│   │  │  ResearchAgent │ KnowledgeAgent │ TemplateAgent  │   │   │
│   │  │  ScopeGuardAgent │ ReportAgent                   │   │   │
│   │  └──────────────────────┬──────────────────────────┘   │   │
│   └───────────────────────  │ ─────────────────────────────┘   │
│                             │                                    │
│   ┌─────────────────────────┼───────────────────────────────┐   │
│   │         UTILITY LAYER   │                               │   │
│   │  wellbeing_utils.py  supabase_client.py                 │   │
│   │  supabase_user_management.py  hs_module.py              │   │
│   └─────────────────────────┼───────────────────────────────┘   │
└─────────────────────────────┼────────────────────────────────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
        ┌──────────┐  ┌──────────────┐  ┌────────────────┐
        │  Groq    │  │   Ollama     │  │   Supabase     │
        │ LLaMA    │  │  Phi-3 Mini  │  │  PostgreSQL    │
        │  3.3 70B │  │  (local)     │  │  (13 tables)   │
        └──────────┘  └──────────────┘  └────────────────┘
               │              │
        ┌──────────────────────────────┐
        │    LOCAL PERSISTENCE         │
        │  neurosense_data.json        │
        │  data/research_chat_history  │
        │  static/uploads/avatars/     │
        │  knowledge/ (KB entries)     │
        │  reports/ (PDF/CSV temp)     │
        └──────────────────────────────┘
```

---

## 3. Technology Stack

### Frontend

| Component | Technology | Version |
|---|---|---|
| UI Framework | HTML5 + CSS3 + Vanilla JavaScript | Latest |
| Fonts | Google Fonts (Outfit, DM Sans, JetBrains Mono) | Latest |
| Charts | Chart.js | 4.4.1 |
| Camera | HTML5 Canvas API | — |
| Speech Input | Web Speech API (SpeechRecognition) | Browser-native |
| Speech Output | SpeechSynthesis API | Browser-native |
| Hand Tracking | MediaPipe Hands | via CDN |
| Auth Client | Supabase JS Client | Latest |

### Backend

| Component | Technology | Version |
|---|---|---|
| Web Framework | Flask | ≥ 3.0.0 |
| LLM API (cloud) | Groq API (LLaMA-3.3-70B) | Latest |
| LLM (local) | Ollama (Phi-3 Mini, 3.8B params) | Latest |
| Image Processing | OpenCV | ≥ 4.9.0 |
| Numerical | NumPy | ≥ 1.26.0 |
| Face Detection | MTCNN | Latest |
| Emotion Classification | FER CNN library | Latest |
| Gesture Classification | scikit-learn RandomForestClassifier | Latest |
| Hand Landmarks | MediaPipe (Python) | Latest |
| TTS (local) | pyttsx3 | Latest |
| TTS (cloud fallback) | gTTS | Latest |
| PDF Generation | ReportLab / WeasyPrint | Latest |
| Database | Supabase (PostgreSQL) | Latest |
| Auth | Supabase Auth | Latest |

### File / Directory Structure

```
neurosense-ai/
├── app.py                        # Flask app, all routes, agent_reply()
├── hs_module.py                  # Health/session utility module
├── agents/
│   ├── base_agent.py             # BaseAgent (shared LLM + safety)
│   ├── orchestrator.py           # run_safe_therapy_pipeline()
│   ├── safety_agent.py
│   ├── emotion_agent.py
│   ├── social_agent.py
│   ├── wellness_agent.py
│   ├── psychiatrist_agent.py
│   ├── therapy_agent.py
│   ├── hallucination_agent.py
│   ├── research_agent.py
│   ├── scope_guard_agent.py
│   ├── knowledge_agent.py
│   ├── report_agent.py
│   └── template_agent.py
├── utils/
│   ├── supabase_client.py        # Supabase client initialisation
│   ├── supabase_user_management.py
│   └── wellbeing_utils.py        # Score + risk calculation
├── sql/                          # Supabase schema SQL files
├── models/                       # ML model files (word_model.pkl, etc.)
├── knowledge/                    # KB entries for KnowledgeAgent
├── data/                         # research_chat_history.json, etc.
├── templates/                    # Jinja2 HTML templates
├── static/
│   └── uploads/avatars/          # Local avatar storage
├── reports/                      # Temporary PDF/CSV output
├── neurosense_data.json          # Primary local persistence store
└── requirements.txt
```

---

## 4. Agentic AI Architecture

### 4.1 Design Principles

| Principle | Implementation |
|---|---|
| **Single Responsibility** | Each agent does exactly one task; no agent handles both safety and response generation |
| **Fail-Safe Degradation** | Every agent has a deterministic fallback; app never crashes if LLM is unavailable |
| **Transparency** | Every agent returns structured JSON; full agent trace included in every API response for logging and debugging |
| **Safety-First Ordering** | SafetyAgent always runs first; crisis exit before any generative LLM is called |
| **Layered Hallucination Defence** | Regex pre-check → LLM check → secondary regex check (3 layers) |

### 4.2 Agent Inventory

| Agent | File | Responsibility | LLM Backend | Temperature | Fallback Strategy |
|---|---|---|---|---|---|
| SafetyAgent | `safety_agent.py` | Crisis, violence, abuse, medication detection | Groq (+ keyword precheck) | 0.0 | Keyword deterministic precheck |
| EmotionAgent | `emotion_agent.py` | Emotional state analysis (text + facial) | Groq | 0.1 | Mood score from wellbeing check-in |
| SocialAgent | `social_agent.py` | Loneliness, support, social risk analysis | Groq | 0.1 | Deterministic concern mapping |
| WellnessAgent | `wellness_agent.py` | 5 wellness recommendations | Groq | 0.25 | `deterministic_recommendations()` |
| PsychiatristAgent | `psychiatrist_agent.py` | Professional referral guidance (not diagnosis) | Groq | 0.1 | `deterministic_referral()` |
| TherapyAgent | `therapy_agent.py` | CBT/DBT user-facing response generation | Groq | 0.45 | `safe_support_fallback()` |
| HallucinationAgent | `hallucination_agent.py` | Final response validation (no diagnosis/Rx) | Groq (+ regex) | 0.0 | `safe_support_fallback()` |
| ResearchAgent | `research_agent.py` | Structured mental-health education | Ollama (local) | — | Instructional fallback message |
| TemplateAgent | `template_agent.py` | Research Chat template selection | Ollama (optional) | — | Keyword category detection |
| ScopeGuardAgent | `scope_guard_agent.py` | Knowledge Chat scope enforcement | **None (no LLM)** | — | Keyword allow/deny list |
| KnowledgeAgent | `knowledge_agent.py` | Grounded KB answers | Ollama (optional) | — | Extractive KB fallback |
| ReportAgent | `report_agent.py` | Assessment + Solution report data | Groq | 0.25 | Structured fallback report dict |

### 4.3 BaseAgent Foundation

**File:** `agents/base_agent.py`

All 12 agents inherit from `BaseAgent`. Shared capabilities:

```
BaseAgent
│
├── call_llm(system_prompt, user_prompt, temperature, max_tokens, json_mode)
│     └── Returns empty string on any failure (never raises)
│
├── call_json(system_prompt, user_prompt, fallback)
│     └── Returns parsed dict OR fallback dict if LLM fails
│
├── parse_json(raw, fallback)
│     └── Strips markdown fences → regex extract → never raises
│
├── clean_history(history)
│     └── Normalises to [{role, content}] format from any input type
│
├── contains_unsafe_medical_claim(text)
│     └── Regex guard: 40+ patterns across 5 categories
│           - Diagnosis claims
│           - Medication / prescription advice
│           - Guaranteed recovery promises
│           - Discouraging professional help
│           - Unsafe crisis guidance
│
├── safe_with_fallback()
│     └── Hardcoded supportive message (no LLM required)
│
└── crisis_response()
      └── Hardcoded crisis response with all Indian helplines:
            Tele-MANAS : 14416
            iCALL      : 9152987821
            KIRAN      : 1800-599-0019
            Vandrevala : +91 9999 666 555
            AASRA      : 022-27546669
```

**GLOBAL_SAFETY_RULES** constant (15 rules, imported by all agents):
- No mental illness diagnosis
- No medication prescription or dosage changes
- Non-diagnostic wording required ("you may be feeling...", "it may help to...")
- Mandatory crisis escalation protocol with Indian helpline numbers

### 4.4 Orchestrator Pipeline

**File:** `agents/orchestrator.py` → `run_safe_therapy_pipeline()`

**Called by:** `agent_reply()` in `app.py` for every Normal Chat, Voice Chat, and Hand Sign Chat message.

#### Pipeline Stage Sequence

| Stage | Agent | Activation | Output | Supabase Effect |
|---|---|---|---|---|
| 1 | SafetyAgent | Every message (mandatory) | `risk_level`, `self_harm`, `allow_normal_response` | None — classification only |
| 2 | EmotionAgent | Non-crisis messages | `dominant_emotion`, `mood_score_estimate`, `emotional_summary` | Mood updated in session sentiment |
| 3 | SocialAgent | Non-crisis messages | `social_risk`, `support_availability`, `main_social_factors` | None |
| 4 | WellnessAgent | Non-crisis messages | `top_practices[5]`, `immediate_action`, `note` | Passed to `/api/wellbeing_checkin` response |
| 5 | PsychiatristAgent | Every message | `needs_professional_referral`, `urgency`, `user_facing_message` | Logged via `professional_help_logs` |
| 6 | TherapyAgent | Non-crisis, after stages 2–5 | `reply`, `response_type`, `technique_used` | Logged to `chat_messages` via `log_msg()` |
| 7 | HallucinationAgent | Every draft reply | `safe: bool`, `issues[]`, `corrected_reply` | Corrected reply replaces draft before storage |

#### Complete Pipeline Return Schema

```json
{
  "reply": "final user-facing response string",
  "safe": true,
  "risk_level": "none | low | medium | high | crisis",
  "response_type": "supportive | grounding | referral | crisis",
  "technique_used": "CBT | DBT | grounding | validation | reflection | referral",
  "agents": {
    "safety_agent": { "..." },
    "emotion_agent": { "..." },
    "social_agent": { "..." },
    "wellness_agent": { "..." },
    "clinical_escalation_agent": { "..." },
    "therapy_agent": { "..." },
    "hallucination_agent": { "..." }
  },
  "wellness": {
    "top_practices": ["..."],
    "immediate_action": "...",
    "note": "..."
  },
  "referral": {
    "needs_professional_referral": true,
    "urgency": "none | routine | soon | urgent | emergency",
    "recommended_professional": "...",
    "user_facing_message": "..."
  }
}
```

---

## 5. Individual Agent Specifications

### SafetyAgent

| Property | Value |
|---|---|
| File | `agents/safety_agent.py` |
| Temperature | **0.0** (fully deterministic) |
| Max Tokens | 500 |
| Two-Phase | Phase A: keyword precheck (no LLM) → Phase B: LLM classification |

**Output Schema:**
```json
{
  "risk_level": "none | low | medium | high | crisis",
  "self_harm": true,
  "violence": false,
  "abuse": false,
  "medical_advice_requested": false,
  "allow_normal_response": true,
  "reason": "short reason string"
}
```

---

### EmotionAgent

| Property | Value |
|---|---|
| File | `agents/emotion_agent.py` |
| Temperature | 0.1 |
| Max Tokens | 600 |
| Input | FER/DeepFace facial emotion + user message + wellbeing check-in + chat history |

**Output Schema:**
```json
{
  "dominant_emotion": "happy | calm | neutral | sad | anxious | angry | overwhelmed | stressed | lonely",
  "emotional_intensity": "low | moderate | high",
  "mood_score_estimate": 0,
  "emotional_summary": "short non-diagnostic summary",
  "confidence": "low | medium | high"
}
```
> `mood_score_estimate` is always clamped to `[0, 100]` after LLM output.

---

### SocialAgent

| Property | Value |
|---|---|
| File | `agents/social_agent.py` |
| Temperature | 0.1 |
| Max Tokens | 650 |

**Output Schema:**
```json
{
  "social_risk": "low | medium | high",
  "support_availability": "yes | maybe | no | unknown",
  "main_social_factors": ["factor1", "factor2"],
  "summary": "short non-diagnostic summary",
  "recommended_support_action": "one practical safe action"
}
```

---

### WellnessAgent

| Property | Value |
|---|---|
| File | `agents/wellness_agent.py` |
| Temperature | 0.25 |
| Max Tokens | 850 |

**`deterministic_recommendations()` Mapping:**

| Condition | Recommendation |
|---|---|
| High stress / anxious | Box Breathing (4s inhale, 4s hold, 4s exhale, 4s hold) |
| Poor / very poor sleep | Sleep Wind-Down Ritual |
| No social connection / no support | Contact Trusted Individual |
| Sad / self-doubt | Thought Journaling |
| All other | Grounding 5-4-3-2-1 / Small Action Steps / Water & Movement |

**Output Schema:**
```json
{
  "top_practices": [
    {
      "title": "practice name",
      "description": "short practical instruction",
      "frequency": "when or how often",
      "category": "stress | sleep | social | grounding | journaling | professional_help"
    }
  ],
  "immediate_action": "one very small action user can do now",
  "note": "short safety note"
}
```

---

### PsychiatristAgent (Clinical Escalation)

| Property | Value |
|---|---|
| File | `agents/psychiatrist_agent.py` |
| Temperature | 0.1 |
| Max Tokens | 750 |
| Note | NOT a psychiatrist — decides on escalation urgency only, does not diagnose |

**`deterministic_referral()` Logic:**

| Condition | Urgency | Recommended Professional |
|---|---|---|
| `risk_level == "crisis"` OR `self_harm == True` | emergency | Emergency services or crisis line |
| Medication keywords in message | soon | Psychiatrist |
| Stress ≥ 4 OR emotional_safety ≤ 2 OR mood overwhelmed/sad OR sleep very_poor | soon | Psychologist or psychiatrist |
| `support_available == "no"` | routine | Counsellor or psychologist |
| All other | — | `needs_professional_referral: false` |

**Output Schema:**
```json
{
  "needs_professional_referral": true,
  "urgency": "none | routine | soon | urgent | emergency",
  "recommended_professional": "none | counsellor | psychologist | psychiatrist | emergency services or crisis helpline",
  "reason": "short non-diagnostic reason",
  "user_facing_message": "safe message for the user",
  "professional_summary": "brief summary user can show to a professional"
}
```

---

### TherapyAgent

| Property | Value |
|---|---|
| File | `agents/therapy_agent.py` |
| Temperature | **0.45** (highest of analytical agents — allows natural varied language) |
| Max Tokens | 650 |
| Role | Only agent that generates user-facing response text |
| Length | 3–6 sentences, CBT/DBT-inspired |

**Output Schema:**
```json
{
  "reply": "final user-facing response",
  "response_type": "supportive | grounding | referral | crisis",
  "technique_used": "CBT | DBT | grounding | validation | reflection | referral"
}
```

---

### HallucinationAgent

| Property | Value |
|---|---|
| File | `agents/hallucination_agent.py` |
| Temperature | **0.0** (fully deterministic) |
| Max Tokens | 800 |
| Two-Phase | Phase A: regex precheck (40+ patterns) → Phase B: LLM verification |

**Regex Pattern Categories (Phase A):**

| Category | Example Patterns |
|---|---|
| Diagnosis claims | "you have depression", "I diagnose you with", "your diagnosis is" |
| Medication advice | "start taking medication", "take X mg", "prescribe" |
| Guaranteed recovery | "this will cure you", "100% effective", "no side effects" |
| Anti-professional | "you don't need a doctor", "avoid therapy", "ignore your therapist" |
| Unsafe crisis | "self harm is okay", "ignore suicidal thoughts" |

---

### ScopeGuardAgent

| Property | Value |
|---|---|
| File | `agents/scope_guard_agent.py` |
| LLM Calls | **None** — keyword matching only, intentional by design |

**Scope Categories:**

| Scope | Keywords | Action |
|---|---|---|
| `crisis` | suicide, self-harm keywords | Permitted — crisis response |
| `safe_smalltalk` | greetings, thanks, farewell | Permitted — canned response |
| `medication_boundary` | medication, dose keywords | Permitted — boundary message |
| `diagnosis_boundary` | diagnosis request keywords | Permitted — boundary message |
| `mental_health` | 100+ wellbeing terms | Permitted — full KB response |
| `out_of_scope` | stocks, recipes, cricket, politics | **Blocked** |

**Real-life wellbeing override:** Queries containing "mentally", "leave", "trip", or "burnout" → classified as `mental_health` scope regardless of other keywords.

---

### ReportAgent

| Property | Value |
|---|---|
| File | `agents/report_agent.py` |
| Temperature | 0.25 |
| Max Tokens | 1500 |
| Report ID Format | Assessment: `NSA-YYYYMMDDHHMM-USERNAME` / Solution: `NSP-YYYYMMDDHHMM-USERNAME` |

---

## 6. Supabase Database Architecture

### 6.1 Client Initialisation

**File:** `utils/supabase_client.py`

| Client | Key Used | RLS | Purpose |
|---|---|---|---|
| `supabase_public` | Anon key | **Enforced** | Frontend-side operations |
| `supabase` (service role) | Service role key | **Bypassed** | Flask backend writes — Flask acts as trusted access-control layer |

### 6.2 Database Schema — 13 Tables

| Table | Key Columns | Purpose |
|---|---|---|
| `user_profiles` | `id (UUID FK → auth.users)`, `full_name`, `email`, `phone`, `role`, `preferred_language`, `is_active`, `avatar_url` | Core user identity |
| `usage_limits` | `user_id`, `usage_date`, `daily_messages`, `monthly_messages`, `reports_generated`, `research_queries`, `knowledge_queries` | Per-day usage tracking for rate limiting |
| `chat_sessions` | `id`, `user_id`, `session_type`, `dominant_emotion`, `average_mood_score`, `summary` | Session metadata for analytics |
| `chat_messages` | `id`, `session_id`, `sender`, `message`, `emotion`, `mood_score` | Per-message records with emotion context |
| `emotion_logs` | `id`, `user_id`, `session_id`, `emotion`, `confidence`, `source_type (camera/voice/text/sign)` | Fine-grained emotion detection history |
| `generated_reports` | `id`, `user_id`, `session_id`, `report_type`, `report_title`, `file_url` | Assessment / Solution PDF metadata |
| `user_settings` | `id`, `user_id`, `emotion_detection`, `voice_enabled`, `theme`, `anonymous_reports` | Per-user feature toggles |
| `admin_logs` | `id`, `admin_id`, `action`, `target_user`, `metadata (JSONB)` | Admin audit trail |
| `wellbeing_checkins` | `user_id`, `mood`, `stress`, `social_connection`, `sleep`, `wellbeing_score`, `risk_level` | Mental & social wellbeing check-in records |
| `neurosense_reports` | `user_id`, `report_id`, `report_type`, `risk_level`, `top_emotion`, `mood_trend`, `wellbeing_score` | Richer report metadata for dashboard |
| `mental_health_templates` | `user_id`, `template_key`, `title`, `category`, `prompt`, `output_type`, `is_prebuilt`, `is_active`, `usage_count` | Prebuilt + custom Research Chat templates |
| `research_chat_history` | `user_id`, `template_id`, `query`, `answer`, `model`, `risk_level`, `safety (JSONB)`, `agent_trace (JSONB)` | Full Research Chat Q&A audit log |
| `professional_help_logs` | `user_id`, `wellbeing_checkin_id`, `urgency`, `recommendations`, `resources` | Professional referral event log |

### 6.3 Row Level Security

All 13 tables use RLS — enforced at the PostgreSQL engine level regardless of application code.

| Table | Operation | RLS Policy | Notes |
|---|---|---|---|
| `user_profiles` | SELECT | `auth.uid() = id` | Users see only their own row |
| `user_profiles` | UPDATE | `auth.uid() = id` | Users update only their own profile |
| `usage_limits` | SELECT | `auth.uid() = user_id` | Daily usage visible to owner only |
| `usage_limits` | INSERT/UPDATE | `auth.uid() = user_id` | Flask backend uses service role; bypasses RLS |
| `chat_sessions` | SELECT/INSERT/UPDATE | `auth.uid() = user_id` | Session data scoped to owner |
| `chat_messages` | SELECT/INSERT | Session's `user_id = auth.uid()` | Checked via JOIN on `chat_sessions` |
| `generated_reports` | SELECT/INSERT | `auth.uid() = user_id` | PDF metadata private per user |
| `emotion_logs` | SELECT/INSERT | `auth.uid() = user_id` | Emotion data private per user |
| `user_settings` | ALL | `auth.uid() = user_id` | Full CRUD for own settings |
| `admin_logs` | SELECT | `role = admin` via `user_profiles` JOIN | Admin-only audit access |
| `storage.objects (avatars)` | SELECT | `bucket_id = 'avatars'` public read | Public avatar images |
| `storage.objects (avatars)` | INSERT/UPDATE | Folder name matches `auth.uid()` | Users modify only their own folder |

### 6.4 Authentication Architecture

```
Browser (Supabase JS Client)
  │
  ├── Sign in (email/password or OAuth)
  ├── Supabase Auth returns JWT access_token
  │
  ▼
POST /api/auth/sync
  │
  ├── supabase.auth.get_user(access_token)  ← JWT verified ONCE
  ├── get_or_create_profile()
  └── _set_login_session_from_profile()
        session = { user_id, name, email, lang, role, user_key }

All subsequent API calls:
  └── Flask session cookie (encrypted with SECRET_KEY)
        No JWT re-verification — backend session used
```

---

## 7. Persistence Architecture

### Dual Persistence Strategy

```
Every Write Operation
        │
        ├── Layer 1 (Primary — always):
        │     neurosense_data.json (local)
        │     Atomic write pattern:
        │       1. Write to neurosense_data.json.tmp
        │       2. f.flush() + os.fsync() (kernel buffer → disk)
        │       3. os.replace() (atomic rename)
        │     Prevents data corruption if process killed mid-write
        │
        └── Layer 2 (Secondary — best-effort):
              Supabase (13 tables)
              Any failure: silently caught → return {ok: False}
              App remains fully functional during Supabase outage
```

### Local Store Contents (`neurosense_data.json`)

```
store[user_key]
  ├── sessions[]
  ├── emotion_logs[]
  ├── message_counts
  ├── streak_days
  ├── reports[]
  ├── wellbeing_checkins[]  (capped at 20 entries)
  ├── safety_plan
  ├── practice_logs[]
  └── feedback_logs[]
```

### Usage Limit Tracking (`usage_limits` table)

| Field | Increment Trigger | Limit |
|---|---|---|
| `daily_messages` | `/api/chat`, `/api/voice_chat`, `/api/hand_enter` | 100/day |
| `monthly_messages` | Same as above | 2000/month |
| `reports_generated` | `/api/report/generate`, `/api/generate_and_download` | 20 reports |
| `knowledge_queries` | `/api/knowledge_chat` (allowed + scoped) | Tracked |
| `image_uploads` | `/api/user/avatar` | Tracked |
| `sign_sessions` | `/api/hand_enter` | Tracked |
| `voice_minutes` | `/api/voice_chat` | Reserved (future) |
| `research_queries` | `/api/research_chat` | Planned rate limit |

### Report Token Security

```
POST /api/report/generate
  ├── PDF/CSV written to temp location on server
  ├── UUID token → _report_tokens dict (TTL: 5 min)
  └── Return { token }

GET /api/report/download?token=<UUID>
  ├── Validate token in _report_tokens
  ├── Check TTL not expired
  ├── Extract file bytes
  ├── Delete temp file from disk
  ├── Remove UUID from _report_tokens
  └── Stream file to browser
        (Prevents unauthorised downloads + auto-clears temp storage)
```

---

## 8. Module Interaction Matrix

| Calling Module | Called Module / Service | Method / Endpoint |
|---|---|---|
| `app.py` (agent_reply) | `agents/orchestrator.py` | `run_safe_therapy_pipeline()` |
| `orchestrator.py` | All 7 pipeline agents | `run()` / `analyze()` |
| `app.py` | `utils/supabase_user_management.py` | `get_or_create_profile()` |
| `app.py` | `utils/wellbeing_utils.py` | `build_checkin_response()` |
| `app.py` | `utils/supabase_client.py` | `supabase`, `supabase_public` |
| `agents/base_agent.py` | Groq API | `POST /openai/v1/chat/completions` |
| `agents/research_agent.py` | Ollama (local) | `POST /api/generate` |
| `agents/knowledge_agent.py` | Ollama (local) + KB files | `retrieve_knowledge()` |
| `utils/supabase_client.py` | Supabase PostgreSQL | All 13 tables via REST API |
| `app.py` | `neurosense_data.json` | `_save_store()` atomic write |
| Frontend JS | `app.py` API endpoints | REST HTTP |
| Frontend JS | Supabase JS Client | Auth sync |

---

## 9. AI Model Architecture

### Facial Emotion Recognition Pipeline

```
Webcam Frame (every 1600ms)
  │
  ├── HTML5 Canvas → base64 JPEG
  ├── base64 decode → np.frombuffer → cv2.imdecode
  ├── BGR → RGB (cv2.cvtColor)
  ├── MTCNN face detection
  │     └── No face → { emotion: null }
  ├── Face region bounding box extraction
  ├── FER CNN classifier → emotion_scores dict
  │     { happy, sad, angry, fear, disgust, surprise, neutral }
  ├── dominant = argmax(emotion_scores)
  └── session['sentiment'] = dominant
```

**Detectable Emotions:** happiness, sadness, anger, fear, disgust, surprise, neutral

### Hand Sign Recognition Architecture

```
Training: RandomForestClassifier
  ├── n_estimators = 150 decision trees
  ├── Feature vector: 21 landmarks × (x, y, z) × 2 hands = 126 floats
  ├── 100 samples per word class
  ├── Minimum 4 consecutive stable predictions before word is appended
  └── Confidence threshold: 0.40 (below → return null prediction)

Currently trained: 30 sign classes
Accuracy: 96.7%
```

### LLM Architecture

| Usage | Model | Hosting | Use Case |
|---|---|---|---|
| All pipeline agents (stages 1–7) | LLaMA-3.3-70B | Groq API (cloud) | Fast, low-latency inference |
| ResearchAgent, KnowledgeAgent, TemplateAgent | Phi-3 Mini (3.8B) | Ollama (local) | Privacy-preserving research queries |

**Why two backends:**
- Groq provides sub-second latency for real-time therapy pipeline
- Ollama ensures research/knowledge queries never leave the device

---

## 10. Security Architecture

### Access Control Layers

```
Layer 1 — Supabase Auth (JWT)
  └── Email/password or OAuth → JWT issued at login only

Layer 2 — Flask Session (server-side)
  └── Encrypted cookie (SECRET_KEY) used for all subsequent requests
        user_id, name, email, lang, role, user_key

Layer 3 — Row Level Security (PostgreSQL)
  └── auth.uid() = user_id enforced at DB engine level
        Protects even against application-layer bugs

Layer 4 — Admin Access Control
  └── ADMIN_EMAILS env variable (no DB elevation path)
        is_admin_user() checked on every request in real time

Layer 5 — Input Validation
  └── All user input validated before processing
        Avatar: allowed extensions (png, jpg, jpeg, webp)
                allowed MIME types
                max file size: 5MB
                secure_filename() + regex user_id sanitisation
        Wellbeing: all fields normalised in build_checkin_response()
        Chat: BANNED_WORDS list checked before agent pipeline
```

### Medical Safety Guardrails

```
GLOBAL_SAFETY_RULES (15 rules, shared across all agents)
  ├── No mental illness diagnosis
  ├── No medication prescription or dosage changes
  ├── Non-diagnostic wording required
  └── Crisis escalation protocol always active

contains_unsafe_medical_claim() regex (40+ patterns)
  ├── Called in: BaseAgent, TherapyAgent post-generation, HallucinationAgent
  └── Three-layer protection on every response:
        1. HallucinationAgent regex precheck
        2. HallucinationAgent LLM verification
        3. Secondary regex on corrected reply

Crisis Response (never generated by LLM)
  └── crisis_fallback_response() — hardcoded, returned directly
        Contains all Indian helplines (Tele-MANAS, iCALL, KIRAN, Vandrevala, AASRA)
```

### Data Privacy

- **Zero third-party transmission** of personal health data during inference
- All language model inference runs locally via Ollama (research/knowledge) or Groq with no persistent storage of conversation content
- Local `neurosense_data.json` stores all session data on the user's own device
- Soft-delete pattern: `is_active = false` (data preserved, account deactivated)
- Report files auto-deleted from server after one-time token download

# folder structure command
tree -a \
  -I "venv|venv310|.venv|env|.env|node_modules|.git|__pycache__|*.pyc|*.pyo|.pytest_cache|.mypy_cache|.ruff_cache|logs|*.log|storage|reports/generated|reports/temp|static/uploads|folder_structure.txt"
---

*NeuroSense AI — Architecture Documentation | Group 48 | SRM University Delhi-NCR | May 2026*