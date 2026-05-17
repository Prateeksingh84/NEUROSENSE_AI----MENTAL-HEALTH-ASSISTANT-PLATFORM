# AGENTS.md — NeuroSense AI Multi-Agent System

Complete technical reference for the NeuroSense AI agentic pipeline. Every agent described here is implemented in the `agents/` directory.

---

## Design Philosophy

The multi-agent architecture was chosen because a single monolithic LLM prompt **cannot** simultaneously handle crisis detection, emotional analysis, social wellbeing assessment, hallucination prevention, and therapeutic response generation without inflating prompt length, degrading quality, and creating unpredictable safety failures.

Three governing principles:

| Principle | Implementation |
|---|---|
| **Single Responsibility** | Each agent has one job and one JSON output schema |
| **Fail-Safe Degradation** | Every agent has a deterministic (non-LLM) fallback |
| **Transparency** | Every agent output is included in the `agents` trace in every API response |

---

## Agent Inventory

| Agent | File | Temp | Max Tokens | LLM Backend | Fallback |
|---|---|---|---|---|---|
| SafetyAgent | safety_agent.py | 0.0 | 500 | Groq | Keyword deterministic precheck |
| EmotionAgent | emotion_agent.py | 0.1 | 600 | Groq | Wellbeing check-in mood score |
| SocialAgent | social_agent.py | 0.1 | 650 | Groq | Concern list mapping |
| TherapyAgent | therapy_agent.py | 0.45 | 650 | Groq | safe_support_fallback() |
| WellnessAgent | wellness_agent.py | 0.25 | 850 | Groq | deterministic_recommendations() |
| PsychiatristAgent | psychiatrist_agent.py | 0.1 | 750 | Groq | deterministic_referral() |
| HallucinationAgent | hallucination_agent.py | 0.0 | 800 | Groq | Regex precheck → safe_support_fallback() |
| ResearchAgent | research_agent.py | 0.25 | 1500 | **Ollama (local)** | Instructional fallback string |
| TemplateAgent | template_agent.py | — | 300 | Optional Ollama | Keyword category detection |
| ScopeGuardAgent | scope_guard_agent.py | — | — | **None** | Keyword allow/deny list |
| KnowledgeAgent | knowledge_agent.py | 0.25 | 500 | Optional Ollama | Extractive KB fallback |
| ReportAgent | report_agent.py | 0.25 | 1500 | Groq | Structured fallback dict |

---

## BaseAgent — The Shared Foundation

**File:** `agents/base_agent.py`

All 12 agents inherit from `BaseAgent`. It provides:

### Methods

```python
call_llm(system_prompt, user_prompt, temperature, max_tokens, json_mode) -> str
```
Safe Groq API call. Returns `""` on failure (never raises). Uses `json_mode=True` when structured output is required.

```python
call_json(system_prompt, user_prompt, fallback) -> dict
```
Calls LLM in JSON mode and returns parsed dict. Returns `fallback` dict on any failure including malformed JSON.

