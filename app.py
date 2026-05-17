# ============================================================
# NeuroSense AI — Mental Health Assistant  (FULL CLEAN BUILD)
# All routes tested · delete fixed · no 404s · no import errors
# ============================================================

import sys, os, io, base64, datetime, json, uuid, tempfile, traceback, re, time
import urllib.request
import xml.etree.ElementTree as ET
import httpx
from collections import defaultdict, Counter

# ── ENV MUST BE LOADED FIRST ───────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Validate API Key ───────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY or GROQ_API_KEY in ("YOUR_GROQ_API_KEY_HERE", "your_key_here", ""):
    raise ValueError(
        "\n❌ GROQ_API_KEY not found or invalid!\n"
        "   1. Create a .env file in your project root\n"
        "   2. Add this line:\n"
        "      GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx\n"
        "   3. Get a free key at: https://console.groq.com\n"
    )
print(f"✅ GROQ_API_KEY loaded: {GROQ_API_KEY[:12]}...")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"]  = ""

# ── Groq Client ────────────────────────────────────────────────────────────────
from groq import Groq
chatbot_api = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL  = "llama-3.3-70b-versatile"


def _test_groq() -> bool:
    try:
        r = chatbot_api.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        print(f"✅ Groq API verified. Model: {GROQ_MODEL}")
        return True
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
        return False


# ── Core imports ───────────────────────────────────────────────────────────────
import cv2
import numpy as np
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, send_file,
)
from functools import wraps
from werkzeug.utils import secure_filename

# ── Supabase Enhanced User Management ────────────────────────────────────────
try:
    from utils.supabase_client import supabase
    from utils.supabase_user_management import (
        SUPABASE_READY,
        get_or_create_profile,
        get_profile_with_usage,
        update_user_profile,
        upload_avatar,
        soft_delete_account,
        check_usage_allowed,
        increment_usage,
        list_all_profiles,
    )
except Exception as e:
    SUPABASE_READY = False
    supabase = None
    print(f"⚠️  Supabase user-management disabled: {e}")



# ── Multi-Agent NeuroSense AI Pipeline ───────────────────────────────────────
try:
    from agents.orchestrator import run_safe_therapy_pipeline
    AGENTS_AVAILABLE = True
    print("✅ NeuroSense multi-agent pipeline ready.")
except Exception as e:
    AGENTS_AVAILABLE = False
    run_safe_therapy_pipeline = None
    print(f"⚠️  Multi-agent pipeline disabled: {e}")


# ── Wellbeing + Professional Help Utilities ─────────────────────────────────
try:
    from utils.wellbeing_utils import (
        normalize_checkin,
        build_checkin_response,
        summarize_checkin,
        summarize_wellbeing_trend,
        generate_safe_suggestions,
    )
    WELLBEING_UTILS_AVAILABLE = True
    print("✅ Wellbeing utilities ready.")
except Exception as e:
    WELLBEING_UTILS_AVAILABLE = False
    normalize_checkin = None
    build_checkin_response = None
    summarize_checkin = None
    summarize_wellbeing_trend = None
    generate_safe_suggestions = None
    print(f"⚠️  Wellbeing utilities disabled: {e}")

try:
    from utils.professional_help import (
        recommend_professional_help,
        format_resources_for_report,
        compact_professional_help_summary,
    )
    PROFESSIONAL_HELP_AVAILABLE = True
    print("✅ Professional help utility ready.")
except Exception as e:
    PROFESSIONAL_HELP_AVAILABLE = False
    recommend_professional_help = None
    format_resources_for_report = None
    compact_professional_help_summary = None
    print(f"⚠️  Professional help utility disabled: {e}")


# ── Research Chat + Template Engine + Ollama ─────────────────────────────────
try:
    from utils.ollama_client import ollama_status, get_ollama_client
    from utils.template_store import (
        list_prebuilt_templates,
        list_custom_templates,
        list_all_templates,
        get_template,
        create_custom_template,
        delete_custom_template,
        template_summary,
        TEMPLATE_CATEGORIES,
        OUTPUT_TYPES,
    )
    from agents.template_agent import TemplateAgent
    from agents.research_agent import ResearchAgent
    RESEARCH_ENGINE_AVAILABLE = True
    print("✅ Research Chat + Template Engine ready.")
except Exception as e:
    RESEARCH_ENGINE_AVAILABLE = False
    ollama_status = None
    get_ollama_client = None
    list_prebuilt_templates = None
    list_custom_templates = None
    list_all_templates = None
    get_template = None
    create_custom_template = None
    delete_custom_template = None
    template_summary = None
    TEMPLATE_CATEGORIES = []
    OUTPUT_TYPES = []
    TemplateAgent = None
    ResearchAgent = None
    print(f"⚠️  Research Chat + Template Engine disabled: {e}")

try:
    from agents.safety_agent import SafetyAgent
except Exception as e:
    SafetyAgent = None
    print(f"⚠️  Research SafetyAgent import failed: {e}")

try:
    from agents.hallucination_agent import HallucinationAgent
except Exception as e:
    HallucinationAgent = None
    print(f"⚠️  Research HallucinationAgent import failed: {e}")


# ── Knowledge Chat Engine (Mental-health scoped RAG) ─────────────────────────
try:
    from knowledge.retriever import retrieve_knowledge, knowledge_status as kb_retriever_status
    from agents.scope_guard_agent import ScopeGuardAgent
    from agents.knowledge_agent import KnowledgeAgent
    from utils.knowledge_store import (
        get_knowledge_history,
        append_knowledge_history,
        clear_knowledge_history,
        knowledge_store_status,
    )
    KNOWLEDGE_ENGINE_AVAILABLE = True
    print("✅ Knowledge Chat engine ready.")
except Exception as e:
    KNOWLEDGE_ENGINE_AVAILABLE = False
    retrieve_knowledge = None
    kb_retriever_status = None
    ScopeGuardAgent = None
    KnowledgeAgent = None
    get_knowledge_history = None
    append_knowledge_history = None
    clear_knowledge_history = None
    knowledge_store_status = None
    print(f"⚠️  Knowledge Chat engine disabled: {e}")

# ── Optional: hs_module ───────────────────────────────────────────────────────
try:
    import hs_module as hs
    HS_AVAILABLE = True
except ImportError:
    HS_AVAILABLE = False
    print("⚠️  hs_module not found — hand sign features disabled.")

# ── Translation ────────────────────────────────────────────────────────────────
TRANSLATOR_AVAILABLE = False
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
    print("✅ deep_translator ready.")
except Exception:
    print("⚠️  deep_translator not available.")

# ── Emotion Detection ──────────────────────────────────────────────────────────
EMOTION_BACKEND  = None
emotion_detector = None
FER_AVAILABLE    = False
DeepFace         = None

try:
    from fer import FER
    emotion_detector = FER(mtcnn=True)
    FER_AVAILABLE    = True
    EMOTION_BACKEND  = "fer"
    print("✅ FER ready (with MTCNN).")
except Exception as e1:
    print(f"⚠️  FER failed: {e1}")
    try:
        from deepface import DeepFace as DF
        DeepFace        = DF
        FER_AVAILABLE   = True
        EMOTION_BACKEND = "deepface"
        print("✅ DeepFace ready.")
    except Exception as e2:
        print(f"⚠️  DeepFace failed: {e2}")

FACE_CASCADE = None
try:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
    print("✅ Face cascade loaded.")
except Exception as e:
    print(f"⚠️  Face cascade failed: {e}")

# ── TTS ────────────────────────────────────────────────────────────────────────
TTS_AVAILABLE  = False
GTTS_AVAILABLE = False
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    print("✅ gTTS ready.")
except Exception:
    try:
        import pyttsx3
        TTS_AVAILABLE = True
        print("✅ pyttsx3 TTS ready.")
    except Exception:
        print("⚠️  No TTS engine available.")

# ── Supported Languages ────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en":    {"name": "English",              "native": "English",          "tts": "en"},
    "hi":    {"name": "Hindi",                "native": "हिन्दी",            "tts": "hi"},
    "es":    {"name": "Spanish",              "native": "Español",          "tts": "es"},
    "fr":    {"name": "French",               "native": "Français",         "tts": "fr"},
    "de":    {"name": "German",               "native": "Deutsch",          "tts": "de"},
    "zh-CN": {"name": "Chinese (Simplified)", "native": "简体中文",          "tts": "zh-CN"},
    "ja":    {"name": "Japanese",             "native": "日本語",            "tts": "ja"},
    "ko":    {"name": "Korean",               "native": "한국어",             "tts": "ko"},
    "ar":    {"name": "Arabic",               "native": "العربية",           "tts": "ar"},
    "ru":    {"name": "Russian",              "native": "Русский",          "tts": "ru"},
    "pt":    {"name": "Portuguese",           "native": "Português",        "tts": "pt"},
    "ta":    {"name": "Tamil",                "native": "தமிழ்",             "tts": "ta"},
    "te":    {"name": "Telugu",               "native": "తెలుగు",            "tts": "te"},
    "bn":    {"name": "Bengali",              "native": "বাংলা",             "tts": "bn"},
    "mr":    {"name": "Marathi",              "native": "मराठी",             "tts": "mr"},
    "ml":    {"name": "Malayalam",            "native": "മലയാളം",           "tts": "ml"},
    "kn":    {"name": "Kannada",              "native": "ಕನ್ನಡ",            "tts": "kn"},
    "gu":    {"name": "Gujarati",             "native": "ગુજરાતી",           "tts": "gu"},
    "pa":    {"name": "Punjabi",              "native": "ਪੰਜਾਬੀ",            "tts": "pa"},
    "ur":    {"name": "Urdu",                 "native": "اردو",              "tts": "ur"},
    "it":    {"name": "Italian",              "native": "Italiano",         "tts": "it"},
    "nl":    {"name": "Dutch",                "native": "Nederlands",       "tts": "nl"},
    "pl":    {"name": "Polish",               "native": "Polski",           "tts": "pl"},
    "tr":    {"name": "Turkish",              "native": "Türkçe",           "tts": "tr"},
    "th":    {"name": "Thai",                 "native": "ไทย",              "tts": "th"},
    "vi":    {"name": "Vietnamese",           "native": "Tiếng Việt",      "tts": "vi"},
    "id":    {"name": "Indonesian",           "native": "Bahasa Indonesia", "tts": "id"},
    "sw":    {"name": "Swahili",              "native": "Kiswahili",        "tts": "sw"},
    "he":    {"name": "Hebrew",               "native": "עברית",             "tts": "he"},
    "fa":    {"name": "Persian",              "native": "فارسی",             "tts": "fa"},
}

MOOD_SCORE = {
    "happy": 9, "surprise": 7, "neutral": 5,
    "fear": 3,  "sad": 2,      "disgust": 2,
    "angry": 1, "contempt": 1,
}

# Do NOT block crisis/self-harm words here.
# They must go to SafetyAgent so the app can respond safely.
# Keep this only for clear non-therapeutic spam/adult requests.
BANNED_WORDS = [
    "porn", "explicit sexual content",
]

# ── Persistent Store ───────────────────────────────────────────────────────────
STORE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "neurosense_data.json"
)


def _load_store() -> dict:
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            normalised = {}
            for uid, d in raw.items():
                if isinstance(d.get("streak_days"), list):
                    d["streak_days"] = set(d["streak_days"])
                normalised[uid.strip().lower()] = d
            print(f"✅ Store loaded: {len(normalised)} user(s)")
            return normalised
        except Exception as e:
            print(f"⚠️  Could not load store: {e}")
    return {}


def _save_store():
    try:
        serialisable = {}
        for uid, d in store.items():
            serialisable[uid] = {
                "sessions":      d.get("sessions",      []),
                "emotion_log":   d.get("emotion_log",   []),
                "message_count": d.get("message_count", 0),
                "streak_days":   list(d.get("streak_days", set())),
                "reports":       d.get("reports",       []),
                "wellbeing_checkins": d.get("wellbeing_checkins", []),
                "avatar_url":    d.get("avatar_url", ""),
                "crisis_actions": d.get("crisis_actions", []),
                "safety_plan":   d.get("safety_plan", {}),
                "practice_logs": d.get("practice_logs", []),
                "feedback_logs": d.get("feedback_logs", []),
            }
        tmp_path = STORE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, STORE_PATH)
    except Exception as e:
        print(f"⚠️  Could not save store: {e}")


def _default_user() -> dict:
    return {
        "sessions":      [],
        "emotion_log":   [],
        "message_count": 0,
        "streak_days":   set(),
        "reports":       [],
        "wellbeing_checkins": [],
        "avatar_url": "",
        "crisis_actions": [],
        "safety_plan": {
            "warning_signs": [],
            "coping_steps": [],
            "safe_places": [],
            "trusted_people": [],
            "things_to_avoid": [],
            "professional_resources": [],
            "updated_at": "",
        },
        "practice_logs": [],
        "feedback_logs": [],
    }


_raw  = _load_store()
store = defaultdict(_default_user, {
    k: {
        **_default_user(),
        **v,
        "streak_days": set(v.get("streak_days", [])),
        "reports":     v.get("reports", []),
        "wellbeing_checkins": v.get("wellbeing_checkins", []),
    }
    for k, v in _raw.items()
})

# ── Flask App ──────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "neurosense-secret-2024")

# ── In-memory report token store ──────────────────────────────────────────────
_report_tokens: dict = {}


def _cleanup_report_tokens():
    now     = datetime.datetime.utcnow()
    expired = [k for k, v in list(_report_tokens.items()) if now > v["expires"]]
    for k in expired:
        entry = _report_tokens.pop(k, None)
        if entry:
            try:
                os.unlink(entry["path"])
            except OSError:
                pass


@app.before_request
def _before():
    _cleanup_report_tokens()


# ── Helpers ────────────────────────────────────────────────────────────────────
def ukey() -> str:
    key = session.get("user_key", "").strip()
    if key:
        return key
    email = session.get("email", "").strip().lower()
    name  = session.get("name",  "").strip().lower()
    return email if email else (name if name else "anonymous")


def login_required(f):
    @wraps(f)
    def deco(*args, **kwargs):
        if "name" not in session or not session.get("user_key"):
            if "name" in session and not session.get("user_key"):
                email = session.get("email", "").strip().lower()
                name  = session.get("name",  "").strip().lower()
                session["user_key"] = email if email else name
            else:
                return redirect(url_for("home"))
        return f(*args, **kwargs)
    return deco




# ══════════════════════════════════════════════════════════════════════════════
# ADMIN AUTHENTICATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_admin_emails() -> set:
    """
    Admin access is controlled from .env.

    Example:
        ADMIN_EMAILS=prathamgsingh@gmail.com,prateek05.hestabit@gmail.com
    """
    raw = os.getenv("ADMIN_EMAILS", "")
    return {
        email.strip().lower()
        for email in raw.split(",")
        if email.strip()
    }


def is_admin_user() -> bool:
    """
    Real-time admin check.

    Admin access is based ONLY on the logged-in session email being present
    in ADMIN_EMAILS from .env. This prevents normal users from becoming
    admins because of a stale/frontend role value.
    """
    email = str(session.get("email", "")).strip().lower()

    if not email:
        return False

    return email in _get_admin_emails()


