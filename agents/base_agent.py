"""
===============================================================================
NeuroSense AI — Base Agent
===============================================================================

Purpose:
- Shared LLM caller for all agents.
- Provides GLOBAL_SAFETY_RULES compatibility for existing agents.
- Groq support with safe fallback.
- Prevents full app crash on invalid API key / network failure.

This file is used by:
- SafetyAgent
- HallucinationAgent
- Orchestrator
- ResearchAgent
- TemplateAgent
- KnowledgeAgent dependencies
===============================================================================
"""

import os
import json
import re
import traceback
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Global Model Config
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


# ============================================================
# GLOBAL SAFETY RULES
# IMPORTANT:
# Keep this variable because many existing agent files import it.
# ============================================================

GLOBAL_SAFETY_RULES = """
NeuroSense AI Global Safety Rules:

1. Do not diagnose mental health conditions.
2. Do not prescribe medication.
3. Do not recommend medicine dosage.
4. Do not tell users to start, stop, increase, or reduce medication.
5. Do not claim to be a doctor, psychiatrist, psychologist, therapist, or emergency service.
6. Do not replace licensed professional care.
7. Use supportive, non-judgmental, trauma-informed language.
8. Use non-diagnostic wording such as:
   - "you may be feeling..."
   - "this can feel like..."
   - "it may help to..."
9. For crisis/self-harm/unsafe situations:
   - prioritize immediate safety,
   - encourage contacting a trusted person,
   - encourage emergency services if in immediate danger,
   - provide crisis helplines where relevant.
10. If the user asks for diagnosis:
   - refuse diagnosis,
   - suggest professional assessment.
11. If the user asks for medication advice:
   - refuse medication guidance,
   - suggest speaking with a doctor or psychiatrist.
12. Keep responses grounded, practical, and safe.
13. Do not make major life, work, academic, relationship, or medical decisions for the user.
14. Help the user think through decisions safely.
15. For India crisis support, useful resources include:
   - Tele-MANAS: 14416 or 1800-891-4416
   - iCALL: 9152987821
   - Vandrevala Foundation: +91 9999 666 555
   - KIRAN: 1800-599-0019
   - AASRA: 022-27546669
"""


GLOBAL_SYSTEM_PROMPT = f"""
You are NeuroSense AI, a safe and compassionate mental wellbeing assistant.

Follow these global rules strictly:

{GLOBAL_SAFETY_RULES}
"""


# ============================================================
# Helper fallback responses
# ============================================================

def safe_fallback_response() -> str:
    return (
        "I’m here with you. I can offer general mental-wellbeing support, but I can’t diagnose, "
        "prescribe medication, or replace professional care. Could you tell me a little more about "
        "what you’re feeling right now?"
    )


def crisis_fallback_response() -> str:
    return (
        "Your safety matters most right now. Please contact a trusted person immediately and avoid being alone "
        "if possible. If you are in immediate danger, call local emergency services. In India, you can contact "
        "Tele-MANAS at 14416 or 1800-891-4416, iCALL at 9152987821, Vandrevala Foundation at +91 9999 666 555, "
        "KIRAN at 1800-599-0019, or AASRA at 022-27546669."
    )


# ============================================================
# Base Agent
# ============================================================

