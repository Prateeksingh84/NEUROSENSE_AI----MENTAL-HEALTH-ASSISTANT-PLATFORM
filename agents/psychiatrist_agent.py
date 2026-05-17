"""
===============================================================================
NeuroSense AI — Clinical Escalation Agent
===============================================================================
Purpose:
- Recommend outside professional help when needed.
- Does NOT act as psychiatrist.
- Does NOT diagnose.
- Does NOT prescribe.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class PsychiatristAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ClinicalEscalationAgent",
            temperature=0.1,
            max_tokens=750,
        )

    # -------------------------------------------------------------------------

    def deterministic_referral(
        self,
        safety: Dict[str, Any],
        wellbeing_data: Dict[str, Any],
        user_message: str,
    ) -> Dict[str, Any]:

        mood = wellbeing_data.get("mood", "")
        stress = int(wellbeing_data.get("stress") or 0)
        emotional_safety = int(wellbeing_data.get("emotional_safety") or 5)
        support = wellbeing_data.get("support_available", "")
        sleep = wellbeing_data.get("sleep", "")
        text = (user_message or "").lower()

        medication_words = [
            "medicine",
            "medication",
            "tablet",
            "dose",
            "antidepressant",
            "sleeping pill",
        ]

        if safety.get("risk_level") == "crisis" or safety.get("self_harm"):
            return {
                "needs_professional_referral": True,
                "urgency": "emergency",
                "recommended_professional": "emergency services or crisis helpline",
                "reason": "Immediate safety concern detected.",
                "user_facing_message": (
                    "Because your safety may be at risk, please contact a trusted person "
                    "or crisis helpline immediately."
                ),
                "professional_summary": "User message indicates possible crisis or self-harm risk.",
            }

        if any(word in text for word in medication_words):
            return {
                "needs_professional_referral": True,
                "urgency": "soon",
                "recommended_professional": "psychiatrist",
                "reason": "Medication-related concern should be handled by a qualified psychiatrist or doctor.",
                "user_facing_message": (
                    "I cannot advise on medication. Please speak with a qualified psychiatrist "
                    "or doctor for medication-related questions."
                ),
                "professional_summary": "User asked about medication-related concern.",
            }

        if stress >= 4 or emotional_safety <= 2 or mood in ["overwhelmed", "sad"] or sleep == "very_poor":
            return {
                "needs_professional_referral": True,
                "urgency": "soon",
                "recommended_professional": "psychologist or psychiatrist",
                "reason": "High distress indicators are present in the wellbeing check-in.",
                "user_facing_message": (
                    "It may be helpful to speak with a licensed mental health professional. "
                    "I can support you, but a professional can assess this more properly."
                ),
                "professional_summary": "User shows high distress indicators in check-in.",
            }

        if support == "no":
            return {
                "needs_professional_referral": True,
                "urgency": "routine",
                "recommended_professional": "counsellor or psychologist",
                "reason": "Low support availability may benefit from professional counselling.",
                "user_facing_message": (
                    "Since you may not have someone to talk to today, speaking with a counsellor "
                    "or psychologist could be helpful."
                ),
                "professional_summary": "User reports limited social support.",
            }

        return {
            "needs_professional_referral": False,
            "urgency": "none",
            "recommended_professional": "none",
            "reason": "No strong referral signal detected.",
            "user_facing_message": "",
            "professional_summary": "",
        }

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        safety: Dict[str, Any],
        emotion_analysis: Dict[str, Any],
        social_analysis: Dict[str, Any],
        wellbeing_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}
        history = self.clean_history(history)

        fallback = self.deterministic_referral(
            safety=safety,
            wellbeing_data=wellbeing_data,
            user_message=user_message,
        )

        prompt = f"""
You are the Clinical Escalation Agent for NeuroSense AI.

You are NOT a psychiatrist.
You must NOT diagnose.
You must NOT prescribe medication.
You only decide whether the user should be encouraged to consult qualified human support.

{GLOBAL_SAFETY_RULES}

User message:
{user_message}

Safety:
{json.dumps(safety, ensure_ascii=False)}

Emotion analysis:
{json.dumps(emotion_analysis, ensure_ascii=False)}

Social analysis:
{json.dumps(social_analysis, ensure_ascii=False)}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "needs_professional_referral": true/false,
  "urgency": "none | routine | soon | urgent | emergency",
  "recommended_professional": "none | counsellor | psychologist | psychiatrist | emergency services or crisis helpline",
  "reason": "short non-diagnostic reason",
  "user_facing_message": "safe message for the user",
  "professional_summary": "brief summary user can show to a professional"
}}

Rules:
- Self-harm/immediate danger = emergency.
- Medication-related concern = psychiatrist.
- Persistent/severe distress = psychologist or psychiatrist.
- Social stress/loneliness = counsellor or psychologist.
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(raw, fallback=fallback)

        return parsed