def _admin_forbidden_response(message: str = "You do not have permission to access the Admin Dashboard."):
    """Inline 403 response so the app never crashes if templates/403.html is missing."""
    email = str(session.get("email", "Unknown user"))
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Access Denied • NeuroSense AI</title>
      <style>
        :root {{
          --bg:#f4f7f2; --card:#ffffff; --green:#2d7a3a; --green2:#3fa050;
          --mint:#e8f5e3; --border:#c3e6b8; --text:#1a2e18; --muted:#4a6645; --danger:#d94040;
        }}
        *{{box-sizing:border-box;margin:0;padding:0}}
        body{{min-height:100vh;display:grid;place-items:center;padding:2rem;font-family:Inter,Arial,sans-serif;background:var(--bg);color:var(--text)}}
        .card{{width:min(620px,100%);background:var(--card);border:1.5px solid var(--border);border-radius:28px;padding:2rem;box-shadow:0 24px 70px rgba(45,122,58,.14);text-align:center}}
        .icon{{width:78px;height:78px;margin:0 auto 1rem;display:grid;place-items:center;border-radius:24px;background:#fdecec;color:var(--danger);font-size:2.1rem}}
        h1{{font-size:2rem;font-weight:900}}
        p{{margin-top:.8rem;color:var(--muted);line-height:1.7}}
        .actions{{margin-top:1.4rem;display:flex;justify-content:center;gap:.8rem;flex-wrap:wrap}}
        a{{min-height:44px;padding:0 1.1rem;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;font-weight:900;text-decoration:none}}
        .primary{{background:linear-gradient(135deg,var(--green),var(--green2));color:white}}
        .secondary{{background:var(--mint);color:var(--green);border:1.5px solid var(--border)}}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="icon">🔒</div>
        <h1>Access Denied</h1>
        <p>{message}</p>
        <p>Logged in as: <strong>{email}</strong></p>
        <div class="actions">
          <a class="primary" href="/dashboard">Go to Dashboard</a>
          <a class="secondary" href="/logout">Logout</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html, 403


def admin_required(f):
    """Protect admin-only pages and APIs."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "name" not in session or not session.get("user_key"):
            return redirect(url_for("home"))

        if not is_admin_user():
            wants_json = (
                request.path.startswith("/api/")
                or "application/json" in str(request.headers.get("Accept", "")).lower()
            )
            if wants_json:
                return jsonify({
                    "ok": False,
                    "success": False,
                    "error": "Admin access required.",
                }), 403
            return _admin_forbidden_response()

        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_admin_state():
    """Expose real-time admin state to every Jinja template."""
    try:
        return {"is_admin": is_admin_user()}
    except Exception:
        return {"is_admin": False}


def translate(text: str, target_lang: str) -> str:
    if not TRANSLATOR_AVAILABLE or target_lang == "en" or not text:
        return text
    try:
        if target_lang == "pt-BR":
            target_lang = "pt"
        result = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return result if result else text
    except Exception as e:
        print(f"⚠️  Translation error ({target_lang}): {e}")
        return text


def log_msg(mode: str, role: str, content: str):
    k     = ukey()
    today = datetime.date.today().isoformat()
    d     = store[k]
    d["streak_days"].add(today)
    d["message_count"] += 1

    # Supabase realtime usage tracking: count only user-originated messages.
    if role == "user" and session.get("supabase_user_id"):
        try:
            increment_usage(session["supabase_user_id"], field="daily_messages", amount=1)
            increment_usage(session["supabase_user_id"], field="monthly_messages", amount=1)
        except Exception as e:
            print(f"⚠️  Supabase usage tracking failed: {e}")

    for s in d["sessions"]:
        if s["date"] == today and s["mode"] == mode and not s.get("ended"):
            s["messages"].append({
                "role":    role,
                "content": content,
                "time":    datetime.datetime.now().strftime("%H:%M"),
            })
            _save_store()
            return

    d["sessions"].append({
        "date": today, "mode": mode, "emotions": [], "ended": False,
        "messages": [{
            "role":    role,
            "content": content,
            "time":    datetime.datetime.now().strftime("%H:%M"),
        }],
    })
    _save_store()


def log_emo(emotion: str, confidence: float = None):
    k     = ukey()
    today = datetime.date.today().isoformat()

    item = {
        "ts": datetime.datetime.now().isoformat(),
        "emotion": emotion,
    }

    if confidence is not None:
        try:
            conf = float(confidence)
            if conf <= 1:
                conf = conf * 100
            item["confidence"] = round(conf, 2)
        except Exception:
            pass

    store[k]["emotion_log"].append(item)

    for s in store[k]["sessions"]:
        if s["date"] == today and not s.get("ended"):
            s["emotions"].append(emotion)

    _save_store()


# ── JSON Parse Helper ──────────────────────────────────────────────────────────
def _parse_llm_json(raw: str) -> dict:
    if not raw:
        raise ValueError("Empty response from LLM")

    text = raw.strip().lstrip("\ufeff")

    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.split("```", 1)[0].strip()
    elif text.startswith("```"):
        text = text[3:]
        if text.startswith("\n"):
            text = text[1:]
        text = text.split("```", 1)[0].strip()

    if not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

    return json.loads(text)


# ── Core AI Reply ──────────────────────────────────────────────────────────────
def ai_reply(
    user_input: str,
    sentiment:  str  = "neutral",
    lang:       str  = "en",
    history:    list = None,
) -> str:
    eng_input = translate(user_input, "en") if lang != "en" else user_input
    lang_name = SUPPORTED_LANGUAGES.get(lang, {}).get("name", "English")

    sys_msg = (
        f"You are NeuroSense AI — a compassionate, evidence-based mental health "
        f"support assistant.\n"
        f"User's current emotional state: {sentiment}\n"
        f"Respond in: {lang_name}\n\n"
        "Guidelines:\n"
        "- Be warm, empathetic, and non-judgmental\n"
        "- Use CBT and DBT techniques where appropriate\n"
        "- Never diagnose or prescribe medication\n"
        "- Keep responses concise (3-5 sentences max)\n"
        "- If the user seems in crisis, provide crisis resources\n\n"
        "India Crisis Resources: "
        "iCall: 9152987821 | Vandrevala: 1860-2662-345 | NIMHANS: 14416"
    )

    messages = [{"role": "system", "content": sys_msg}]
    if history:
        for h in history[-10:]:
            role = h.get("role", "user")
            text = h.get("content", "")
            if role in ("user", "assistant") and text:
                if role == "user" and lang != "en":
                    text = translate(text, "en") or text
                messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": eng_input})

    try:
        response = chatbot_api.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Groq API error in ai_reply: {e}")
        reply = "I'm having trouble connecting right now. Please try again in a moment."

    if lang != "en":
        reply = translate(reply, lang)
    return reply




# ── Multi-Agent Reply Helper ─────────────────────────────────────────────────
def latest_wellbeing_checkin() -> dict:
    """Return latest saved wellbeing check-in for current user."""
    try:
        items = store[ukey()].get("wellbeing_checkins", [])
        return items[-1] if items else {}
    except Exception:
        return {}


def agent_reply(
    user_input: str,
    sentiment: str = "neutral",
    lang: str = "en",
    history: list = None,
) -> dict:
    """
    Strict multi-agent response wrapper.

    Uses:
    - SafetyAgent
    - EmotionAgent
    - SocialAgent
    - TherapyAgent
    - WellnessAgent
    - ClinicalEscalationAgent
    - HallucinationAgent

    Falls back to ai_reply() only if agents are unavailable or crash.
    """
    history = history or []
    wellbeing_data = latest_wellbeing_checkin()

    if not AGENTS_AVAILABLE or run_safe_therapy_pipeline is None:
        fallback = ai_reply(user_input, sentiment, lang, history=history)
        return {
            "reply": fallback,
            "safe": True,
            "risk_level": "unknown",
            "response_type": "fallback_ai_reply",
            "technique_used": "fallback",
            "agents": {},
            "wellness": {},
            "referral": {},
            "used_agents": False,
        }

    try:
        result = run_safe_therapy_pipeline(
            user_message=user_input,
            emotion=sentiment or "neutral",
            wellbeing_data=wellbeing_data,
            history=history,
            lang=lang,
            include_trace=True,
        )

        reply = result.get("reply") or ai_reply(user_input, sentiment, lang, history=history)

        if lang != "en" and reply:
            # Agents usually handle language, but this is a safety fallback.
            # translate() returns original if translator unavailable.
            reply = translate(reply, lang)

        result["reply"] = reply
        result["used_agents"] = True
        return result

    except Exception as e:
        print(f"❌ Agent pipeline failed, falling back to ai_reply: {e}")
        traceback.print_exc()
        fallback = ai_reply(user_input, sentiment, lang, history=history)
        return {
            "reply": fallback,
            "safe": True,
            "risk_level": "unknown",
            "response_type": "agent_fallback",
            "technique_used": "fallback",
            "agents": {},
            "wellness": {},
            "referral": {},
            "used_agents": False,
            "agent_error": str(e),
        }

# ── AI Report Generation ───────────────────────────────────────────────────────
def generate_ai_report(user_data: dict) -> dict:
    efreq     = user_data.get("emotion_freq", {})
    total_det = sum(efreq.values()) or 1
    top_emo   = max(efreq, key=efreq.get) if efreq else "neutral"
    valid_m   = [v for v in user_data.get("mood_timeline", []) if v is not None]
    avg_mood  = round(sum(valid_m) / len(valid_m), 1) if valid_m else 5.0

    if len(valid_m) >= 2:
        trend = (
            "improving" if valid_m[-1] > valid_m[0] else
            "declining" if valid_m[-1] < valid_m[0] else "stable"
        )
    else:
        trend = "stable"

    recent          = user_data.get("recent_sessions", [])
    session_summary = ""
    for s in recent[:3]:
        msgs      = s.get("messages", [])
        user_msgs = [m["content"] for m in msgs if m.get("role") == "user"][:2]
        if user_msgs:
            session_summary += (
                f"\n- Session ({s.get('mode','chat')}): "
                + " | ".join(user_msgs)
            )

    emo_breakdown = {
        k: f"{v / total_det * 100:.0f}%"
        for k, v in sorted(efreq.items(), key=lambda x: x[1], reverse=True)[:5]
    }

    prompt = f"""You are the NeuroSense AI Report Agent generating a structured, non-diagnostic mental wellness report.

PATIENT DATA:
- Name: {user_data.get('name', 'User')}
- Total sessions: {user_data.get('total_sessions', 0)}
- Total messages: {user_data.get('total_messages', 0)}
- Engagement streak (days): {user_data.get('streak', 0)}
- Average mood score: {avg_mood}/10
- Mood trend: {trend}
- Dominant emotion: {top_emo} ({efreq.get(top_emo, 0)} detections)
- Emotion breakdown: {json.dumps(emo_breakdown)}
- Recent session excerpts: {session_summary or 'No session data yet'}

CRITICAL INSTRUCTIONS:
- Return ONLY a raw JSON object
- Do NOT include any markdown formatting
- Do NOT include ```json or ``` fences
- Do NOT include any text before or after the JSON
- Start your response directly with {{ and end with }}

Required JSON structure:
{{
  "overall_assessment": "1-2 sentence clinical summary",
  "mood_analysis": "2-3 sentences about mood patterns",
  "emotional_patterns": "2-3 sentences about emotional profile",
  "strengths": ["strength1", "strength2", "strength3"],
  "areas_for_growth": ["area1", "area2", "area3"],
  "top5_practices": [
    {{"title": "Practice Name", "description": "Why and how", "frequency": "Daily/Weekly", "icon": "emoji"}},
    {{"title": "Practice Name", "description": "Why and how", "frequency": "Daily/Weekly", "icon": "emoji"}},
    {{"title": "Practice Name", "description": "Why and how", "frequency": "Daily/Weekly", "icon": "emoji"}},
    {{"title": "Practice Name", "description": "Why and how", "frequency": "Daily/Weekly", "icon": "emoji"}},
    {{"title": "Practice Name", "description": "Why and how", "frequency": "Daily/Weekly", "icon": "emoji"}}
  ],
  "immediate_actions": ["action1", "action2", "action3"],
  "professional_referral": "yes/no with brief reason",
  "quality_score": 7,
  "engagement_score": 7,
  "progress_score": 7,
  "risk_level": "low",
  "next_session_focus": "One-sentence recommendation"
}}"""

    try:
        response = chatbot_api.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        print(f"🔍 LLM raw response (first 200 chars): {raw[:200]}")

        report_data = _parse_llm_json(raw)

        now = datetime.datetime.now()
        report_data["generated_at"] = now.isoformat()
        report_data["report_id"]    = (
            f"NS-{now.strftime('%Y%m%d%H%M')}-"
            f"{user_data.get('name', 'U').upper()[:4]}"
        )
        report_data["avg_mood"]    = avg_mood
        report_data["mood_trend"]  = trend
        report_data["top_emotion"] = top_emo

        return {"success": True, "report": _safe_report_payload(report_data)}

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        fallback = _fallback_report(user_data, avg_mood, trend, top_emo)
        return {"success": True, "report": _safe_report_payload(fallback), "warning": "Used fallback report"}
    except Exception as e:
        print(f"❌ AI report generation error: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def _fallback_report(user_data: dict, avg_mood: float, trend: str, top_emo: str) -> dict:
    now = datetime.datetime.now()
    return {
        "generated_at":       now.isoformat(),
        "report_id":          f"NS-{now.strftime('%Y%m%d%H%M')}-{user_data.get('name','U').upper()[:4]}",
        "avg_mood":           avg_mood,
        "mood_trend":         trend,
        "top_emotion":        top_emo,
        "overall_assessment": (
            f"Based on {user_data.get('total_sessions', 0)} sessions and "
            f"{user_data.get('total_messages', 0)} messages, the user shows "
            f"a {trend} mood pattern with a dominant emotion of {top_emo}."
        ),
        "mood_analysis":      f"Average mood score is {avg_mood}/10 with a {trend} trend.",
        "emotional_patterns": f"The most frequently detected emotion is {top_emo}.",
        "strengths":          ["Consistent engagement", "Openness to support", "Self-awareness"],
        "areas_for_growth":   ["Emotional regulation", "Stress management", "Building support network"],
        "top5_practices": [
            {"title": "Mindful Breathing",    "description": "5-minute daily breathing exercises.",      "frequency": "Daily",   "icon": "🧘"},
            {"title": "Gratitude Journaling", "description": "Write 3 things you're grateful for.",      "frequency": "Daily",   "icon": "📓"},
            {"title": "Physical Activity",    "description": "30 minutes of light exercise.",            "frequency": "Daily",   "icon": "🚶"},
            {"title": "Social Connection",    "description": "Reach out to a trusted friend.",           "frequency": "Weekly",  "icon": "🤝"},
            {"title": "Sleep Hygiene",        "description": "Consistent schedule, 7-9 hours/night.",   "frequency": "Daily",   "icon": "😴"},
        ],
        "immediate_actions":     ["Continue regular sessions", "Practice one mindfulness technique daily", "Reach out to a support person"],
        "professional_referral": "Recommended for a routine mental health check-in.",
        "quality_score":         7,
        "engagement_score":      max(3, min(10, user_data.get("total_sessions", 1))),
        "progress_score":        7,
        "risk_level":            "low",
        "next_session_focus":    "Explore coping strategies and emotional regulation techniques.",
    }


# ── Build User Data Helper ─────────────────────────────────────────────────────
def _build_user_data() -> dict:
    k = ukey()
    d = store[k]

    efreq: dict = defaultdict(int)
    for e in d["emotion_log"]:
        efreq[e["emotion"]] += 1

    last7     = [
        (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        for i in range(6, -1, -1)
    ]
    last7_fmt = [
        datetime.datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b")
        for iso in last7
    ]
    dcounts = [
        sum(len(s["messages"]) for s in d["sessions"] if s["date"] == day)
        for day in last7
    ]
    mood_tl = []
    for day in last7:
        emos = [
            e
            for s in d["sessions"] if s["date"] == day
            for e in s["emotions"]
        ]
        mood_tl.append(
            round(sum(MOOD_SCORE.get(e, 5) for e in emos) / len(emos), 1)
            if emos else None
        )

    valid_m     = [v for v in mood_tl if v is not None]
    avg_mood    = round(sum(valid_m) / len(valid_m), 2) if valid_m else 5.0
    top_emotion = max(efreq, key=efreq.get) if efreq else "neutral"
    recent      = sorted(d["sessions"], key=lambda x: x["date"], reverse=True)[:5]
    today       = datetime.date.today()

    return {
        "name":          session.get("name",  "User"),
        "email":         session.get("email", "—"),
        "lang":          session.get("lang",  "EN").upper(),
        "report_date":   today.strftime("%d %B %Y"),
        "report_id":     (
            f"NS-{today.strftime('%Y%m%d')}-"
            f"{session.get('name','U').upper()[:6]}"
        ),
        "emotion_freq":  dict(efreq),
        "mood_timeline": mood_tl,
        "daily_labels":  last7_fmt,
        "daily_counts":  dcounts,
        "total_messages":    d["message_count"],
        "streak":            len(d["streak_days"]),
        "top_emotion":       top_emotion,
        "total_sessions":    len(d["sessions"]),
        "avg_mood":          avg_mood,
        "recent_sessions":   recent,
        "sign_data":         {},
        "daily_messages_today": sum(
            len(s["messages"])
            for s in d["sessions"]
            if s["date"] == today.isoformat()
        ),
        "daily_msg_limit":   100,
        "monthly_msg_limit": 2000,
        "role":              "user",
        "is_active":         True,
        "created_at":        today.strftime("%d %b %Y"),
        "last_active":       datetime.datetime.now().strftime("%d %b %Y %H:%M"),
        "saved_reports":     d.get("reports", []),
        "wellbeing_checkins": d.get("wellbeing_checkins", []),
        "latest_wellbeing_checkin": (d.get("wellbeing_checkins", [])[-1] if d.get("wellbeing_checkins") else None),
    }


# ── Language Helper ────────────────────────────────────────────────────────────
def _fmt_langs() -> dict:
    return {
        code: f"{info['native']} ({info['name']})"
        for code, info in SUPPORTED_LANGUAGES.items()
    }



# ── Insights Dashboard Helpers ────────────────────────────────────────────────
def _clean_text(value: str, limit: int = 180) -> str:
    """Small helper for dashboard snippets."""
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value[:limit] + ("..." if len(value) > limit else "")


def _time_greeting() -> dict:
    """Return energetic greeting based on local server time."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return {
            "title": "Good Morning",
            "emoji": "🌞",
            "line": "A fresh start is here — one calm step can shape your whole day.",
        }
    if 12 <= hour < 17:
        return {
            "title": "Good Afternoon",
            "emoji": "⚡",
            "line": "You are halfway through the day — pause, reset, and keep moving gently.",
        }
    if 17 <= hour < 22:
        return {
            "title": "Good Evening",
            "emoji": "🌙",
            "line": "You showed up today — let’s make this evening calm, focused, and meaningful.",
        }
    return {
        "title": "Hello",
        "emoji": "✨",
        "line": "Rest matters too — slow down and give yourself a softer moment.",
    }


def _mode_label(mode: str) -> str:
    m = str(mode or "chat").lower()
    if "voice" in m:
        return "Voice Chat"
    if "hand" in m or "sign" in m:
        return "Sign Language"
    if "knowledge" in m:
        return "Knowledge Chat"
    if "research" in m:
        return "Research Chat"
    if "practice" in m:
        return "Best Practices"
    return "Text Chat"


def _emotion_label(value: str) -> str:
    value = str(value or "neutral").strip().lower()
    return value[:1].upper() + value[1:] if value else "Neutral"


def _latest_user_messages(limit: int = 8) -> list:
    """Collect recent user-authored messages from local sessions."""
    items = []
    try:
        for s in store[ukey()].get("sessions", []) or []:
            for m in s.get("messages", []) or []:
                if (m.get("role") or "").lower() == "user":
                    items.append({
                        "date": s.get("date", ""),
                        "time": m.get("time", ""),
                        "mode": s.get("mode", "chat"),
                        "content": m.get("content", ""),
                    })
    except Exception:
        return []
    return items[-limit:]


def _build_today_thought(top_emotion: str = "neutral") -> dict:
    """Create a safe, non-diagnostic thought based on recent chat/session patterns."""
    messages = " ".join(m.get("content", "") for m in _latest_user_messages(limit=6)).lower()
    top = str(top_emotion or "neutral").lower()

    if any(w in messages for w in ["stress", "pressure", "overwhelmed", "workload", "deadline"]):
        text = "You’ve been carrying a lot lately. Small steps still count, and rest is productive too."
        tags = ["Stress reset", "Small steps", "Rest is okay"]
    elif any(w in messages for w in ["sleep", "tired", "exhausted", "fatigue"]):
        text = "Your energy deserves care. A calmer evening routine can support tomorrow’s focus."
        tags = ["Sleep support", "Recovery", "Gentle routine"]
    elif top in ["sad", "fear", "angry", "disgust"]:
        text = "Difficult emotions are signals, not failures. You can slow down and respond with kindness."
        tags = ["Self-compassion", "Emotional pause", "Support"]
    elif top in ["happy", "surprise"]:
        text = "You’re noticing brighter moments. Let’s protect that momentum with one simple healthy practice."
        tags = ["Progress", "Momentum", "Gratitude"]
    else:
        text = "You’re showing up for yourself, and that’s something to be proud of. Keep choosing one small helpful action."
        tags = ["Consistency", "Self-care", "Progress"]

    return {
        "text": text,
        "tags": tags,
        "source": "Based on recent chat patterns",
    }


def _build_history_logs(limit: int = 6) -> list:
    """Build a recent NeuroSense history timeline from sessions, reports, practices and safety actions."""
    d = store[ukey()]
    logs = []

    for s in d.get("sessions", []) or []:
        msgs = s.get("messages", []) or []
        if not msgs:
            continue
        last_msg = msgs[-1]
        mode_label = _mode_label(s.get("mode", "chat"))
        logs.append({
            "type": "session",
            "icon": "🎙️" if "voice" in str(s.get("mode", "")).lower() else "💬",
            "title": f"{mode_label} used",
            "detail": _clean_text(next((m.get("content", "") for m in reversed(msgs) if m.get("role") == "user"), "Session activity saved."), 58),
            "time": last_msg.get("time", "Recent"),
            "date": s.get("date", ""),
            "sort": f"{s.get('date','')} {last_msg.get('time','00:00')}",
        })

    for r in d.get("reports", []) or []:
        created = r.get("generated_at") or r.get("created_at") or r.get("date") or ""
        logs.append({
            "type": "report",
            "icon": "📄",
            "title": "Report generated",
            "detail": _clean_text(r.get("title") or r.get("report_type") or "Wellness insight report", 58),
            "time": _format_time_from_iso(created),
            "date": _format_date_from_iso(created),
            "sort": created,
        })

    for p in d.get("practice_logs", []) or []:
        logs.append({
            "type": "practice",
            "icon": "🌱",
            "title": "Best Practice completed",
            "detail": f"{p.get('practice','Practice')} • {max(1, int((p.get('duration_seconds') or 60) / 60))} min",
            "time": p.get("time", "Recent"),
            "date": p.get("date", ""),
            "sort": f"{p.get('date','')} {p.get('time','00:00')}",
        })

    for c in d.get("crisis_actions", []) or []:
        logs.append({
            "type": "safety",
            "icon": "🛡️",
            "title": "Crisis Support opened" if c.get("action") == "page_opened" else "Safety action used",
            "detail": str(c.get("action", "Safety action")).replace("_", " ").title(),
            "time": c.get("time", "Recent"),
            "date": c.get("date", ""),
            "sort": f"{c.get('date','')} {c.get('time','00:00')}",
        })

    if not logs:
        logs.append({
            "type": "welcome",
            "icon": "✨",
            "title": "Welcome to NeuroSense AI",
            "detail": "Start a chat, complete a practice, or open a report to build your history.",
            "time": "Now",
            "date": datetime.date.today().isoformat(),
            "sort": datetime.datetime.now().isoformat(),
        })

    return sorted(logs, key=lambda x: x.get("sort", ""), reverse=True)[:limit]


def _format_time_from_iso(value: str) -> str:
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%I:%M %p")
    except Exception:
        return "Recent"


def _format_date_from_iso(value: str) -> str:
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return datetime.date.today().isoformat()


def _most_used_mode() -> dict:
    d = store[ukey()]
    counts = Counter()
    total_messages = 0
    for s in d.get("sessions", []) or []:
        count = len(s.get("messages", []) or [])
        counts[_mode_label(s.get("mode", "chat"))] += count
        total_messages += count
    if not counts:
        return {"label": "Voice Chat", "percent": 0}
    label, count = counts.most_common(1)[0]
    return {"label": label, "percent": int(round((count / max(total_messages, 1)) * 100))}


def _today_energy(avg_mood: float, today_messages: int, practice_count: int) -> dict:
    score = int(round((float(avg_mood or 5) * 7) + min(today_messages, 20) + min(practice_count * 5, 20)))
    score = max(10, min(100, score))
    if score >= 75:
        label = "High"
    elif score >= 50:
        label = "Balanced"
    else:
        label = "Low"
    return {"label": label, "score": score, "display": round(score / 10, 1)}


def _practice_recommendations(top_emotion: str = "neutral") -> list:
    """Change daily and adapt to emotion/session patterns."""
    recent_text = " ".join(m.get("content", "") for m in _latest_user_messages(limit=8)).lower()
    top = str(top_emotion or "neutral").lower()

    pool = [
        {"title": "Box Breathing", "icon": "🫁", "minutes": 4, "tag": "Calm your mind", "href": "/best_practices#box-breathing", "match": ["stress", "anxiety", "pressure", "overwhelmed", "fear"]},
        {"title": "5-4-3-2-1 Grounding", "icon": "✋", "minutes": 5, "tag": "Reconnect with now", "href": "/best_practices#grounding", "match": ["anxiety", "panic", "fear", "overthinking"]},
        {"title": "Gratitude Note", "icon": "💚", "minutes": 3, "tag": "Shift focus gently", "href": "/best_practices#gratitude", "match": ["sad", "low", "tired", "neutral"]},
        {"title": "Thought Reframe", "icon": "🔁", "minutes": 5, "tag": "Find a balanced thought", "href": "/best_practices#thought-reframe", "match": ["worry", "can't", "failure", "angry", "sad"]},
        {"title": "Sleep Wind-down", "icon": "🌙", "minutes": 6, "tag": "Prepare for rest", "href": "/best_practices#sleep-winddown", "match": ["sleep", "tired", "exhausted", "night"]},
        {"title": "Task Breakdown", "icon": "✅", "minutes": 7, "tag": "Make work smaller", "href": "/best_practices#task-breakdown", "match": ["work", "deadline", "project", "overwhelmed", "pressure"]},
        {"title": "Support Message", "icon": "🤝", "minutes": 2, "tag": "Reach one person", "href": "/best_practices#social-support", "match": ["lonely", "alone", "isolated", "support"]},
        {"title": "Short Walk", "icon": "🚶", "minutes": 10, "tag": "Clear your head", "href": "/best_practices#short-walk", "match": ["neutral", "tired", "stress", "focus"]},
    ]

    scored = []
    day_seed = int(datetime.date.today().strftime("%j"))
    for i, item in enumerate(pool):
        score = ((i + day_seed) % 5)
        if top in item["match"]:
            score += 7
        if any(word in recent_text for word in item["match"]):
            score += 5
        scored.append((score, item))

    selected = [item for score, item in sorted(scored, key=lambda x: x[0], reverse=True)[:4]]
    return selected


def _daily_news_items() -> list:
    """Fetch mental-health/fitness RSS headlines daily, with safe local fallback."""
    cache = getattr(app, "_neurosense_news_cache", None)
    today = datetime.date.today().isoformat()
    if isinstance(cache, dict) and cache.get("date") == today:
        return cache.get("items", [])

    fallback = [
        {
            "category": "Mental Wellness",
            "title": "Morning sunlight may support mood and daily rhythm",
            "summary": "A few minutes outside can help reset your body clock and support energy.",
            "time": "Today",
            "url": "https://news.google.com/search?q=mental%20health%20wellness%20fitness",
            "image": "🌅",
        },
        {
            "category": "Sleep",
            "title": "Consistent sleep schedules support emotional balance",
            "summary": "Regular sleep and wake timing can make recovery feel easier.",
            "time": "Today",
            "url": "https://news.google.com/search?q=sleep%20mental%20health%20wellness",
            "image": "🛌",
        },
        {
            "category": "Movement",
            "title": "Short walks can help focus and reduce stress load",
            "summary": "Gentle movement can support clarity during busy or overwhelming days.",
            "time": "Today",
            "url": "https://news.google.com/search?q=fitness%20mental%20health%20walk",
            "image": "🚶",
        },
    ]

    items = []
    try:
        import urllib.request
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        url = "https://news.google.com/rss/search?q=mental%20health%20fitness%20wellness%20OR%20sleep%20OR%20stress&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            xml = resp.read()
        root = ET.fromstring(xml)
        for item in root.findall(".//item")[:3]:
            title = _clean_text(item.findtext("title") or "Mental health update", 78)
            link = item.findtext("link") or "https://news.google.com/"
            pub = item.findtext("pubDate") or ""
            try:
                dt = parsedate_to_datetime(pub)
                time_label = dt.strftime("%I:%M %p")
            except Exception:
                time_label = "Today"
            category = "Wellness"
            low = title.lower()
            if "sleep" in low:
                category = "Sleep"
            elif any(w in low for w in ["fitness", "walk", "exercise", "movement"]):
                category = "Movement"
            elif any(w in low for w in ["stress", "anxiety", "mental"]):
                category = "Mental Wellness"
            items.append({
                "category": category,
                "title": title,
                "summary": "Tap to read the latest wellness update from a news source.",
                "time": time_label,
                "url": link,
                "image": "📰",
            })
    except Exception as e:
        print(f"⚠️ Daily news fetch failed, using fallback: {e}")
        items = fallback

    if len(items) < 3:
        items = (items + fallback)[:3]

    app._neurosense_news_cache = {"date": today, "items": items}
    return items


def _build_insights_context() -> dict:
    """Build all dynamic values for the redesigned Insights dashboard."""
    user_data = _build_user_data()
    d = store[ukey()]
    today = datetime.date.today().isoformat()

    today_messages = sum(
        len(s.get("messages", []) or [])
        for s in d.get("sessions", []) or []
        if s.get("date") == today
    )

    today_practices = len([
        p for p in d.get("practice_logs", []) or []
        if p.get("date") == today and p.get("completed", True)
    ])

    mood_values = [v for v in user_data.get("mood_timeline", []) if v is not None]
    mood_percent = int(round((sum(mood_values) / max(len(mood_values), 1)) * 10)) if mood_values else int(round(user_data.get("avg_mood", 5) * 10))
    mood_percent = max(0, min(100, mood_percent))

    top_emotion = user_data.get("top_emotion", "neutral")
    greeting = _time_greeting()
    mode = _most_used_mode()
    energy = _today_energy(user_data.get("avg_mood", 5), today_messages, today_practices)

    return {
        "greeting": greeting,
        "daily_checkin": {
            "headline": "You’re showing up for yourself, and that’s something to be proud of.",
            "mood_trend": "Improving" if mood_percent >= 60 else "Needs care",
            "mood_percent": mood_percent,
            "streak": user_data.get("streak", 0),
            "activity_percent": min(100, int(round((today_messages / 10) * 100))) if today_messages else 0,
            "top_emotion": _emotion_label(top_emotion),
        },
        "today_thought": _build_today_thought(top_emotion),
        "history_logs": _build_history_logs(limit=5),
        "summary_cards": {
            "most_used_mode": mode,
            "today_energy": energy,
            "practice_streak": _practice_streak_days() if "_practice_streak_days" in globals() else 0,
            "mood_percent": mood_percent,
        },
        "recommended_practices": _practice_recommendations(top_emotion),
        "news_items": _daily_news_items(),
        "generated_date": datetime.datetime.now().strftime("%d %b %Y • %A"),
        "user_data": user_data,
    }



def _research_user_id() -> str:
    """Stable user id for local template/history storage."""
    return str(
        session.get("supabase_user_id")
        or session.get("email")
        or session.get("user_key")
        or "guest"
    ).lower()


def _research_history_path() -> str:
    os.makedirs("data", exist_ok=True)
    return os.path.join("data", "research_chat_history.json")


def _load_research_history() -> dict:
    path = _research_history_path()
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_research_history(data: dict) -> None:
    path = _research_history_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_research_history(limit: int = 20) -> list:
    data = _load_research_history()
    user_id = _research_user_id()
    items = data.get(user_id, [])
    return items[-limit:] if isinstance(items, list) else []


def _append_research_history(entry: dict, limit: int = 50) -> None:
    data = _load_research_history()
    user_id = _research_user_id()
    data.setdefault(user_id, [])
    data[user_id].append(entry)
    data[user_id] = data[user_id][-limit:]
    _save_research_history(data)


def _latest_checkin_for_research() -> dict:
    try:
        k = ukey()
        checkins = store[k].get("wellbeing_checkins", [])
        return checkins[-1] if checkins else {}
    except Exception:
        return {}


def _research_chat_context(limit: int = 8) -> list:
    """Convert saved research history into assistant/user chat context."""
    context = []
    for item in _get_research_history(limit=limit):
        q = item.get("query")
        a = item.get("answer")
        if q:
            context.append({"role": "user", "content": str(q)[:1200]})
        if a:
            context.append({"role": "assistant", "content": str(a)[:1600]})
    return context[-limit:]


def _safe_research_fallback(query: str = "") -> str:
    return (
        "I can help with general mental-health education and safe wellness guidance, "
        "but I cannot diagnose, prescribe medication, or replace a licensed professional. "
        "Please ask your question again, and I will keep the answer practical and safe. "
        "If you feel unsafe, contact a trusted person, emergency services, or a crisis helpline immediately."
    )


# ── Knowledge Chat Helpers ───────────────────────────────────────────────────
def _knowledge_user_id() -> str:
    """Stable user id for local knowledge chat history."""
    return str(
        session.get("supabase_user_id")
        or session.get("email")
        or session.get("user_key")
        or "guest"
    ).lower()


def _fallback_scope_check(question: str) -> dict:
    """Fallback scope guard if ScopeGuardAgent is unavailable.

    Updated behaviour:
    - Allows safe greetings/small talk.
    - Allows practical real-life wellbeing questions when the user mentions mental state,
      work stress, leave, rest, break, trip, burnout, or exhaustion.
    - Still blocks unrelated topics when there is no mental-health context.
    """
    q = " ".join((question or "").lower().split())

    greeting_terms = [
        "hi", "hii", "hiii", "hello", "hey", "heyy", "namaste",
        "good morning", "good afternoon", "good evening",
    ]

    thanks_terms = [
        "thanks", "thank you", "thankyou", "thx", "appreciate it",
    ]

    bye_terms = [
        "bye", "goodbye", "see you", "see ya", "take care", "talk later",
    ]

    help_terms = [
        "help", "what can you do", "how can you help",
        "who are you", "what is knowledge chat", "what can i ask",
    ]

    crisis_terms = [
        "suicide", "kill myself", "end my life", "hurt myself", "self harm",
        "self-harm", "unsafe", "want to die", "i want to die", "no reason to live",
        "don't want to live", "dont want to live",
    ]

    medication_terms = [
        "which medicine", "what medicine", "dose", "dosage", "prescribe",
        "start medication", "stop medication", "tablet", "antidepressant",
        "sleeping pill", "increase dose", "reduce dose",
    ]

    diagnosis_terms = [
        "diagnose me", "do i have depression", "do i have anxiety",
        "am i depressed", "am i bipolar", "what disorder do i have",
        "clinical diagnosis",
    ]

    allowed_terms = [
        # Direct mental-health words
        "mental", "mentally", "mental health", "not feeling well mentally",
        "not feeling good mentally", "not okay mentally", "feeling low", "feel low",
        "wellbeing", "well-being", "wellness", "emotion", "mood",
        "sad", "sadness", "depressed", "depression",

        # Stress / burnout / overload
        "stress", "stressed", "stressful", "pressure", "overloaded",
        "overwhelmed", "burnout", "burned out", "exhausted", "drained",
        "mentally tired", "mentally exhausted", "tired mentally",

        # Anxiety-like / sleep / social
        "anxiety", "anxious", "panic", "fear", "nervous", "overthinking",
        "sleep", "insomnia", "can't sleep", "tired", "fatigue",
        "lonely", "loneliness", "alone", "relationship", "social support",

        # Coping and real-life wellbeing decisions
        "therapy", "counsellor", "counselor", "psychologist", "psychiatrist",
        "grounding", "breathing", "anger", "self doubt", "confidence",
        "journal", "journaling", "coping", "cope", "rest", "take rest",
        "break", "take a break", "leave", "leave work", "take leave",
        "work break", "break from work", "trip", "go for a trip", "vacation",
        "travel", "should i go", "should i take leave", "should i rest",

        # Work/academic pressure
        "work stress", "office stress", "job stress", "workload", "work pressure",
        "academic", "exam", "study", "college",

        # NeuroSense app/report scope
        "neurosense", "report", "check-in", "checkin", "template", "agent",
        "assessment", "solution report", "wellness plan", "wellbeing score",
        "mood trend", "emotion detection",
    ]

    if q in greeting_terms:
        return {
            "allowed": True,
            "scope": "safe_smalltalk",
            "risk_level": "none",
            "response_type": "greeting",
            "reason": "Safe greeting allowed.",
        }

    if q in thanks_terms:
        return {
            "allowed": True,
            "scope": "safe_smalltalk",
            "risk_level": "none",
            "response_type": "thanks",
            "reason": "Safe thanks allowed.",
        }

    if q in bye_terms:
        return {
            "allowed": True,
            "scope": "safe_smalltalk",
            "risk_level": "none",
            "response_type": "bye",
            "reason": "Safe goodbye allowed.",
        }

    if q in help_terms:
        return {
            "allowed": True,
            "scope": "safe_smalltalk",
            "risk_level": "none",
            "response_type": "help",
            "reason": "Safe help request allowed.",
        }

    if any(term in q for term in crisis_terms):
        return {
            "allowed": True,
            "scope": "crisis_safety",
            "risk_level": "crisis",
            "response_type": "crisis",
            "reason": "Crisis/safety wording detected.",
            "requires_professional_help": True,
        }

    if any(term in q for term in medication_terms):
        return {
            "allowed": True,
            "scope": "professional_help",
            "risk_level": "medium",
            "response_type": "medication_boundary",
            "reason": "Medication-related wording detected.",
            "requires_professional_help": True,
            "medication_guardrail": True,
        }

    if any(term in q for term in diagnosis_terms):
        return {
            "allowed": True,
            "scope": "professional_help",
            "risk_level": "medium",
            "response_type": "diagnosis_boundary",
            "reason": "Diagnosis-related wording detected.",
            "requires_professional_help": True,
            "diagnosis_guardrail": True,
        }

    allowed = any(term in q for term in allowed_terms)

    return {
        "allowed": allowed,
        "scope": "mental_health" if allowed else "out_of_scope",
        "risk_level": "low" if allowed else "blocked",
        "response_type": "knowledge_answer" if allowed else "refusal",
        "reason": "Mental-health/NeuroSense wellbeing scope matched." if allowed else "Question is outside NeuroSense AI mental-health scope.",
        "requires_professional_help": False,
    }

def _knowledge_history(limit: int = 20) -> list:
    """Load knowledge chat history using utils store if available, else empty."""
    if get_knowledge_history:
        try:
            return get_knowledge_history(user_id=_knowledge_user_id(), limit=limit)
        except Exception as e:
            print(f"⚠️  Knowledge history load failed: {e}")
    return []


def _append_knowledge_history(entry: dict) -> bool:
    """Append knowledge chat history using utils store if available."""
    if append_knowledge_history:
        try:
            append_knowledge_history(user_id=_knowledge_user_id(), entry=entry, limit=60)
            return True
        except Exception as e:
            print(f"⚠️  Knowledge history save failed: {e}")
    return False


def _clear_knowledge_history() -> bool:
    """Clear knowledge chat history using utils store if available."""
    if clear_knowledge_history:
        try:
            clear_knowledge_history(user_id=_knowledge_user_id())
            return True
        except Exception as e:
            print(f"⚠️  Knowledge history clear failed: {e}")
    return False


def _knowledge_context_for_agent(limit: int = 8) -> list:
    """Convert knowledge history into chat context."""
    context = []
    for item in _knowledge_history(limit=limit):
        q = item.get("question") or item.get("query")
        a = item.get("answer")
        if q:
            context.append({"role": "user", "content": str(q)[:1200]})
        if a:
            context.append({"role": "assistant", "content": str(a)[:1600]})
    return context[-limit:]


def _knowledge_out_of_scope_reply() -> str:
    return (
        "I can only answer questions related to NeuroSense AI and mental-health/wellbeing areas such as stress, "
        "anxiety-like feelings, sleep, loneliness, emotions, mood tracking, coping skills, professional help, "
        "crisis safety, reports, and app usage. Please ask a question within those areas."
    )


def _knowledge_crisis_reply() -> str:
    return (
        "Your safety matters most right now. I cannot handle crisis support alone. Please contact a trusted person "
        "immediately, call local emergency services if you are in immediate danger, or contact a crisis helpline: "
        "Tele MANAS 14416 or 1800-891-4416, iCALL 9152987821, or Vandrevala Foundation +91 9999 666 555."
    )


def _knowledge_smalltalk_reply(question: str) -> str:
    """
    Allow safe small talk in Knowledge Chat.

    Knowledge Chat remains mental-health scoped, but greetings like:
    hi, hello, thanks, bye, what can you do
    should feel interactive.
    """

    q = " ".join(str(question or "").strip().lower().split())

    greeting_words = {
        "hi", "hii", "hiii", "hello", "hey", "heyy", "namaste",
        "good morning", "good afternoon", "good evening",
    }

    thanks_words = {
        "thanks", "thank you", "thankyou", "thx", "appreciate it",
    }

    bye_words = {
        "bye", "goodbye", "see you", "see ya", "take care", "talk later",
    }

    help_words = {
        "help", "what can you do", "how can you help",
        "who are you", "what is knowledge chat", "what can i ask",
    }

    if q in greeting_words:
        return (
            "Hi 👋 I’m NeuroSense Knowledge Chat. "
            "I can help you with mental-health education, NeuroSense AI reports, "
            "wellbeing check-ins, stress, anxiety-like feelings, sleep, loneliness, "
            "academic pressure, coping practices, professional-help guidance, and app usage.\n\n"
            "You can ask me something like: **“How can I manage stress better?”** or "
            "**“Explain my wellness plan in simple words.”**"
        )

    if q in thanks_words:
        return (
            "You’re welcome 😊 I’m here to help with NeuroSense AI and mental-wellbeing questions. "
            "You can ask me about reports, coping steps, mood tracking, stress, sleep, or professional support."
        )

    if q in bye_words:
        return (
            "Take care 👋 Small consistent steps matter. "
            "You can come back anytime to ask about your wellbeing report, coping practices, or mental-health support."
        )

    if q in help_words:
        return (
            "I’m NeuroSense Knowledge Chat 📚. I answer only from approved NeuroSense AI and mental-health knowledge.\n\n"
            "### You can ask about\n"
            "- Stress and emotional overload\n"
            "- Anxiety-like feelings and grounding\n"
            "- Sleep and recovery\n"
            "- Loneliness and social support\n"
            "- Academic pressure\n"
            "- Mood tracking and wellbeing check-ins\n"
            "- Assessment and solution reports\n"
            "- Professional help guidance\n"
            "- Crisis safety\n\n"
            "You can also upload your **Mental Wellness Assessment** and **Personalized Wellness Plan** reports, "
            "then ask questions about them."
        )

    return ""



# ── Supabase Session / Quota Helpers ──────────────────────────────────────────
def _set_login_session_from_profile(user_id: str, profile: dict, access_token: str = ""):
    """Keep Flask session in sync with Supabase profile."""
    full_name = (profile or {}).get("full_name") or (profile or {}).get("name") or "User"
    email     = (profile or {}).get("email") or ""
    phone     = (profile or {}).get("phone") or ""
    lang      = (profile or {}).get("preferred_language") or "en"
    role      = (profile or {}).get("role") or "user"

    session.update(
        supabase_user_id = user_id,
        supabase_token   = access_token or "",
        name             = full_name,
        email            = email,
        phone            = phone,
        lang             = lang,
        role             = role,
        user_key         = email.lower() if email else str(user_id).lower(),
        sentiment        = session.get("sentiment", "neutral"),
    )


def _current_user_id():
    return session.get("supabase_user_id")


def _quota_response_if_blocked(kind="messages"):
    """Return JSON response tuple when Supabase usage limit is reached, else None."""
    user_id = _current_user_id()
    if not user_id:
        return None
    try:
        allowed = check_usage_allowed(user_id)
        if allowed.get("ok") and not allowed.get("allowed", True):
            return jsonify({
                "ok": False,
                "error": "Daily or monthly usage limit reached.",
                "usage": allowed.get("usage"),
                "kind": kind,
            }), 429
    except Exception as e:
        print(f"⚠️  Usage limit check failed: {e}")
    return None


# ── Supabase Persistence Helpers ─────────────────────────────────────────────
def _supabase_can_write() -> bool:
    """Return True only when Supabase is configured and current user has an id."""
    return bool(SUPABASE_READY and supabase is not None and session.get("supabase_user_id"))


def _valid_uuid(value) -> bool:
    """Check whether value is a valid UUID string."""
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False


def _supabase_insert(table_name: str, payload: dict):
    """
    Safe Supabase insert wrapper.

    This app must continue working even if Supabase is down or the user is using
    the local fallback login, so every Supabase write is best-effort.
    """
    if not _supabase_can_write():
        return None

    try:
        res = supabase.table(table_name).insert(payload).execute()
        data = getattr(res, "data", None)

        if isinstance(data, list) and data:
            return data[0]

        return data

    except Exception as e:
        print(f"⚠️  Supabase insert failed for {table_name}: {e}")
        traceback.print_exc()
        return None


def _supabase_delete_by_report_id(report_id: str):
    """Best-effort delete for report metadata."""
    if not _supabase_can_write() or not report_id:
        return False

    try:
        supabase.table("neurosense_reports") \
            .delete() \
            .eq("user_id", session.get("supabase_user_id")) \
            .eq("report_id", report_id) \
            .execute()
        return True
    except Exception as e:
        print(f"⚠️  Supabase report metadata delete failed: {e}")
        return False


def _save_wellbeing_checkin_to_supabase(entry: dict):
    """
    Save a normalized wellbeing check-in to Supabase.

    Table required:
        public.wellbeing_checkins
    """
    if not _supabase_can_write() or not isinstance(entry, dict):
        return None

    user_id = session.get("supabase_user_id")

    payload = {
        "user_id": user_id,
        "mood": entry.get("mood", "neutral"),
        "stress": int(entry.get("stress") or 3),
        "social_connection": int(entry.get("social_connection") or 3),
        "sleep": entry.get("sleep", "okay"),
        "concerns": entry.get("concerns", []) or [],
        "emotional_safety": int(entry.get("emotional_safety") or 3),
        "support_available": entry.get("support_available", "maybe"),
        "current_thoughts": entry.get("current_thoughts", ""),
        "wellbeing_score": int(entry.get("wellbeing_score") or 50),
        "risk_level": entry.get("risk_level", "medium"),
        "score_explanation": entry.get("score_explanation", {}) or {},
        "risk_explanation": entry.get("risk_explanation", ""),
        "source": entry.get("source", "mode_checkin"),
        "created_at": entry.get("created_at") or datetime.datetime.utcnow().isoformat(),
    }

    row = _supabase_insert("wellbeing_checkins", payload)

    if row and isinstance(row, dict):
        entry["supabase_id"] = row.get("id")
        entry["db_id"] = row.get("id")

    return row


def _save_professional_help_to_supabase(result: dict, checkin: dict = None):
    """
    Save professional help / referral guidance to Supabase.

    Table required:
        public.professional_help_logs
    """
    if not _supabase_can_write() or not isinstance(result, dict):
        return None

    checkin = checkin or {}
    checkin_id = (
        checkin.get("supabase_id")
        or checkin.get("db_id")
        or checkin.get("wellbeing_checkin_id")
    )

    if not _valid_uuid(checkin_id):
        checkin_id = None

    payload = {
        "user_id": session.get("supabase_user_id"),
        "wellbeing_checkin_id": checkin_id,
        "urgency": result.get("urgency", "none"),
        "emergency": bool(result.get("emergency", False)),
        "needs_professional_help": bool(result.get("needs_professional_help", False)),
        "issue_tags": result.get("issue_tags", []) or [],
        "recommendations": result.get("recommendations", []) or [],
        "resources": result.get("resources", []) or [],
        "user_facing_message": result.get("user_facing_message", ""),
        "disclaimer": result.get("disclaimer", ""),
        "source": result.get("source", "professional_help_api"),
    }

    row = _supabase_insert("professional_help_logs", payload)

    if row and isinstance(row, dict):
        result["supabase_log_id"] = row.get("id")
        result["db_id"] = row.get("id")

    return row


def _latest_wellbeing_score_from_user_data(user_data: dict):
    latest = (user_data or {}).get("latest_wellbeing_checkin") or {}

    try:
        score = latest.get("wellbeing_score")
        return int(score) if score is not None else None
    except Exception:
        return None


def _save_report_metadata_to_supabase(
    user_data: dict,
    report_type: str,
    fmt: str,
    report_payload: dict = None,
    file_name: str = "",
    file_path: str = "",
    download_url: str = "",
):
    """
    Save assessment / solution / combined report metadata to Supabase.

    Table required:
        public.neurosense_reports
    """
    if not _supabase_can_write():
        return None

    user_data = user_data or {}
    report_payload = report_payload or {}
    latest = user_data.get("latest_wellbeing_checkin") or {}

    report_id = (
        report_payload.get("report_id")
        or user_data.get("report_id")
        or f"NS-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )

    risk_level = (
        report_payload.get("risk_level")
        or latest.get("risk_level")
        or "unknown"
    )

    if risk_level not in ["unknown", "low", "medium", "high", "crisis"]:
        risk_level = "unknown"

    title_map = {
        "assessment": "Mental Wellness Assessment Report",
        "solution": "Personalized Wellness Plan",
        "combined": "Combined NeuroSense AI Report",
        "therapy": "NeuroSense AI Report",
    }

    summary = (
        report_payload.get("summary")
        or report_payload.get("overall_assessment")
        or report_payload.get("mood_analysis")
        or f"{title_map.get(report_type, 'NeuroSense AI Report')} generated successfully."
    )

    payload = {
        "user_id": session.get("supabase_user_id"),
        "report_id": report_id,
        "report_type": report_type if report_type in ["assessment", "solution", "combined", "therapy"] else "solution",
        "format": fmt if fmt in ["pdf", "csv"] else "pdf",
        "title": title_map.get(report_type, "NeuroSense AI Report"),
        "summary": str(summary)[:2000],
        "risk_level": risk_level,
        "top_emotion": report_payload.get("top_emotion") or user_data.get("top_emotion", "neutral"),
        "mood_trend": report_payload.get("mood_trend") or user_data.get("mood_trend", "stable"),
        "wellbeing_score": _latest_wellbeing_score_from_user_data(user_data),
        "file_name": file_name,
        "file_path": file_path,
        "download_url": download_url,
        "report_payload": report_payload,
        "generated_at": report_payload.get("generated_at") or datetime.datetime.utcnow().isoformat(),
    }

    return _supabase_insert("neurosense_reports", payload)



def _supabase_select(table_name: str, filters: dict = None, order_by: str = None, desc: bool = True, limit: int = None):
    """
    Safe Supabase select wrapper. Best-effort only.
    """
    if not _supabase_can_write():
        return []

    try:
        q = supabase.table(table_name).select("*")

        for key, value in (filters or {}).items():
            q = q.eq(key, value)

        if order_by:
            q = q.order(order_by, desc=desc)

        if limit:
            q = q.limit(limit)

        res = q.execute()
        data = getattr(res, "data", None)
        return data if isinstance(data, list) else []

    except Exception as e:
        print(f"⚠️  Supabase select failed for {table_name}: {e}")
        return []


def _supabase_delete(table_name: str, filters: dict):
    """
    Safe Supabase delete wrapper. Best-effort only.
    """
    if not _supabase_can_write():
        return False

    try:
        q = supabase.table(table_name).delete()

        for key, value in (filters or {}).items():
            q = q.eq(key, value)

        q.execute()
        return True

    except Exception as e:
        print(f"⚠️  Supabase delete failed for {table_name}: {e}")
        return False


def _supabase_template_row_to_app(row: dict) -> dict:
    """Convert Supabase mental_health_templates row into frontend/template_store format."""
    row = row or {}
    return {
        "id": row.get("template_key") or row.get("id"),
        "supabase_id": row.get("id"),
        "user_id": row.get("user_id"),
        "title": row.get("title", "Untitled Template"),
        "category": row.get("category", "stress"),
        "description": row.get("description", ""),
        "prompt": row.get("prompt", ""),
        "output_type": row.get("output_type", "plan"),
        "risk_level": row.get("risk_level", "low"),
        "is_prebuilt": bool(row.get("is_prebuilt", False)),
        "is_active": bool(row.get("is_active", True)),
        "usage_count": row.get("usage_count", 0),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _load_custom_templates_from_supabase() -> list:
    """
    Load custom templates for the current Supabase user.

    Table required:
        public.mental_health_templates
    """
    if not _supabase_can_write():
        return []

    rows = _supabase_select(
        "mental_health_templates",
        filters={
            "user_id": session.get("supabase_user_id"),
            "is_active": True,
        },
        order_by="created_at",
        desc=True,
        limit=100,
    )

    return [_supabase_template_row_to_app(row) for row in rows]


def _save_template_to_supabase(template: dict):
    """
    Save a custom template to Supabase.

    Table required:
        public.mental_health_templates
    """
    if not _supabase_can_write() or not isinstance(template, dict):
        return None

    payload = {
        "user_id": session.get("supabase_user_id"),
        "template_key": template.get("id"),
        "title": template.get("title", "Untitled Template"),
        "category": template.get("category", "stress"),
        "description": template.get("description", ""),
        "prompt": template.get("prompt", ""),
        "output_type": template.get("output_type", "plan"),
        "risk_level": template.get("risk_level", "low"),
        "is_prebuilt": False,
        "is_active": True,
    }

    row = _supabase_insert("mental_health_templates", payload)

    if row and isinstance(row, dict):
        template["supabase_id"] = row.get("id")
        template["db_id"] = row.get("id")

    return row


def _delete_template_from_supabase(template_id: str) -> bool:
    """Soft-delete custom template row by template_key for current user."""
    if not _supabase_can_write() or not template_id:
        return False

    try:
        supabase.table("mental_health_templates") \
            .update({"is_active": False, "updated_at": datetime.datetime.utcnow().isoformat()}) \
            .eq("user_id", session.get("supabase_user_id")) \
            .eq("template_key", template_id) \
            .execute()
        return True
    except Exception as e:
        print(f"⚠️  Supabase template soft-delete failed: {e}")
        return False


def _increment_template_usage_supabase(template: dict):
    """Increment template usage count for a Supabase custom template if possible."""
    if not _supabase_can_write() or not isinstance(template, dict):
        return False

    supabase_id = template.get("supabase_id") or template.get("db_id")
    template_key = template.get("id")

    try:
        if _valid_uuid(supabase_id):
            try:
                supabase.rpc("increment_template_usage", {"template_uuid": supabase_id}).execute()
                return True
            except Exception:
                pass

        # Fallback: select current usage and update.
        rows = _supabase_select(
            "mental_health_templates",
            filters={"user_id": session.get("supabase_user_id"), "template_key": template_key},
            limit=1,
        )
        if rows:
            current = int(rows[0].get("usage_count") or 0)
            supabase.table("mental_health_templates") \
                .update({"usage_count": current + 1, "updated_at": datetime.datetime.utcnow().isoformat()}) \
                .eq("id", rows[0].get("id")) \
                .execute()
            return True

    except Exception as e:
        print(f"⚠️  Supabase template usage increment failed: {e}")

    return False


def _save_research_history_to_supabase(entry: dict, safety: dict = None, professional_help: dict = None, agent_trace: dict = None):
    """
    Save research chat history to Supabase.

    Table required:
        public.research_chat_history
    """
    if not _supabase_can_write() or not isinstance(entry, dict):
        return None

    template_uuid = entry.get("template_supabase_id")
    if not _valid_uuid(template_uuid):
        template_uuid = None

    payload = {
        "user_id": session.get("supabase_user_id"),
        "template_id": template_uuid,
        "template_key": entry.get("template_id"),
        "template_title": entry.get("template_title"),
        "query": entry.get("query", ""),
        "answer": entry.get("answer", ""),
        "model": entry.get("model", ""),
        "used_ollama": bool(entry.get("used_ollama", False)),
        "risk_level": entry.get("risk_level", "none") if entry.get("risk_level") in ["none", "low", "medium", "high", "crisis"] else "none",
        "safety": safety or entry.get("safety", {}) or {},
        "professional_help": professional_help or entry.get("professional_help", {}) or {},
        "agent_trace": agent_trace or entry.get("agent_trace", {}) or {},
        "created_at": entry.get("created_at") or datetime.datetime.utcnow().isoformat(),
    }

    row = _supabase_insert("research_chat_history", payload)

    if row and isinstance(row, dict):
        entry["supabase_id"] = row.get("id")
        entry["db_id"] = row.get("id")

    return row


def _load_research_history_from_supabase(limit: int = 50) -> list:
    """Load research chat history from Supabase for current user."""
    if not _supabase_can_write():
        return []

    rows = _supabase_select(
        "research_chat_history",
        filters={"user_id": session.get("supabase_user_id")},
        order_by="created_at",
        desc=True,
        limit=limit,
    )

    items = []
    for row in rows:
        items.append({
            "id": row.get("id"),
            "supabase_id": row.get("id"),
            "query": row.get("query", ""),
            "answer": row.get("answer", ""),
            "template_id": row.get("template_key"),
            "template_title": row.get("template_title"),
            "model": row.get("model"),
            "used_ollama": row.get("used_ollama"),
            "risk_level": row.get("risk_level", "none"),
            "created_at": row.get("created_at"),
        })

    return list(reversed(items))


def _clear_research_history_from_supabase() -> bool:
    """Delete research chat history rows for current user."""
    return _supabase_delete(
        "research_chat_history",
        filters={"user_id": session.get("supabase_user_id")},
    )


def _save_template_run_to_supabase(entry: dict, selected_template: dict = None, safety: dict = None):
    """
    Save template run log to Supabase.

    Table required:
        public.template_run_logs
    """
    if not _supabase_can_write() or not isinstance(entry, dict):
        return None

    selected_template = selected_template or {}
    template_uuid = selected_template.get("supabase_id") or selected_template.get("db_id")
    if not _valid_uuid(template_uuid):
        template_uuid = None

    payload = {
        "user_id": session.get("supabase_user_id"),
        "template_id": template_uuid,
        "template_key": entry.get("template_id") or selected_template.get("id"),
        "template_title": entry.get("template_title") or selected_template.get("title"),
        "query": entry.get("query", ""),
        "output": entry.get("answer", ""),
        "model": entry.get("model", ""),
        "used_ollama": bool(entry.get("used_ollama", False)),
        "risk_level": entry.get("risk_level", "none") if entry.get("risk_level") in ["none", "low", "medium", "high", "crisis"] else "none",
        "safety": safety or {},
        "created_at": entry.get("created_at") or datetime.datetime.utcnow().isoformat(),
    }

    return _supabase_insert("template_run_logs", payload)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── LANDING PAGE ──────────────────────────────────────────────────────────────
@app.route("/")
def landing():
    """
    Public landing page.

    Required template:
        templates/index.html
    """
    return render_template("index.html")


# ── AUTH / LOGIN PAGE ─────────────────────────────────────────────────────────
@app.route("/auth", methods=["GET", "POST"])
def home():
    """
    Login / registration page.

    Existing login.html stays separate from the landing page.
    Form POST fallback is kept for your current Flask session flow.
    """
    if request.method == "POST":
        raw_name  = request.form.get("name",  "").strip()
        raw_email = request.form.get("email", "").strip()

        session.update(
            name      = raw_name,
            email     = raw_email,
            user_key  = (raw_email.lower() if raw_email else raw_name.lower()),
            phone     = request.form.get("phone", "").strip(),
            lang      = request.form.get("lang", "en"),
            sentiment = "neutral",
        )
        return redirect(url_for("mode_select"))

    return render_template(
        "login.html",
        languages=_fmt_langs(),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        app_url=os.getenv("APP_URL", "http://localhost:5000"),
    )


@app.route("/auth/callback")
def auth_callback():
    return render_template(
        "auth_callback.html",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
    )


@app.route("/mode")
@login_required
def mode_select():
    return render_template(
        "mode_select.html",
        name=session["name"],
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )


@app.route("/normal_chat")
@login_required
def normal_chat():
    return render_template(
        "normal_chat.html",
        name=session["name"],
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )


@app.route("/voice_chat")
@login_required
def voice_chat():
    current_lang = session.get("lang", "en")
    if current_lang not in SUPPORTED_LANGUAGES:
        current_lang = "en"
        session["lang"] = "en"

    return render_template(
        "voice_chat.html",
        name=session["name"],
        lang=current_lang,
        languages=_fmt_langs(),
    )


@app.route("/hand_chat")
@login_required
def hand_chat():
    session.setdefault("hand_sentence", "")
    return render_template(
        "hand_chat.html",
        name=session["name"],
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )




def _default_safety_plan() -> dict:
    """Default editable safety plan shown on the crisis support page."""
    return {
        "warning_signs": [
            "Feeling overwhelmed",
            "Racing thoughts",
            "Wanting to isolate",
        ],
        "coping_steps": [
            "Move near another person",
            "Try slow breathing for 60 seconds",
            "Message or call a trusted person",
        ],
        "safe_places": [
            "A room near family or friends",
            "A public or well-lit place",
        ],
        "trusted_people": [],
        "things_to_avoid": [
            "Being alone if danger feels immediate",
            "Objects or places that increase risk",
        ],
        "professional_resources": [
            "Tele-MANAS 14416",
            "Emergency services 112",
        ],
        "updated_at": "",
    }


def _get_local_safety_plan() -> dict:
    try:
        plan = store[ukey()].get("safety_plan") or {}
    except Exception:
        plan = {}

    default = _default_safety_plan()
    merged = {**default, **(plan if isinstance(plan, dict) else {})}

    # Normalize list-like fields so the template can safely loop over them.
    for key in [
        "warning_signs",
        "coping_steps",
        "safe_places",
        "trusted_people",
        "things_to_avoid",
        "professional_resources",
    ]:
        value = merged.get(key, [])
        if isinstance(value, str):
            value = [line.strip() for line in value.split("\n") if line.strip()]
        elif not isinstance(value, list):
            value = []
        merged[key] = [str(item).strip() for item in value if str(item).strip()]

    return merged


def _append_crisis_action(action: str, details: dict = None) -> dict:
    """Append a non-diagnostic crisis support action log to local store."""
    details = details or {}
    entry = {
        "id": str(uuid.uuid4()),
        "action": str(action or "unknown"),
        "details": details,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "date": datetime.date.today().isoformat(),
    }

    try:
        d = store[ukey()]
        d.setdefault("crisis_actions", [])
        d["crisis_actions"].append(entry)
        d["crisis_actions"] = d["crisis_actions"][-100:]
        _save_store()
    except Exception as e:
        print(f"⚠️ Crisis action log save failed: {e}")

    return entry


def _load_crisis_actions(limit: int = 12) -> list:
    try:
        items = store[ukey()].get("crisis_actions", []) or []
        return list(reversed(items[-limit:]))
    except Exception:
        return []


def _support_profile_context() -> dict:
    """Load emergency contact fields for the crisis support page."""
    profile = {}
    user_id = _current_user_id()

    if user_id:
        try:
            data = _safe_profile_with_usage(user_id)
            profile = data.get("profile") or {}
        except Exception as e:
            print(f"⚠️ Support profile context fallback: {e}")

    emergency_name = (
        profile.get("emergency_contact_name")
        or profile.get("emergency_name")
        or session.get("emergency_contact_name")
        or "Trusted Person"
    )
    emergency_phone = (
        profile.get("emergency_contact_phone")
        or profile.get("emergency_phone")
        or session.get("emergency_contact_phone")
        or ""
    )

    return {
        "profile": profile,
        "emergency_contact_name": emergency_name,
        "emergency_contact_phone": emergency_phone,
        "has_emergency_contact": bool(str(emergency_phone).strip()),
    }


@app.route("/support")
@login_required
def support_page():
    """Dedicated crisis/support page with real-time safety tools."""
    ctx = _support_profile_context()
    _append_crisis_action("page_opened", {"source": "support_page"})

    return render_template(
        "support.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        safety_plan=_get_local_safety_plan(),
        crisis_actions=_load_crisis_actions(limit=8),
        **ctx,
    )


@app.route("/api/crisis/action_log", methods=["GET", "POST"])
@login_required
def crisis_action_log_api():
    """Save or read crisis-support UI actions such as check-in, slider, call click, timer start."""
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "actions": _load_crisis_actions(limit=25),
        })

    data = request.get_json(silent=True) or {}
    action = data.get("action") or "unknown"
    details = data.get("details") or {}

    allowed_actions = {
        "page_opened",
        "safety_check",
        "intensity_change",
        "helpline_click",
        "emergency_contact_call",
        "emergency_contact_sms",
        "breathing_timer_start",
        "breathing_timer_complete",
        "grounding_step",
        "safety_plan_saved",
        "copy_message",
        "still_unsafe",
    }

    if action not in allowed_actions:
        action = "unknown"

    entry = _append_crisis_action(action, details)

    return jsonify({
        "ok": True,
        "entry": entry,
        "actions": _load_crisis_actions(limit=12),
    })


@app.route("/api/crisis/safety_plan", methods=["GET", "POST"])
@login_required
def crisis_safety_plan_api():
    """Read or update the user's local safety plan."""
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "safety_plan": _get_local_safety_plan(),
        })

    data = request.get_json(silent=True) or {}
    plan = _get_local_safety_plan()

    for key in [
        "warning_signs",
        "coping_steps",
        "safe_places",
        "trusted_people",
        "things_to_avoid",
        "professional_resources",
    ]:
        value = data.get(key, plan.get(key, []))
        if isinstance(value, str):
            value = [line.strip() for line in value.split("\n") if line.strip()]
        elif not isinstance(value, list):
            value = []
        plan[key] = [str(item).strip() for item in value if str(item).strip()]

    plan["updated_at"] = datetime.datetime.utcnow().isoformat()

    try:
        store[ukey()]["safety_plan"] = plan
        _append_crisis_action("safety_plan_saved", {"items": sum(len(plan.get(k, [])) for k in plan if isinstance(plan.get(k), list))})
        _save_store()
    except Exception as e:
        print(f"⚠️ Safety plan save failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok": True,
        "safety_plan": plan,
        "actions": _load_crisis_actions(limit=12),
    })


