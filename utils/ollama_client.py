"""
===============================================================================
NeuroSense AI — Ollama Client
===============================================================================

Purpose:
- Local Ollama model support for Research Chat, Templates, and Knowledge Chat.
- Provides compatibility constants/functions expected by older agent files:
    OLLAMA_RESEARCH_MODEL
    OLLAMA_FAST_MODEL
    OLLAMA_FALLBACK_MODEL
    OLLAMA_BASE_URL
    OLLAMA_TIMEOUT
    STRICT_MENTAL_HEALTH_SYSTEM
    MENTAL_HEALTH_SYSTEM_PROMPT
    get_ollama_client
    ollama_status
    parse_json_safely
    extract_json_array_safely

Design:
- Fail safely.
- Never crash Flask app if Ollama is unavailable.
===============================================================================
"""

import os
import json
import re
import requests
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Ollama Config
# ============================================================

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
).strip().rstrip("/")

OLLAMA_RESEARCH_MODEL = os.getenv(
    "OLLAMA_RESEARCH_MODEL",
    "qwen2.5:3b"
).strip()

OLLAMA_FAST_MODEL = os.getenv(
    "OLLAMA_FAST_MODEL",
    "qwen2.5:3b"
).strip()

OLLAMA_FALLBACK_MODEL = os.getenv(
    "OLLAMA_FALLBACK_MODEL",
    "qwen2.5:1.5b"
).strip()

OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))


# ============================================================
# Strict Mental Health System Prompt
# Required by ResearchAgent / TemplateAgent imports
# ============================================================

STRICT_MENTAL_HEALTH_SYSTEM = """
You are NeuroSense AI, a strict mental-health and wellbeing assistant.

Scope:
You may answer only about:
- mental wellbeing
- emotional support
- stress
- anxiety-like feelings
- sleep
- loneliness
- academic pressure
- work pressure
- burnout
- self-doubt
- anger regulation
- mood tracking
- wellbeing check-ins
- NeuroSense AI reports
- professional help guidance
- crisis safety
- safe coping practices

Strict safety rules:
1. Do not diagnose mental health conditions.
2. Do not prescribe medication.
3. Do not recommend medicine names, dosage, or medication changes.
4. Do not claim to be a psychiatrist, doctor, psychologist, therapist, or emergency service.
5. Do not replace licensed professional care.
6. Use non-diagnostic wording such as:
   - "you may be feeling..."
   - "this can feel like..."
   - "it may help to..."
7. If user asks for diagnosis, refuse diagnosis and recommend professional assessment.
8. If user asks for medication, refuse medication advice and recommend a qualified doctor/psychiatrist.
9. If user may be unsafe or at risk of self-harm:
   - prioritize immediate safety,
   - encourage contacting a trusted person,
   - encourage local emergency services if in immediate danger,
   - provide crisis helplines where relevant.
10. Do not answer unrelated topics such as politics, sports, hacking, coding, finance, celebrity gossip, recipes, or general trivia.
11. If a question is outside scope, politely redirect to mental-health/wellbeing topics.
12. Give practical, grounded, supportive answers.
13. Do not hallucinate facts.
14. If unsure, say you do not have enough approved information.
15. Do not make major life/work/medical decisions for the user; help them think through decisions safely.

India crisis resources when needed:
- Tele-MANAS: 14416 or 1800-891-4416
- iCALL: 9152987821
- Vandrevala Foundation: +91 9999 666 555
- KIRAN: 1800-599-0019
- AASRA: 022-27546669
"""

# Alias for older files that may import this name
MENTAL_HEALTH_SYSTEM_PROMPT = STRICT_MENTAL_HEALTH_SYSTEM


# ============================================================
# JSON Helpers
# ============================================================

