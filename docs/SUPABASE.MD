# SUPABASE.md — NeuroSense AI Database & Auth Layer

Complete technical reference for the Supabase PostgreSQL integration in NeuroSense AI.

---

## Why Supabase?

| Requirement | Supabase Feature Used |
|---|---|
| User authentication (email/OAuth) | Supabase Auth (built-in JWT) |
| Data privacy per user | Row Level Security (RLS) on every table |
| Profile & usage persistence | PostgreSQL tables |
| Avatar storage | Supabase Storage (S3-compatible bucket) |
| Admin analytics | Service role client (bypasses RLS) |
| Offline resilience | Dual-path: local JSON store + Supabase |

---

## Client Initialisation

**File:** `utils/supabase_client.py`

Two separate clients are initialised:

```python
# Public client — frontend operations (respects RLS)
supabase_public: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Service role client — Flask backend writes (bypasses RLS)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

**Three required environment variables** (validated at import time — app fails to start if missing):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

The service role client bypasses RLS intentionally — the Flask backend is the authoritative trusted layer that enforces its own access checks before writing.

---

## Database Schema — 13 Tables

### Table 1: `user_profiles`
Links to `auth.users` via FK. Core identity record.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | References auth.users(id) ON DELETE CASCADE |
| full_name | TEXT | Not null, default 'User' |
| email | TEXT UNIQUE | — |
| phone | TEXT | — |
| avatar_url | TEXT | Local path or Supabase Storage URL |
| role | TEXT | CHECK IN ('admin', 'user'), default 'user' |
| account_status | TEXT | CHECK IN ('active', 'disabled', 'deleted') |
| preferred_language | TEXT | Default 'en' |
| emergency_contact_name | TEXT | For crisis support page |
| emergency_contact_phone | TEXT | For crisis support page |
| daily_limit | INTEGER | Default 100 |
| monthly_limit | INTEGER | Default 2000 |
| last_active | TIMESTAMPTZ | Updated on each login |
| created_at / updated_at | TIMESTAMPTZ | Auto |

### Table 2: `usage_limits`
Per-user per-day usage tracking for rate limiting.

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| user_id | UUID | FK → user_profiles(id) |
| usage_date | DATE | DEFAULT current_date |
| month_key | TEXT | Format: 'YYYY-MM' |
| daily_messages | INT | Default 0 |
| monthly_messages | INT | Default 0 |
| daily_limit | INT | Default 100 |
| monthly_limit | INT | Default 2000 |
| reports_generated | INT | Default 0 |
| voice_minutes | INT | Reserved |
| sign_sessions | INT | — |
| research_queries | INT | — |
| knowledge_queries | INT | — |
| image_uploads | INT | — |
| UNIQUE | (user_id, usage_date) | One row per user per day |

### Table 3: `chat_sessions`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID | FK → user_profiles |
| session_type | TEXT | CHECK IN ('normal', 'voice', 'sign') |
| dominant_emotion | TEXT | — |
| average_mood_score | NUMERIC(4,2) | — |
| summary | TEXT | — |
| started_at / ended_at | TIMESTAMPTZ | — |

### Table 4: `chat_messages`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| session_id | UUID | FK → chat_sessions |
| sender | TEXT | CHECK IN ('user', 'assistant') |
| message | TEXT | — |
| translated_message | TEXT | — |
| emotion | TEXT | Detected at message time |
| mood_score | NUMERIC(4,2) | — |

### Table 5: `emotion_logs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID | FK → user_profiles |
| session_id | UUID | FK → chat_sessions |
| emotion | TEXT | One of 7 classes |
| confidence | NUMERIC(5,2) | 0–100 scale |
| source_type | TEXT | CHECK IN ('camera', 'voice', 'text', 'sign') |
| detected_at | TIMESTAMPTZ | — |

### Table 6: `generated_reports`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID | FK → user_profiles |
| session_id | UUID | FK → chat_sessions, ON DELETE SET NULL |
| report_type | TEXT | CHECK IN ('pdf', 'csv') |
| report_title | TEXT | — |
| file_url | TEXT | Download path |

### Table 7: `user_settings`