@app.route("/dashboard")
@login_required
def dashboard():
    insights = _build_insights_context()
    user_data = insights.get("user_data", {})

    return render_template(
        "dashboard.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        insights=insights,
        is_admin=is_admin_user(),

        # Backward-compatible values for any existing JS/template references
        emotion_freq=user_data.get("emotion_freq", {}),
        daily_labels=user_data.get("daily_labels", []),
        daily_counts=user_data.get("daily_counts", []),
        mood_timeline=user_data.get("mood_timeline", []),
        avg_mood=user_data.get("avg_mood", 5.0),
        total_messages=user_data.get("total_messages", 0),
        streak=user_data.get("streak", 0),
        recent_sessions=user_data.get("recent_sessions", []),
        top_emotion=user_data.get("top_emotion", "neutral"),
        total_sessions=user_data.get("total_sessions", 0),
        emotion_backend=EMOTION_BACKEND or "unavailable",
        saved_reports=user_data.get("saved_reports", []),
    )


@app.route("/api/insights_data")
@login_required
def insights_data_api():
    """Real-time Insights dashboard data for refresh/polling."""
    return jsonify({
        "ok": True,
        "insights": _build_insights_context(),
    })




# ── Reliability / Trust APIs ─────────────────────────────────────────────────

def _safe_report_payload(report: dict) -> dict:
    """Best-effort safety sanitizer for generated report payloads.

    Keeps reports non-diagnostic and non-prescriptive. This does not replace
    the HallucinationAgent, but it protects the final payload if the LLM ever
    overclaims.
    """
    if not isinstance(report, dict):
        return report

    blocked_phrases = [
        "you have depression",
        "you have anxiety disorder",
        "you are bipolar",
        "diagnosed with",
        "clinical diagnosis",
        "you should take medication",
        "start medication",
        "stop medication",
        "increase your dose",
        "reduce your dose",
        "prescribe",
    ]

    disclaimer = (
        "This report is a supportive wellness summary only. It is not a diagnosis, "
        "medication advice, or a replacement for professional care."
    )

    def clean_value(value):
        if isinstance(value, str):
            lowered = value.lower()
            if any(phrase in lowered for phrase in blocked_phrases):
                return (
                    "This section was adjusted for safety. NeuroSense AI can summarize "
                    "wellness patterns, but it cannot diagnose, prescribe medication, "
                    "or make clinical certainty claims. Please consult a qualified professional "
                    "for medical or mental-health concerns."
                )
            return value
        if isinstance(value, list):
            return [clean_value(v) for v in value]
        if isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        return value

    cleaned = clean_value(report)
    cleaned["safety_disclaimer"] = disclaimer
    cleaned["confidence"] = cleaned.get("confidence") or "medium"
    cleaned["confidence_reason"] = cleaned.get("confidence_reason") or (
        "Generated from available session, emotion, wellbeing, and practice data. "
        "Confidence improves as the user records more check-ins and sessions."
    )
    return cleaned


