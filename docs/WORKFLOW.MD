# NeuroSense AI — System Workflow Documentation

> **Project:** NeuroSense AI: A Multimodal Mental Health Assistant
> **Team:** Devashish Biswas (11022210072) · Prateek (11022210084) · Lakshay (11022210087)
> **Institution:** SRM University Delhi-NCR | B.Tech CSE DSAI (IBM) | May 2026

---

## Table of Contents

1. [High-Level System Workflow](#1-high-level-system-workflow)
2. [User Onboarding Workflow](#2-user-onboarding-workflow)
3. [Wellbeing Check-in Workflow](#3-wellbeing-check-in-workflow)
4. [Multi-Agent Pipeline Workflow](#4-multi-agent-pipeline-workflow)
5. [Chat Mode Workflows](#5-chat-mode-workflows)
   - 5.1 [Text Chat](#51-text-chat-workflow)
   - 5.2 [Voice Chat](#52-voice-chat-workflow)
   - 5.3 [Hand Sign Chat](#53-hand-sign-chat-workflow)
   - 5.4 [Research Chat](#54-research-chat-workflow)
   - 5.5 [Knowledge Chat](#55-knowledge-chat-workflow)
6. [Emotion Detection Workflow](#6-emotion-detection-workflow)
7. [Supabase Persistence Workflow](#7-supabase-persistence-workflow)
8. [Report Generation Workflow](#8-report-generation-workflow)
9. [Admin System Workflow](#9-admin-system-workflow)
10. [Error & Fallback Workflow](#10-error--fallback-workflow)

---

## 1. High-Level System Workflow

```
User Opens NeuroSense AI
          │
          ▼
  Supabase Auth (Login / Register)
          │
          ├── JWT Token issued by Supabase Auth
          │
          ▼
  POST /api/auth/sync
          │
          ├── Backend verifies JWT via supabase.auth.get_user()
          ├── get_or_create_profile()  →  user_profiles table
          └── _set_login_session_from_profile()  →  Flask session set
                        │
                        ▼
          Wellbeing Check-in (mandatory before chat)
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Choose Chat Mode            │
        │  ┌─────┐ ┌──────┐ ┌───────┐  │
        │  │Text │ │Voice │ │ Sign  │  │
        │  └──┬──┘ └──┬───┘ └──┬────┘  │
        │     │       │        │        │
        │     └───────┴────────┘        │
        │             │                 │
        │    run_safe_therapy_pipeline() │
        │             │                 │
        │     Multi-Agent Pipeline      │
        │   (7 Agents in sequence)      │
        └───────────────────────────────┘
                        │
                        ▼
           Final Response → User UI
                        │
                        ▼
        Dual Persistence: Local JSON + Supabase
```

---

## 2. User Onboarding Workflow

```
Step 1: Registration
  │
  ├── User submits email + password via Supabase Auth JS client
  ├── Supabase creates auth.users record
  └── JWT access token returned to browser

Step 2: Token Sync (POST /api/auth/sync)
  │
  ├── Frontend sends access_token in POST body
  ├── Flask backend calls supabase.auth.get_user(access_token)
  ├── On success: get_or_create_profile() runs
  │     ├── Profile exists? → Fetch + _normalize_profile()
  │     ├── Profile missing? → INSERT into user_profiles
  │     └── INSERT failure (schema mismatch)? → Retry with minimal payload
  │           {id, email, full_name} + update remaining fields
  └── _set_login_session_from_profile() sets Flask session:
        {user_id, name, email, lang, role, user_key}

Step 3: Subsequent Requests
  │
  ├── Flask session cookie (encrypted with SECRET_KEY) used for all API auth
  └── JWT token NOT re-verified on every call — only on login
```

### Error Handling at Auth Sync

| Error Type | HTTP Code Returned |
|---|---|
| `httpx.ConnectError` (Supabase unreachable) | Custom error dict |
| Invalid / expired JWT token | Custom error dict |
| Generic unexpected exception | Custom error dict |

---

## 3. Wellbeing Check-in Workflow

```
User completes Check-in Form
  │
  ├── Fields collected:
  │     mood           → happy / calm / neutral / sad / anxious / angry / overwhelmed
  │     stress         → integer 1–5
  │     social_connection → integer 1–5
  │     emotional_safety  → integer 1–5
  │     sleep          → good / okay / poor / very_poor
  │     support_available → yes / maybe / no
  │     concerns       → multi-select list (academic, family, loneliness, etc.)
  │     current_thoughts → free text (max 1200 chars)
  │
  ▼
POST /api/wellbeing_checkin
  │
  ├── build_checkin_response(raw_data)  [utils/wellbeing_utils.py]
  │     ├── Validate + normalise all fields
  │     ├── Compute Wellbeing Score (starts at 100, deductions applied)
  │     │     stress × 8                         (max −40)
  │     │     (6 − social_connection) × 6        (max −30)
  │     │     (6 − emotional_safety) × 7         (max −35)
  │     │     sleep: poor=−10, very_poor=−18     (max −18)
  │     │     support: maybe=−8, no=−15          (max −15)
  │     │     concerns: −4 per item, cap −20     (max −20)
  │     │     difficult mood: flat −12           (max −12)
  │     │     Score clamped to [0, 100]
  │     └── Determine risk_level:
  │           score ≤ 30 OR stress > 4 OR emotional_safety < 2 → HIGH
  │           score < 60 OR stress > 3 OR sleep poor/very_poor → MEDIUM
  │           all other                                         → LOW
  │
  ├── Append to local store[user_key]["wellbeing_checkins"] (cap: 20 entries)
  ├── _save_wellbeing_checkin_to_supabase(entry)  →  wellbeing_checkins table
  │     └── On success: attach supabase_id to entry
  ├── Update session["sentiment"] if mood field is set
  └── _save_store() — atomic write (tmp → fsync → os.replace)
```

### Risk Level → System Response

| Risk Level | Trigger | System Action |
|---|---|---|
| **HIGH** | Stress > 4 OR emotional_safety < 2 OR support = no OR mood = overwhelmed OR score ≤ 30 | PsychiatristAgent urgency = soon/emergency; WellnessAgent adds professional help practice |
| **MEDIUM** | Stress > 3 OR social_connection < 2 OR sleep poor/very_poor OR mood sad/anxious/angry OR score < 60 | Referral guidance appended to therapy reply |
| **LOW** | All other; score > 60 | Supportive response + 5 wellness suggestions only |

---

## 4. Multi-Agent Pipeline Workflow

> Entry point: `run_safe_therapy_pipeline()` in `agents/orchestrator.py`
> Called by: `agent_reply()` in `app.py` for every Text, Voice, and Hand Sign chat message.

```
User Message
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 1 — SafetyAgent  (temperature: 0.0)                 │
│                                                            │
│  Phase A — Keyword Precheck (microseconds, no LLM):        │
│    "suicide / kill myself / end my life / self harm        │
│     / i want to die / no reason to live"  →  CRISIS        │
│    violence terms                          →  HIGH          │
│    "abuse / medication"                   →  MEDIUM         │
│                                                            │
│  Phase B — LLM Classification (if no keyword crisis):      │
│    Groq LLM classifies: risk_level, self_harm, violence,   │
│    abuse, medical_advice_requested, allow_normal_response  │
│                                                            │
│  Output: { risk_level, self_harm, allow_normal_response }  │
└───────────────────┬────────────────────────────────────────┘
                    │
          risk_level = "crisis"?
                    │
          ┌─────── YES ──── CRISIS EARLY-EXIT ─────────────┐
          │     crisis_fallback_response() called           │
          │     response_type = "crisis"                    │
          │     Hardcoded Indian helpline numbers returned  │
          │     Pipeline TERMINATES — no further LLM calls  │
          └─────────────────────────────────────────────────┘
                    │
                   NO
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 2 — EmotionAgent  (temperature: 0.1)                │
│                                                            │
│  Input: FER/DeepFace emotion + user message + check-in     │
│  Output: dominant_emotion, emotional_intensity,            │
│          mood_score_estimate [0–100], emotional_summary    │
│  Effect: Updates session["sentiment"]                      │
└───────────────────┬────────────────────────────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 3 — SocialAgent  (temperature: 0.1)                 │
│                                                            │
│  Input: support_available, social_connection, concerns     │
│  Output: social_risk, support_availability,                │
│          main_social_factors, recommended_support_action   │
│  Fallback: maps support_available field directly (no LLM)  │
└───────────────────┬────────────────────────────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 4 — WellnessAgent  (temperature: 0.25)              │
│                                                            │
│  Input: emotional state + social state + sleep + stress    │
│  Output: top_practices[5], immediate_action, note          │
│  Fallback: deterministic_recommendations() mapping:        │
│    anxious → Box Breathing                                 │
│    poor sleep → Sleep Wind-Down Ritual                     │
│    no support → Contact Trusted Individual                 │
│    sad → Thought Journaling                                │
│    else → Grounding 5-4-3-2-1 / Small Action Steps        │
└───────────────────┬────────────────────────────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 5 — PsychiatristAgent  (temperature: 0.1)           │
│                                                            │
│  Purpose: Clinical escalation (NOT diagnosis)              │
│  Output: needs_professional_referral, urgency,             │
│          recommended_professional, user_facing_message     │
│  Fallback: deterministic_referral() — 5 condition map      │
└───────────────────┬────────────────────────────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 6 — TherapyAgent  (temperature: 0.45)               │
│                                                            │
│  Only agent generating user-facing text                    │
│  Input: all upstream agent outputs as structured context   │
│  Output: 3–6 sentence CBT/DBT-inspired response           │
│  + Referral message injected if needs_professional_referral│
│    is True and no user_facing_message present in reply     │
└───────────────────┬────────────────────────────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────┐
│  Stage 7 — HallucinationAgent  (temperature: 0.0)          │
│                                                            │
│  Phase A — Regex Precheck (40+ patterns, 5 categories):    │
│    diagnosis claims / medication advice /                  │
│    guaranteed recovery / anti-therapy advice /             │
│    unsafe crisis guidance                                  │
│    → Any match: replace draft with safe_support_fallback() │
│                                                            │
│  Phase B — LLM Verification:                               │
│    Validate corrected reply against full context           │
│                                                            │
│  Phase C — Secondary contains_unsafe_medical_claim() check │
│    → Still unsafe: replace with safe_support_fallback()    │
└───────────────────┬────────────────────────────────────────┘
                    ▼
         Final Response Returned
   {
     reply, safe, risk_level, response_type,
     technique_used, agents{...}, wellness{...}, referral{...}
   }
                    │
                    ▼
     Logged to chat_messages via log_msg()
```

---

## 5. Chat Mode Workflows

### 5.1 Text Chat Workflow

```
User types message → POST /api/chat
  │
  ├── Check BANNED_WORDS list
  ├── Retrieve session["sentiment"] (current FER emotion)
  ├── Translate input → English (if lang != 'en')
  ├── increment_usage(daily_messages, monthly_messages)
  ├── run_safe_therapy_pipeline()  [7 agents]
  ├── Translate response → user's language (if needed)
  ├── log_msg() → chat_messages (Supabase)
  └── Return JSON { reply, safe, risk_level, ... }
```

### 5.2 Voice Chat Workflow

```
User clicks mic button
  │
  ├── Web Speech API SpeechRecognition initialised
  ├── Language locale set from LANG_MAP[selected_lang]
  ├── continuous=true, interimResults=true
  │
  WHILE recording:
  │   ├── Interim transcript displayed in UI
  │   └── Final transcript accumulated in curTx
  │
  User clicks Stop / Send
  │
  ├── POST curTx → /api/voice_chat (same pipeline as text chat)
  ├── AI reply received
  ├── SpeechSynthesisUtterance(reply) created
  │     ├── language set, rate=0.88, pitch=1.0
  │     └── speechSynthesis.speak(utterance)
  └── Reply displayed in chat UI simultaneously
```

### 5.3 Hand Sign Chat Workflow

```
TRAINING PHASE (one-time, offline):
  │
  ├── User enters word label (e.g., "HAPPY")
  ├── MediaPipe extracts 21 landmarks × (x, y, z) per hand
  │     Hand 1: 63 floats | Hand 2: 63 floats (zeros if absent)
  │     feature_vector = 126 floats
  ├── 100 samples captured per word → appended to CSV
  ├── Repeat for each vocabulary word
  ├── RandomForestClassifier(n_estimators=150) trained on CSV
  └── Model serialised → word_model.pkl

INFERENCE PHASE (every 350ms poll):
  │
  ├── JavaScript polls /api/hand_predict
  ├── Decode frame → MediaPipe extracts 126-feature vector
  ├── clf.predict([features]) → predicted word
  ├── confidence = max(clf.predict_proba([features]))
  │     IF confidence < 0.40 → return {predicted: null}
  │
  ├── Compare pred with session['hand_last_pred']
  │     IF same → session['hand_pred_count'] += 1
  │     ELSE    → session['hand_pred_count'] = 1
  │
  ├── IF hand_pred_count >= 4 (STABLE_THRESHOLD):
  │     ├── Append word to session['hand_sentence']
  │     ├── Apply capitalisation rules
  │     ├── Reset count and last_pred
  │     └── Return { appended: true, sentence: updated }
  │
  └── User clicks Send → POST /api/hand_enter
        ├── increment_usage(sign_sessions)
        └── run_safe_therapy_pipeline()  [7 agents]
```

### 5.4 Research Chat Workflow

```
User submits research query → POST /api/research_chat
  │
  ├── ScopeGuardAgent checks scope (keyword-only, no LLM)
  │     ├── mental_health scope? → ALLOWED
  │     └── out_of_scope?        → BLOCKED, return boundary message
  │
  ├── TemplateAgent selects best template (keyword / Ollama)
  │     10 categories: sleep, anxiety, stress, loneliness,
  │     academic_pressure, relationship, self_doubt, anger,
  │     mood_tracking, professional_help, crisis_safety
  │     Default fallback: stress_management_plan
  │
  ├── ResearchAgent generates structured 6-paragraph response (Ollama local)
  │     ├── Explanation Simplified
  │     ├── What Might Be Going On (non-diagnostic)
  │     ├── Safe Ways to Cope (3–5 options)
  │     ├── Questions for Reflection (2 questions)
  │     ├── When to See a Professional
  │     └── Important Safety Notice
  │     + _post_filter() removes unsafe language
  │
  ├── increment_usage(research_queries)
  │
  └── Dual persistence:
        ├── Local JSON: data/research_chat_history.json (cap: 50/user)
        └── Supabase: research_chat_history table (query, answer,
              template metadata, safety, agent_trace as JSONB)
```

### 5.5 Knowledge Chat Workflow

```
User submits KB query → POST /api/knowledge_chat
  │
  ├── ScopeGuardAgent keyword check
  │     Special "real-life wellbeing override":
  │     "mentally / leave / trip / burnout" → classified as mental_health
  │
  ├── KnowledgeAgent (Ollama + extractive fallback)
  │     ├── retrieve_knowledge() — vector or keyword retrieval
  │     ├── Build context from fetched KB entries
  │     ├── Generate supportive chatbot-style response (no headings)
  │     └── _extractive_fallback() if Ollama unavailable
  │
  ├── increment_usage(knowledge_queries)
  └── Return grounded response + safety metadata
```

---

## 6. Emotion Detection Workflow

```
Every 1600ms — JavaScript polls /api/emotion_detect
  │
  ├── HTML5 Canvas captures webcam frame
  ├── Frame encoded as base64 JPEG
  ├── POST to /api/emotion_detect
  │
  Backend:
  ├── Decode base64 → NumPy array (np.frombuffer)
  ├── Reconstruct image via cv2.imdecode()
  ├── Convert BGR → RGB (cv2.cvtColor)
  ├── MTCNN face detection on RGB frame
  │     IF no face detected → return { emotion: null }
  ├── Extract face region bounding box
  ├── FER CNN classifier on face region
  ├── Get emotion scores dict { happy, sad, angry, fear, disgust, surprise, neutral }
  ├── dominant = argmax(emotion_scores)
  ├── Store in session['sentiment']
  └── Return JSON { emotion, scores, confidence }
        │
        ▼
  EmotionAgent uses this on every chat message
  to blend facial data with text-based emotional context
```

---

## 7. Supabase Persistence Workflow

```
┌─────────────────────────────────────────────────┐
│  DUAL PERSISTENCE STRATEGY                      │
│                                                 │
│  Primary Layer (always):                        │
│    neurosense_data.json (local)                 │
│    Atomic write: .tmp → fsync → os.replace()    │
│                                                 │
│  Secondary Layer (best-effort):                 │
│    Supabase (13 tables)                         │
│    Failure silently caught, returns {ok: False} │
│    Core app remains fully functional offline    │
└─────────────────────────────────────────────────┘

On every Supabase write:
  │
  ├── _supabase_insert() / _supabase_update() helper called
  ├── Exceptions caught → return None (never raise)
  ├── Caller checks: if result is not None → extract supabase_id
  └── All 13 tables use RLS (Row Level Security)
        auth.uid() = user_id enforced at DB engine level

Supabase Client Types:
  ├── supabase_public  (anon key)  — frontend ops, RLS enforced
  └── supabase         (service role key) — Flask backend, bypasses RLS
        (Flask acts as the trusted access-control layer)
```

### Data Read Preference (Research History Example)

```
GET /api/research_chat/history
  │
  ├── _supabase_can_write() == True?
  │     YES → fetch from Supabase research_chat_history table
  │           (cross-device history for logged-in users)
  └── NO / offline → fetch from local data/research_chat_history.json
```

---

## 8. Report Generation Workflow

```
POST /api/report/generate
  │
  ├── ReportAgent generates structured report data
  │     (temperature: 0.25, max_tokens: 1500)
  │     ├── Assessment Report ID: NSA-YYYYMMDDHHMM-USERNAME
  │     └── Solution Report ID:   NSP-YYYYMMDDHHMM-USERNAME
  │
  ├── PDF/CSV file written to temporary server location
  ├── UUID token generated → stored in _report_tokens dict (TTL: 5 min)
  ├── Metadata saved to neurosense_reports table (Supabase)
  ├── increment_usage(reports_generated)
  └── Return { token, report_id }

GET /api/report/download?token=<UUID>
  │
  ├── Validate token exists in _report_tokens
  ├── Check token not expired (5-minute window)
  ├── Extract file bytes from temp location
  ├── Delete temporary file from disk
  ├── Remove UUID from _report_tokens
  └── Stream file to user's browser
        (prevents unauthorised downloads + auto-clears temp storage)
```

---

## 9. Admin System Workflow

```
Admin Access Control:
  │
  ├── ADMIN_EMAILS env variable (comma-separated list)
  ├── is_admin_user() checks session["email"] against list on EVERY request
  └── No DB role elevation — user_profiles.role ignored for admin check

@admin_required decorator:
  ├── JSON API requests → return 403 JSON
  └── Browser requests → return inline HTML 403 (no template dependency)

GET /api/admin/realtime
  └── Live platform stats from user_profiles table

GET /api/project/accuracy — Real-Time Accuracy Engine:
  │
  ├── User Feedback Score     (30%) — helpful / total feedback
  ├── Safety Pass Rate        (25%) — non-unsafe / total safety events
  ├── Emotion Confidence      (20%) — avg confidence across emotion_logs
  ├── Report Success Rate     (15%) — no-error reports / total reports
  └── Session Completion Rate (10%) — sessions ≥ 2 msgs / total sessions

POST /api/user/delete_account
  └── Soft-delete: is_active = false (data preserved)
```

---

## 10. Error & Fallback Workflow

```
Every Agent in Pipeline:
  │
  ├── LLM call wrapped in try/except
  ├── Groq client = None? → skip LLM, use deterministic fallback immediately
  └── LLM returns invalid JSON? → parse_json() strips fences + regex extracts
        Still fails? → fallback dict returned (never raises exception)

Global Safety Safety Net (BaseAgent):
  │
  ├── contains_unsafe_medical_claim(text) — 40+ regex patterns
  ├── safe_with_fallback()     — hardcoded supportive message
  └── crisis_response()        — hardcoded crisis response with all helplines:
        Tele-MANAS   : 14416
        iCALL        : 9152987821
        KIRAN        : 1800-599-0019
        Vandrevala   : +91 9999 666 555
        AASRA        : 022-27546669

Usage Limit Failures:
  └── increment_usage() wrapped in try/except
        Returns {ok: False} on failure — never blocks user message

Supabase Outage:
  └── All Supabase helpers return None on failure
        App operates entirely on local neurosense_data.json
        Core mental health support experience unaffected
```

---

*NeuroSense AI — Workflow Documentation | Group 48 | SRM University Delhi-NCR | May 2026*