```python
parse_json(raw, fallback) -> dict
```
Parses raw LLM string as JSON. Strips markdown fences (` ```json ` blocks). Uses regex `\{.*\}` extraction if needed. Never raises.

```python
clean_history(history) -> list[dict]
```
Normalises chat history from any input format to `[{"role": "...", "content": "..."}]`.

```python
contains_unsafe_medical_claim(text) -> bool
```
Regex guard checking 40+ patterns across five categories:
- Diagnosis: `"you have depression"`, `"you have anxiety disorder"`, `"I diagnose you with"`
- Medication: `"start taking medication"`, `"take X mg"`, `"prescribe"`
- Guaranteed cure: `"this will cure you"`, `"100% effective"`, `"no side effects"`
- Discouraging professional help: `"you don't need a doctor"`, `"avoid therapy"`
- Unsafe crisis: `"self harm is okay"`, `"ignore suicidal thoughts"`

```python
safe_support_fallback() -> str
```
Returns hardcoded supportive message when no LLM output is usable.

```python
crisis_response() -> str
```
Returns hardcoded crisis message with all India helplines: Tele-MANAS (14416), iCALL (9152987821), Vandrevala Foundation (+91 9999 666 555), KIRAN (1800-599-0019), AASRA (022-27546669).

### GLOBAL_SAFETY_RULES

Defined in `base_agent.py`, imported by **all agents**. Contains 15 rules:
- No mental health diagnosis
- No medication prescription or dosage changes
- Non-diagnostic wording requirements (`"you may be feeling..."`, `"it may help to..."`)
- Crisis escalation protocol with all India helpline numbers
- No guaranteed cure claims
- No discouraging professional help

The Groq client is initialised at agent startup and set to `None` if the API key is invalid, allowing all agents to skip LLM calls gracefully.

---

## The Main Pipeline — `run_safe_therapy_pipeline()`

**File:** `agents/orchestrator.py`
**Called by:** `agent_reply()` in `app.py` — for every Normal Chat, Voice Chat, and Hand Sign Chat message.

### Pipeline Stage Sequence

| Stage | Agent | Activates When | Output Fields | Supabase Effect |
|---|---|---|---|---|
| 1 | SafetyAgent | Every message (mandatory) | risk_level, self_harm, violence, abuse, medical_advice_requested, allow_normal_response | None |
| 2 | EmotionAgent | Non-crisis only | dominant_emotion, emotional_intensity, mood_score_estimate, emotional_summary | Updates session sentiment |
| 3 | SocialAgent | Non-crisis only | social_risk, support_availability, main_social_factors, recommended_support_action | None |
| 4 | WellnessAgent | Non-crisis only | top_practices[5], immediate_action, note | Passed in API response |
| 5 | PsychiatristAgent | Every message | needs_professional_referral, urgency, recommended_professional, user_facing_message | Logged to professional_help_logs |
| 6 | TherapyAgent | Non-crisis (after 2–5) | reply, response_type, technique_used | Stored via log_msg() |
| 7 | HallucinationAgent | Every draft reply | safe, issues[], corrected_reply | Corrected reply replaces draft |

### Crisis Early-Exit

If Stage 1 returns `risk_level = "crisis"`, the pipeline **terminates immediately**. No further agents are called. The response is built from the hardcoded `crisis_fallback_response()` and returned with:

```json
{
  "reply": "<crisis helplines message>",
  "safe": true,
  "risk_level": "crisis",
  "response_type": "crisis",
  "referral": {
    "needs_professional_referral": true,
    "urgency": "emergency",
    "recommended_professional": "emergency services or crisis helpline"
  }
}
```

This design ensures no LLM inference can dilute or delay a crisis response.

### Referral Message Injection

After Stage 6, if `PsychiatristAgent` says `needs_professional_referral = True`, the `user_facing_message` is appended to the therapy reply (if not already present). TherapyAgent never needs to know about clinical escalation logic.

### Triple-Layer Hallucination Blocking

1. `HallucinationAgent.deterministic_check()` — instant regex scan before any LLM call
2. `HallucinationAgent.run()` — LLM verification against full context
3. Post-correction `contains_unsafe_medical_claim()` check on the corrected reply — if still unsafe, hardcoded fallback is used

### Complete Pipeline Return Schema

```json
{
  "reply": "final user-facing text",
  "safe": true,
  "risk_level": "none | low | medium | high | crisis",
  "response_type": "supportive | grounding | referral | crisis",
  "technique_used": "CBT | DBT | grounding | validation | reflection | referral",
  "agents": {
    "safety_agent": { "risk_level": "...", "self_harm": false, ... },
    "emotion_agent": { "dominant_emotion": "...", "mood_score_estimate": 72, ... },
    "social_agent": { "social_risk": "...", ... },
    "wellness_agent": { "top_practices": [...], ... },
    "clinical_escalation_agent": { "needs_professional_referral": false, ... },
    "therapy_agent": { "reply": "...", "technique_used": "..." },
    "hallucination_agent": { "safe": true, "issues": [] }
  },
  "wellness": { "top_practices": [...], "immediate_action": "...", "note": "..." },
  "referral": { "needs_professional_referral": false, "urgency": "none", ... }
}
```

---

## Individual Agent Specifications

### SafetyAgent

**Temperature:** 0.0 (fully deterministic)

**Two-stage classification:**

**Stage 1 — Keyword Precheck (instant, no LLM):**

| Term Category | Example Terms | Result |
|---|---|---|
| Crisis/Self-harm | "suicide", "kill myself", "end my life", "self harm", "i want to die" | risk_level = crisis, allow_normal_response = false |
| Violence | "kill someone", "murder", "attack someone" | risk_level = high |
| Abuse | "domestic violence", "abuse", "blackmail" | risk_level = medium |
| Medication | "medicine", "antidepressant", "dose", "prescribe" | medical_advice_requested = true |

**Stage 2 — LLM Classification (only when Stage 1 is inconclusive):**

Output schema:
```json
{
  "risk_level": "none | low | medium | high | crisis",
  "self_harm": true/false,
  "violence": true/false,
  "abuse": true/false,
  "medical_advice_requested": true/false,
  "allow_normal_response": true/false,
  "reason": "short reason string"
}
```

---

### EmotionAgent

**Temperature:** 0.1 | **Inputs:** user message, detected facial emotion, wellbeing check-in, chat history

The `mood_score_estimate` is clamped to `[0, 100]` post-processing regardless of LLM output.

Output schema:
```json
{
  "dominant_emotion": "happy | calm | neutral | sad | anxious | angry | overwhelmed | stressed | lonely",
  "emotional_intensity": "low | moderate | high",
  "mood_score_estimate": 0,
  "emotional_summary": "non-diagnostic summary",
  "confidence": "low | medium | high"
}
```

---

### SocialAgent

**Temperature:** 0.1 | **Inputs:** user message, wellbeing check-in, chat history

Analyses loneliness, relationship stress, academic pressure, support availability.

**Deterministic fallback logic:**
- `support_available = "no"` or `"maybe"` → `social_risk = "medium"`
- Concerns list passed directly to `main_social_factors`

Output schema:
```json
{
  "social_risk": "low | medium | high",
  "support_availability": "yes | maybe | no | unknown",
  "main_social_factors": ["loneliness", "academic_pressure"],
  "summary": "short non-diagnostic summary",
  "recommended_support_action": "one practical safe action"
}
```

---

### WellnessAgent

**Temperature:** 0.25 | **Generates:** exactly 5 wellness recommendations

**Deterministic fallback mapping (`deterministic_recommendations()`):**

| Condition | Recommendation |
|---|---|
| stress ≥ 4 OR mood in (anxious, overwhelmed, angry) | Box Breathing (4-4-4-4 cycle) |
| mood in (sad, overwhelmed) OR "self_doubt" in concerns | Thought Journal |
| sleep in (poor, very_poor) | Sleep Wind-Down Routine (no screens 30min before bed) |
| social_connection ≤ 2 OR support = no/maybe OR "loneliness" in concerns | Trusted Person Check-In |
| (Always fills remaining slots) | 5-4-3-2-1 Grounding, Small Action Plan, Hydration & Movement |

Output schema:
```json
{
  "top_practices": [
    {
      "title": "Box Breathing",
      "description": "Breathe in 4s, hold 4s, breathe out 4s, hold 4s",
      "frequency": "2–3 times daily",
      "category": "stress_regulation"
    }
  ],
  "immediate_action": "one small action right now",
  "note": "safety note — not medical treatment"
}
```

---

### PsychiatristAgent (Clinical Escalation Agent)

**⚠️ This agent is NOT a psychiatrist. It decides referral urgency only.**

**Temperature:** 0.1

**Deterministic referral logic (`deterministic_referral()`):**

| Trigger | Urgency | Recommended Professional |
|---|---|---|
| risk_level = crisis OR self_harm = True | emergency | emergency services or crisis helpline |
| Medication keywords in message | soon | psychiatrist |
| stress ≥ 4, emotional_safety ≤ 2, mood = overwhelmed, sleep = very_poor | soon | psychologist or psychiatrist |
| support_available = "no" | routine | counsellor or psychologist |
| No triggers | none | none |

Output schema:
```json
{
  "needs_professional_referral": true/false,
  "urgency": "none | routine | soon | urgent | emergency",
  "recommended_professional": "none | counsellor | psychologist | psychiatrist | emergency services or crisis helpline",
  "reason": "short non-diagnostic reason",
  "user_facing_message": "safe message for user",
  "professional_summary": "brief summary user can show to a professional"
}
```

---

### TherapyAgent

**Temperature:** 0.45 (highest — allows natural varied language)

The only agent whose job is to generate user-facing text. Uses CBT/DBT-inspired approaches. Explicitly instructed: no diagnosis, no medication, no psychiatrist impersonation. Post-generation `contains_unsafe_medical_claim()` check before passing to HallucinationAgent.

Output schema:
```json
{
  "reply": "3–6 sentence warm supportive response",
  "response_type": "supportive | grounding | referral | crisis",
  "technique_used": "CBT | DBT | grounding | validation | reflection | referral"
}
```

---

### HallucinationAgent

**Temperature:** 0.0 (fully deterministic)

**Stage 1 — Regex Precheck (40+ patterns, 5 categories):**
- Diagnosis claims: `"you have depression"`, `"I diagnose you with"`, `"your diagnosis is"`
- Medication/prescription: `"start taking medication"`, `"take X mg"`, `"prescribe"`, `"prescription"`
- Guaranteed cure: `"this will cure you"`, `"100% effective"`, `"no side effects"`, `"this always works"`
- Discouraging professional help: `"you don't need a doctor"`, `"avoid therapy"`, `"ignore your therapist"`
- Unsafe crisis guidance: `"self harm is okay"`, `"ignore suicidal thoughts"`, `"you should kill yourself"`

**Stage 2 — LLM Verification** against full context.

**Stage 3 — Post-correction regex check** — if corrected reply still contains unsafe content, hardcoded `safe_support_fallback()` used.

Output schema:
```json
{
  "safe": true/false,
  "issues": ["description of issue if any"],
  "corrected_reply": "safe version of the response"
}
```

---

### ResearchAgent

**Backend:** Ollama (local model — not Groq). All inference stays on device.

Generates structured mental-health education responses for the **Research Chat** feature. Output format is six Markdown sections:

1. `### 1. Simple Explanation` — topic in plain language
2. `### 2. What May Be Happening` — non-diagnostic possibilities from context only
3. `### 3. Safe Coping Steps` — 3–5 practical low-risk steps
4. `### 4. Reflection Prompt` — 2 reflection questions
5. `### 5. When To Seek Professional Help` — counsellor/psychologist/psychiatrist/helpline
6. `### 6. Safety Note` — explicit non-diagnosis disclaimer

Post-generation `_post_filter()` replaces unsafe phrases:
- `"you have depression"` → `"you may be experiencing low mood"`
- `"take medication"` → `"speak with a qualified doctor about medication"`

---

### ScopeGuardAgent

**No LLM calls ever.** Pure keyword matching for speed and adversarial robustness.

**Scope categories:**

| Category | Example Trigger | Response Type | Allowed? |
|---|---|---|---|
| crisis | "suicide", "kill myself", "want to die" | crisis | ✅ Yes (redirected) |
| safe_smalltalk | "hi", "thanks", "bye", "help" | greeting/thanks/bye/help | ✅ Yes |
| medication_boundary | "which medicine", "dose", "antidepressant" | medication_boundary | ✅ Yes (guardrail) |
| diagnosis_boundary | "do I have depression", "am I bipolar" | diagnosis_boundary | ✅ Yes (guardrail) |
| mental_health | "stress", "sleep", "burnout", "leave", "trip" | knowledge_answer | ✅ Yes |
| out_of_scope | "cricket score", "stocks", "recipe", "hack" | refusal | ❌ No |

**Important design note:** Questions like *"I am mentally not well, should I take leave or go for a trip?"* are allowed because "mentally", "leave", "trip", and "burnout" all match the mental_health scope even though they contain lifestyle decision words.

---

### KnowledgeAgent

**Backend:** Ollama (with extractive fallback when Ollama unavailable)

Retrieves approved knowledge base entries, builds context, generates grounded conversational answers. **Not report-style** — answers like a supportive chatbot.

Key instruction for life decisions: if user asks *"should I leave work?"*, agent says *"I cannot decide for you, but..."* and provides balanced decision support across 5 dimensions.

`_post_filter()` removes rigid headings and unsafe phrases from Ollama output before returning.

---

### TemplateAgent

Template selection operates in two modes:

**Mode 1 — Keyword detection (instant, no LLM):**

| Keywords | Category |
|---|---|
| "sleep", "insomnia", "tired" | sleep |
| "anxiety", "anxious", "panic", "overthinking" | anxiety |
| "stress", "overwhelmed", "burnout" | stress |
| "alone", "lonely", "isolated" | loneliness |
| "exam", "study", "college", "assignment" | academic_pressure |
| "relationship", "breakup", "partner" | relationship |
| "confidence", "self doubt", "worthless" | self_doubt |
| "anger", "angry", "rage" | anger |
| "suicide", "self harm", "unsafe" | crisis_safety |

**Mode 2 — Optional Ollama classification** for ambiguous queries.

**Default fallback:** `stress_management_plan` template (safest general-purpose).

---

### ReportAgent

**Temperature:** 0.25 | **Max Tokens:** 1500

Generates structured data for two report types:

- **Assessment Report** (`generate_assessment_report()`) → Report ID format: `NSA-YYYYMMDDHHMM-USERNAME`
- **Solution Report** (`generate_solution_report()`) → Report ID format: `NSP-YYYYMMDDHHMM-USERNAME`

Both have identical safety constraints: no diagnosis, no prescription, no invented details. Both have structured fallback dicts returned when LLM output fails.

---

## `run_analysis_only()` — Lightweight Helper

A secondary function in `orchestrator.py` that runs only the analysis agents (Safety, Emotion, Social, Wellness, PsychiatristAgent) without TherapyAgent or HallucinationAgent. Used for report generation where a response text is not needed.