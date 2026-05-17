"""
===============================================================================
NeuroSense AI — Emotion Agent
===============================================================================
Purpose:
- Combine detected emotion, text tone, wellbeing score, and history.
- Return emotional interpretation without diagnosis.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class EmotionAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="EmotionAgent",
            temperature=0.1,
            max_tokens=600,
        )

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        detected_emotion: str = "neutral",
        wellbeing_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}
        history = self.clean_history(history)

        fallback = {
            "dominant_emotion": detected_emotion or "neutral",
            "emotional_intensity": "moderate",
            "mood_score_estimate": wellbeing_data.get("wellbeing_score", 50),
            "emotional_summary": (
                "The user's emotional state appears to need supportive attention."
            ),
            "confidence": "medium",
        }

        prompt = f"""
You are the Emotion Analysis Agent for NeuroSense AI.

{GLOBAL_SAFETY_RULES}

Analyze the user's emotional state using only the given data.
Do not diagnose.

User message:
{user_message}

Detected facial/emotion result:
{detected_emotion}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "dominant_emotion": "happy | calm | neutral | sad | anxious | angry | overwhelmed | stressed | lonely",
  "emotional_intensity": "low | moderate | high",
  "mood_score_estimate": 0,
  "emotional_summary": "short non-diagnostic summary",
  "confidence": "low | medium | high"
}}

Rules:
- mood_score_estimate must be 0 to 100.
- If data is limited, confidence should be low or medium.
- Do not say the user has a disorder.
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(raw, fallback=fallback)

        try:
            parsed["mood_score_estimate"] = max(
                0,
                min(100, int(parsed.get("mood_score_estimate", 50)))
            )
        except Exception:
            parsed["mood_score_estimate"] = fallback["mood_score_estimate"]

        return parsed