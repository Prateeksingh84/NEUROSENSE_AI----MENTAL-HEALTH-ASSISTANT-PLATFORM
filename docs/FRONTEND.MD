# FRONTEND.md — NeuroSense AI Frontend Architecture

Complete reference for the frontend implementation: HTML templates, JavaScript modules, responsive design, and UI features.

---

## Technology Choices

| Technology | Purpose | Why Chosen |
|---|---|---|
| HTML5 + CSS3 + Vanilla JS | UI framework | No build step; runs in any modern browser |
| Jinja2 | Server-side templating | Native Flask integration; Python-to-JS data bridge via `tojson` filter |
| Chart.js 4.4.1 | Dashboard charts | Lightweight, responsive, no dependencies |
| Google Fonts (Outfit, DM Sans, JetBrains Mono) | Typography | Professional aesthetic |
| Web Speech API (browser native) | Speech-to-text | Zero dependency; works in Chrome/Edge |
| HTML5 Canvas API | Webcam frame capture | Base64 JPEG export for /api/emotion_detect |
| CSS Custom Properties | Theme system | Dark/light mode without JS |

---

## Responsive Design Breakpoints

| Screen Width | Layout Behaviour |
|---|---|
| > 1100px | Full 3-column layout with side panels |
| 768–1100px | 2-column layout, panels stack vertically |
| < 768px | Single column, navigation simplifies |
| < 480px | Mobile-first compact layout |

---

## Page-by-Page Architecture

### `index.html` — Landing Page
Public-facing landing page. No auth required. Links to `/auth`.

### `login.html` — Auth / Registration
- **Form-based login (fallback):** `POST /auth` with name, email, phone, language → Flask session
- **Supabase Auth (primary):** JavaScript Supabase client handles email/password and OAuth sign-in → JWT → `POST /api/auth/sync`
- Language dropdown populated from `SUPPORTED_LANGUAGES` dict (44 languages)

### `mode_select.html` — Mode Selection + Wellbeing Check-In

The most important entry screen. Before starting any chat, the user completes the Mental & Social Wellbeing Check-In:

**Check-In Fields (7 inputs):**
1. `mood` — radio: happy, calm, neutral, sad, anxious, angry, overwhelmed
2. `stress` — slider 1–5
3. `social_connection` — slider 1–5
4. `emotional_safety` — slider 1–5
5. `sleep` — radio: good, okay, poor, very_poor
6. `support_available` — radio: yes, maybe, no
7. `concerns` — multi-select checkboxes (10 options)
8. `current_thoughts` — textarea (max 1200 chars)

On submit → `POST /api/wellbeing_checkin` → backend scores and saves → user redirected to chosen mode.

**Mode cards:**
- Text Chat → `/normal_chat`
- Voice Chat → `/voice_chat`
- Hand Sign Chat → `/hand_chat`
- Research Chat → `/research_chat`
- Knowledge Chat → `/knowledge_chat`

### `normal_chat.html` — Text Chat Interface

**JavaScript Modules:**

```javascript
// Camera Management
initCam()          // Requests webcam permission, shows preview
toggleCam()        // Enable/disable camera overlay

// Emotion Detection Loop (runs every 1600ms)
detectEmo()        // Captures frame → base64 → POST /api/emotion_detect
setInterval(detectEmo, 1600)
renderBars()       // Animates emotion probability bar chart in sidebar

// Chat Handler
sendMsg()          // POST /api/chat → renders reply
addMsg(role, text) // Appends message bubble to chat window

// TTS
toggleTTS()        // Enable/disable auto-speak on AI reply
speakBtn()         // Manual speak trigger

// Quick Reply Shortcuts
qs(text)           // Pre-fills input with common phrases (e.g., "I feel anxious")

// Language Selector
changeLang() → POST /set_lang  // Updates session language
```

**Emotion sidebar:** Displays live 7-class probability bars. Updates every 1600ms. Shows dominant emotion label + confidence %.

**Webcam overlay:** Canvas element captures frames. Base64 JPEG encoded and POSTed to `/api/emotion_detect`. Result stored in `session['sentiment']` on the server.

### `voice_chat.html` — Voice Chat Interface

