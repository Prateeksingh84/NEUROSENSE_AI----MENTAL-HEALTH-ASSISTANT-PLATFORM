"""
===============================================================================
NeuroSense AI — Therapy Response Agent
===============================================================================
Purpose:
- Generate the supportive response.
- Uses CBT/DBT-inspired supportive language.
- Does not diagnose or prescribe.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class TherapyAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="TherapyAgent",
            temperature=0.45,
            max_tokens=650,
        )

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        safety: Dict[str, Any],
        emotion_analysis: Dict[str, Any],
        social_analysis: Dict[str, Any],
        wellbeing_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        lang: str = "en",
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}
        history = self.clean_history(history)

        fallback_reply = self.safe_support_fallback()

        if safety.get("risk_level") == "crisis":
            return {
                "reply": self.crisis_response(),
                "response_type": "crisis",
                "technique_used": "crisis_escalation",
            }

        prompt = f"""
You are NeuroSense AI, a compassionate mental health support assistant.

{GLOBAL_SAFETY_RULES}

Your task:
Generate a short, warm, supportive response to the user.

Important:
- Do NOT diagnose.
- Do NOT prescribe.
- Do NOT say "you have depression/anxiety".
- Do NOT pretend to be a psychiatrist.
- Use supportive CBT/DBT-style language.
- Keep response concise: 3 to 6 sentences.
- If medication is mentioned, recommend consulting a qualified doctor/psychiatrist.
- If risk is high, encourage human support.

User message:
{user_message}

Safety classification:
{json.dumps(safety, ensure_ascii=False)}

Emotion analysis:
{json.dumps(emotion_analysis, ensure_ascii=False)}

Social analysis:
{json.dumps(social_analysis, ensure_ascii=False)}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

Language code requested:
{lang}

Return ONLY valid JSON:
{{
  "reply": "final user-facing response",
  "response_type": "supportive | grounding | referral | crisis",
  "technique_used": "CBT | DBT | grounding | validation | reflection | referral"
}}

Rules:
- If language is not English, respond in that language if possible.
- If not sure, say the observation is limited.
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(
            raw,
            fallback={
                "reply": fallback_reply,
                "response_type": "supportive",
                "technique_used": "validation",
            }
        )

        reply = parsed.get("reply", fallback_reply)

        if self.contains_unsafe_medical_claim(reply):
            parsed["reply"] = fallback_reply
            parsed["response_type"] = "safe_fallback"
            parsed["technique_used"] = "validation"

        return parsed