| Column | Type | Default |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID UNIQUE | — |
| emotion_detection | BOOLEAN | true |
| voice_enabled | BOOLEAN | true |
| analytics_enabled | BOOLEAN | true |
| sign_language_enabled | BOOLEAN | false |
| anonymous_reports | BOOLEAN | false |
| auto_delete_sessions | BOOLEAN | false |
| theme | TEXT | 'dark' |

### Table 8: `admin_logs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| admin_id | UUID | FK → user_profiles |
| action | TEXT | e.g., "delete_user", "view_analytics" |
| target_user | UUID | FK → user_profiles |
| metadata | JSONB | Arbitrary action context |

### Table 9: `wellbeing_checkins`
Core mental health check-in records.

| Column | Type | Notes |
|---|---|---|
| user_id | UUID | FK → user_profiles |
| mood | TEXT | one of 7 valid moods |
| stress | INT | 1–5 |
| social_connection | INT | 1–5 |
| sleep | TEXT | good/okay/poor/very_poor |
| concerns | TEXT[] | Array of concern tags |
| emotional_safety | INT | 1–5 |
| support_available | TEXT | yes/maybe/no |
| current_thoughts | TEXT | Max 1200 chars |
| wellbeing_score | INT | 0–100 (calculated backend) |
| risk_level | TEXT | low/medium/high |
| score_explanation | JSONB | Deduction breakdown |
| risk_explanation | TEXT | Human-readable risk reason |
| source | TEXT | 'mode_checkin' |

### Table 10: `neurosense_reports`
Rich report metadata for dashboard analytics.

| Column | Type | Notes |
|---|---|---|
| user_id | UUID | — |
| report_id | TEXT | e.g., NSA-202506141200-PRAT |
| report_type | TEXT | assessment/solution/combined/therapy |
| format | TEXT | pdf/csv |
| title | TEXT | — |
| summary | TEXT | Max 2000 chars |
| risk_level | TEXT | — |
| top_emotion | TEXT | — |
| mood_trend | TEXT | improving/stable/declining |
| wellbeing_score | INT | From latest check-in |
| report_payload | JSONB | Full LLM report data |
| generated_at | TIMESTAMPTZ | — |

### Table 11: `mental_health_templates`
Prebuilt + user custom Research Chat templates.

| Column | Type | Notes |
|---|---|---|
| user_id | UUID | NULL for prebuilt templates |
| template_key | TEXT | Unique string ID (e.g., "stress_management_plan") |
| title | TEXT | Display name |
| category | TEXT | stress/sleep/anxiety/loneliness/etc. |
| description | TEXT | — |
| prompt | TEXT | Full LLM instruction prompt |
| output_type | TEXT | plan/analysis/exercise/guide/reflection |
| risk_level | TEXT | low/medium/high |
| is_prebuilt | BOOLEAN | — |
| is_active | BOOLEAN | Soft-delete flag |
| usage_count | INT | Incremented on each run |

### Table 12: `research_chat_history`
Full Research Chat Q&A audit log.

| Column | Type | Notes |
|---|---|---|
| user_id | UUID | — |
| template_id | UUID | FK → mental_health_templates |
| template_key | TEXT | — |
| template_title | TEXT | — |
| query | TEXT | User's research question |
| answer | TEXT | Full Ollama/agent response |
| model | TEXT | Model name used |
| used_ollama | BOOLEAN | — |
| risk_level | TEXT | none/low/medium/high/crisis |
| safety | JSONB | Full SafetyAgent output |
| professional_help | JSONB | Full PsychiatristAgent output |
| agent_trace | JSONB | Full orchestrator trace |

### Table 13: `professional_help_logs`

| Column | Type | Notes |
|---|---|---|
| user_id | UUID | — |
| wellbeing_checkin_id | UUID | FK → wellbeing_checkins |
| urgency | TEXT | none/routine/soon/urgent/emergency |
| emergency | BOOLEAN | — |
| needs_professional_help | BOOLEAN | — |
| issue_tags | TEXT[] | — |
| recommendations | JSONB | — |
| resources | JSONB | Crisis helplines, etc. |
| user_facing_message | TEXT | — |
| disclaimer | TEXT | — |