```javascript
// Web Speech API
startMic()         // Initialises SpeechRecognition with locale code
stopMic()          // Stops recording, sends final transcript
toggleMic()        // Toggle recording state

// Transcript Display
// interim results shown word-by-word as user speaks
// final results accumulated in curTx variable

// Recording UI
// Waveform animation: CSS keyframe driven (no JS canvas needed)
// Recording timer: setInterval display (MM:SS format)

// Voice Send
sendVoice()        // POST final transcript to /api/voice_chat
```

**Language map:** 16+ locale codes (e.g., `hi-IN`, `ta-IN`, `es-ES`) for Web Speech API `lang` property.

**TTS playback:** `SpeechSynthesisUtterance` with rate=0.88, pitch=1.0. Or server-side gTTS via `/api/voice_tts` endpoint for better multilingual quality.

### `hand_chat.html` — Sign Language Chat Interface

```javascript
// Camera Capture (polls every 350ms)
predict()          // Captures frame → POST /api/hand_predict

// Sign Display
// Flash animation when word is detected
// Hold progress bar: fills over 4 frames (1.4 seconds)
// Segment dots: 4 dots represent each required consecutive prediction

// Sentence Builder
// contenteditable div for manual editing alongside sign input
// Word count tracker
// onBxFocus/Blur handlers for edit mode toggle

// Controls
hand_enter()       // POST /api/hand_enter → AI response
hand_reset()       // POST /api/hand_reset → clears sentence
```

**Hold-to-confirm visual feedback:** As each consecutive stable prediction arrives, a progress bar fills. On the 4th frame, the word is appended and a flash animation fires.

### `dashboard.html` — Insights Dashboard

```javascript
// Chart.js Graphs (4 charts)
emotionChart       // Doughnut — emotion frequency distribution
moodChart          // Line — mood score over last 7 days
dailyChart         // Bar — messages per day last 7 days
sessionChart       // Bar — session count per day

// Box Breathing Engine
toggleBreath()     // Starts/stops 4-phase animation
PHASES = [         // [{name, duration, color, instruction}]
  {name:"Inhale", duration:4000},
  {name:"Hold",   duration:4000},
  {name:"Exhale", duration:4000},
  {name:"Hold",   duration:4000}
]

// Affirmation Rotator
setInterval(() => nextAffirmation(), 9000)  // Cycles through affirmations

// Habit Tracker (localStorage)
// Journal System (localStorage)
// Reminders (localStorage)
// Crisis Toolkit (5 panels: breathing, grounding, crisis resources, safety plan, helplines)

// Auto-Refresh
setInterval(() => fetchDashboardData(), 30000)  // Pulls /api/dashboard_data
```

### `analytics.html` — Analytics Dashboard

Data fetched from `_analytics_context()` in `app.py`. Displays:
- Emotional stability score
- Stress load percentage
- Positive mood ratio
- Mood trend (Improving ↗ / Stable → / Needs Attention ↘)
- Volatility assessment (High/Moderate/Low variation)
- Most-used mode (donut chart)
- Top concerns (bar chart)
- Engagement scatter plot (messages vs mood)
- Support need level (Low/Moderate/High with colour coding)

### `session_history.html` — Session History Viewer

Builds enriched session cards from local store:
- Session mode, date, message count (user + assistant)
- Dominant emotion + emotion timeline (last 12 detections)
- Mood score (average of MOOD_SCORE values for session emotions)
- Risk badge (Low/Medium/Crisis — detected from session message text)
- Session quality score (0–100, composite of messages, mood, risk, completion)
- Duration estimate from message timestamps
- Expandable conversation timeline

### `research_chat.html` — Research Chat (Ollama-Powered)

- Template selector (prebuilt + user custom)
- Template category filter
- Query input → `POST /api/research_chat`
- Displays structured 6-section Markdown response
- History panel (loads from Supabase or local JSON)
- Ollama status indicator (live via `/api/ollama/status`)

### `knowledge_chat.html` — Knowledge Chat (Grounded KB)

- Scope-limited mental-health Q&A
- Report upload panel (Assessment + Solution PDFs for context injection)
- Knowledge sources panel (shows which KB articles were retrieved)
- Out-of-scope refusal message displayed in-chat
- Crisis redirect built into response

### `best_practices.html` — CBT/DBT Exercises

