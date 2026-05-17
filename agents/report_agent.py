"""
===============================================================================
NeuroSense AI — Report Agent
===============================================================================
Purpose:
- Generate structured assessment report data.
- Generate structured solution/wellness report data.
- Does not diagnose.
===============================================================================
"""

import json
import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class ReportAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ReportAgent",
            temperature=0.25,
            max_tokens=1500,
        )

    # -------------------------------------------------------------------------

    def build_report_id(
        self,
        prefix: str,
        user_name: str = "USER"
    ) -> str:

        now = datetime.datetime.now()

        safe_name = "".join(
            c for c in user_name.upper()
            if c.isalnum()
        )[:6] or "USER"

        return f"{prefix}-{now.strftime('%Y%m%d%H%M')}-{safe_name}"

    # -------------------------------------------------------------------------

    def generate_assessment_report(
        self,
        user_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        fallback = {
            "report_id": self.build_report_id(
                "NSA",
                user_data.get("name", "USER")
            ),
            "report_type": "assessment",
            "generated_at": datetime.datetime.now().isoformat(),
            "summary": "Limited data available. This report is observational only.",
            "session_data": user_data.get("recent_sessions", []),
            "detected_emotions": user_data.get("emotion_freq", {}),
            "mood_trend": user_data.get("mood_trend", "stable"),
            "wellbeing_checkins": user_data.get("wellbeing_checkins", []),
            "conversation_history_summary": "Not enough data available.",
            "engagement_patterns": {
                "total_messages": user_data.get("total_messages", 0),
                "total_sessions": user_data.get("total_sessions", 0),
                "streak": user_data.get("streak", 0),
            },
            "risk_level": "low",
            "limitations": "This is not a diagnosis and does not replace professional care.",
        }

        prompt = f"""
You are the Assessment Report Agent for NeuroSense AI.

Generate an OBSERVATIONAL mental wellness assessment report.

{GLOBAL_SAFETY_RULES}

Use only the provided user data.
Do not diagnose.
Do not prescribe.
Do not invent details.
If data is limited, say so.

User data:
{json.dumps(user_data, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "report_type": "assessment",
  "summary": "observational summary",
  "session_data": {{
    "total_sessions": 0,
    "recent_session_summary": "short summary"
  }},
  "detected_emotions": {{
    "dominant_emotion": "emotion",
    "emotion_distribution": {{}},
    "interpretation": "non-diagnostic interpretation"
  }},
  "mood_trend": {{
    "trend": "improving | stable | declining | limited_data",
    "average_mood": 0,
    "interpretation": "short interpretation"
  }},
  "wellbeing_checkin_responses": {{
    "summary": "summary",
    "latest_score": 0,
    "risk_level": "low | medium | high"
  }},
  "conversation_history_summary": "short safe summary",
  "engagement_patterns": {{
    "total_messages": 0,
    "streak_days": 0,
    "engagement_level": "low | moderate | high"
  }},
  "limitations": "This is not a clinical diagnosis."
}}
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(raw, fallback=fallback)

        parsed["report_id"] = self.build_report_id(
            "NSA",
            user_data.get("name", "USER")
        )

        parsed["generated_at"] = datetime.datetime.now().isoformat()
        parsed["report_type"] = "assessment"

        return parsed

    # -------------------------------------------------------------------------

    def generate_solution_report(
        self,
        user_data: Dict[str, Any],
        wellness: Optional[Dict[str, Any]] = None,
        referral: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        wellness = wellness or {}
        referral = referral or {}

        fallback = {
            "report_id": self.build_report_id(
                "NSP",
                user_data.get("name", "USER")
            ),
            "report_type": "solution",
            "generated_at": datetime.datetime.now().isoformat(),
            "summary": "A safe wellness plan based on available data.",
            "top5_suggestions": wellness.get("top_practices", []),
            "daily_practices": [],
            "grounding_practices": [],
            "sleep_support": [],
            "social_support_plan": [],
            "professional_help": referral,
            "crisis_resources": [
                "Tele MANAS: 14416",
                "iCALL: 9152987821",
                "Vandrevala Foundation: +91 9999 666 555",
            ],
            "disclaimer": "This is not medical treatment or diagnosis.",
        }

        prompt = f"""
You are the Solution Report Agent for NeuroSense AI.

Generate a user-facing wellness plan.

{GLOBAL_SAFETY_RULES}

Use only the provided data.
Do not diagnose.
Do not prescribe.
Do not say this is medical treatment.

User data:
{json.dumps(user_data, ensure_ascii=False)}

Wellness recommendations:
{json.dumps(wellness, ensure_ascii=False)}

Professional referral guidance:
{json.dumps(referral, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "report_type": "solution",
  "summary": "short supportive summary",
  "top5_suggestions": [
    {{
      "title": "suggestion",
      "why": "why this helps",
      "how_to_do": "simple steps",
      "frequency": "daily/weekly/as needed"
    }}
  ],
  "daily_practices": ["practice1", "practice2"],
  "grounding_practices": ["practice1"],
  "sleep_support": ["suggestion1"],
  "social_support_plan": ["step1"],
  "professional_help": {{
    "recommended": true/false,
    "professional_type": "none | counsellor | psychologist | psychiatrist | emergency services",
    "reason": "short reason"
  }},
  "crisis_resources": ["resource1", "resource2"],
  "disclaimer": "not diagnosis or medical treatment"
}}

Rules:
- Exactly 5 top5_suggestions if possible.
- Include professional help if referral says it is needed.
- Use safe, practical language.
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(raw, fallback=fallback)

        parsed["report_id"] = self.build_report_id(
            "NSP",
            user_data.get("name", "USER")
        )

        parsed["generated_at"] = datetime.datetime.now().isoformat()
        parsed["report_type"] = "solution"

        return parsed