---

## Row Level Security — All 13 Tables

RLS is enabled on every table. Users can only access their own rows. Even if application code has a bug, the database returns zero rows for unauthorised access.

| Table | Operation | Policy |
|---|---|---|
| user_profiles | SELECT | `auth.uid() = id` |
| user_profiles | UPDATE | `auth.uid() = id` |
| user_profiles | INSERT | `auth.uid() = id` |
| usage_limits | SELECT | `auth.uid() = user_id` |
| usage_limits | INSERT/UPDATE | `auth.uid() = user_id` (Flask uses service role, bypasses) |
| chat_sessions | SELECT/INSERT/UPDATE | `auth.uid() = user_id` |
| chat_messages | SELECT/INSERT | `EXISTS (SELECT 1 FROM chat_sessions s WHERE s.id = session_id AND s.user_id = auth.uid())` |
| generated_reports | SELECT/INSERT | `auth.uid() = user_id` |
| emotion_logs | SELECT/INSERT | `auth.uid() = user_id` |
| user_settings | ALL | `auth.uid() = user_id` |
| admin_logs | SELECT | `EXISTS (SELECT 1 FROM user_profiles p WHERE p.id = auth.uid() AND p.role = 'admin')` |
| storage.objects (avatars) | SELECT | `bucket_id = 'avatars'` (public) |
| storage.objects (avatars) | INSERT/UPDATE | `bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]` |

---

## Authentication Flow

```
1. User signs in via Supabase Auth in browser (email/password or OAuth)
   └─► Supabase returns JWT access_token to browser

2. Frontend POSTs token to /api/auth/sync
   └─► Flask calls supabase.auth.get_user(access_token)
   └─► Verifies token server-side (handles network errors separately)

3. Flask calls get_or_create_profile(user_id, email, full_name, ...)
   └─► Fetches existing profile OR inserts new one
   └─► Minimal retry on schema cache mismatch

4. _set_login_session_from_profile() populates Flask session:
   └─► supabase_user_id, supabase_token, name, email, phone, lang, role, user_key

5. All subsequent requests use Flask session cookie (signed with SECRET_KEY)
   └─► JWT verified only once at login — no per-request Supabase auth call
```

**Error codes returned by `/api/auth/sync`:**
- `MISSING_ACCESS_TOKEN` — no JWT sent
- `SUPABASE_NOT_CONFIGURED` — missing env vars (503)
- `SUPABASE_NETWORK_ERROR` — DNS/connectivity failure (503)
- `SUPABASE_AUTH_VERIFY_FAILED` — invalid/expired token (401)
- `INVALID_SUPABASE_SESSION` — user object null (401)

---

## User Management Functions

**File:** `utils/supabase_user_management.py`

### `get_or_create_profile(user_id, email, full_name, name, phone, preferred_language, role, **kwargs)`

Handles three cases:
1. Profile exists → fetch and return normalised
2. Profile absent → insert full payload
3. Insert fails (schema cache mismatch) → retry with minimal payload (`id`, `email`, `full_name` only) then apply remaining fields as Python defaults

Accepts both `full_name=` and `name=` for backward compatibility. `**kwargs` absorbs any extra fields safely.

### `_normalize_profile(profile, fallback_name)`

Ensures profile always has: `full_name`, `name`, `email`, `phone`, `role`, `preferred_language`, `is_active`.

### `get_today_usage(user_id)` / `increment_usage(user_id, field, amount)`

Allowed usage fields:
```python
ALLOWED_USAGE_FIELDS = [
    "daily_messages", "monthly_messages", "reports_generated",
    "image_uploads", "voice_minutes", "sign_sessions",
    "research_queries", "knowledge_queries"
]
```

Usage increment triggers:

| Field | Trigger |
|---|---|
| daily_messages | Every user chat message (/api/chat, /api/voice_chat, /api/hand_enter) |
| monthly_messages | Same as daily_messages |
| reports_generated | /api/report/generate, /api/generate_and_download |
| knowledge_queries | /api/knowledge_chat (allowed + scoped only) |
| image_uploads | /api/user/avatar |
| sign_sessions | /api/hand_enter |
| voice_minutes | Reserved for future duration tracking |
| research_queries | Planned for /api/research_chat |