def _log_feedback(payload: dict) -> dict:
    now = datetime.datetime.now()
    entry = {
        "id": str(uuid.uuid4()),
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "created_at": now.isoformat(),
        "target": str(payload.get("target") or "insight")[:80],
        "label": str(payload.get("label") or payload.get("feedback") or "helpful")[:40],
        "value": payload.get("value", True),
        "context": str(payload.get("context") or "")[:1000],
        "page": str(payload.get("page") or request.path)[:120],
    }
    d = store[ukey()]
    d.setdefault("feedback_logs", [])
    d["feedback_logs"].append(entry)
    d["feedback_logs"] = d["feedback_logs"][-500:]
    _save_store()
    return entry


@app.route("/api/feedback", methods=["GET", "POST"])
@login_required
def feedback_api():
    """Save/read Helpful / Not helpful feedback for insights and practices."""
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "feedback": list(reversed(store[ukey()].get("feedback_logs", [])[-50:])),
        })

    data = request.get_json(silent=True) or {}
    entry = _log_feedback(data)
    return jsonify({"ok": True, "success": True, "entry": entry, "feedback": entry})


@app.route("/api/user/export-data")
@login_required
def export_user_data_api():
    """Download current user's local NeuroSense data as JSON."""
    k = ukey()
    data = store[k].copy()
    if isinstance(data.get("streak_days"), set):
        data["streak_days"] = sorted(list(data["streak_days"]))

    export_payload = {
        "exported_at": datetime.datetime.now().isoformat(),
        "user_key": k,
        "profile": {
            "name": session.get("name", "User"),
            "email": session.get("email", ""),
            "lang": session.get("lang", "en"),
        },
        "data": data,
        "safety_note": (
            "This export contains local wellness app data. Keep it private and avoid sharing it publicly."
        ),
    }

    payload = json.dumps(export_payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"neurosense_export_{datetime.date.today().isoformat()}.json"
    return send_file(
        io.BytesIO(payload),
        mimetype="application/json",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/api/user/clear-data", methods=["POST"])
@login_required
def clear_user_data_api():
    """Clear selected local user data while keeping account/profile intact."""
    data = request.get_json(silent=True) or {}
    clear_type = str(data.get("type") or "").strip().lower()
    d = store[ukey()]

    allowed = {
        "sessions": ["sessions", "emotion_log", "message_count"],
        "practice_logs": ["practice_logs"],
        "crisis_actions": ["crisis_actions"],
        "feedback_logs": ["feedback_logs"],
        "reports": ["reports"],
        "wellbeing_checkins": ["wellbeing_checkins"],
        "all_history": [
            "sessions", "emotion_log", "message_count", "reports",
            "wellbeing_checkins", "crisis_actions", "practice_logs", "feedback_logs"
        ],
    }

    if clear_type not in allowed:
        return jsonify({
            "ok": False,
            "error": "Invalid clear type.",
            "allowed": sorted(allowed.keys()),
        }), 400

    for key in allowed[clear_type]:
        if key == "message_count":
            d[key] = 0
        elif key == "emotion_log":
            d[key] = []
        elif key == "streak_days":
            d[key] = set()
        else:
            d[key] = []

    if clear_type in ("sessions", "all_history"):
        d["streak_days"] = set()

    _save_store()
    return jsonify({"ok": True, "cleared": clear_type})


@app.route("/api/reliability/status")
@login_required
def reliability_status_api():
    """Frontend-friendly reliability status for trust badges."""
    d = store[ukey()]
    return jsonify({
        "ok": True,
        "last_updated": datetime.datetime.now().isoformat(),
        "safety_boundary": "Supportive wellness guidance only; no diagnosis or medication advice.",
        "data_points": {
            "sessions": len(d.get("sessions", []) or []),
            "emotion_logs": len(d.get("emotion_log", []) or []),
            "practice_logs": len(d.get("practice_logs", []) or []),
            "wellbeing_checkins": len(d.get("wellbeing_checkins", []) or []),
        },
        "confidence_note": "Insight confidence improves as more sessions/check-ins are recorded.",
    })



# ── Daily Mental Health / Fitness / Wellness News API ─────────────────────────
_NEWS_CACHE = {"date": None, "items": []}


def _clean_news_text(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fallback_wellness_news():
    return [
        {
            "title": "Morning sunlight may support mood",
            "description": "A few minutes outside can help reset your body clock and support daily rhythm.",
            "category": "Mental Wellness",
            "source": "WHO",
            "published": "Today",
            "url": "https://www.who.int/news-room/fact-sheets/detail/mental-health-strengthening-our-response",
            "icon": "☀️",
        },
        {
            "title": "Consistent sleep supports emotional balance",
            "description": "Regular sleep and wake timing can help stabilize energy and focus.",
            "category": "Sleep",
            "source": "CDC",
            "published": "Today",
            "url": "https://www.cdc.gov/sleep/about/index.html",
            "icon": "😴",
        },
        {
            "title": "Short walks can improve focus",
            "description": "Gentle movement can help reduce stress and reset attention during the day.",
            "category": "Movement",
            "source": "WHO",
            "published": "Today",
            "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            "icon": "🚶",
        },
    ]


def fetch_daily_wellness_news():
    today = datetime.date.today().isoformat()
    if _NEWS_CACHE.get("date") == today and _NEWS_CACHE.get("items"):
        return _NEWS_CACHE["items"]

    rss_urls = [
        "https://news.google.com/rss/search?q=mental%20health%20wellbeing%20sleep%20fitness&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=stress%20management%20mental%20health%20fitness&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=sleep%20health%20wellness%20exercise&hl=en-IN&gl=IN&ceid=IN:en",
    ]
    keywords = ["mental", "health", "wellness", "wellbeing", "sleep", "stress", "anxiety", "fitness", "exercise", "walking", "mindfulness", "meditation", "mood", "brain", "lifestyle"]
    icon_rules = {
        "sleep": ("😴", "Sleep"),
        "fitness": ("🏃", "Movement"),
        "exercise": ("🚶", "Movement"),
        "walking": ("🚶", "Movement"),
        "stress": ("🧘", "Stress Recovery"),
        "anxiety": ("🌿", "Stress Recovery"),
        "mindfulness": ("🌿", "Mindfulness"),
        "meditation": ("🧘", "Mindfulness"),
        "mental": ("🧠", "Mental Wellness"),
        "mood": ("☀️", "Mental Wellness"),
        "wellness": ("☀️", "Wellness"),
        "wellbeing": ("☀️", "Wellbeing"),
    }
    items = []
    seen = set()

    for rss_url in rss_urls:
        try:
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            for node in root.findall(".//item"):
                title = _clean_news_text(node.findtext("title"))
                link = _clean_news_text(node.findtext("link"))
                pub_date = _clean_news_text(node.findtext("pubDate"))
                description = _clean_news_text(node.findtext("description"))
                if not title or not link:
                    continue
                low = title.lower()
                if low in seen or not any(k in low for k in keywords):
                    continue
                seen.add(low)
                source = "Google News"
                if " - " in title:
                    title, source = [x.strip() for x in title.rsplit(" - ", 1)]
                icon, category = "🧠", "Mental Wellness"
                for keyword, values in icon_rules.items():
                    if keyword in low:
                        icon, category = values
                        break
                items.append({
                    "title": title[:140],
                    "description": (description or "Read the latest wellness update from a public news source.")[:220],
                    "category": category,
                    "source": source,
                    "published": pub_date or "Today",
                    "url": link,
                    "icon": icon,
                })
                if len(items) >= 6:
                    break
        except Exception as e:
            print(f"⚠️ Wellness news fetch failed: {e}")
        if len(items) >= 6:
            break

    if not items:
        items = _fallback_wellness_news()
    _NEWS_CACHE["date"] = today
    _NEWS_CACHE["items"] = items
    return items


@app.route("/api/wellness-news")
@login_required
def api_wellness_news():
    try:
        return jsonify({
            "ok": True,
            "success": True,
            "date": datetime.date.today().isoformat(),
            "items": fetch_daily_wellness_news(),
        })
    except Exception as e:
        print(f"❌ Wellness news API failed: {e}")
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "items": _fallback_wellness_news(),
            "error": str(e),
        }), 200

@app.route("/reports")
@login_required
def reports_page():
    """
    Reports page with separate Assessment and Solution report downloads.

    Required template:
        templates/reports.html

    Required JS:
        static/js/report.js
    """
    return render_template(
        "reports.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )

@app.route("/research_chat")
@login_required
def research_chat_page():
    """Research Chat page powered by Ollama + agents."""
    return render_template(
        "research_chat.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )




@app.route("/knowledge_chat")
@login_required
def knowledge_chat_page():
    """Knowledge Chat page: grounded NeuroSense AI mental-health Q&A."""
    return render_template(
        "knowledge_chat.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )

@app.route("/templates")
@login_required
def templates_page():
    """Mental health template library page."""
    return render_template(
        "templates.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )


@app.route("/templates/create")
@login_required
def create_template_page():
    """Create custom mental-health support template page."""
    return render_template(
        "create_template.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        categories=TEMPLATE_CATEGORIES,
        output_types=OUTPUT_TYPES,
    )


@app.route("/reports/assessment")
@login_required
def assessment_report_page():
    """
    Assessment report preview page.

    Required template:
        templates/assessment_report.html

    Fix:
    - _build_user_data() already contains keys like name, email, and lang.
    - Passing name=... and **user_data together causes:
      TypeError: render_template() got multiple values for keyword argument 'name'.
    - Build one context dictionary and pass it once.
    """
    try:
        user_data = _build_user_data()
    except Exception as e:
        traceback.print_exc()
        return redirect(url_for("reports_page"))

    context = {
        **user_data,
        "name": session.get("name", user_data.get("name", "User")),
        "lang": session.get("lang", user_data.get("lang", "en")),
        "languages": _fmt_langs(),
    }

    return render_template(
        "assessment_report.html",
        **context,
    )


@app.route("/reports/solution")
@login_required
def solution_report_page():
    """
    Solution / Wellness Plan preview page.

    Required template:
        templates/solution_report.html

    Fix:
    - Avoid duplicate name/lang values in render_template().
    - Keep safe suggestions and professional-help guidance intact.
    """
    try:
        user_data = _build_user_data()
    except Exception as e:
        traceback.print_exc()
        return redirect(url_for("reports_page"))

    latest_checkin = user_data.get("latest_wellbeing_checkin") or {}

    suggestions = []
    professional_help = {}

    try:
        if generate_safe_suggestions:
            suggestions = generate_safe_suggestions(latest_checkin, limit=5)
    except Exception as e:
        print(f"⚠️  Could not generate safe suggestions: {e}")

    try:
        if recommend_professional_help:
            professional_help = recommend_professional_help(
                checkin=latest_checkin,
                message=latest_checkin.get("current_thoughts", "") if isinstance(latest_checkin, dict) else "",
                emotion=user_data.get("top_emotion", "neutral"),
                safety={},
            )
    except Exception as e:
        print(f"⚠️  Could not generate professional help guidance: {e}")

    context = {
        **user_data,
        "name": session.get("name", user_data.get("name", "User")),
        "lang": session.get("lang", user_data.get("lang", "en")),
        "languages": _fmt_langs(),
        "suggestions": suggestions,
        "professional_help": professional_help,
    }

    return render_template(
        "solution_report.html",
        **context,
    )



@app.route("/set_lang", methods=["POST"])
def set_lang():
    session["lang"] = request.json.get("lang", "en")
    return jsonify({"ok": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ══════════════════════════════════════════════════════════════════════════════
#  API — SUPABASE AUTH + ENHANCED USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/auth/sync", methods=["POST"])
def sync_supabase_session():
    """
    Sync Supabase Auth user with Flask session.

    Frontend should send:
    {
      "access_token": "...",
      "user": {... optional ...}
    }

    This version handles Supabase DNS/network failures clearly instead of
    returning a confusing 401 when the internet/DNS is temporarily down.
    """
    try:
        payload = request.get_json(silent=True) or {}

        access_token = (
            payload.get("access_token")
            or payload.get("token")
            or payload.get("session", {}).get("access_token")
            or ""
        )

        frontend_user = payload.get("user") or {}

        if not access_token:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Missing Supabase access token. Please login again.",
                "code": "MISSING_ACCESS_TOKEN",
            }), 401

        if not SUPABASE_READY or supabase is None:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Supabase client is not configured on backend. Check SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY in .env.",
                "code": "SUPABASE_NOT_CONFIGURED",
            }), 503

        try:
            user_res = supabase.auth.get_user(access_token)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            print(f"❌ Supabase network/DNS error during auth sync: {e}")
            traceback.print_exc()

            return jsonify({
                "ok": False,
                "success": False,
                "error": "Cannot connect to Supabase right now. Check internet/DNS and Supabase URL, then try again.",
                "code": "SUPABASE_NETWORK_ERROR",
            }), 503

        except Exception as e:
            print(f"❌ Supabase get_user failed: {e}")
            traceback.print_exc()

            return jsonify({
                "ok": False,
                "success": False,
                "error": "Could not verify Supabase session. Please login again.",
                "code": "SUPABASE_AUTH_VERIFY_FAILED",
            }), 401

        user_obj = getattr(user_res, "user", None)

        if not user_obj:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Invalid Supabase session. Please login again.",
                "code": "INVALID_SUPABASE_SESSION",
            }), 401

        user_id = getattr(user_obj, "id", None) or frontend_user.get("id")
        email = getattr(user_obj, "email", None) or frontend_user.get("email", "")
        phone = getattr(user_obj, "phone", None) or frontend_user.get("phone", "")

        metadata = getattr(user_obj, "user_metadata", None) or {}
        frontend_metadata = frontend_user.get("user_metadata", {}) if isinstance(frontend_user, dict) else {}

        full_name = (
            metadata.get("full_name")
            or metadata.get("name")
            or metadata.get("display_name")
            or frontend_metadata.get("full_name")
            or frontend_metadata.get("name")
            or (email.split("@")[0] if email else "")
            or phone
            or "User"
        )

        preferred_language = (
            metadata.get("preferred_language")
            or frontend_metadata.get("preferred_language")
            or session.get("lang", "en")
            or "en"
        )

        profile = {}

        try:
            # New helper versions may accept full_name.
            profile = get_or_create_profile(
                user_id=user_id,
                email=email,
                phone=phone,
                full_name=full_name,
                preferred_language=preferred_language,
            )

        except TypeError:
            try:
                # Older helper versions may accept name instead of full_name.
                profile = get_or_create_profile(
                    user_id=user_id,
                    email=email,
                    phone=phone,
                    name=full_name,
                    preferred_language=preferred_language,
                )
            except TypeError:
                # Very old helper versions may accept fewer fields.
                profile = get_or_create_profile(
                    user_id=user_id,
                    email=email,
                    phone=phone,
                    name=full_name,
                )

        except Exception as e:
            print(f"⚠️ Profile sync failed, using local session fallback: {e}")
            traceback.print_exc()
            profile = {
                "id": user_id,
                "email": email,
                "phone": phone,
                "full_name": full_name,
                "name": full_name,
                "preferred_language": preferred_language,
                "role": "user",
            }

        # Best-effort last_login update. This must not break login.
        try:
            updated_profile = update_user_profile(
                user_id,
                {"last_login": datetime.datetime.utcnow().isoformat()}
            )
            if updated_profile:
                profile = updated_profile
        except Exception as e:
            print(f"⚠️ last_login update failed: {e}")

        # Guarantee required keys for session sync.
        if not isinstance(profile, dict):
            profile = {}

        profile.setdefault("id", user_id)
        profile.setdefault("email", email)
        profile.setdefault("phone", phone)
        profile.setdefault("full_name", full_name)
        profile.setdefault("name", full_name)
        profile.setdefault("preferred_language", preferred_language)
        profile.setdefault("role", "user")

        _set_login_session_from_profile(
            user_id=user_id,
            profile=profile,
            access_token=access_token,
        )

        return jsonify({
            "ok": True,
            "success": True,
            "message": "Session synced successfully.",
            "redirect": "/dashboard",
            "profile": profile,
        })

    except Exception as e:
        print(f"❌ /api/auth/sync failed: {e}")
        traceback.print_exc()

        return jsonify({
            "ok": False,
            "success": False,
            "error": str(e),
            "code": "AUTH_SYNC_FAILED",
        }), 500

@app.route("/api/auth/logout", methods=["POST"])
def supabase_logout_api():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def auth_me_api():
    if not session.get("supabase_user_id"):
        return jsonify({"ok": False, "authenticated": False})

    return jsonify({
        "ok": True,
        "authenticated": True,
        "user": {
            "id": session.get("supabase_user_id"),
            "name": session.get("name"),
            "email": session.get("email"),
            "phone": session.get("phone"),
            "role": session.get("role", "user"),
            "lang": session.get("lang", "en"),
        }
    })




def _safe_profile_with_usage(user_id):
    """
    Safe wrapper around Supabase profile + usage.

    This prevents dashboard/profile buttons from breaking if the Supabase
    usage_limits table is missing optional columns such as created_at.
    The correct DB fix is still to add created_at/updated_at to usage_limits,
    but the UI should not crash while testing.
    """
    default_profile = {
        "id": user_id,
        "full_name": session.get("name", "User"),
        "email": session.get("email", ""),
        "phone": session.get("phone", ""),
        "preferred_language": session.get("lang", "en"),
        "role": session.get("role", "user"),
    }

    default_usage = {
        "daily_messages": 0,
        "monthly_messages": 0,
        "reports_generated": 0,
        "image_uploads": 0,
        "voice_minutes": 0,
        "sign_sessions": 0,
        "research_queries": 0,
        "knowledge_queries": 0,
        "usage_date": datetime.date.today().isoformat(),
        "month_key": datetime.datetime.now().strftime("%Y-%m"),
    }

    default_limits = {
        "daily_messages": 100,
        "monthly_messages": 3000,
        "reports_generated": 50,
        "image_uploads": 100,
        "voice_minutes": 300,
        "sign_sessions": 100,
        "research_queries": 100,
        "knowledge_queries": 100,
    }

    if not SUPABASE_READY or not user_id:
        return {
            "profile": default_profile,
            "usage": default_usage,
            "limits": default_limits,
            "usage_warning": "Supabase not ready; using local fallback usage values.",
        }

    try:
        return get_profile_with_usage(user_id)
    except Exception as e:
        print(f"⚠️  Safe profile usage fallback activated: {e}")
        traceback.print_exc()
        return {
            "profile": default_profile,
            "usage": default_usage,
            "limits": default_limits,
            "usage_warning": str(e),
        }




def _clamp_percent(value) -> int:
    try:
        return int(max(0, min(100, round(float(value)))))
    except Exception:
        return 0


def _analytics_context(user_data: dict) -> dict:
    """Build the derived analytics payload expected by templates/analytics.html."""
    user_data = user_data or {}
    try:
        local_sessions = store[ukey()].get("sessions", []) or []
        local_checkins = store[ukey()].get("wellbeing_checkins", []) or []
    except Exception:
        local_sessions = []
        local_checkins = []

    emotion_freq = user_data.get("emotion_freq", {}) or {}
    mood_timeline = user_data.get("mood_timeline", []) or []
    valid_moods = [float(v) for v in mood_timeline if v is not None]
    avg_mood = round(float(user_data.get("avg_mood", 5.0) or 5.0), 1)
    total_messages = int(user_data.get("total_messages", 0) or 0)
    total_sessions = int(user_data.get("total_sessions", len(local_sessions)) or 0)

    top_emotion = (
        user_data.get("top_emotion")
        or (max(emotion_freq, key=emotion_freq.get) if emotion_freq else "neutral")
    )
    dominant_emotion = str(top_emotion).replace("_", " ").title()

    total_emotions = sum(int(v or 0) for v in emotion_freq.values())
    positive_count = sum(int(emotion_freq.get(e, 0) or 0) for e in ("happy", "surprise", "neutral"))
    difficult_count = sum(
        int(emotion_freq.get(e, 0) or 0)
        for e in ("fear", "sad", "disgust", "angry", "contempt")
    )
    positive_mood_ratio = _clamp_percent((positive_count / total_emotions) * 100) if total_emotions else 50
    stress_load = _clamp_percent(
        ((difficult_count / total_emotions) * 65 if total_emotions else 25)
        + ((10 - avg_mood) * 3.5)
    )
    mood_range = (max(valid_moods) - min(valid_moods)) if len(valid_moods) >= 2 else 0
    emotional_stability = _clamp_percent(100 - (mood_range * 10) - (stress_load * 0.35))

    delta = (valid_moods[-1] - valid_moods[0]) if len(valid_moods) >= 2 else 0
    if delta >= 1:
        mood_trend = {
            "emoji": "↗",
            "label": "Improving",
            "description": "Recent mood signals are trending upward compared with earlier activity.",
        }
    elif delta <= -1:
        mood_trend = {
            "emoji": "↘",
            "label": "Needs Attention",
            "description": "Recent mood signals are lower than earlier activity, so a supportive check-in may help.",
        }
    else:
        mood_trend = {
            "emoji": "→",
            "label": "Stable",
            "description": "Recent mood signals look broadly steady across available activity.",
        }

    if mood_range >= 5:
        volatility = {
            "label": "High Variation",
            "description": "Mood signals vary noticeably across recent sessions.",
        }
    elif mood_range >= 2.5:
        volatility = {
            "label": "Moderate Variation",
            "description": "Mood signals show some movement without sharp swings.",
        }
    else:
        volatility = {
            "label": "Low Variation",
            "description": "Mood signals are relatively consistent in the available data.",
        }

    mode_counts = Counter(s.get("mode", "chat") for s in local_sessions if isinstance(s, dict))
    if not mode_counts:
        mode_counts = Counter({"chat": max(total_sessions, 1)})
    mode_labels = [str(k).replace("_", " ").title() for k, _ in mode_counts.most_common()]
    mode_values = [int(v) for _, v in mode_counts.most_common()]

    concern_counts = Counter()
    for checkin_item in local_checkins:
        concerns = checkin_item.get("concerns", []) if isinstance(checkin_item, dict) else []
        if isinstance(concerns, str):
            concerns = [concerns]
        for item in concerns or []:
            label = str(item).strip().replace("_", " ").title()
            if label:
                concern_counts[label] += 1

    if not concern_counts:
        keyword_map = {
            "Stress": ("stress", "pressure", "overload", "workload"),
            "Sleep": ("sleep", "insomnia", "tired", "fatigue"),
            "Loneliness": ("lonely", "alone", "social"),
            "Anxiety": ("anxious", "anxiety", "fear", "worry"),
            "Mood": ("sad", "angry", "mood", "emotion"),
        }
        text_blob = " ".join(
            str(m.get("content", ""))
            for s in local_sessions
            for m in (s.get("messages", []) or [])
            if isinstance(m, dict)
        ).lower()
        for label, words in keyword_map.items():
            count = sum(text_blob.count(word) for word in words)
            if count:
                concern_counts[label] = count

    if not concern_counts:
        concern_counts = Counter({"General Wellbeing": 1})
    concern_labels = [label for label, _ in concern_counts.most_common(5)]
    concern_values = [int(value) for _, value in concern_counts.most_common(5)]
    top_concern = concern_labels[0] if concern_labels else "General Wellbeing"
    concern_data = {
        "top": top_concern,
        "message": f"{top_concern} is the most visible repeated theme in the available activity.",
    }

    latest_checkin = (
        user_data.get("latest_wellbeing_checkin")
        or (local_checkins[-1] if local_checkins else {})
        or {}
    )
    checkin_score = _clamp_percent(latest_checkin.get("wellbeing_score", 50))
    social_score = latest_checkin.get("social_connection")
    stress_score = latest_checkin.get("stress")
    risk_level = str(latest_checkin.get("risk_level", "unknown") or "unknown").lower()

    support_level = _clamp_percent((100 - checkin_score) * 0.7 + stress_load * 0.3)
    if risk_level in ("high", "crisis") or support_level >= 70:
        support_need = {
            "level": max(support_level, 75),
            "label": "High",
            "color": "red",
            "message": "Consider reaching out to a trusted person or qualified professional support.",
        }
    elif risk_level == "medium" or support_level >= 40:
        support_need = {
            "level": max(support_level, 45),
            "label": "Moderate",
            "color": "yellow",
            "message": "A structured self-care step and a supportive check-in may be useful.",
        }
    else:
        support_need = {
            "level": max(support_level, 15),
            "label": "Low",
            "color": "green",
            "message": "Current indicators suggest routine self-care and continued tracking.",
        }

    pressure_label = "Not recorded"
    if stress_score is not None:
        try:
            stress_int = int(stress_score)
            pressure_label = "High" if stress_int >= 4 else "Moderate" if stress_int == 3 else "Low"
        except Exception:
            pressure_label = str(stress_score).title()

    social_label = "Not recorded"
    if social_score is not None:
        try:
            social_int = int(social_score)
            social_label = "Strong" if social_int >= 4 else "Moderate" if social_int == 3 else "Limited"
        except Exception:
            social_label = str(social_score).title()

    checkin = {
        "score": checkin_score,
        "sleep": str(latest_checkin.get("sleep", "Not recorded")).replace("_", " ").title(),
        "social": social_label,
        "pressure": pressure_label,
        "message": (
            "Latest check-in data is included in this view."
            if latest_checkin
            else "No wellbeing check-in has been saved yet."
        ),
    }

    daily_counts = user_data.get("daily_counts", []) or []
    engagement_points = []
    for index, mood in enumerate(mood_timeline):
        if mood is None:
            continue
        engagement_points.append({
            "x": int(daily_counts[index]) if index < len(daily_counts) else 0,
            "y": float(mood),
        })
    if not engagement_points:
        engagement_points = [{"x": total_messages, "y": avg_mood}]

    suggested_action = (
        "Use one short grounding exercise today and log a wellbeing check-in."
        if support_need["label"] != "Low"
        else "Continue regular check-ins and note any recurring mood changes."
    )

    analytics = {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "avg_mood": avg_mood,
        "dominant_emotion": dominant_emotion,
        "emotional_stability": emotional_stability,
        "stress_load": stress_load,
        "positive_mood_ratio": positive_mood_ratio,
        "mood_trend": mood_trend,
        "volatility": volatility,
        "concern_data": concern_data,
        "mode_data": {"dominant": mode_labels[0] if mode_labels else "Chat"},
        "checkin": checkin,
        "support_need": support_need,
        "professional_help_note": (
            "Recommended now" if support_need["label"] == "High" else "Optional supportive resource"
        ),
        "suggested_action": suggested_action,
        "pattern_insights": [
            {
                "title": "Dominant emotion",
                "text": f"{dominant_emotion} appears most often in recorded emotion signals.",
            },
            {
                "title": "Engagement",
                "text": f"{total_sessions} sessions and {total_messages} messages are included in this summary.",
            },
            {
                "title": "Wellbeing theme",
                "text": concern_data["message"],
            },
        ],
    }

    return {
        "analytics": analytics,
        "mode_labels": mode_labels,
        "mode_values": mode_values,
        "concern_labels": concern_labels,
        "concern_values": concern_values,
        "engagement_points": engagement_points,
    }


# ============================================================
# Dashboard Extra Pages — Analytics + Session History
# ============================================================

@app.route("/analytics")
@login_required
def analytics_page():
    """Dashboard analytics page."""
    try:
        user_data = _build_user_data()
    except Exception as e:
        print(f"⚠️ analytics _build_user_data fallback: {e}")
        traceback.print_exc()
        user_data = {}

    emotion_freq = user_data.get("emotion_freq", {}) or {}
    mood_timeline = user_data.get("mood_timeline", []) or []
    daily_labels = user_data.get("daily_labels", []) or []
    analytics_context = _analytics_context(user_data)

    return render_template(
        "analytics.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        emotion_freq=emotion_freq,
        mood_timeline=mood_timeline,
        daily_labels=daily_labels,
        total_messages=user_data.get("total_messages", 0),
        total_sessions=user_data.get("total_sessions", 0),
        avg_mood=user_data.get("avg_mood", 5.0),
        **analytics_context,
    )



@app.route("/session_history")
@login_required
def session_history_page():
    """
    Rich Session History page.

    Builds real-time style session cards from the local NeuroSense store:
    - mode
    - message count
    - user / assistant turns
    - dominant emotion
    - mood score
    - risk badge
    - session quality estimate
    - expandable conversation timeline
    """
    try:
        user_data = _build_user_data()
    except Exception as e:
        print(f"⚠️ session_history _build_user_data fallback: {e}")
        traceback.print_exc()
        user_data = {}

    def _safe_text(value, fallback=""):
        if value is None:
            return fallback
        return str(value).strip() or fallback

    def _pretty_mode(mode):
        raw = _safe_text(mode, "chat").replace("_", " ").strip().lower()
        mapping = {
            "chat": "Normal Chat",
            "normal": "Normal Chat",
            "normal chat": "Normal Chat",
            "voice": "Voice Chat",
            "voice chat": "Voice Chat",
            "hand": "Hand Sign Chat",
            "hand chat": "Hand Sign Chat",
            "knowledge": "Knowledge Chat",
            "knowledge chat": "Knowledge Chat",
            "research": "Research Chat",
            "research chat": "Research Chat",
        }
        return mapping.get(raw, raw.title() if raw else "Normal Chat")

    def _emotion_emoji(emotion):
        e = _safe_text(emotion, "neutral").lower()
        return {
            "happy": "😊",
            "surprise": "😮",
            "neutral": "😐",
            "fear": "😟",
            "sad": "😔",
            "disgust": "😕",
            "angry": "😠",
            "contempt": "😒",
        }.get(e, "😐")

    def _risk_from_messages(messages):
        text = " ".join([_safe_text(m.get("content", "")) for m in messages if isinstance(m, dict)]).lower()

        crisis_terms = [
            "suicide", "kill myself", "end my life", "hurt myself", "self harm",
            "self-harm", "i want to die", "no reason to live", "don't want to live",
            "dont want to live",
        ]
        medium_terms = [
            "panic", "anxiety", "depressed", "depression", "overwhelmed",
            "burnout", "abuse", "medication", "medicine", "dose", "tablet",
        ]

        if any(term in text for term in crisis_terms):
            return {
                "label": "Crisis",
                "class": "crisis",
                "message": "Safety-sensitive wording detected. Professional or emergency support may be needed.",
            }

        if any(term in text for term in medium_terms):
            return {
                "label": "Medium",
                "class": "medium",
                "message": "Some stress or support-related signals were present in this session.",
            }

        return {
            "label": "Low",
            "class": "low",
            "message": "No immediate high-risk wording detected in this saved session.",
        }

    def _session_summary(mode, messages, emotions):
        user_msgs = [
            _safe_text(m.get("content", ""))
            for m in messages
            if isinstance(m, dict) and m.get("role") == "user" and _safe_text(m.get("content", ""))
        ]

        assistant_msgs = [
            _safe_text(m.get("content", ""))
            for m in messages
            if isinstance(m, dict) and m.get("role") == "assistant" and _safe_text(m.get("content", ""))
        ]

        if user_msgs:
            first = user_msgs[0][:160]
            if len(user_msgs) > 1:
                return f"The session focused on: {first}... The user continued the discussion across {len(user_msgs)} user message(s)."
            return f"The session focused on: {first}"

        if assistant_msgs:
            return f"Assistant support was generated in {_pretty_mode(mode)} mode."

        if emotions:
            dominant = Counter(emotions).most_common(1)[0][0]
            return f"Session saved with dominant emotion: {dominant}."

        return "Session data saved. More messages will create a richer summary."

    def _parse_time_to_minutes(value):
        try:
            if not value:
                return None
            parts = str(value).split(":")
            if len(parts) < 2:
                return None
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return None

    def _duration_text(messages):
        times = [
            _parse_time_to_minutes(m.get("time"))
            for m in messages
            if isinstance(m, dict) and m.get("time")
        ]
        times = [t for t in times if t is not None]

        if len(times) < 2:
            return "Live/short session"

        diff = max(times) - min(times)
        if diff <= 0:
            return "Under 1 min"

        return f"{diff} min"

    def _session_quality(total_messages, mood_score, risk_label, ended):
        score = 55
        score += min(total_messages * 4, 22)
        score += max(0, min(float(mood_score or 5), 10) - 5) * 3

        if str(risk_label).lower() == "low":
            score += 10
        elif str(risk_label).lower() == "medium":
            score -= 5
        elif str(risk_label).lower() == "crisis":
            score -= 18

        if ended:
            score += 5

        return int(max(15, min(round(score), 100)))

    enriched_sessions = []
    conversation_history = []

    # Primary source: local in-memory/json store because it contains the full messages and emotions.
    try:
        raw_sessions = store[ukey()].get("sessions", []) or []
    except Exception as e:
        print(f"⚠️ session_history local sessions failed: {e}")
        raw_sessions = []

    # Fallback from _build_user_data if needed.
    if not raw_sessions:
        raw_sessions = user_data.get("sessions", []) or user_data.get("recent_sessions", []) or []

    for idx, raw in enumerate(raw_sessions, start=1):
        if not isinstance(raw, dict):
            continue

        messages = raw.get("messages", []) or []
        emotions = raw.get("emotions", []) or []
        mode = raw.get("mode", "chat")
        date = raw.get("date") or raw.get("created_at") or "Recent session"
        ended = bool(raw.get("ended", False))

        if not isinstance(messages, list):
            messages = []
        if not isinstance(emotions, list):
            emotions = []

        for m in messages:
            if isinstance(m, dict):
                conversation_history.append({
                    "role": m.get("role", "message"),
                    "content": m.get("content", ""),
                    "time": m.get("time", ""),
                    "created_at": date,
                    "mode": _pretty_mode(mode),
                })

        emotion_counts = Counter([_safe_text(e, "neutral").lower() for e in emotions])
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
        mood_values = [MOOD_SCORE.get(_safe_text(e, "neutral").lower(), 5) for e in emotions]
        mood_score = round(sum(mood_values) / len(mood_values), 1) if mood_values else 5.0

        user_count = len([m for m in messages if isinstance(m, dict) and m.get("role") == "user"])
        assistant_count = len([m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"])
        total_messages = len(messages)
        risk = _risk_from_messages(messages)
        quality_score = _session_quality(total_messages, mood_score, risk.get("label"), ended)

        first_time = ""
        last_time = ""
        if messages:
            first_time = _safe_text(messages[0].get("time", ""), "") if isinstance(messages[0], dict) else ""
            last_time = _safe_text(messages[-1].get("time", ""), "") if isinstance(messages[-1], dict) else ""

        enriched_sessions.append({
            "index": idx,
            "title": f"Session {idx}",
            "date": date,
            "created_at": date,
            "mode": _pretty_mode(mode),
            "mode_raw": mode,
            "messages": messages,
            "total_messages": total_messages,
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "dominant_emotion": dominant_emotion,
            "dominant_emotion_emoji": _emotion_emoji(dominant_emotion),
            "emotion_timeline": [
                {
                    "label": _safe_text(e, "neutral").title(),
                    "emoji": _emotion_emoji(e),
                }
                for e in emotions[-12:]
            ],
            "mood_score": mood_score,
            "risk": risk,
            "quality_score": quality_score,
            "duration": _duration_text(messages),
            "started_at": first_time or "—",
            "last_activity": last_time or "—",
            "ended": ended,
            "status": "Ended" if ended else "Active / Saved",
            "summary": raw.get("summary") or _session_summary(mode, messages, emotions),
        })

    enriched_sessions = list(reversed(enriched_sessions))

    # Page-level quick stats.
    total_sessions = len(enriched_sessions)
    total_messages = sum(s.get("total_messages", 0) for s in enriched_sessions)
    avg_mood = round(
        sum(float(s.get("mood_score", 5)) for s in enriched_sessions) / total_sessions,
        1,
    ) if total_sessions else 5.0

    all_emotions = [s.get("dominant_emotion", "neutral") for s in enriched_sessions]
    dominant_overall = Counter(all_emotions).most_common(1)[0][0] if all_emotions else "neutral"

    active_session = enriched_sessions[0] if enriched_sessions else None

    history_stats = {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "avg_mood": avg_mood,
        "dominant_emotion": dominant_overall,
        "active_session": active_session,
    }

    return render_template(
        "session_history.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        sessions=enriched_sessions,
        conversation_history=conversation_history,
        history_stats=history_stats,
    )



# ── Best Practices Real-time Practice Helpers ────────────────────────────────
def _load_practice_logs(limit: int = 20) -> list:
    """Return recent best-practice completion logs for current user."""
    try:
        logs = store[ukey()].get("practice_logs", []) or []
        if not isinstance(logs, list):
            return []
        return list(reversed(logs[-limit:]))
    except Exception:
        return []


def _practice_today_count() -> int:
    today = datetime.date.today().isoformat()
    try:
        return sum(
            1 for item in store[ukey()].get("practice_logs", [])
            if str(item.get("date", "")).startswith(today)
        )
    except Exception:
        return 0


def _practice_streak_days() -> int:
    """Compute consecutive days with at least one completed practice."""
    try:
        logs = store[ukey()].get("practice_logs", []) or []
        days = {
            str(item.get("date", ""))[:10]
            for item in logs
            if item.get("completed", True) and item.get("date")
        }
        streak = 0
        cursor = datetime.date.today()
        while cursor.isoformat() in days:
            streak += 1
            cursor -= datetime.timedelta(days=1)
        return streak
    except Exception:
        return 0


def _most_used_practice() -> str:
    try:
        names = [
            str(item.get("practice", "")).strip()
            for item in store[ukey()].get("practice_logs", [])
            if str(item.get("practice", "")).strip()
        ]
        return Counter(names).most_common(1)[0][0] if names else "Not enough data"
    except Exception:
        return "Not enough data"


def _append_practice_log(data: dict) -> dict:
    """Save a safe local practice log entry."""
    now = datetime.datetime.now()
    data = data or {}

    def _safe_int(value, default=0, minimum=0, maximum=10):
        try:
            value = int(value)
            return max(minimum, min(maximum, value))
        except Exception:
            return default

    entry = {
        "id": str(uuid.uuid4()),
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "created_at": now.isoformat(),
        "practice": str(data.get("practice") or "Practice").strip()[:80],
        "mood": str(data.get("mood") or "neutral").strip()[:40],
        "stress_before": _safe_int(data.get("stress_before"), 5),
        "stress_after": _safe_int(data.get("stress_after"), _safe_int(data.get("stress_before"), 5)),
        "duration_seconds": max(0, min(3600, int(data.get("duration_seconds") or 0))),
        "notes": str(data.get("notes") or "").strip()[:1200],
        "reflection": str(data.get("reflection") or "").strip()[:2000],
        "completed": bool(data.get("completed", True)),
        "source": "best_practices",
    }

    d = store[ukey()]
    d.setdefault("practice_logs", [])
    d["practice_logs"].append(entry)
    d["practice_logs"] = d["practice_logs"][-300:]
    _save_store()

    return entry


@app.route("/best_practices")
@login_required
def best_practices_page():
    practice_logs = _load_practice_logs(limit=10)
    practice_stats = {
        "today_completed": _practice_today_count(),
        "practice_streak": _practice_streak_days(),
        "most_used_practice": _most_used_practice(),
        "total_completed": len(store[ukey()].get("practice_logs", []) or []),
    }

    return render_template(
        "best_practices.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
        practice_logs=practice_logs,
        practice_stats=practice_stats,
        latest_emotion=session.get("sentiment", "neutral"),
    )


@app.route("/api/practices/log", methods=["GET", "POST"])
@login_required
def practice_log_api():
    """Create/read best-practice logs for breathing, grounding, journaling, reframing, etc."""
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "logs": _load_practice_logs(limit=25),
            "stats": {
                "today_completed": _practice_today_count(),
                "practice_streak": _practice_streak_days(),
                "most_used_practice": _most_used_practice(),
                "total_completed": len(store[ukey()].get("practice_logs", []) or []),
            }
        })

    data = request.get_json(silent=True) or {}
    entry = _append_practice_log(data)

    return jsonify({
        "ok": True,
        "entry": entry,
        "logs": _load_practice_logs(limit=10),
        "stats": {
            "today_completed": _practice_today_count(),
            "practice_streak": _practice_streak_days(),
            "most_used_practice": _most_used_practice(),
            "total_completed": len(store[ukey()].get("practice_logs", []) or []),
        }
    })


@app.route("/agent_config")
@login_required
def agent_config_page():
    return render_template(
        "agent_config.html",
        name=session.get("name", "User"),
        lang=session.get("lang", "en"),
        languages=_fmt_langs(),
    )


@app.route("/profile")
@login_required
def profile_page():
    user_id = _current_user_id()

    if not user_id:
        return redirect(url_for("home"))

    try:
        data = _safe_profile_with_usage(user_id)
        return render_template(
            "profile.html",
            profile=data.get("profile"),
            usage=data.get("usage"),
            limits=data.get("limits"),
            languages=_fmt_langs(),
        )
    except Exception as e:
        traceback.print_exc()
        return redirect(url_for("dashboard"))


@app.route("/settings")
@login_required
def settings_page():
    user_id = _current_user_id()
    profile = None
    usage = None
    limits = None

    if user_id:
        try:
            data = _safe_profile_with_usage(user_id)
            profile = data.get("profile")
            usage = data.get("usage")
            limits = data.get("limits")
        except Exception:
            traceback.print_exc()

    return render_template(
        "settings.html",
        profile=profile,
        usage=usage,
        limits=limits,
        languages=_fmt_langs(),
    )


@app.route("/api/user/profile", methods=["GET"])
@login_required
def get_user_profile_api():
    user_id = _current_user_id()

    if not user_id:
        return jsonify({
            "ok": False,
            "error": "Supabase user session missing. Please login through /auth."
        }), 401

    try:
        data = _safe_profile_with_usage(user_id)
        return jsonify({"ok": True, **data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/user/profile", methods=["POST"])
@login_required
def update_user_profile_api():
    user_id = _current_user_id()

    if not user_id:
        return jsonify({"ok": False, "error": "Supabase user session missing."}), 401

    data = request.get_json(silent=True) or {}

    try:
        profile = update_user_profile(user_id, data)

        session["name"]  = profile.get("full_name", session.get("name", "User"))
        session["phone"] = profile.get("phone", session.get("phone", ""))
        session["lang"]  = profile.get("preferred_language", session.get("lang", "en"))
        session["role"]  = profile.get("role", session.get("role", "user"))

        return jsonify({"ok": True, "profile": profile})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/user/avatar", methods=["POST"])
@login_required
def upload_user_avatar_api():
    """
    Upload profile photo.

    Frontend must send:
        FormData.append("avatar", file)

    Saves file locally to:
        static/uploads/avatars/

    Updates:
    - user_profiles.avatar_url in Supabase, best-effort
    - Flask session/local JSON store, best-effort
    """
    user_id = _current_user_id()

    if not user_id:
        return jsonify({
            "ok": False,
            "success": False,
            "error": "Supabase user session missing. Please login again."
        }), 401

    if "avatar" not in request.files:
        return jsonify({
            "ok": False,
            "success": False,
            "error": "Upload field must be named 'avatar'."
        }), 400

    file = request.files["avatar"]

    if not file or not file.filename:
        return jsonify({
            "ok": False,
            "success": False,
            "error": "No avatar file selected."
        }), 400

    try:
        allowed_extensions = {"png", "jpg", "jpeg", "webp"}
        allowed_mime_types = {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
        }

        original_filename = secure_filename(file.filename or "")
        extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""

        if extension not in allowed_extensions:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Only PNG, JPG, JPEG, and WEBP images are allowed."
            }), 400

        if file.mimetype and file.mimetype not in allowed_mime_types:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Invalid image type. Please upload PNG, JPG, JPEG, or WEBP."
            }), 400

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size = 5 * 1024 * 1024
        if file_size > max_size:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Image size must be less than 5 MB."
            }), 400

        upload_folder = os.path.join(app.root_path, "static", "uploads", "avatars")
        os.makedirs(upload_folder, exist_ok=True)

        safe_user_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))
        new_filename = f"{safe_user_id}_{int(time.time())}.{extension}"
        save_path = os.path.join(upload_folder, new_filename)

        file.save(save_path)

        avatar_url = f"/static/uploads/avatars/{new_filename}"

        profile = {}

        # Update Supabase profile best-effort.
        try:
            profile = update_user_profile(user_id, {"avatar_url": avatar_url}) or {}
        except Exception as e:
            print(f"⚠️ Supabase avatar_url update failed: {e}")
            traceback.print_exc()

        # Update local session/store best-effort.
        try:
            session["avatar_url"] = avatar_url
            k = ukey()
            store[k]["avatar_url"] = avatar_url
            _save_store()
        except Exception as e:
            print(f"⚠️ Local avatar save failed: {e}")

        return jsonify({
            "ok": True,
            "success": True,
            "avatar_url": avatar_url,
            "profile": profile,
        })

    except Exception as e:
        print(f"❌ Avatar upload failed: {e}")
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/user/usage", methods=["GET"])
@login_required
def user_usage_api():
    user_id = _current_user_id()

    if not user_id:
        return jsonify({"ok": False, "error": "Supabase user session missing."}), 401

    try:
        data = _safe_profile_with_usage(user_id)
        return jsonify({
            "ok": True,
            "usage": data.get("usage"),
            "limits": data.get("limits"),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/user/delete_account", methods=["POST"])
@login_required
def delete_user_account_api():
    user_id = _current_user_id()

    if not user_id:
        return jsonify({"ok": False, "error": "Supabase user session missing."}), 401

    data = request.get_json(silent=True) or {}
    confirm = (data.get("confirm") or "").strip().upper()

    if confirm != "DELETE":
        return jsonify({"ok": False, "error": "Type DELETE to confirm account deletion."}), 400

    try:
        soft_delete_account(user_id)
        session.clear()
        return jsonify({"ok": True, "message": "Account deleted successfully."})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/admin/users")
@login_required
@admin_required
def admin_users_api():
    try:
        return jsonify({"ok": True, "users": list_all_profiles()})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  API — SESSION
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/end_session", methods=["POST"])
@login_required
def end_session():
    mode  = (request.json or {}).get("mode", "normal_chat")
    k     = ukey()
    today = datetime.date.today().isoformat()
    d     = store[k]

    ended_session = None
    for s in d["sessions"]:
        if s["date"] == today and s["mode"] == mode and not s.get("ended"):
            s["ended"]    = True
            s["ended_at"] = datetime.datetime.now().isoformat()
            ended_session = s
            break

    _save_store()

    if not ended_session:
        return jsonify({"ok": False, "message": "No active session found."})

    msgs        = ended_session.get("messages", [])
    emos        = ended_session.get("emotions", [])
    emo_counts  = Counter(emos)
    top_emo     = emo_counts.most_common(1)[0][0] if emo_counts else "neutral"
    mood_scores = [MOOD_SCORE.get(e, 5) for e in emos]
    avg_mood    = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 5.0
    user_msgs   = [m["content"] for m in msgs if m.get("role") == "user"]

    return jsonify({
        "ok": True,
        "summary": {
            "mode":           mode,
            "date":           today,
            "duration_msgs":  len(msgs),
            "user_messages":  len(user_msgs),
            "top_emotion":    top_emo,
            "avg_mood":       avg_mood,
            "emotion_counts": dict(emo_counts),
        },
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — REPORTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/generate_report", methods=["POST"])
@login_required
def generate_report_api():
    ud     = _build_user_data()
    result = generate_ai_report(ud)

    if result.get("success"):
        k = ukey()
        report_entry = {
            "id":           result["report"]["report_id"],
            "generated_at": result["report"]["generated_at"],
            "report":       result["report"],
        }
        store[k]["reports"].append(report_entry)
        store[k]["reports"] = store[k]["reports"][-10:]
        _save_store()

        # Best-effort Supabase metadata save for AI-generated report summary.
        _save_report_metadata_to_supabase(
            user_data=ud,
            report_type=result["report"].get("report_type", "therapy"),
            fmt="pdf",
            report_payload=result["report"],
            file_name="",
        )

        if session.get("supabase_user_id"):
            try:
                increment_usage(session["supabase_user_id"], field="reports_generated", amount=1)
            except Exception as e:
                print(f"⚠️  Report usage tracking failed: {e}")

    return jsonify(result)


@app.route("/api/report_preview")
@login_required
def report_preview():
    ud        = _build_user_data()
    efreq     = ud["emotion_freq"]
    total_det = sum(efreq.values()) or 1
    top_emo   = ud["top_emotion"]
    valid_m   = [v for v in ud["mood_timeline"] if v is not None]

    trend = "stable"
    if len(valid_m) >= 2:
        trend = (
            "improving" if valid_m[-1] > valid_m[0] else
            "declining" if valid_m[-1] < valid_m[0] else "stable"
        )

    return jsonify({
        "report_id":      ud["report_id"],
        "report_date":    ud["report_date"],
        "name":           ud["name"],
        "total_messages": ud["total_messages"],
        "streak":         ud["streak"],
        "avg_mood":       ud["avg_mood"],
        "top_emotion":    top_emo,
        "total_sessions": ud["total_sessions"],
        "mood_trend":     trend,
        "emotion_breakdown": [
            {"emotion": e, "count": c, "pct": round(c / total_det * 100, 1)}
            for e, c in sorted(efreq.items(), key=lambda x: x[1], reverse=True)
        ],
    })


@app.route("/api/saved_reports")
@login_required
def saved_reports_api():
    k       = ukey()
    reports = store[k].get("reports", [])
    return jsonify({"reports": list(reversed(reports))})


# ── DELETE REPORT ─────────────────────────────────────────────────────────────
@app.route("/api/report/delete", methods=["POST"])
@login_required
def delete_report():
    """
    Delete a saved report by report_id.
    Body JSON: { "report_id": "NS-..." }
    """
    try:
        data      = request.get_json(silent=True) or {}
        report_id = data.get("report_id", "").strip()

        if not report_id:
            return jsonify({"ok": False, "error": "No report_id provided"}), 400

        k = ukey()

        before = len(store[k].get("reports", []))
        store[k]["reports"] = [
            r for r in store[k].get("reports", [])
            if r.get("id") != report_id
        ]
        after = len(store[k]["reports"])

        if before == after:
            return jsonify({"ok": False, "error": f"Report '{report_id}' not found"}), 404

        _save_store()
        _supabase_delete_by_report_id(report_id)
        print(f"🗑  Report deleted: {report_id} (user: {k})")
        return jsonify({"ok": True, "deleted": report_id})

    except Exception as e:
        print(f"❌ Delete report error: {e}")
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ── GENERATE REPORT FILE ──────────────────────────────────────────────────────
@app.route("/api/report/generate", methods=["POST"])
@login_required
def report_generate():
    try:
        from generate_report import generate_therapy_pdf, generate_therapy_csv
    except ImportError as e:
        return jsonify({"ok": False, "error": f"generate_report.py missing: {e}"}), 500

    body        = request.get_json(force=True, silent=True) or {}
    fmt         = str(body.get("format", "pdf")).lower().strip()
    report_type = str(body.get("report_type", "solution")).lower().strip()
    saved_id    = body.get("report_id", "")

    if fmt not in ("pdf", "csv"):
        return jsonify({"ok": False, "error": "format must be 'pdf' or 'csv'"}), 400

    if report_type not in ("assessment", "solution", "combined", "therapy"):
        return jsonify({
            "ok": False,
            "error": "report_type must be 'assessment', 'solution', or 'combined'"
        }), 400

    try:
        user_data = _build_user_data()
        user_data["report_type"] = report_type
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"Failed to build user data: {e}"}), 500

    if saved_id:
        k = ukey()
        matched = next((r for r in store[k].get("reports", []) if r.get("id") == saved_id), None)
        if matched:
            user_data["saved_reports"] = [{"report": matched.get("report", matched)}]
        else:
            return jsonify({"ok": False, "error": f"Saved report '{saved_id}' not found."}), 404

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=f".{fmt}")
        os.close(fd)
        generator = generate_therapy_pdf if fmt == "pdf" else generate_therapy_csv
        ok        = generator(user_data, tmp_path)
        if ok is False:
            raise RuntimeError("Generator returned False.")
    except Exception as e:
        traceback.print_exc()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return jsonify({"ok": False, "error": f"File generation failed: {e}"}), 500

    try:
        file_size = os.path.getsize(tmp_path)
    except OSError:
        file_size = 0

    if file_size == 0:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return jsonify({"ok": False, "error": "Generated file is empty."}), 500

    print(f"✅ Report file ready: {tmp_path} ({file_size:,} bytes)")

    if session.get("supabase_user_id"):
        try:
            increment_usage(session["supabase_user_id"], field="reports_generated", amount=1)
        except Exception as e:
            print(f"⚠️  Report file usage tracking failed: {e}")

    name_safe_for_meta = user_data.get("name", "User").replace(" ", "_")
    report_id_for_meta = user_data.get("report_id", "NS")
    file_name_for_meta = f"NeuroSense_{report_type}_{report_id_for_meta}_{name_safe_for_meta}.{fmt}"

    supabase_report = _save_report_metadata_to_supabase(
        user_data=user_data,
        report_type=report_type,
        fmt=fmt,
        report_payload={
            "report_id": report_id_for_meta,
            "report_type": report_type,
            "format": fmt,
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "source": "api_report_generate",
            "saved_report_id": saved_id or None,
        },
        file_name=file_name_for_meta,
        file_path="temporary_download_token",
    )

    token = str(uuid.uuid4())
    _report_tokens[token] = {
        "path":      tmp_path,
        "format":    fmt,
        "expires":   datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        "name":      user_data.get("name",      "User"),
        "report_id": user_data.get("report_id", "NS"),
        "report_type": report_type,
    }

    return jsonify({
        "ok": True,
        "token": token,
        "format": fmt,
        "report_type": report_type,
        "supabase_saved": bool(supabase_report),
        "supabase_report_id": supabase_report.get("id") if isinstance(supabase_report, dict) else None,
    })


# ── DOWNLOAD REPORT ───────────────────────────────────────────────────────────
@app.route("/api/report/download")
def report_download():
    token = request.args.get("token", "").strip()

    if not token:
        return jsonify({"ok": False, "error": "Missing token."}), 400

    entry = _report_tokens.get(token)
    if not entry:
        return (
            "<h2 style='font-family:sans-serif;color:#c00'>"
            "⚠️ Download link expired or already used.<br>"
            "<small>Please click Download again.</small></h2>",
            403,
        )

    if datetime.datetime.utcnow() > entry["expires"]:
        _report_tokens.pop(token, None)
        try:
            os.unlink(entry["path"])
        except OSError:
            pass
        return (
            "<h2 style='font-family:sans-serif;color:#c00'>"
            "⏰ Download link expired.<br>"
            "<small>Please click Download again.</small></h2>",
            403,
        )

    file_path = entry["path"]
    if not os.path.exists(file_path):
        _report_tokens.pop(token, None)
        return (
            "<h2 style='font-family:sans-serif;color:#c00'>"
            "❌ Report file not found.<br>"
            "<small>Please generate the report again.</small></h2>",
            404,
        )

    name_safe   = entry.get("name", "User").replace(" ", "_")
    report_id   = entry.get("report_id", "NS")
    report_type = entry.get("report_type", "report")
    ext         = entry["format"]
    fname       = f"NeuroSense_{report_type}_{report_id}_{name_safe}.{ext}"
    mime        = "application/pdf" if ext == "pdf" else "text/csv"

    _report_tokens.pop(token, None)

    try:
        with open(file_path, "rb") as fh:
            file_bytes = fh.read()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Could not read file: {e}"}), 500
    finally:
        try:
            os.unlink(file_path)
        except OSError:
            pass

    print(f"📥 Download served: {fname} ({len(file_bytes):,} bytes)")
    return send_file(
        io.BytesIO(file_bytes),
        mimetype      = mime,
        as_attachment = True,
        download_name = fname,
    )


# ── GENERATE AND DOWNLOAD (combined) ─────────────────────────────────────────
@app.route("/api/generate_and_download", methods=["POST"])
@login_required
def generate_and_download():
    try:
        from generate_report import generate_therapy_pdf, generate_therapy_csv
    except ImportError as e:
        return jsonify({"ok": False, "error": f"generate_report.py missing: {e}"}), 500

    body        = request.get_json(force=True, silent=True) or {}
    fmt         = str(body.get("format", "pdf")).lower().strip()
    report_type = str(body.get("report_type", "solution")).lower().strip()

    if fmt not in ("pdf", "csv"):
        return jsonify({"ok": False, "error": "format must be 'pdf' or 'csv'"}), 400

    if report_type not in ("assessment", "solution", "combined", "therapy"):
        return jsonify({
            "ok": False,
            "error": "report_type must be 'assessment', 'solution', or 'combined'"
        }), 400

    try:
        user_data = _build_user_data()
        user_data["report_type"] = report_type
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"Failed to build user data: {e}"}), 500

    ai_result = generate_ai_report(user_data)
    if not ai_result.get("success"):
        return jsonify({"ok": False, "error": ai_result.get("error", "AI report failed")}), 500

    ai_report = ai_result["report"]
    ai_report["report_type"] = report_type

    k = ukey()
    report_entry = {
        "id":           ai_report["report_id"],
        "generated_at": ai_report["generated_at"],
        "report":       ai_report,
    }
    store[k]["reports"].append(report_entry)
    store[k]["reports"] = store[k]["reports"][-10:]
    _save_store()
    if session.get("supabase_user_id"):
        try:
            increment_usage(session["supabase_user_id"], field="reports_generated", amount=1)
        except Exception as e:
            print(f"⚠️  Combined report usage tracking failed: {e}")

    user_data["saved_reports"] = [{"report": ai_report}]
    user_data["report_type"] = report_type

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=f".{fmt}")
        os.close(fd)
        generator = generate_therapy_pdf if fmt == "pdf" else generate_therapy_csv
        ok        = generator(user_data, tmp_path)
        if ok is False:
            raise RuntimeError("Generator returned False")
    except Exception as e:
        traceback.print_exc()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return jsonify({"ok": False, "error": f"File generation failed: {e}"}), 500

    try:
        file_size = os.path.getsize(tmp_path)
    except OSError:
        file_size = 0

    if file_size == 0:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return jsonify({"ok": False, "error": "Generated file is empty."}), 500

    name_safe_for_meta = user_data.get("name", "User").replace(" ", "_")
    report_id_for_meta = ai_report.get("report_id", "NS")
    file_name_for_meta = f"NeuroSense_{report_type}_{report_id_for_meta}_{name_safe_for_meta}.{fmt}"

    supabase_report = _save_report_metadata_to_supabase(
        user_data=user_data,
        report_type=report_type,
        fmt=fmt,
        report_payload=ai_report,
        file_name=file_name_for_meta,
        file_path="temporary_download_token",
    )

    token = str(uuid.uuid4())
    _report_tokens[token] = {
        "path":      tmp_path,
        "format":    fmt,
        "expires":   datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        "name":      user_data.get("name",      "User"),
        "report_id": ai_report.get("report_id", "NS"),
        "report_type": report_type,
    }

    return jsonify({
        "ok":          True,
        "token":       token,
        "format":      fmt,
        "report_type": report_type,
        "report_id":   ai_report["report_id"],
        "report":      ai_report,
        "supabase_saved": bool(supabase_report),
        "supabase_report_id": supabase_report.get("id") if isinstance(supabase_report, dict) else None,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — CHAT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
@login_required
def chat_api():
    data = request.json or {}
    msg  = data.get("message", "").strip()
    mode = data.get("mode", "normal_chat")
    requested_lang = str(data.get("lang") or session.get("lang", "en")).strip()
    if requested_lang not in SUPPORTED_LANGUAGES:
        requested_lang = "en"
    session["lang"] = requested_lang
    lang = requested_lang

    if not msg:
        return jsonify({"reply": translate("Please write a message so I can support you.", lang)})

    # Keep spam/adult filter minimal. Crisis words must reach SafetyAgent.
    if any(w in msg.lower() for w in BANNED_WORDS):
        return jsonify({"reply": translate(
            "⚠️ I'm here for safe mental health support. Please share what you're feeling or what support you need.",
            lang,
        )})

    blocked = _quota_response_if_blocked("chat_message")
    if blocked:
        return blocked

    log_msg(mode, "user", msg)

    today   = datetime.date.today().isoformat()
    k       = ukey()
    history = []

    for s in store[k]["sessions"]:
        if s["date"] == today and s["mode"] == mode:
            history = s["messages"][:-1]
            break

    agent_result = agent_reply(
        user_input=msg,
        sentiment=session.get("sentiment", "neutral"),
        lang=lang,
        history=history,
    )

    rep = agent_result.get("reply", "I’m here with you.")
    log_msg(mode, "assistant", rep)

    return jsonify({
        "ok": True,
        "reply": rep,
        "used_agents": agent_result.get("used_agents", False),
        "risk_level": agent_result.get("risk_level", "unknown"),
        "response_type": agent_result.get("response_type", "supportive"),
        "technique_used": agent_result.get("technique_used", "validation"),
        "wellness": agent_result.get("wellness", {}),
        "referral": agent_result.get("referral", {}),
        "agents": agent_result.get("agents", {}),
    })


@app.route("/api/voice_chat", methods=["POST"])
@login_required
def voice_chat_api():
    data = request.json or {}
    msg  = data.get("message", "").strip()

    requested_lang = str(data.get("lang") or session.get("lang", "en")).strip()
    if requested_lang not in SUPPORTED_LANGUAGES:
        requested_lang = "en"

    # Keep the Flask session in sync with the language selected inside Voice Chat.
    session["lang"] = requested_lang
    lang = requested_lang

    if not msg:
        return jsonify({
            "ok": False,
            "reply": translate("Please speak or type a message so I can support you.", lang),
            "lang": lang,
            "language_name": SUPPORTED_LANGUAGES.get(lang, {}).get("name", "English"),
        })

    if any(w in msg.lower() for w in BANNED_WORDS):
        return jsonify({
            "ok": False,
            "reply": translate(
                "⚠️ I'm here for safe mental health support. Please share what you're feeling or what support you need.",
                lang,
            ),
            "lang": lang,
            "language_name": SUPPORTED_LANGUAGES.get(lang, {}).get("name", "English"),
        })

    blocked = _quota_response_if_blocked("voice_message")
    if blocked:
        return blocked

    log_msg("voice_chat", "user", msg)

    today   = datetime.date.today().isoformat()
    k       = ukey()
    history = []

    for s in store[k]["sessions"]:
        if s["date"] == today and s["mode"] == "voice_chat":
            history = s["messages"][:-1]
            break

    agent_result = agent_reply(
        user_input=msg,
        sentiment=session.get("sentiment", "neutral"),
        lang=lang,
        history=history,
    )

    rep = agent_result.get("reply", "I’m here with you.")
    log_msg("voice_chat", "assistant", rep)

    return jsonify({
        "ok": True,
        "reply": rep,
        "lang": lang,
        "language_name": SUPPORTED_LANGUAGES.get(lang, {}).get("name", "English"),
        "used_agents": agent_result.get("used_agents", False),
        "risk_level": agent_result.get("risk_level", "unknown"),
        "response_type": agent_result.get("response_type", "supportive"),
        "technique_used": agent_result.get("technique_used", "validation"),
        "wellness": agent_result.get("wellness", {}),
        "referral": agent_result.get("referral", {}),
        "agents": agent_result.get("agents", {}),
    })




# ── Voice Chat TTS Audio Endpoint ─────────────────────────────────────────────

VOICE_TTS_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "zh-CN": "zh-CN",
    "ja": "ja",
    "ko": "ko",
    "ar": "ar",
    "ru": "ru",
    "pt": "pt",
    "ta": "ta",
    "te": "te",
    "bn": "bn",
    "mr": "mr",
    "ml": "ml",
    "kn": "kn",
    "gu": "gu",
    "pa": "pa",
    "ur": "ur",
    "it": "it",
    "nl": "nl",
    "pl": "pl",
    "tr": "tr",
    "th": "th",
    "vi": "vi",
    "id": "id",
    "sw": "sw",
    "he": "he",
    "fa": "fa",
}


@app.route("/api/voice_tts", methods=["POST"])
@login_required
def api_voice_tts():
    """
    Generate clear multilingual voice audio for Voice Chat replies.

    Frontend sends:
        {"text": "reply text", "lang": "hi"}

    Returns:
        audio/mpeg

    Why this exists:
    Browser speechSynthesis on Linux/Chrome often uses poor or missing voices
    for many languages. gTTS gives clearer pronunciation for supported languages.
    """
    try:
        payload = request.get_json(silent=True) or {}

        text = str(payload.get("text", "")).strip()
        lang = str(payload.get("lang", session.get("lang", "en"))).strip()

        if not text:
            return jsonify({
                "ok": False,
                "error": "No text provided for TTS."
            }), 400

        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"

        # Keep audio generation short and responsive.
        if len(text) > 1400:
            text = text[:1400]

        if not GTTS_AVAILABLE:
            return jsonify({
                "ok": False,
                "error": "gTTS is not available. Install it using: pip install gTTS"
            }), 503

        tts_lang = VOICE_TTS_LANG_MAP.get(lang, "en")

        temp_dir = tempfile.gettempdir()
        filename = f"neurosense_tts_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(temp_dir, filename)

        try:
            tts = gTTS(
                text=text,
                lang=tts_lang,
                slow=False,
            )
            tts.save(audio_path)
        except Exception as tts_error:
            print(f"⚠️ gTTS failed for lang={tts_lang}: {tts_error}")
            # Final backend fallback: English voice so the user still gets audible output.
            tts = gTTS(
                text=text,
                lang="en",
                slow=False,
            )
            tts.save(audio_path)

        return send_file(
            audio_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=filename,
            max_age=0,
        )

    except Exception as e:
        print(f"❌ Voice TTS failed: {e}")
        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  API — EMOTION DETECTION
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/emotion_detect", methods=["POST"])
@login_required
def emotion_detect():
    data = (request.json or {}).get("image")
    if not FER_AVAILABLE:
        return jsonify({"emotion": None, "scores": {}, "error": "No emotion backend available"})
    if not data:
        return jsonify({"emotion": None, "scores": {}, "error": "No image data provided"})

    try:
        image_data = data.split(",")[1] if "," in data else data
        img = cv2.imdecode(
            np.frombuffer(base64.b64decode(image_data), np.uint8),
            cv2.IMREAD_COLOR,
        )
        if img is None:
            return jsonify({"emotion": None, "scores": {}, "error": "Failed to decode image"})

        try:
            lab              = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, b_ch = cv2.split(lab)
            clahe            = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            img              = cv2.cvtColor(
                cv2.merge([clahe.apply(l_ch), a_ch, b_ch]),
                cv2.COLOR_LAB2BGR,
            )
        except Exception:
            pass

        if EMOTION_BACKEND == "fer":
            results = emotion_detector.detect_emotions(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not results:
                return jsonify({"emotion": None, "scores": {}, "error": "No face detected"})
            best        = max(results, key=lambda r: r["box"][2] * r["box"][3])
            emotions    = {k: float(v) for k, v in best["emotions"].items()}
            top_emotion = max(emotions, key=emotions.get)
            total       = sum(emotions.values())
            scores      = (
                {k: round(float(v / total), 4) for k, v in emotions.items()}
                if total > 0 else emotions
            )

        elif EMOTION_BACKEND == "deepface":
            result = DeepFace.analyze(
                img, actions=["emotion"], enforce_detection=False,
                detector_backend="opencv", silent=True,
            )
            if isinstance(result, list):
                result = result[0]
            top_emotion = result["dominant_emotion"]
            raw         = {k: float(v) for k, v in result["emotion"].items()}
            total       = sum(raw.values())
            scores      = (
                {k: round(float(v / total), 4) for k, v in raw.items()}
                if total > 0 else raw
            )
        else:
            return jsonify({"emotion": None, "scores": {}, "error": "Unknown emotion backend"})

        confidence = 0
        try:
            confidence = float(scores.get(top_emotion, 0))
            if confidence <= 1:
                confidence = confidence * 100
            confidence = round(confidence, 2)
        except Exception:
            confidence = 0

        session["sentiment"] = str(top_emotion)
        log_emo(str(top_emotion), confidence=confidence)
        return jsonify({
            "emotion": str(top_emotion),
            "scores": scores,
            "confidence": confidence,
            "error": None,
        })

    except Exception as e:
        print(f"❌ Emotion detection error: {e}")
        return jsonify({"emotion": None, "scores": {}, "error": str(e)})


@app.route("/api/emotion_test")
def emotion_test():
    return jsonify({
        "backend":       EMOTION_BACKEND,
        "fer_available": FER_AVAILABLE,
        "status":        "ready" if FER_AVAILABLE else "unavailable",
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — TTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/tts", methods=["POST"])
def tts_api():
    data     = request.json or {}
    text     = data.get("text", "")
    lang     = data.get("lang", session.get("lang", "en"))
    tts_lang = SUPPORTED_LANGUAGES.get(lang, {}).get("tts", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        if GTTS_AVAILABLE:
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return send_file(buf, mimetype="audio/mpeg")

        elif TTS_AVAILABLE:
            import pyttsx3
            engine   = pyttsx3.init()
            engine.setProperty("rate", 160)
            tmp_name = f"temp_tts_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.mp3"
            engine.save_to_file(text, tmp_name)
            engine.runAndWait()
            buf = io.BytesIO()
            with open(tmp_name, "rb") as f:
                buf.write(f.read())
            buf.seek(0)
            try:
                os.remove(tmp_name)
            except OSError:
                pass
            return send_file(buf, mimetype="audio/mpeg")

        else:
            return jsonify({"error": "No TTS engine available"}), 503

    except Exception as e:
        print(f"❌ TTS error: {e}")
        return jsonify({"error": f"TTS failed: {e}"}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  API — HAND SIGN
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/hand_model_status", methods=["GET"])
@login_required
def hand_model_status():
    """Debug endpoint to verify the trained 63-feature hand-sign model is loaded."""
    if not HS_AVAILABLE:
        return jsonify({
            "ok": False,
            "success": False,
            "error": "hs_module not available.",
        }), 500

    try:
        status = hs.get_model_status() if hasattr(hs, "get_model_status") else {}
        return jsonify({
            "ok": True,
            "success": True,
            **status,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/hand_predict", methods=["POST"])
@login_required
def hand_predict():
    """
    Real-time hand sign prediction.

    Important:
    Your trained model expects 63 features:
      21 MediaPipe hand landmarks × (x, y, z)

    This route uses hs_module.predict_with_debug(), which extracts the same
    63 landmark features and returns clear debugging info when recognition fails.
    """
    sentence = session.get("hand_sentence", "")

    if not HS_AVAILABLE:
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "error": "hs_module not available. Check hs_module.py import.",
        }), 500

    payload = request.get_json(silent=True) or {}
    data = payload.get("image")

    if not data:
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "error": "No image frame received from browser.",
        }), 400

    try:
        img = cv2.imdecode(
            np.frombuffer(
                base64.b64decode(data.split(",", 1)[1] if "," in data else data),
                np.uint8,
            ),
            cv2.IMREAD_COLOR,
        )
    except Exception as e:
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "error": f"Could not decode camera image: {str(e)}",
        }), 400

    if img is None:
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "error": "Decoded image is empty.",
        }), 400

    try:
        clf = hs.load_model()
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "no_model": True,
            "error": f"Could not load hand model: {str(e)}",
        }), 500

    if clf is None:
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "no_model": True,
            "error": "data/word_model.pkl not found or hs.load_model() returned None.",
        })

    try:
        if hasattr(hs, "predict_with_debug"):
            result = hs.predict_with_debug(img, clf=clf)
            pred = result.get("label")
            raw_pred = result.get("raw_label")
            confidence = float(result.get("confidence", 0) or 0)
            hand_detected = bool(result.get("hand_detected", False))
            reason = result.get("reason", "unknown")
            top3 = result.get("top3", [])
            features_len = result.get("features_len")
            expected_features = result.get("expected_features")
        else:
            pred, confidence = hs.predict_with_confidence(img, clf=clf)
            raw_pred = pred
            hand_detected = pred is not None
            reason = "ok" if pred else "no_prediction"
            top3 = []
            features_len = None
            expected_features = getattr(clf, "n_features_in_", None)
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "predicted": None,
            "appended": False,
            "sentence": sentence,
            "error": f"Prediction crashed: {str(e)}",
        }), 500

    if not pred:
        session["hand_last_pred"] = None
        session["hand_pred_count"] = 0

        return jsonify({
            "ok": True,
            "success": True,
            "predicted": None,
            "raw_prediction": raw_pred,
            "confidence": round(confidence, 4),
            "hand_detected": hand_detected,
            "appended": False,
            "sentence": sentence,
            "reason": reason,
            "message": _hand_prediction_message(reason),
            "top3": top3,
            "features_len": features_len,
            "expected_features": expected_features,
        })

    pred = str(pred).strip().upper()

    last = session.get("hand_last_pred")
    count = int(session.get("hand_pred_count", 0) or 0)

    if last == pred:
        count += 1
    else:
        count = 1

    session["hand_last_pred"] = pred
    session["hand_pred_count"] = count

    appended = False

    if count >= 3:
        sentence = _apply_hand_sign_to_sentence(sentence, pred)
        session["hand_sentence"] = sentence
        session["hand_pred_count"] = 0
        session["hand_last_pred"] = None
        appended = True

    return jsonify({
        "ok": True,
        "success": True,
        "predicted": pred,
        "raw_prediction": raw_pred,
        "confidence": round(confidence, 4),
        "hand_detected": True,
        "hold_count": int(session.get("hand_pred_count", 0) or 0),
        "appended": appended,
        "sentence": sentence,
        "reason": "ok",
        "top3": top3,
        "features_len": features_len,
        "expected_features": expected_features,
    })


