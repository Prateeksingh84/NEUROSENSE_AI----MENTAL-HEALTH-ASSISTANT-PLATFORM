"""
===============================================================================
NeuroSense AI — Safety Agent
===============================================================================
Purpose:
- Detect self-harm, suicide, crisis, violence, abuse, unsafe medical advice.
- Decide whether normal AI response should continue.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class SafetyAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="SafetyAgent",
            temperature=0.0,
            max_tokens=500,
        )

    # -------------------------------------------------------------------------

    def clean_history(self, history):
        """
        Safely normalize chat history for safety-agent processing.
        Prevents crashes when history is None, malformed, or contains unexpected objects.
        """
        if not history:
            return []

        cleaned = []

        for item in history:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")

                if content is None:
                    content = ""

                cleaned.append({
                    "role": str(role),
                    "content": str(content)
                })

            elif isinstance(item, str):
                cleaned.append({
                    "role": "user",
                    "content": item
                })

        return cleaned

    # -------------------------------------------------------------------------

    def keyword_precheck(self, user_message: str) -> Dict[str, Any]:
        """
        Fast deterministic safety check before LLM.
        """

        text = (user_message or "").lower()

        crisis_terms = [
            "suicide",
            "kill myself",
            "end my life",
            "don't want to live",
            "dont want to live",
            "hurt myself",
            "self harm",
            "self-harm",
            "cut myself",
            "i want to die",
            "i will die",
            "no reason to live",
        ]

        violence_terms = [
            "kill someone",
            "hurt someone",
            "attack someone",
            "murder",
            "violence",
        ]

        abuse_terms = [
            "abuse",
            "domestic violence",
            "harassment",
            "assault",
            "forced",
            "blackmail",
        ]

        medication_terms = [
            "medicine",
            "medication",
            "tablet",
            "dose",
            "antidepressant",
            "sleeping pill",
            "prescribe",
        ]

        if any(term in text for term in crisis_terms):
            return {
                "risk_level": "crisis",
                "self_harm": True,
                "violence": False,
                "abuse": False,
                "medical_advice_requested": False,
                "allow_normal_response": False,
                "reason": "Self-harm or suicide-related wording detected.",
            }

        if any(term in text for term in violence_terms):
            return {
                "risk_level": "high",
                "self_harm": False,
                "violence": True,
                "abuse": False,
                "medical_advice_requested": False,
                "allow_normal_response": False,
                "reason": "Violence-related wording detected.",
            }

        if any(term in text for term in abuse_terms):
            return {
                "risk_level": "medium",
                "self_harm": False,
                "violence": False,
                "abuse": True,
                "medical_advice_requested": False,
                "allow_normal_response": True,
                "reason": "Potential abuse or safety concern detected.",
            }

        if any(term in text for term in medication_terms):
            return {
                "risk_level": "medium",
                "self_harm": False,
                "violence": False,
                "abuse": False,
                "medical_advice_requested": True,
                "allow_normal_response": True,
                "reason": "Medication-related query detected.",
            }

        return {
            "risk_level": "none",
            "self_harm": False,
            "violence": False,
            "abuse": False,
            "medical_advice_requested": False,
            "allow_normal_response": True,
            "reason": "No immediate risk keyword detected.",
        }

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        emotion: str = "neutral",
        wellbeing_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}
        history = self.clean_history(history)

        precheck = self.keyword_precheck(user_message)

        if precheck["risk_level"] in ["crisis", "high"]:
            return precheck

        prompt = f"""
You are the Safety Agent for NeuroSense AI.

Classify the user's mental-health safety risk.

{GLOBAL_SAFETY_RULES}

User message:
{user_message}

Detected emotion:
{emotion}

Latest wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "risk_level": "none | low | medium | high | crisis",
  "self_harm": true/false,
  "violence": true/false,
  "abuse": true/false,
  "medical_advice_requested": true/false,
  "allow_normal_response": true/false,
  "reason": "short reason"
}}

Rules:
- If suicide/self-harm intent appears, risk_level = crisis and allow_normal_response = false.
- If immediate danger appears, risk_level = crisis.
- If medication advice is requested, medical_advice_requested = true.
- Do not diagnose.
"""

        raw = self.call_llm(prompt)

        fallback = precheck

        parsed = self.parse_json(raw, fallback=fallback)

        required = {
            "risk_level",
            "self_harm",
            "violence",
            "abuse",
            "medical_advice_requested",
            "allow_normal_response",
            "reason",
        }

        if not required.issubset(parsed.keys()):
            return fallback

        return parsed