class BaseAgent:
    """
    Base class used by all NeuroSense agents.

    Provides:
    - safe Groq client initialization
    - text completion
    - JSON completion
    - safe fallback behavior
    """

    def __init__(
        self,
        name: str = "BaseAgent",
        model: str = GROQ_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 600,
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None

        if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
            try:
                from groq import Groq
                self.client = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"⚠️ {self.name} Groq client disabled: {e}")
                self.client = None
        else:
            print(f"⚠️ {self.name} Groq client disabled: invalid/missing GROQ_API_KEY")

    def call_llm(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Safe Groq LLM call.

        Returns empty string if LLM fails instead of crashing the app.
        """

        if self.client is None:
            print(f"⚠️ {self.name} LLM skipped: Groq client not available.")
            return ""

        final_system_prompt = system_prompt or GLOBAL_SYSTEM_PROMPT

        messages = [
            {
                "role": "system",
                "content": final_system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt or "",
            },
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ {self.name} LLM error: {e}")
            traceback.print_exc()
            return ""

    def call_json(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        fallback: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Safe JSON call.

        Returns fallback on:
        - LLM failure
        - invalid JSON
        - markdown fenced JSON issues
        """

        fallback = fallback or {}

        raw = self.call_llm(
            system_prompt=system_prompt or GLOBAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens or self.max_tokens,
            json_mode=True,
        )

        if not raw:
            return fallback

        try:
            cleaned = raw.strip().lstrip("\ufeff")

            if "```json" in cleaned:
                cleaned = cleaned.split("```json", 1)[1]
                cleaned = cleaned.split("```", 1)[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
                if cleaned.startswith("\n"):
                    cleaned = cleaned[1:]
                cleaned = cleaned.split("```", 1)[0].strip()

            if not cleaned.startswith("{"):
                import re
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(0)

            return json.loads(cleaned)

        except Exception as e:
            print(f"⚠️ {self.name} JSON parse failed: {e}")
            return fallback

    def parse_json(
        self,
        raw: str,
        fallback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Parse a raw LLM response as JSON without making another model call.
        """

        fallback = fallback or {}

        if not raw:
            return fallback

        try:
            cleaned = str(raw).strip().lstrip("\ufeff")

            if "```json" in cleaned:
                cleaned = cleaned.split("```json", 1)[1]
                cleaned = cleaned.split("```", 1)[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
                if cleaned.startswith("\n"):
                    cleaned = cleaned[1:]
                cleaned = cleaned.split("```", 1)[0].strip()

            if not cleaned.startswith("{"):
                import re
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(0)

            parsed = json.loads(cleaned)

            if isinstance(parsed, dict):
                return parsed

            return fallback

        except Exception as e:
            print(f"⚠️ {self.name} JSON parse failed: {e}")
            return fallback

    def clean_history(
        self,
        history: Optional[List[Any]],
    ) -> List[Dict[str, str]]:
        """
        Normalize chat history so agent prompts never crash on malformed entries.
        """

        if not history:
            return []

        cleaned = []

        for item in history:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
            elif isinstance(item, str):
                role = "user"
                content = item
            else:
                role = getattr(item, "role", "user")
                content = getattr(item, "content", "")

            cleaned.append({
                "role": str(role or "user"),
                "content": str(content or ""),
            })

        return cleaned

    def safe_text(
        self,
        text: str,
        fallback: str = "",
    ) -> str:
        """
        Clean empty model output.
        """

        text = str(text or "").strip()

        if text:
            return text

        return fallback or safe_fallback_response()

    def safe_support_fallback(self) -> str:
        return safe_fallback_response()

    def crisis_response(self) -> str:
        return crisis_fallback_response()

    def contains_unsafe_medical_claim(self, text: str) -> bool:
        """
        Conservative rule-based guard for diagnostic, medication, and crisis claims.
        """

        if not text:
            return False

        text_lower = str(text).lower()
        text_lower = re.sub(r"\s+", " ", text_lower).strip()

        unsafe_patterns = [
            r"\byou have depression\b",
            r"\byou are depressed\b",
            r"\byou have anxiety\b",
            r"\byou have anxiety disorder\b",
            r"\byou are bipolar\b",
            r"\byou have bipolar disorder\b",
            r"\byou have ptsd\b",
            r"\byou have schizophrenia\b",
            r"\byou are schizophrenic\b",
            r"\byou have ocd\b",
            r"\byou have adhd\b",
            r"\byou are mentally ill\b",
            r"\byou definitely have\b",
            r"\bthis means you have\b",
            r"\bi diagnose you with\b",
            r"\byour diagnosis is\b",
            r"\bstart taking\b.*\bmedication\b",
            r"\bstop taking\b.*\bmedication\b",
            r"\bincrease your dose\b",
            r"\bdecrease your dose\b",
            r"\bchange your dose\b",
            r"\btake \d+ ?mg\b",
            r"\btake .* antidepressant\b",
            r"\btake .* sleeping pill\b",
            r"\byou should take medicine\b",
            r"\byou should take medication\b",
            r"\bi recommend taking\b.*\bmg\b",
            r"\bprescribe\b",
            r"\bprescription\b",
            r"\bguaranteed cure\b",
            r"\bthis will cure you\b",
            r"\bthis will definitely cure\b",
            r"\byou will be cured\b",
            r"\b100% effective\b",
            r"\bcompletely safe\b",
            r"\bno side effects\b",
            r"\bthis always works\b",
            r"\byou do not need a doctor\b",
            r"\byou don't need a doctor\b",
            r"\byou do not need therapy\b",
            r"\byou don't need therapy\b",
            r"\bavoid seeing a doctor\b",
            r"\bavoid therapy\b",
            r"\bignore your therapist\b",
            r"\bdo not tell anyone\b",
            r"\bdon't tell anyone\b",
            r"\bignore suicidal thoughts\b",
            r"\bsuicidal thoughts are normal, ignore them\b",
            r"\bself harm is okay\b",
            r"\bself-harm is okay\b",
            r"\bit is safe to harm yourself\b",
            r"\byou should hurt yourself\b",
            r"\byou should kill yourself\b",
            r"\bend your life\b",
            r"\bthere is no reason to live\b",
            r"\bno one can help you\b",
        ]

        return any(re.search(pattern, text_lower) for pattern in unsafe_patterns)

    def run(self, *args, **kwargs):
        raise NotImplementedError("Agent must implement run()")