def _hand_prediction_message(reason: str) -> str:
    reason = str(reason or "unknown")

    if reason == "no_hand_landmarks_detected":
        return "No hand landmarks detected. Move your hand closer, keep the palm visible, and improve lighting."
    if reason == "low_confidence":
        return "Hand detected but confidence is low. Hold the sign steady or retrain with the same camera angle."
    if reason == "feature_count_mismatch":
        return "Model feature mismatch. Your model expects 63 MediaPipe landmark features."
    if reason == "model_not_loaded":
        return "Hand sign model is not loaded. Check data/word_model.pkl."
    if reason == "prediction_error":
        return "Prediction error occurred while reading landmarks."

    return "No confident hand sign detected yet."


def _apply_hand_sign_to_sentence(sentence: str, pred: str) -> str:
    sentence = str(sentence or "").strip()
    pred = str(pred or "").strip().upper()

    if not pred:
        return sentence

    if pred == "SPACE":
        return (sentence + " ").strip() + " "

    if pred == "DELETE":
        words = sentence.split()
        if words:
            words.pop()
        return " ".join(words)

    if pred == "CLEAR":
        return ""

    if pred == "ENTER":
        return sentence

    if pred in [".", ",", "?", "!"]:
        return (sentence.rstrip() + pred).strip()

    words = sentence.split()

    # Avoid accidental duplicate append from the same held sign.
    if words and words[-1].lower() == pred.lower():
        return sentence

    words.append(pred)
    return " ".join(words)