Every `increment_usage()` call is wrapped in try/except and returns `{"ok": False}` on failure — a Supabase outage **never** blocks a user from sending a message.

### Rate Limiting

```python
DEFAULT_DAILY_MESSAGE_LIMIT   = 100
DEFAULT_MONTHLY_MESSAGE_LIMIT = 2000
DEFAULT_REPORT_LIMIT          = 20
```

`check_usage_allowed(user_id)` returns `{"ok": True, "allowed": True/False, "usage": {...}, "limits": {...}}`. The `/api/chat` endpoint calls `_quota_response_if_blocked()` before processing any message, returning HTTP 429 when limits are exceeded.

---

## Avatar Upload

**Endpoint:** `POST /api/user/avatar`

Dual-path strategy:
1. **Local storage** — saved to `static/uploads/avatars/<user_id>_<timestamp>.<ext>` (immediately serveable)
2. **Supabase Storage (best-effort)** — `update_user_profile()` updates `avatar_url`; failure is caught and logged

Validation enforced:
- Extensions: png, jpg, jpeg, webp
- MIME types: image/png, image/jpeg, image/webp
- Max size: 5 MB
- Filename sanitised with `secure_filename()` and regex-cleaned user ID

---

## Report Token System

Report downloads use a one-time token system to prevent unauthorised file access.

```
POST /api/report/generate
  └─► Generates file to temp path
  └─► Creates UUID token in _report_tokens dict with 5-minute expiry
  └─► Returns {"ok": true, "token": "<uuid>"}

GET /api/report/download?token=<uuid>
  └─► Validates token exists and not expired
  └─► Reads file bytes from temp path
  └─► Deletes temp file
  └─► Removes token from dict
  └─► Streams file to browser
```

`_cleanup_report_tokens()` runs on every request via `@app.before_request` to purge expired tokens.

---

## Best-Effort Write Pattern

Every Supabase write in the application uses `_supabase_insert()` or `_supabase_delete()` which catch all exceptions and return `None` on failure. The application functions fully using local JSON (`neurosense_data.json`) even when Supabase is completely unreachable.

**Local JSON store (`neurosense_data.json`) persistence fields:**
- `sessions` — full chat history with messages and emotions
- `emotion_log` — timestamped emotion detections
- `message_count` — total message counter
- `streak_days` — set of ISO date strings for streak calculation
- `reports` — saved AI-generated reports (last 10)
- `wellbeing_checkins` — last 20 check-ins
- `avatar_url` — local path
- `crisis_actions` — crisis support UI event log
- `safety_plan` — user's personalised crisis safety plan
- `practice_logs` — best practice completion history
- `feedback_logs` — helpful/not helpful feedback

**Atomic write pattern in `_save_store()`:**
```python
# 1. Write to .tmp file
# 2. f.flush() + os.fsync() — force kernel buffer to disk
# 3. os.replace() — atomic rename (no corruption on kill)
```

---

## Admin System

### Access Control

Admin access controlled entirely via `ADMIN_EMAILS` environment variable (comma-separated list). `is_admin_user()` checks session email against this list in real-time on every request. No database role elevation — even `user_profiles.role = 'admin'` has no effect.

The `@admin_required` decorator:
- For JSON API requests → returns 403 JSON
- For browser requests → returns inline HTML 403 page (no template dependency)

### Real-Time Accuracy Engine (`/api/project/accuracy`)

Weighted composite score from live application signals:

| Signal | Weight | Calculation |
|---|---|---|
| User feedback score | 30% | Positive feedback / total feedback |
| Safety pass rate | 25% | 100 – (unsafe events / total safety events × 100) |
| Emotion confidence | 20% | Average confidence across all emotion_log entries |
| Report success rate | 15% | Successful reports / total reports |
| Session completion rate | 10% | Completed sessions / total sessions |

Grade thresholds: ≥90% = Excellent, ≥80% = Very Good, ≥70% = Good, <70% = Needs Improvement.