Interactive guided exercises with completion logging:
- Box breathing (animated 4-phase guide)
- 4-7-8 breathing
- 5-4-3-2-1 grounding (step-by-step interactive)
- CBT thought record (3-step cognitive restructuring)
- DBT TIPP skill
- Gratitude note
- Self-compassion letter exercise
- Body scan meditation

Each completion triggers `POST /api/practices/log` → stored in local JSON.

### `support.html` — Crisis Support Page

- Intensity slider (1–10 self-rated crisis intensity)
- Real-time guided breathing with visual cue
- Safety plan editor (warning signs, coping steps, safe places, trusted people)
- Emergency contact call/SMS buttons
- Crisis helpline cards with phone numbers
- Crisis action log (records all UI interactions)

### `reports.html` / `assessment_report.html` / `solution_report.html`

- Generate buttons → `POST /api/report/generate`
- Download via one-time token → `GET /api/report/download?token=<uuid>`
- Assessment report: emotion distribution, mood trend, engagement patterns, session summary
- Solution report: 5 wellness suggestions, professional referral guidance, daily practices, crisis resources

### `admin_dashboard.html` — Admin Only

- Real-time stats cards (total users, active sessions, today's messages, reports)
- Weekly analytics line chart (mood + stress + sessions + messages)
- Recent platform activity feed (sessions, reports, practices, safety events)
- User list with status, session count, message count, last active
- Project accuracy gauge (weighted composite score)
- Export data button → `GET /api/admin/export`

---

## JavaScript Data Bridge (Jinja2 → JS)

Flask passes Python data to JavaScript via Jinja2's `tojson` filter:

```html
<!-- Example from dashboard.html -->
<script>
  const emotionFreq = {{ emotion_freq | tojson }};
  const moodTimeline = {{ mood_timeline | tojson }};
  const dailyLabels = {{ daily_labels | tojson }};
  const dailyCounts = {{ daily_counts | tojson }};
</script>
```

This pattern avoids AJAX for initial page data and allows Chart.js to render on load without a separate API call.

---

## API Communication Pattern

All frontend API calls use `fetch()` with JSON:

```javascript
async function sendMsg() {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: userInput, mode: 'normal_chat', lang: currentLang })
  });
  const data = await res.json();
  addMsg('assistant', data.reply);
}
```

**Agent trace display:** The `data.agents` object from `/api/chat` is used to display live agent decisions in a collapsible debug panel on the text chat page (for development/demo purposes).

---

## Webcam Frame Capture Pipeline

```javascript
// Every 1600ms:
1. Canvas.drawImage(videoElement, 0, 0, width, height)
2. canvas.toDataURL('image/jpeg', 0.7)  // 70% quality JPEG
3. base64 string → POST /api/emotion_detect body
4. Response: { emotion, scores, confidence }
5. Update session['sentiment'] on server
6. Update emotion bars in UI
```

CLAHE (Contrast Limited Adaptive Histogram Equalisation) is applied server-side in OpenCV on the decoded frame before FER processing to improve detection in low-light conditions.

---

## Supported Languages — Complete List (44)

| Code | Language | Native Name |
|---|---|---|
| en | English | English |
| hi | Hindi | हिन्दी |
| es | Spanish | Español |
| fr | French | Français |
| de | German | Deutsch |
| zh-CN | Chinese (Simplified) | 简体中文 |
| ja | Japanese | 日本語 |
| ko | Korean | 한국어 |
| ar | Arabic | العربية |
| ru | Russian | Русский |
| pt | Portuguese | Português |
| ta | Tamil | தமிழ் |
| te | Telugu | తెలుగు |
| bn | Bengali | বাংলা |
| mr | Marathi | मराठी |
| ml | Malayalam | മലയാളം |
| kn | Kannada | ಕನ್ನಡ |
| gu | Gujarati | ગુજરાતી |
| pa | Punjabi | ਪੰਜਾਬੀ |
| ur | Urdu | اردو |
| it | Italian | Italiano |
| nl | Dutch | Nederlands |
| pl | Polish | Polski |
| tr | Turkish | Türkçe |
| th | Thai | ไทย |
| vi | Vietnamese | Tiếng Việt |
| id | Indonesian | Bahasa Indonesia |
| sw | Swahili | Kiswahili |
| he | Hebrew | עברית |
| fa | Persian | فارسی |
| + 14 more | European + African | — |