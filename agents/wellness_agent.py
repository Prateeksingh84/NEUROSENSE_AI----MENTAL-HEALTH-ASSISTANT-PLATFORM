"""
===============================================================================
NeuroSense AI — Wellness Recommendation Agent
===============================================================================
Purpose:
- Generate safe, practical wellness practices.
- Suggestions are supportive, not medical treatment.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class WellnessAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="WellnessAgent",
            temperature=0.25,
            max_tokens=850,
        )

    # -------------------------------------------------------------------------

    def deterministic_recommendations(
        self,
        wellbeing_data: Dict[str, Any],
        emotion_analysis: Dict[str, Any],
    ) -> List[Dict[str, str]]:

        mood = wellbeing_data.get("mood", "")
        sleep = wellbeing_data.get("sleep", "")
        stress = int(wellbeing_data.get("stress") or 0)
        social = int(wellbeing_data.get("social_connection") or 3)
        support = wellbeing_data.get("support_available", "")
        concerns = wellbeing_data.get("concerns", []) or []
        dominant = emotion_analysis.get("dominant_emotion", "")

        recs = []

        if stress >= 4 or dominant in ["anxious", "overwhelmed", "stressed"]:
            recs.append({
                "title": "Box Breathing",
                "description": "Breathe in for 4 seconds, hold for 4, breathe out for 4, and hold again for 4.",
                "frequency": "2–3 times daily",
                "category": "stress_regulation",
            })

        if sleep in ["poor", "very_poor"]:
            recs.append({
                "title": "Sleep Wind-Down Routine",
                "description": "Avoid screens for 30 minutes before sleep and write down tomorrow’s tasks before bed.",
                "frequency": "Nightly",
                "category": "sleep",
            })

        if social <= 2 or support in ["no", "maybe"] or "loneliness" in concerns:
            recs.append({
                "title": "Trusted Person Check-In",
                "description": "Send a short message to one trusted person saying you could use a quick conversation.",
                "frequency": "Today",
                "category": "social_support",
            })

        if mood in ["sad", "overwhelmed"] or "self_doubt" in concerns:
            recs.append({
                "title": "Thought Journal",
                "description": "Write one difficult thought, one feeling, and one kinder alternative thought.",
                "frequency": "Daily",
                "category": "reflection",
            })

        if len(recs) < 5:
            recs.append({
                "title": "5-4-3-2-1 Grounding",
                "description": "Notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.",
                "frequency": "Whenever overwhelmed",
                "category": "grounding",
            })

        if len(recs) < 5:
            recs.append({
                "title": "Small Action Plan",
                "description": "Choose one small task that takes less than 5 minutes and complete only that.",
                "frequency": "Once today",
                "category": "activation",
            })

        if len(recs) < 5:
            recs.append({
                "title": "Hydration and Movement",
                "description": "Drink water and take a 5-minute walk or stretch break.",
                "frequency": "Daily",
                "category": "body_care",
            })

        return recs[:5]

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        emotion_analysis: Dict[str, Any],
        social_analysis: Dict[str, Any],
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}

        fallback_recs = self.deterministic_recommendations(
            wellbeing_data,
            emotion_analysis
        )

        prompt = f"""
You are the Wellness Recommendation Agent for NeuroSense AI.

{GLOBAL_SAFETY_RULES}

Generate safe wellness recommendations only.
Do not diagnose.
Do not prescribe.
Do not give medical treatment.

User message:
{user_message}

Emotion analysis:
{json.dumps(emotion_analysis, ensure_ascii=False)}

Social analysis:
{json.dumps(social_analysis, ensure_ascii=False)}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "top_practices": [
    {{
      "title": "practice name",
      "description": "short practical instruction",
      "frequency": "when/how often",
      "category": "stress | sleep | social | grounding | journaling | professional_help"
    }}
  ],
  "immediate_action": "one very small action user can do now",
  "note": "short safety note"
}}

Rules:
- Exactly 5 top_practices.
- Practices must be low-risk and practical.
- If data suggests high risk, include professional help as one practice.
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(
            raw,
            fallback={
                "top_practices": fallback_recs,
                "immediate_action": fallback_recs[0]["description"],
                "note": "These are general wellness suggestions, not medical treatment.",
            }
        )

        practices = parsed.get("top_practices", [])

        if not isinstance(practices, list) or len(practices) < 5:
            parsed["top_practices"] = fallback_recs

        parsed["top_practices"] = parsed["top_practices"][:5]

        return parsed