def parse_json_safely(
    raw_text: str,
    fallback: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM/Ollama output.

    Handles:
    - raw JSON
    - ```json fenced blocks
    - generic ``` fenced blocks
    - extra text before/after JSON
    - invalid/empty output
    """

    fallback = fallback or {}

    if not raw_text:
        return fallback

    text = str(raw_text).strip().lstrip("\ufeff")

    if not text:
        return fallback

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else fallback
    except Exception:
        pass

    try:
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0].strip()

        elif text.startswith("```"):
            text = text[3:]
            if text.startswith("\n"):
                text = text[1:]
            text = text.split("```", 1)[0].strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else fallback
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            json_text = match.group(0).strip()
            parsed = json.loads(json_text)
            return parsed if isinstance(parsed, dict) else fallback

    except Exception as e:
        print(f"⚠️ parse_json_safely failed: {e}")

    return fallback


def extract_json_array_safely(
    raw_text: str,
    fallback: Optional[List[Any]] = None
) -> List[Any]:
    """
    Safely parse JSON array from LLM output.
    """

    fallback = fallback or []

    if not raw_text:
        return fallback

    text = str(raw_text).strip().lstrip("\ufeff")

    if not text:
        return fallback

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else fallback
    except Exception:
        pass

    try:
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0].strip()

        elif text.startswith("```"):
            text = text[3:]
            if text.startswith("\n"):
                text = text[1:]
            text = text.split("```", 1)[0].strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else fallback
        except Exception:
            pass

        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            parsed = json.loads(match.group(0).strip())
            return parsed if isinstance(parsed, list) else fallback

    except Exception as e:
        print(f"⚠️ extract_json_array_safely failed: {e}")

    return fallback


# ============================================================
# Ollama Client
# ============================================================

class OllamaClient:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        default_model: str = OLLAMA_RESEARCH_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
    ):
        self.base_url = str(base_url or OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or OLLAMA_RESEARCH_MODEL
        self.timeout = int(timeout or OLLAMA_TIMEOUT)

    def is_available(self) -> bool:
        try:
            res = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> Dict[str, Any]:
        try:
            res = requests.get(
                f"{self.base_url}/api/tags",
                timeout=8,
            )

            if res.status_code != 200:
                return {
                    "ok": False,
                    "error": f"Ollama returned status {res.status_code}",
                    "models": [],
                    "model_names": [],
                }

            data = res.json()
            models = data.get("models", []) or []
            model_names = []

            for model in models:
                name = model.get("name")
                if name:
                    model_names.append(name)

            return {
                "ok": True,
                "models": models,
                "model_names": model_names,
            }

        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "models": [],
                "model_names": [],
            }

    def has_model(self, model_name: str) -> bool:
        if not model_name:
            return False

        status = self.list_models()

        if not status.get("ok"):
            return False

        return model_name in (status.get("model_names") or [])

    def choose_model(self, preferred_model: Optional[str] = None) -> str:
        """
        Choose a model safely.

        Priority:
        1. preferred_model if installed
        2. OLLAMA_RESEARCH_MODEL if installed
        3. OLLAMA_FAST_MODEL if installed
        4. OLLAMA_FALLBACK_MODEL if installed
        5. first installed model
        6. preferred/default even if not found
        """

        preferred_model = preferred_model or self.default_model

        status = self.list_models()
        model_names: List[str] = status.get("model_names", []) if status.get("ok") else []

        if preferred_model in model_names:
            return preferred_model

        if OLLAMA_RESEARCH_MODEL in model_names:
            return OLLAMA_RESEARCH_MODEL

        if OLLAMA_FAST_MODEL in model_names:
            return OLLAMA_FAST_MODEL

        if OLLAMA_FALLBACK_MODEL in model_names:
            return OLLAMA_FALLBACK_MODEL

        if model_names:
            return model_names[0]

        return preferred_model

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 700,
    ) -> str:
        """
        Generate text using Ollama /api/generate.

        Returns empty string on failure instead of crashing app.
        """

        selected_model = self.choose_model(model or self.default_model)

        payload = {
            "model": selected_model,
            "prompt": prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            res = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            if res.status_code != 200:
                print(f"❌ Ollama generate status {res.status_code}: {res.text[:300]}")
                return ""

            data = res.json()
            return str(data.get("response", "")).strip()

        except requests.exceptions.Timeout:
            print(
                f"❌ Ollama generate timeout after {self.timeout}s. "
                f"Use smaller model like qwen2.5:3b or qwen2.5:1.5b, or increase OLLAMA_TIMEOUT."
            )
            return ""

        except Exception as e:
            print(f"❌ Ollama generate error: {e}")
            return ""

    def chat(
        self,
        messages,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 700,
    ) -> str:
        """
        Chat style call using Ollama /api/chat.
        """

        selected_model = self.choose_model(model or self.default_model)

        payload = {
            "model": selected_model,
            "messages": messages or [],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            res = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )

            if res.status_code != 200:
                print(f"❌ Ollama chat status {res.status_code}: {res.text[:300]}")
                return ""

            data = res.json()
            msg = data.get("message", {}) or {}
            return str(msg.get("content", "")).strip()

        except requests.exceptions.Timeout:
            print(
                f"❌ Ollama chat timeout after {self.timeout}s. "
                f"Use qwen2.5:3b or qwen2.5:1.5b, or increase OLLAMA_TIMEOUT."
            )
            return ""

        except Exception as e:
            print(f"❌ Ollama chat error: {e}")
            return ""

    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 700,
        fallback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate text and parse it as JSON safely.
        """

        raw = self.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return parse_json_safely(raw, fallback=fallback or {})


_OLLAMA_CLIENT = None


def get_ollama_client() -> OllamaClient:
    global _OLLAMA_CLIENT

    if _OLLAMA_CLIENT is None:
        _OLLAMA_CLIENT = OllamaClient()

    return _OLLAMA_CLIENT


def ollama_status() -> Dict[str, Any]:
    client = get_ollama_client()
    models = client.list_models()

    model_names = models.get("model_names", []) if models.get("ok") else []

    return {
        "ok": bool(models.get("ok")),
        "base_url": OLLAMA_BASE_URL,
        "default_model": OLLAMA_RESEARCH_MODEL,
        "fast_model": OLLAMA_FAST_MODEL,
        "fallback_model": OLLAMA_FALLBACK_MODEL,
        "timeout": OLLAMA_TIMEOUT,
        "available": client.is_available(),
        "models": model_names,
        "message": (
            "Ollama is ready."
            if models.get("ok")
            else models.get("error", "Ollama is not available.")
        ),
    }


if __name__ == "__main__":
    print(json.dumps(ollama_status(), indent=2))