@app.route("/api/hand_enter", methods=["POST"])
@login_required
def hand_enter():
    data = request.json or {}
    sent = data.get("sentence", "").strip()
    lang = session.get("lang", "en")

    if not sent:
        return jsonify({"reply": translate("No sentence provided.", lang)})

    if any(w in sent.lower() for w in BANNED_WORDS):
        return jsonify({"reply": translate(
            "⚠️ I'm here for safe mental health support. Please share what you're feeling or what support you need.",
            lang,
        )})

    blocked = _quota_response_if_blocked("sign_message")
    if blocked:
        return blocked

    if session.get("supabase_user_id"):
        try:
            increment_usage(session["supabase_user_id"], field="sign_sessions", amount=1)
        except Exception as e:
            print(f"⚠️  Sign usage tracking failed: {e}")

    log_msg("hand_chat", "user", sent)

    today   = datetime.date.today().isoformat()
    k       = ukey()
    history = []

    for s in store[k]["sessions"]:
        if s["date"] == today and s["mode"] == "hand_chat":
            history = s["messages"][:-1]
            break

    agent_result = agent_reply(
        user_input=sent,
        sentiment=session.get("sentiment", "neutral"),
        lang=lang,
        history=history,
    )

    rep = agent_result.get("reply", "I’m here with you.")
    log_msg("hand_chat", "assistant", rep)

    session["hand_sentence"]   = ""
    session["hand_last_pred"]  = None
    session["hand_pred_count"] = 0

    return jsonify({
        "ok": True,
        "reply": rep,
        "used_agents": agent_result.get("used_agents", False),
        "risk_level": agent_result.get("risk_level", "unknown"),
        "response_type": agent_result.get("response_type", "supportive"),
        "technique_used": agent_result.get("technique_used", "validation"),
        "wellness": agent_result.get("wellness", {}),
        "referral": agent_result.get("referral", {}),
        "agents": agent_result.get("agents", {}),
    })


@app.route("/api/hand_reset", methods=["POST"])
@login_required
def hand_reset():
    session["hand_sentence"] = ""
    session["hand_last_pred"] = None
    session["hand_pred_count"] = 0

    return jsonify({
        "ok": True,
        "success": True,
        "sentence": "",
        "message": "Hand sentence reset.",
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — DASHBOARD DATA
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/dashboard_data")
@login_required
def dashboard_data():
    k = ukey()
    d = store[k]

    efreq: dict = defaultdict(int)
    for e in d["emotion_log"]:
        efreq[e["emotion"]] += 1

    last7     = [
        (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        for i in range(6, -1, -1)
    ]
    last7_fmt = [
        datetime.datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b")
        for iso in last7
    ]
    dcounts = [
        sum(len(s["messages"]) for s in d["sessions"] if s["date"] == day)
        for day in last7
    ]
    mood_tl = []
    for day in last7:
        emos = [
            e
            for s in d["sessions"] if s["date"] == day
            for e in s["emotions"]
        ]
        mood_tl.append(
            round(sum(MOOD_SCORE.get(e, 5) for e in emos) / len(emos), 1)
            if emos else None
        )

    valid_m     = [v for v in mood_tl if v is not None]
    avg_mood    = round(sum(valid_m) / len(valid_m), 2) if valid_m else 5.0
    top_emotion = max(efreq, key=efreq.get) if efreq else "neutral"

    return jsonify({
        "emotion_freq":   dict(efreq),
        "daily_labels":   last7_fmt,
        "daily_counts":   dcounts,
        "mood_timeline":  mood_tl,
        "avg_mood":       avg_mood,
        "top_emotion":    top_emotion,
        "total_messages": d["message_count"],
        "total_sessions": len(d["sessions"]),
        "streak":         len(d["streak_days"]),
    })




# ══════════════════════════════════════════════════════════════════════════════
#  API — WELLBEING CHECK-IN
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/wellbeing_checkin", methods=["POST"])
@login_required
def wellbeing_checkin_api():
    """
    Save the Mental & Social Wellbeing Check-In from /mode.

    Updated strict version:
    - backend recalculates score/risk
    - does not trust frontend score blindly
    - returns safe suggestions
    - saves only normalized check-in data
    """
    data = request.get_json(silent=True) or {}

    k = ukey()
    d = store[k]
    d.setdefault("wellbeing_checkins", [])

    try:
        if WELLBEING_UTILS_AVAILABLE and build_checkin_response:
            result = build_checkin_response(data)
            entry = result["checkin"]
        else:
            # Fallback if utils file is missing. Keeps app running.
            entry = {
                "mood": data.get("mood") or "neutral",
                "stress": int(data.get("stress") or 3),
                "social_connection": int(data.get("social_connection") or 3),
                "sleep": data.get("sleep") or "okay",
                "concerns": data.get("concerns", []),
                "emotional_safety": int(data.get("emotional_safety") or 3),
                "support_available": data.get("support_available") or "maybe",
                "current_thoughts": data.get("current_thoughts", ""),
                "created_at": data.get("created_at") or datetime.datetime.utcnow().isoformat(),
                "wellbeing_score": data.get("wellbeing_score", 50),
                "risk_level": data.get("risk_level", "medium"),
            }
            result = {
                "ok": True,
                "checkin": entry,
                "wellbeing_score": entry.get("wellbeing_score"),
                "risk_level": entry.get("risk_level"),
                "suggestions": [],
                "summary": {},
                "disclaimer": "This is not a diagnosis. It is a supportive wellbeing indicator.",
            }

        entry["id"] = str(uuid.uuid4())
        entry["saved_at"] = datetime.datetime.now().isoformat()

        # Best-effort Supabase save. Keeps local JSON working if Supabase is unavailable.
        supabase_row = _save_wellbeing_checkin_to_supabase(entry)

        if supabase_row and isinstance(supabase_row, dict):
            result["supabase_saved"] = True
            result["supabase_id"] = supabase_row.get("id")
            result["checkin"]["supabase_id"] = supabase_row.get("id")
        else:
            result["supabase_saved"] = False

        d["wellbeing_checkins"].append(entry)
        d["wellbeing_checkins"] = d["wellbeing_checkins"][-20:]

        # Keep AI sentiment aligned with check-in mood when available.
        if entry.get("mood"):
            session["sentiment"] = str(entry["mood"])

        _save_store()

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.route("/api/wellbeing_checkins", methods=["GET"])
@login_required
def wellbeing_checkins_api():
    """Return saved wellbeing check-ins for the current user."""
    k = ukey()
    checkins = store[k].get("wellbeing_checkins", [])

    trend = {}
    if WELLBEING_UTILS_AVAILABLE and summarize_wellbeing_trend:
        try:
            trend = summarize_wellbeing_trend(checkins)
        except Exception as e:
            print(f"⚠️  Wellbeing trend failed: {e}")

    return jsonify({
        "ok": True,
        "checkins": list(reversed(checkins)),
        "trend": trend,
    })


@app.route("/api/professional_help", methods=["POST"])
@login_required
def professional_help_api():
    """
    Professional support guidance OUTSIDE NeuroSense AI.

    This endpoint does not diagnose or prescribe.
    It maps the user's latest check-in/message to safe referral guidance:
    counsellor, psychologist, psychiatrist, or crisis helpline.
    """
    if not PROFESSIONAL_HELP_AVAILABLE or recommend_professional_help is None:
        return jsonify({
            "ok": False,
            "error": "Professional help utility is not available. Make sure utils/professional_help.py exists.",
        }), 503

    data = request.get_json(silent=True) or {}

    k = ukey()
    latest_checkin = (
        store[k].get("wellbeing_checkins", [])[-1]
        if store[k].get("wellbeing_checkins")
        else {}
    )

    checkin = data.get("checkin") or latest_checkin
    message = data.get("message") or ""
    emotion = data.get("emotion") or session.get("sentiment", "neutral")
    safety = data.get("safety") or {}

    try:
        result = recommend_professional_help(
            checkin=checkin,
            message=message,
            emotion=emotion,
            safety=safety,
        )

        supabase_log = _save_professional_help_to_supabase(result, checkin=checkin)

        if supabase_log and isinstance(supabase_log, dict):
            result["supabase_saved"] = True
            result["supabase_log_id"] = supabase_log.get("id")
        else:
            result["supabase_saved"] = False

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  API — RESEARCH CHAT + TEMPLATE ENGINE + OLLAMA
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/ollama/status")
@login_required
def ollama_status_api():
    """Check local Ollama availability and installed models."""
    if not RESEARCH_ENGINE_AVAILABLE or ollama_status is None:
        return jsonify({
            "ok": False,
            "available": False,
            "error": "Research engine is not available. Check utils/ollama_client.py and template files.",
        }), 503

    try:
        status = ollama_status()
        return jsonify({
            "ok": True,
            **status,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "available": False,
            "error": str(e),
        }), 500


@app.route("/api/templates", methods=["GET"])
@login_required
def list_templates_api():
    """Return prebuilt + custom mental-health templates from local store and Supabase."""
    if not RESEARCH_ENGINE_AVAILABLE or list_prebuilt_templates is None:
        return jsonify({
            "ok": False,
            "error": "Template engine is not available.",
        }), 503

    try:
        user_id = _research_user_id()
        prebuilt = list_prebuilt_templates()
        local_custom = list_custom_templates(user_id=user_id) if list_custom_templates else []
        supabase_custom = _load_custom_templates_from_supabase()

        # Merge custom templates by app id/template_key. Supabase rows win so db metadata is preserved.
        custom_map = {}
        for item in local_custom:
            custom_map[item.get("id")] = item
        for item in supabase_custom:
            custom_map[item.get("id")] = item

        custom = list(custom_map.values())

        return jsonify({
            "ok": True,
            "prebuilt": prebuilt,
            "custom": custom,
            "templates": prebuilt + custom,
            "summary": template_summary() if template_summary else {},
            "categories": TEMPLATE_CATEGORIES,
            "output_types": OUTPUT_TYPES,
            "supabase_enabled": _supabase_can_write(),
            "supabase_custom_count": len(supabase_custom),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.route("/api/templates", methods=["POST"])
@login_required
def create_template_api():
    """Create a custom safe support template and save it locally + Supabase."""
    if not RESEARCH_ENGINE_AVAILABLE or create_custom_template is None:
        return jsonify({
            "ok": False,
            "error": "Template creation is not available.",
        }), 503

    data = request.get_json(silent=True) or {}

    try:
        template = create_custom_template(
            payload=data,
            user_id=_research_user_id(),
        )

        supabase_row = _save_template_to_supabase(template)

        return jsonify({
            "ok": True,
            "template": template,
            "message": "Template created successfully.",
            "supabase_saved": bool(supabase_row),
            "supabase_id": supabase_row.get("id") if isinstance(supabase_row, dict) else None,
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 400


@app.route("/api/templates/<template_id>", methods=["DELETE"])
@login_required
def delete_template_api(template_id):
    """Delete user's custom template locally and soft-delete it in Supabase."""
    if not RESEARCH_ENGINE_AVAILABLE or delete_custom_template is None:
        return jsonify({
            "ok": False,
            "error": "Template deletion is not available.",
        }), 503

    try:
        deleted_local = delete_custom_template(
            template_id=template_id,
            user_id=_research_user_id(),
        )
        deleted_supabase = _delete_template_from_supabase(template_id)
        deleted = bool(deleted_local or deleted_supabase)

        return jsonify({
            "ok": deleted,
            "deleted": deleted,
            "local_deleted": bool(deleted_local),
            "supabase_deleted": bool(deleted_supabase),
            "message": "Template deleted." if deleted else "Template not found or not owned by user.",
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.route("/api/research_chat/history", methods=["GET"])
@login_required
def research_chat_history_api():
    """Return research chat history. Prefer Supabase when available, fallback to local JSON."""
    try:
        if _supabase_can_write():
            history = _load_research_history_from_supabase(limit=50)
        else:
            history = list(reversed(_get_research_history(limit=50)))

        return jsonify({
            "ok": True,
            "history": history,
            "source": "supabase" if _supabase_can_write() else "local_json",
        })
    except Exception as e:
        print(f"⚠️  Supabase history load failed, using local JSON: {e}")
        return jsonify({
            "ok": True,
            "history": list(reversed(_get_research_history(limit=50))),
            "source": "local_json_fallback",
        })


@app.route("/api/research_chat/history", methods=["DELETE"])
@login_required
def clear_research_chat_history_api():
    """Clear saved research chat history locally and in Supabase."""
    data = _load_research_history()
    user_id = _research_user_id()
    data[user_id] = []
    _save_research_history(data)

    supabase_deleted = _clear_research_history_from_supabase()

    return jsonify({
        "ok": True,
        "message": "Research chat history cleared.",
        "supabase_deleted": bool(supabase_deleted),
    })


@app.route("/api/research_chat", methods=["POST"])
@login_required
def research_chat_api():
    """
    Research Chat endpoint.

    Flow:
    - SafetyAgent checks risk
    - TemplateAgent chooses a mental-health template
    - Professional help utility prepares outside support guidance
    - ResearchAgent generates structured answer using local Ollama
    - HallucinationAgent validates final answer when available
    """
    if not RESEARCH_ENGINE_AVAILABLE or ResearchAgent is None or TemplateAgent is None:
        return jsonify({
            "ok": False,
            "error": "Research engine is not available. Make sure Ollama/template/research agent files exist.",
        }), 503

    blocked = _quota_response_if_blocked(kind="research_chat")
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    query = str(data.get("query") or data.get("message") or "").strip()
    requested_template_id = data.get("template_id") or ""
    source = data.get("source") or "research_chat"

    if not query:
        return jsonify({
            "ok": False,
            "error": "Research query is required.",
        }), 400

    if len(query) > 4000:
        return jsonify({
            "ok": False,
            "error": "Research query is too long. Please keep it under 4000 characters.",
        }), 400

    latest_checkin = data.get("wellbeing_data") or _latest_checkin_for_research()
    emotion = data.get("emotion") or session.get("sentiment", "neutral")
    history = _research_chat_context(limit=8)

    try:
        # 1. Safety classification
        if SafetyAgent:
            safety = SafetyAgent().run(
                user_message=query,
                emotion=emotion,
                wellbeing_data=latest_checkin,
                history=history,
            )
        else:
            safety = {
                "risk_level": "none",
                "self_harm": False,
                "allow_normal_response": True,
                "reason": "SafetyAgent unavailable; fallback used.",
            }

        # Crisis response should not go to research generation.
        if safety.get("risk_level") == "crisis":
            answer = (
                "I’m really sorry you’re feeling this much pain. Your safety matters most right now. "
                "Please contact someone you trust immediately and reach out to a crisis helpline: "
                "Tele MANAS 14416 or 1800-891-4416, iCALL 9152987821, or Vandrevala Foundation +91 9999 666 555. "
                "If you are in immediate danger, call local emergency services now."
            )

            entry = {
                "id": str(uuid.uuid4()),
                "query": query,
                "answer": answer,
                "template_id": requested_template_id,
                "template_title": "Crisis Safety",
                "model": "safety_fallback",
                "risk_level": "crisis",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
            _append_research_history(entry)
            supabase_history_row = _save_research_history_to_supabase(
                entry,
                safety=safety,
                professional_help={},
                agent_trace={"source": source, "crisis_fallback": True},
            )

            return jsonify({
                "ok": True,
                "answer": answer,
                "risk_level": "crisis",
                "template": {"id": requested_template_id, "title": "Crisis Safety"},
                "used_ollama": False,
                "safety": safety,
                "history_item": entry,
                "supabase_saved": bool(supabase_history_row),
                "supabase_history_id": supabase_history_row.get("id") if isinstance(supabase_history_row, dict) else None,
            })

        # 2. Template selection
        template_selection = TemplateAgent().select_template(
            query=query,
            user_id=_research_user_id(),
            requested_template_id=requested_template_id,
            wellbeing_data=latest_checkin,
        )
        selected_template = template_selection.get("template") or {}

        # If an explicit custom template exists only in Supabase, use it.
        if requested_template_id and (not selected_template or not selected_template.get("id")):
            for item in _load_custom_templates_from_supabase():
                if item.get("id") == requested_template_id:
                    selected_template = item
                    template_selection = {"ok": True, "template": item, "selection_method": "supabase_explicit"}
                    break

        # 3. Professional support guidance
        professional_help = {}
        if PROFESSIONAL_HELP_AVAILABLE and recommend_professional_help:
            try:
                professional_help = recommend_professional_help(
                    checkin=latest_checkin,
                    message=query,
                    emotion=emotion,
                    safety=safety,
                )
            except Exception as e:
                print(f"⚠️  Research professional help guidance failed: {e}")

        # 4. Research generation through Ollama
        research_result = ResearchAgent().run(
            query=query,
            wellbeing_data=latest_checkin,
            emotion=emotion,
            template=selected_template,
            history=history,
            safety=safety,
            professional_help=professional_help,
        )

        draft_answer = research_result.get("answer") or _safe_research_fallback(query)

        # 5. Hallucination/safety validation
        hallucination_check = {
            "safe": True,
            "issues": [],
            "corrected_reply": draft_answer,
        }

        if HallucinationAgent:
            try:
                hallucination_check = HallucinationAgent().run(
                    user_message=query,
                    draft_reply=draft_answer,
                    safety=safety,
                    emotion_analysis={
                        "dominant_emotion": emotion,
                        "source": "research_chat",
                    },
                    social_analysis={},
                    wellness={},
                    referral=professional_help,
                    wellbeing_data=latest_checkin,
                )
            except Exception as e:
                print(f"⚠️  Research hallucination check failed: {e}")

        final_answer = (
            hallucination_check.get("corrected_reply")
            if not hallucination_check.get("safe", True)
            else draft_answer
        )

        if not final_answer:
            final_answer = _safe_research_fallback(query)

        # 6. Save local research history
        entry = {
            "id": str(uuid.uuid4()),
            "query": query,
            "answer": final_answer,
            "template_id": selected_template.get("id"),
            "template_supabase_id": selected_template.get("supabase_id") or selected_template.get("db_id"),
            "template_title": selected_template.get("title"),
            "template_category": selected_template.get("category"),
            "source": source,
            "selection_method": template_selection.get("selection_method"),
            "model": research_result.get("model"),
            "used_ollama": research_result.get("used_ollama", False),
            "risk_level": safety.get("risk_level", "none"),
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        _append_research_history(entry)

        supabase_history_row = _save_research_history_to_supabase(
            entry,
            safety=safety,
            professional_help=professional_help,
            agent_trace={
                "source": source,
                "template_selection": template_selection,
                "hallucination_check": hallucination_check,
            },
        )

        supabase_template_log = None
        if source == "template_run" or requested_template_id:
            supabase_template_log = _save_template_run_to_supabase(
                entry,
                selected_template=selected_template,
                safety=safety,
            )
            _increment_template_usage_supabase(selected_template)

        # Optional usage increment
        if session.get("supabase_user_id"):
            try:
                increment_usage(session["supabase_user_id"], field="monthly_messages", amount=1)
            except Exception:
                pass

        return jsonify({
            "ok": True,
            "answer": final_answer,
            "risk_level": safety.get("risk_level", "none"),
            "template": selected_template,
            "template_selection": template_selection,
            "professional_help": professional_help,
            "safety": safety,
            "hallucination_check": hallucination_check,
            "model": research_result.get("model"),
            "used_ollama": research_result.get("used_ollama", False),
            "history_item": entry,
            "supabase_saved": bool(supabase_history_row),
            "supabase_history_id": supabase_history_row.get("id") if isinstance(supabase_history_row, dict) else None,
            "template_run_saved": bool(supabase_template_log),
            "template_run_id": supabase_template_log.get("id") if isinstance(supabase_template_log, dict) else None,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.route("/api/templates/run", methods=["POST"])
@login_required
def run_template_api():
    """Run a selected prebuilt/custom template through Research Chat."""
    data = request.get_json(silent=True) or {}
    template_id = data.get("template_id") or ""
    message = str(data.get("message") or data.get("query") or "").strip()

    if not template_id:
        return jsonify({
            "ok": False,
            "error": "template_id is required.",
        }), 400

    if not message:
        message = "Run this template using my latest wellbeing check-in context."

    # Reuse the same research logic by constructing the payload directly.
    current_session = dict(session)

    with app.test_request_context(
        "/api/research_chat",
        method="POST",
        json={
            "query": message,
            "template_id": template_id,
            "source": "template_run",
            "wellbeing_data": data.get("wellbeing_data") or _latest_checkin_for_research(),
            "emotion": data.get("emotion") or session.get("sentiment", "neutral"),
        },
    ):
        # Preserve the real logged-in Flask session inside this internal call.
        for key, value in current_session.items():
            session[key] = value
        return research_chat_api()




# ══════════════════════════════════════════════════════════════════════════════
#  API — KNOWLEDGE CHAT (MENTAL-HEALTH SCOPED, GROUNDED)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/knowledge/status")
@login_required
def knowledge_status_api():
    """Knowledge Chat health endpoint."""
    retriever = kb_retriever_status() if KNOWLEDGE_ENGINE_AVAILABLE and kb_retriever_status else {}
    store_status = knowledge_store_status() if KNOWLEDGE_ENGINE_AVAILABLE and knowledge_store_status else {}

    return jsonify({
        "ok": True,
        "knowledge_engine_available": KNOWLEDGE_ENGINE_AVAILABLE,
        "retriever": retriever,
        "store": store_status,
        "scope": [
            "stress",
            "anxiety-like feelings",
            "sleep",
            "loneliness",
            "academic pressure",
            "relationship stress",
            "self-doubt",
            "anger regulation",
            "mood tracking",
            "professional help guidance",
            "crisis safety",
            "NeuroSense AI app usage",
        ],
        "guardrails": [
            "mental-health scope only",
            "retrieval-grounded answers",
            "no diagnosis",
            "no medication prescription",
            "no psychiatrist impersonation",
            "crisis escalation",
            "hallucination checking",
        ],
    })


@app.route("/api/knowledge_chat/history", methods=["GET"])
@login_required
def knowledge_chat_history_api():
    """Return Knowledge Chat history."""
    try:
        return jsonify({
            "ok": True,
            "history": _knowledge_history(limit=50),
            "source": "local_json",
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/knowledge_chat/history", methods=["DELETE"])
@login_required
def clear_knowledge_chat_history_api():
    """Clear Knowledge Chat history."""
    cleared = _clear_knowledge_history()
    return jsonify({
        "ok": True,
        "cleared": bool(cleared),
        "message": "Knowledge chat history cleared.",
    })




def _extract_uploaded_report_text(file_storage) -> dict:
    """
    Extract text from uploaded report files for Knowledge Chat context.

    Supports:
    - .txt
    - .csv
    - .json
    - .pdf if pypdf or PyPDF2 is installed

    The extracted text is used only as user-provided mental-health report context.
    """

    if not file_storage or not file_storage.filename:
        raise ValueError("No file uploaded.")

    filename = file_storage.filename
    ext = os.path.splitext(filename.lower())[1]
    raw = file_storage.read()

    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("File too large. Maximum allowed size is 5MB.")

    text = ""

    if ext in [".txt", ".csv"]:
        text = raw.decode("utf-8", errors="ignore")

    elif ext == ".json":
        try:
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            text = json.dumps(obj, indent=2, ensure_ascii=False)
        except Exception:
            text = raw.decode("utf-8", errors="ignore")

    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw))
            pages = []
            for page in reader.pages[:8]:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages)
        except Exception:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                pages = []
                for page in reader.pages[:8]:
                    pages.append(page.extract_text() or "")
                text = "\n".join(pages)
            except Exception:
                raise ValueError("PDF reading needs pypdf or PyPDF2. Install with: pip install pypdf")

    else:
        raise ValueError("Unsupported file type. Use PDF, CSV, TXT, or JSON.")

    text = str(text or "").strip()

    if not text:
        raise ValueError("Could not extract readable text from this file.")

    text = text[:12000]
    lowered = text.lower()

    mental_keywords = [
        "mental", "wellness", "wellbeing", "mood", "emotion", "stress",
        "anxiety", "sleep", "loneliness", "support", "assessment", "solution",
        "practice", "grounding", "professional", "risk", "session", "neurosense",
        "report", "therapy", "counsellor", "psychologist", "psychiatrist",
    ]

    if not any(word in lowered for word in mental_keywords):
        raise ValueError("This file does not look related to mental wellness or NeuroSense AI reports.")

    summary = text[:900].replace("\n", " ")

    return {
        "filename": filename,
        "extension": ext,
        "extracted_text": text,
        "summary": summary,
        "char_count": len(text),
    }


@app.route("/api/knowledge_chat/upload_report", methods=["POST"])
@login_required
def knowledge_chat_upload_report_api():
    """
    Upload report context for Knowledge Chat.

    Expected form data:
    - file
    - report_type = assessment | solution

    The UI uploads:
    1. Mental Wellness Assessment
    2. Personalized Wellness Plan
    """

    report_type = str(request.form.get("report_type", "")).lower().strip()

    if report_type not in ["assessment", "solution"]:
        return jsonify({"ok": False, "error": "report_type must be assessment or solution."}), 400

    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Missing file."}), 400

    try:
        extracted = _extract_uploaded_report_text(request.files["file"])
        extracted["report_type"] = report_type
        extracted["ok"] = True
        return jsonify(extracted)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/knowledge_chat", methods=["POST"])
@login_required
def knowledge_chat_api():
    """
    Knowledge Chat API.

    Mental-health-only grounded chat:
    - Allows greetings/small talk.
    - Blocks unrelated topics.
    - Uses ScopeGuardAgent if available.
    - Uses KnowledgeAgent if available.
    - Falls back safely if any module is unavailable.
    - Can use uploaded report context from frontend.
    """

    body = request.get_json(silent=True) or {}

    question = (
        body.get("query")
        or body.get("question")
        or body.get("message")
        or ""
    ).strip()

    report_context = body.get("report_context", {}) or {}

    if not question:
        return jsonify({
            "ok": False,
            "error": "Question is required.",
        }), 400

    if len(question) > 3000:
        return jsonify({
            "ok": False,
            "error": "Question is too long. Please keep it under 3000 characters.",
        }), 400

    blocked = _quota_response_if_blocked(kind="knowledge")
    if blocked:
        return blocked

    latest_checkin = body.get("wellbeing_data") or _latest_checkin_for_research()
    emotion = body.get("emotion") or session.get("sentiment", "neutral")
    history = _knowledge_context_for_agent(limit=8)

    # 1. Scope guard
    try:
        if ScopeGuardAgent:
            scope_agent = ScopeGuardAgent()

            try:
                scope = scope_agent.run(
                    question=question,
                    wellbeing_data=latest_checkin,
                    emotion=emotion,
                )
            except TypeError:
                if hasattr(scope_agent, "run"):
                    scope = scope_agent.run(question)
                else:
                    scope = scope_agent.analyze(question)
        else:
            scope = _fallback_scope_check(question)

    except Exception as e:
        print(f"⚠️ Knowledge scope guard failed: {e}")
        scope = _fallback_scope_check(question)

    # 1.1 Fallback override for real-life wellbeing questions.
    # Some older ScopeGuardAgent versions block questions like
    # "I am not feeling well mentally; should I take leave or go for a trip?".
    # This override keeps the mental-health scope strict, but allows such
    # wellbeing-related life-decision questions when fallback detects them.
    try:
        fallback_scope = _fallback_scope_check(question)
        if (
            not scope.get("allowed", False)
            and fallback_scope.get("allowed", False)
            and fallback_scope.get("scope") in ["mental_health", "safe_smalltalk", "professional_help", "crisis_safety"]
        ):
            print("ℹ️ Knowledge scope overridden by fallback wellbeing scope check.")
            scope = fallback_scope
    except Exception as e:
        print(f"⚠️ Knowledge fallback scope override failed: {e}")

    # 1.5 Safe small talk before RAG blocking.
    smalltalk_answer = _knowledge_smalltalk_reply(question)

    if smalltalk_answer:
        entry = {
            "id": str(uuid.uuid4()),
            "question": question,
            "query": question,
            "answer": smalltalk_answer,
            "scope": {
                "allowed": True,
                "scope": "safe_smalltalk",
                "risk_level": "none",
                "response_type": "smalltalk",
                "reason": "Safe Knowledge Chat greeting/small-talk.",
            },
            "risk_level": "none",
            "model": "smalltalk_rule",
            "sources": [
                {
                    "id": "safe_smalltalk",
                    "title": "Safe Knowledge Chat Interaction",
                }
            ],
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        _append_knowledge_history(entry)

        return jsonify({
            "ok": True,
            "answer": smalltalk_answer,
            "allowed": True,
            "scope": entry["scope"],
            "risk_level": "none",
            "sources": entry["sources"],
            "source_count": 1,
            "model": "smalltalk_rule",
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "history_item": entry,
        })

    # 2. Crisis handling
    if scope.get("risk_level") == "crisis" or scope.get("response_type") == "crisis":
        answer = _knowledge_crisis_reply()

        entry = {
            "id": str(uuid.uuid4()),
            "question": question,
            "query": question,
            "answer": answer,
            "scope": scope,
            "risk_level": "crisis",
            "model": "safety_rule",
            "sources": [
                {
                    "id": "crisis_safety",
                    "title": "Crisis Safety",
                }
            ],
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        _append_knowledge_history(entry)

        return jsonify({
            "ok": True,
            "answer": answer,
            "allowed": True,
            "scope": scope,
            "risk_level": "crisis",
            "sources": entry["sources"],
            "source_count": 1,
            "model": "safety_rule",
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "history_item": entry,
        })

    # 3. Block unrelated/out-of-scope questions
    if not scope.get("allowed", False):
        answer = _knowledge_out_of_scope_reply()

        entry = {
            "id": str(uuid.uuid4()),
            "question": question,
            "query": question,
            "answer": answer,
            "scope": scope,
            "risk_level": scope.get("risk_level", "blocked"),
            "model": "scope_guard",
            "sources": [],
            "used_model": False,
            "used_ollama": False,
            "grounded": False,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        _append_knowledge_history(entry)

        return jsonify({
            "ok": True,
            "answer": answer,
            "allowed": False,
            "scope": scope,
            "risk_level": scope.get("risk_level", "blocked"),
            "sources": [],
            "source_count": 0,
            "model": "scope_guard",
            "used_model": False,
            "used_ollama": False,
            "grounded": False,
            "history_item": entry,
        })

    # 4. Safety check
    try:
        if SafetyAgent:
            safety = SafetyAgent().run(
                user_message=question,
                emotion=emotion,
                wellbeing_data=latest_checkin,
                history=history,
            )
        else:
            safety = {
                "risk_level": scope.get("risk_level", "none"),
                "allow_normal_response": scope.get("risk_level") != "crisis",
                "reason": "Fallback safety classification.",
            }
    except Exception as e:
        print(f"⚠️ Knowledge safety check failed: {e}")
        safety = {
            "risk_level": scope.get("risk_level", "none"),
            "allow_normal_response": scope.get("risk_level") != "crisis",
            "reason": "Fallback safety classification after SafetyAgent error.",
        }

    if safety.get("risk_level") == "crisis":
        answer = _knowledge_crisis_reply()

        entry = {
            "id": str(uuid.uuid4()),
            "question": question,
            "query": question,
            "answer": answer,
            "scope": scope,
            "safety": safety,
            "risk_level": "crisis",
            "model": "safety_rule",
            "sources": [{"id": "crisis_safety", "title": "Crisis Safety"}],
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        _append_knowledge_history(entry)

        return jsonify({
            "ok": True,
            "answer": answer,
            "allowed": True,
            "scope": scope,
            "safety": safety,
            "risk_level": "crisis",
            "sources": entry["sources"],
            "source_count": 1,
            "model": "safety_rule",
            "used_model": False,
            "used_ollama": False,
            "grounded": True,
            "history_item": entry,
        })

    # 5. Build uploaded report context safely
    assessment_context = ""
    solution_context = ""

    try:
        if isinstance(report_context, dict):
            if report_context.get("assessment"):
                assessment_context = str(
                    report_context["assessment"].get("extracted_text", "")
                )[:6000]

            if report_context.get("solution"):
                solution_context = str(
                    report_context["solution"].get("extracted_text", "")
                )[:6000]
    except Exception as e:
        print(f"⚠️ Report context parse failed: {e}")

    context_note = ""

    if assessment_context or solution_context:
        context_note = f"""

UPLOADED REPORT CONTEXT:
The following report context is user-provided and must be used only for mental-health/wellness support.

1. Mental Wellness Assessment:
{assessment_context or "Not provided"}

2. Personalized Wellness Plan:
{solution_context or "Not provided"}

Important:
- Do not diagnose.
- Do not prescribe medication.
- Use this context only for mental-health support.
- If report data is insufficient, say so clearly.
"""

    query_for_agent = f"{question}\n\n{context_note}" if context_note else question

    # 6. Retrieve approved KB snippets if retriever is available.
    sources = []
    try:
        if retrieve_knowledge:
            try:
                retrieved = retrieve_knowledge(
                    question,
                    top_k=int(body.get("top_k") or 5),
                    scope=scope.get("scope") or "mental_health",
                )
            except TypeError:
                retrieved = retrieve_knowledge(
                    question,
                    top_k=int(body.get("top_k") or 5),
                )

            if isinstance(retrieved, dict):
                sources = retrieved.get("sources", []) or retrieved.get("items", []) or []
            else:
                sources = retrieved or []
    except Exception as e:
        print(f"⚠️ Knowledge retrieval failed: {e}")
        sources = []

    # 7. Professional help guidance when relevant.
    professional_help = {}
    if PROFESSIONAL_HELP_AVAILABLE and recommend_professional_help:
        try:
            professional_help = recommend_professional_help(
                checkin=latest_checkin,
                message=question,
                emotion=emotion,
                safety=safety,
            )
        except Exception as e:
            print(f"⚠️ Knowledge professional help guidance failed: {e}")

    # 8. Generate grounded answer.
    try:
        if KNOWLEDGE_ENGINE_AVAILABLE and KnowledgeAgent:
            try:
                result = KnowledgeAgent().run(
                    question=query_for_agent,
                    sources=sources,
                    scope=scope,
                    safety=safety,
                    wellbeing_data=latest_checkin,
                    emotion=emotion,
                    history=history,
                    professional_help=professional_help,
                    report_context=report_context,
                )
            except TypeError:
                result = KnowledgeAgent().run(
                    query=query_for_agent,
                    scope_result=scope,
                )
        else:
            result = {
                "answer": (
                    "Knowledge Chat engine is not fully available right now. "
                    "I can still help with NeuroSense AI and mental-health topics, but please restart the app "
                    "after checking knowledge agent imports."
                ),
                "sources": sources,
                "model": "fallback",
                "used_ollama": False,
                "used_model": False,
                "grounded": bool(sources),
            }

        draft_answer = (
            result.get("answer") if isinstance(result, dict) else str(result or "")
        ) or (
            "I found relevant approved knowledge, but could not generate a complete answer. "
            "Please try asking again in a simpler way."
        )

    except Exception as e:
        print(f"❌ KnowledgeAgent failed: {e}")
        traceback.print_exc()
        result = {
            "model": "error_fallback",
            "used_model": False,
            "used_ollama": False,
            "grounded": False,
        }
        draft_answer = (
            "I could not generate a grounded answer right now. "
            "Please try again, or ask a simpler question about stress, sleep, mood, reports, or professional help."
        )

    # 9. Hallucination/safety validation.
    hallucination_check = {
        "safe": True,
        "issues": [],
        "corrected_reply": draft_answer,
    }

    if HallucinationAgent:
        try:
            hallucination_check = HallucinationAgent().run(
                user_message=question,
                draft_reply=draft_answer,
                safety=safety,
                emotion_analysis={
                    "dominant_emotion": emotion,
                    "source": "knowledge_chat",
                },
                social_analysis={},
                wellness={},
                referral=professional_help,
                wellbeing_data=latest_checkin,
            )
        except Exception as e:
            print(f"⚠️ Knowledge hallucination check failed: {e}")

    final_answer = (
        hallucination_check.get("corrected_reply")
        if not hallucination_check.get("safe", True)
        else draft_answer
    ) or draft_answer

    final_sources = sources
    if isinstance(result, dict) and result.get("sources"):
        final_sources = result.get("sources")

    used_model = bool(
        result.get("used_model", result.get("used_ollama", False))
    ) if isinstance(result, dict) else False

    used_ollama = bool(
        result.get("used_ollama", used_model)
    ) if isinstance(result, dict) else False

    model = (
        result.get("model") if isinstance(result, dict) else "knowledge_agent"
    ) or "knowledge_agent"

    grounded = bool(
        (result.get("grounded") if isinstance(result, dict) else False)
        or final_sources
        or assessment_context
        or solution_context
    )

    # 10. Save usage
    if session.get("supabase_user_id"):
        try:
            increment_usage(session["supabase_user_id"], field="knowledge_queries", amount=1)
        except Exception as e:
            print(f"⚠️ Knowledge usage increment failed: {e}")

    # 11. Save history
    entry = {
        "id": str(uuid.uuid4()),
        "question": question,
        "query": question,
        "answer": final_answer,
        "scope": scope,
        "safety": safety,
        "risk_level": safety.get("risk_level", scope.get("risk_level", "none")),
        "model": model,
        "sources": final_sources,
        "source_count": len(final_sources),
        "used_model": used_model,
        "used_ollama": used_ollama,
        "grounded": grounded,
        "report_context": {
            "assessment_uploaded": bool(assessment_context),
            "solution_uploaded": bool(solution_context),
        },
        "hallucination_check": hallucination_check,
        "professional_help": professional_help,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }

    _append_knowledge_history(entry)

    return jsonify({
        "ok": True,
        "answer": final_answer,
        "allowed": True,
        "scope": scope,
        "safety": safety,
        "risk_level": entry["risk_level"],
        "sources": final_sources,
        "source_count": len(final_sources),
        "professional_help": professional_help,
        "hallucination_check": hallucination_check,
        "model": model,
        "used_model": used_model,
        "used_ollama": used_ollama,
        "grounded": grounded,
        "history_item": entry,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — AGENT STATUS / DEBUG TRACE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/agents/status")
@login_required
def agents_status_api():
    """Simple health endpoint to verify multi-agent pipeline is loaded."""
    return jsonify({
        "ok": True,
        "agents_available": AGENTS_AVAILABLE,
        "wellbeing_utils_available": WELLBEING_UTILS_AVAILABLE,
        "professional_help_available": PROFESSIONAL_HELP_AVAILABLE,
        "research_engine_available": RESEARCH_ENGINE_AVAILABLE,
        "knowledge_engine_available": KNOWLEDGE_ENGINE_AVAILABLE,
        "knowledge": (kb_retriever_status() if KNOWLEDGE_ENGINE_AVAILABLE and kb_retriever_status else {"available": False}),
        "ollama": (ollama_status() if RESEARCH_ENGINE_AVAILABLE and ollama_status else {"available": False}),
        "template_summary": (template_summary() if RESEARCH_ENGINE_AVAILABLE and template_summary else {}),
        "supabase_research_tables": {
            "enabled": _supabase_can_write(),
            "mental_health_templates": True,
            "research_chat_history": True,
            "template_run_logs": True,
        },
        "knowledge_chat": {
            "enabled": KNOWLEDGE_ENGINE_AVAILABLE,
            "scope_guard": bool(ScopeGuardAgent),
            "knowledge_agent": bool(KnowledgeAgent),
            "retriever": bool(retrieve_knowledge),
        },
        "pipeline": [
            "SafetyAgent",
            "EmotionAgent",
            "SocialAgent",
            "TherapyAgent",
            "WellnessAgent",
            "ClinicalEscalationAgent",
            "HallucinationAgent",
            "TemplateAgent",
            "ResearchAgent (Ollama)",
            "ScopeGuardAgent",
            "KnowledgeAgent (grounded mental-health KB)",
        ],
        "guardrails": [
            "no diagnosis",
            "no medication prescription",
            "no psychiatrist impersonation",
            "crisis escalation",
            "hallucination checking",
            "professional referral guidance",
            "knowledge base grounded answers",
            "out-of-scope refusal",
        ],
    })

# ══════════════════════════════════════════════════════════════════════════════
#  PRINT ALL REGISTERED ROUTES ON STARTUP (for debugging)
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  REAL-TIME ADMIN DASHBOARD HELPERS + ROUTES
# ══════════════════════════════════════════════════════════════════════════════

def _admin_safe_int(value, default=0):
    try:
        return int(value or 0)
    except Exception:
        return default


def _admin_mode_label(mode: str) -> str:
    mode = str(mode or "normal_chat").lower()
    if "voice" in mode:
        return "Voice Chat"
    if "hand" in mode or "sign" in mode:
        return "Sign Chat"
    if "research" in mode:
        return "Research Chat"
    if "knowledge" in mode:
        return "Knowledge Chat"
    if "practice" in mode:
        return "Best Practices"
    return "Text Chat"


def _admin_dt_sort(date_value="", time_value="") -> str:
    return f"{date_value or ''} {time_value or '00:00'}"


def _admin_human_date(date_value: str) -> str:
    try:
        d = datetime.datetime.strptime(str(date_value), "%Y-%m-%d").date()
        today = datetime.date.today()
        if d == today:
            return "Today"
        if d == today - datetime.timedelta(days=1):
            return "Yesterday"
        return d.strftime("%d %b %Y")
    except Exception:
        return "—"


def _admin_avatar_letter(name_or_email: str) -> str:
    text = str(name_or_email or "User").strip()
    return (text[:1] or "U").upper()


def _admin_build_local_users() -> list:
    users = []
    today = datetime.date.today().isoformat()

    try:
        for key, value in store.items():
            sessions = value.get("sessions", []) or []
            reports = value.get("reports", []) or []
            practice_logs = value.get("practice_logs", []) or []
            emotion_log = value.get("emotion_log", []) or []
            crisis_actions = value.get("crisis_actions", []) or []

            last_session = sessions[-1] if sessions else {}
            last_date = last_session.get("date") or ""
            last_time = ""
            if last_session.get("messages"):
                last_time = (last_session.get("messages") or [])[-1].get("time", "")

            name = key.split("@")[0].replace(".", " ").replace("_", " ").title() if key else "User"
            status = "active" if last_date == today else ("warning" if sessions else "inactive")

            users.append({
                "id": key,
                "user_key": key,
                "name": name,
                "email": key,
                "avatar_letter": _admin_avatar_letter(name),
                "role": "Admin" if session.get("email", "").lower() == str(key).lower() else "User",
                "status": status,
                "sessions": len(sessions),
                "messages": _admin_safe_int(value.get("message_count", 0)),
                "reports": len(reports),
                "practices": len(practice_logs),
                "emotions": len(emotion_log),
                "crisis_actions": len(crisis_actions),
                "last_active": _admin_human_date(last_date),
                "sort": _admin_dt_sort(last_date, last_time),
            })
    except Exception as e:
        print(f"⚠️ Admin local users build failed: {e}")

    return sorted(users, key=lambda x: x.get("sort", ""), reverse=True)


def _admin_build_supabase_users() -> list:
    if not SUPABASE_READY or not list_all_profiles:
        return []

    try:
        raw_users = list_all_profiles() or []
    except Exception as e:
        print(f"⚠️ Admin Supabase users failed: {e}")
        return []

    users = []
    for idx, u in enumerate(raw_users):
        if not isinstance(u, dict):
            continue
        name = u.get("full_name") or u.get("name") or u.get("email") or f"User {idx + 1}"
        email = u.get("email") or "—"
        users.append({
            "id": u.get("id") or email,
            "user_key": email or u.get("id") or name,
            "name": name,
            "email": email,
            "avatar_url": u.get("avatar_url") or "",
            "avatar_letter": _admin_avatar_letter(name),
            "role": u.get("role", "User"),
            "status": "active" if u.get("is_active", True) else "inactive",
            "sessions": _admin_safe_int(u.get("sessions", u.get("total_sessions", 0))),
            "messages": _admin_safe_int(u.get("daily_messages", u.get("messages", 0))),
            "reports": _admin_safe_int(u.get("reports_generated", u.get("reports", 0))),
            "practices": _admin_safe_int(u.get("practices", 0)),
            "emotions": _admin_safe_int(u.get("emotion_detections", 0)),
            "crisis_actions": _admin_safe_int(u.get("crisis_actions", 0)),
            "last_active": u.get("last_active") or u.get("updated_at") or "—",
            "sort": u.get("updated_at") or u.get("last_active") or "",
        })
    return users


def _admin_weekly_analytics() -> dict:
    labels = []
    mood_scores = []
    stress_levels = []
    session_counts = []
    message_counts = []

    today = datetime.date.today()
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        iso = day.isoformat()
        labels.append(day.strftime("%a"))

        emotions = []
        msg_count = 0
        session_count = 0

        for value in store.values():
            for s in value.get("sessions", []) or []:
                if s.get("date") == iso:
                    session_count += 1
                    msg_count += len(s.get("messages", []) or [])
                    emotions.extend(s.get("emotions", []) or [])
            for e in value.get("emotion_log", []) or []:
                if str(e.get("ts", "")).startswith(iso):
                    emotions.append(e.get("emotion", "neutral"))

        if emotions:
            scores = [MOOD_SCORE.get(str(e).lower(), 5) for e in emotions]
            mood = round(sum(scores) / len(scores), 1)
            negative = sum(1 for e in emotions if str(e).lower() in ("sad", "angry", "fear", "disgust", "contempt"))
            stress = round(min(10, max(1, (10 - mood) + (negative / max(len(emotions), 1)) * 3)), 1)
        else:
            mood = 5
            stress = 5

        mood_scores.append(mood)
        stress_levels.append(stress)
        session_counts.append(session_count)
        message_counts.append(msg_count)

    return {
        "labels": labels,
        "mood_scores": mood_scores,
        "stress_levels": stress_levels,
        "session_counts": session_counts,
        "message_counts": message_counts,
    }


def _admin_recent_activity(limit: int = 8) -> list:
    activity = []

    for key, value in store.items():
        user_name = key.split("@")[0].replace(".", " ").title() if key else "User"

        for s in value.get("sessions", []) or []:
            msgs = s.get("messages", []) or []
            if not msgs:
                continue
            mode = _admin_mode_label(s.get("mode"))
            last_msg = msgs[-1]
            activity.append({
                "icon": "🎤" if "Voice" in mode else ("🧠" if "Research" in mode else "💬"),
                "title": f"{mode} session activity",
                "subtitle": f"{user_name} • {len(msgs)} messages saved",
                "time": last_msg.get("time") or _admin_human_date(s.get("date")),
                "type": "session",
                "sort": _admin_dt_sort(s.get("date", ""), last_msg.get("time", "")),
            })

        for r in value.get("reports", []) or []:
            generated_at = r.get("generated_at") or r.get("created_at") or r.get("date") or ""
            activity.append({
                "icon": "📄",
                "title": "PDF / wellness report generated",
                "subtitle": f"{user_name} generated a wellness insight report",
                "time": "Recent",
                "type": "report",
                "sort": str(generated_at),
            })

        for p in value.get("practice_logs", []) or []:
            activity.append({
                "icon": "🌱",
                "title": "Best practice completed",
                "subtitle": f"{user_name} completed {p.get('practice', 'a wellness practice')}",
                "time": p.get("time") or _admin_human_date(p.get("date", "")),
                "type": "practice",
                "sort": _admin_dt_sort(p.get("date", ""), p.get("time", "")),
            })

        for c in value.get("crisis_actions", []) or []:
            action = str(c.get("action", "safety action")).replace("_", " ").title()
            activity.append({
                "icon": "🛡️",
                "title": "Crisis / safety action recorded",
                "subtitle": f"{user_name} • {action}",
                "time": c.get("time") or _admin_human_date(c.get("date", "")),
                "type": "safety",
                "sort": _admin_dt_sort(c.get("date", ""), c.get("time", "")),
            })

    if not activity:
        activity.append({
            "icon": "✨",
            "title": "No platform activity yet",
            "subtitle": "Start using chats, reports, practices, or crisis support to see real-time activity here.",
            "time": "Now",
            "type": "empty",
            "sort": datetime.datetime.now().isoformat(),
        })

    return sorted(activity, key=lambda x: x.get("sort", ""), reverse=True)[:limit]



# ══════════════════════════════════════════════════════════════════════════════
#  REAL-TIME PROJECT ACCURACY ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _accuracy_percent(numerator, denominator, fallback=0):
    try:
        denominator = float(denominator)
        if denominator <= 0:
            return fallback
        return round((float(numerator) / denominator) * 100, 2)
    except Exception:
        return fallback


def _accuracy_avg(values, fallback=0):
    try:
        values = [float(v) for v in values if v is not None]
        if not values:
            return fallback
        return round(sum(values) / len(values), 2)
    except Exception:
        return fallback


def _calculate_realtime_project_accuracy():
    """
    Live NeuroSense AI reliability score.

    This is not fake ML benchmark accuracy. It is a real-time quality score
    calculated from stored app signals: feedback, safety events, emotion
    confidence, report success, and session completion.
    """
    all_users = list(store.values())

    total_sessions = 0
    completed_sessions = 0
    total_reports = 0
    successful_reports = 0
    total_emotions = 0
    emotion_confidence_values = []
    total_feedback = 0
    positive_feedback = 0
    total_safety_events = 0
    unsafe_events = 0
    total_messages = 0

    for user_data in all_users:
        sessions = user_data.get("sessions", []) or []
        reports = user_data.get("reports", []) or []
        emotions = user_data.get("emotion_log", []) or []
        feedback_logs = user_data.get("feedback_logs", []) or []
        crisis_actions = user_data.get("crisis_actions", []) or []

        total_sessions += len(sessions)
        completed_sessions += len([
            s for s in sessions
            if s.get("ended") or len(s.get("messages", []) or []) >= 2
        ])

        total_reports += len(reports)
        successful_reports += len([
            r for r in reports
            if r and not r.get("error") and not r.get("failed")
        ])

        total_emotions += len(emotions)
        for e in emotions:
            conf = e.get("confidence")
            if conf is not None:
                try:
                    conf = float(conf)
                    if conf <= 1:
                        conf = conf * 100
                    emotion_confidence_values.append(conf)
                except Exception:
                    pass

        for s in sessions:
            total_messages += len(s.get("messages", []) or [])

        for f in feedback_logs:
            total_feedback += 1
            value = str(
                f.get("feedback")
                or f.get("label")
                or f.get("rating")
                or f.get("value")
                or ""
            ).lower()
            if value in ["helpful", "positive", "yes", "like", "good", "1", "true"]:
                positive_feedback += 1

        total_safety_events += len(crisis_actions)
        unsafe_events += len([
            c for c in crisis_actions
            if str(c.get("risk", "")).lower() in ["high", "critical", "unsafe"]
        ])

    feedback_score = _accuracy_percent(positive_feedback, total_feedback, fallback=85)
    safety_pass_rate = 100 - _accuracy_percent(unsafe_events, total_safety_events, fallback=0)
    emotion_confidence = _accuracy_avg(emotion_confidence_values, fallback=80 if total_emotions else 75)
    report_success_rate = _accuracy_percent(successful_reports, total_reports, fallback=90)
    session_completion_rate = _accuracy_percent(completed_sessions, total_sessions, fallback=80)

    overall_accuracy = round(
        (feedback_score * 0.30)
        + (safety_pass_rate * 0.25)
        + (emotion_confidence * 0.20)
        + (report_success_rate * 0.15)
        + (session_completion_rate * 0.10),
        2,
    )

    if overall_accuracy >= 90:
        grade = "Excellent"
    elif overall_accuracy >= 80:
        grade = "Very Good"
    elif overall_accuracy >= 70:
        grade = "Good"
    else:
        grade = "Needs Improvement"

    return {
        "overall_accuracy": overall_accuracy,
        "grade": grade,
        "breakdown": {
            "user_feedback_score": feedback_score,
            "safety_pass_rate": safety_pass_rate,
            "emotion_confidence": emotion_confidence,
            "report_success_rate": report_success_rate,
            "session_completion_rate": session_completion_rate,
        },
        "weights": {
            "user_feedback_score": 30,
            "safety_pass_rate": 25,
            "emotion_confidence": 20,
            "report_success_rate": 15,
            "session_completion_rate": 10,
        },
        "raw": {
            "total_users": len(all_users),
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_messages": total_messages,
            "total_reports": total_reports,
            "successful_reports": successful_reports,
            "total_emotion_detections": total_emotions,
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "total_safety_events": total_safety_events,
            "unsafe_events": unsafe_events,
        },
        "updated_at": datetime.datetime.now().strftime("%I:%M %p"),
    }


@app.route("/api/project/accuracy", methods=["GET"])
@login_required
def api_project_accuracy():
    try:
        accuracy = _calculate_realtime_project_accuracy()
        return jsonify({
            "ok": True,
            "success": True,
            "accuracy": accuracy,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "error": str(e),
        }), 500

def _admin_realtime_payload() -> dict:
    today = datetime.date.today().isoformat()
    users = _admin_build_supabase_users() or _admin_build_local_users()

    total_sessions = 0
    active_sessions = 0
    total_messages = 0
    total_reports = 0
    total_emotions = 0
    total_practices = 0
    total_crisis = 0
    today_sessions = 0
    today_messages = 0

    for value in store.values():
        sessions = value.get("sessions", []) or []
        total_sessions += len(sessions)
        total_messages += _admin_safe_int(value.get("message_count", 0))
        total_reports += len(value.get("reports", []) or [])
        total_emotions += len(value.get("emotion_log", []) or [])
        total_practices += len(value.get("practice_logs", []) or [])
        total_crisis += len(value.get("crisis_actions", []) or [])

        for s in sessions:
            if s.get("date") == today:
                today_sessions += 1
                today_messages += len(s.get("messages", []) or [])
                if not s.get("ended"):
                    active_sessions += 1

    weekly = _admin_weekly_analytics()

    stats = {
        "total_users": len(users) if users else len(store),
        "active_sessions": active_sessions,
        "total_sessions": total_sessions,
        "today_sessions": today_sessions,
        "today_messages": today_messages,
        "total_messages": total_messages,
        "total_reports": total_reports,
        "emotion_detections": total_emotions,
        "total_practices": total_practices,
        "total_crisis_actions": total_crisis,
        "supabase_ready": bool(SUPABASE_READY),
        "last_updated": datetime.datetime.now().strftime("%I:%M:%S %p"),
    }

    return {
        "ok": True,
        "stats": stats,
        "weekly": weekly,
        "recent_activity": _admin_recent_activity(limit=8),
        "users": users[:20],
        "project_accuracy": _calculate_realtime_project_accuracy(),
    }


@app.route("/admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    payload = _admin_realtime_payload()
    return render_template(
        "admin_dashboard.html",
        name=session.get("name", "Admin"),
        email=session.get("email", "admin@neurosense.ai"),
        role="admin",
        is_admin=True,
        initial_admin_data=payload,
    )


@app.route("/admin")
@login_required
@admin_required
def admin():
    return redirect(url_for("admin_dashboard"))


@app.route("/api/admin/realtime")
@login_required
@admin_required
def admin_realtime_api():
    try:
        return jsonify(_admin_realtime_payload())
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "success": False, "error": str(e)}), 500


@app.route("/api/admin/export")
@login_required
@admin_required
def admin_export_api():
    try:
        payload = _admin_realtime_payload()
        payload["exported_at"] = datetime.datetime.now().isoformat()
        return jsonify(payload)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "success": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DELETE USER API — ADMIN ONLY
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/admin/users/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_user_api():
    """
    Admin-only delete/remove user endpoint.

    Deletes from the local NeuroSense store using user_key/email/id/name.
    Optionally attempts Supabase soft-delete/deactivation when configured.
    """
    try:
        payload = request.get_json(silent=True) or {}

        confirm = str(payload.get("confirm", "")).strip()
        if confirm != "DELETE":
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Confirmation failed. Please type DELETE."
            }), 400

        raw_target = str(
            payload.get("user_key")
            or payload.get("user_id")
            or payload.get("email")
            or payload.get("id")
            or ""
        ).strip()

        if not raw_target:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Missing user identifier."
            }), 400

        target = raw_target.lower()
        current_email = str(session.get("email", "")).strip().lower()
        current_key = str(session.get("user_key", "")).strip().lower()

        if target in {current_email, current_key}:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "You cannot delete your own logged-in admin account."
            }), 400

        deleted_keys = []
        matched_key = None

        for key in list(store.keys()):
            key_norm = str(key).strip().lower()
            if key_norm == target:
                matched_key = key
                break

        if not matched_key:
            for key, user_data in list(store.items()):
                possible_values = {
                    str(key).strip().lower(),
                    str(user_data.get("email", "")).strip().lower(),
                    str(user_data.get("name", "")).strip().lower(),
                    str(user_data.get("user_id", "")).strip().lower(),
                    str(user_data.get("id", "")).strip().lower(),
                }
                if target in possible_values:
                    matched_key = key
                    break

        if matched_key and matched_key in store:
            del store[matched_key]
            deleted_keys.append(str(matched_key))
            _save_store()

        supabase_deleted = False
        supabase_error = None
        try:
            if SUPABASE_READY and supabase is not None and soft_delete_account:
                soft_delete_account(raw_target)
                supabase_deleted = True
        except Exception as e:
            supabase_error = str(e)

        if not deleted_keys and not supabase_deleted:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "User not found in local store. Nothing was deleted.",
                "target": raw_target,
                "available_store_keys": list(store.keys())[:10],
                "supabase_error": supabase_error
            }), 404

        return jsonify({
            "ok": True,
            "success": True,
            "message": "User removed successfully.",
            "target": raw_target,
            "deleted_local_keys": deleted_keys,
            "supabase_deleted": supabase_deleted,
            "supabase_error": supabase_error,
            "updated_at": datetime.datetime.now().strftime("%I:%M %p")
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "success": False,
            "error": str(e)
        }), 500

def _print_routes():
    print("\n📋 Registered Flask Routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        print(f"   {methods:8s}  {rule}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧠  NeuroSense AI — Multilingual Mental Health Companion")
    print(f"📁  Data file     : {STORE_PATH}")
    print(f"👥  Users in store: {len(store)}")
    print("=" * 70)
    print(f"   📊  Emotion backend : {EMOTION_BACKEND or '❌ unavailable'}")
    print(f"   🌍  Translation     : {'✅' if TRANSLATOR_AVAILABLE else '❌'}")
    print(f"   🔊  TTS             : {'✅ gTTS' if GTTS_AVAILABLE else ('✅ pyttsx3' if TTS_AVAILABLE else '❌')}")
    print(f"   👤  Face cascade    : {'✅' if FACE_CASCADE else '❌'}")
    print(f"   🤖  Groq model      : {GROQ_MODEL}")
    print("=" * 70)

    _test_groq()
    _print_routes()

    print("\n1: Start Web App\n2: Hand Sign Training\n")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        print("\n🌐  Server starting at http://localhost:5000\n")
        app.run(debug=True, use_reloader=False, threaded=True, port=5000)
    elif choice == "2":
        if HS_AVAILABLE:
            hs.run_cli()
        else:
            print("❌ hs_module not available.")
    else:
        print("Invalid choice.")
