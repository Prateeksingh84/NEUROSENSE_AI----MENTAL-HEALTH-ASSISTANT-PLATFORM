"""
===============================================================================
NeuroSense AI — Social Wellbeing Agent
===============================================================================
Purpose:
- Analyze loneliness, support availability, relationship/family/academic stress.
- Suggest social support level without diagnosing.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class SocialAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="SocialAgent",
            temperature=0.1,
            max_tokens=650,
        )

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        wellbeing_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}
        history = self.clean_history(history)

        concerns = wellbeing_data.get("concerns", []) or []
        support_available = wellbeing_data.get("support_available", "unknown")
        social_score = wellbeing_data.get("social_connection", None)

        fallback = {
            "social_risk": "medium" if support_available in ["no", "maybe"] else "low",
            "support_availability": support_available,
            "main_social_factors": concerns,
            "summary": "Social support may be useful based on the current check-in.",
            "recommended_support_action": "Consider talking to a trusted person if comfortable.",
        }

        prompt = f"""
You are the Social Wellbeing Agent for NeuroSense AI.

{GLOBAL_SAFETY_RULES}

Analyze social wellbeing using only this context.
Do not diagnose.

User message:
{user_message}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "social_risk": "low | medium | high",
  "support_availability": "yes | maybe | no | unknown",
  "main_social_factors": ["factor1", "factor2"],
  "summary": "short non-diagnostic summary",
  "recommended_support_action": "one practical safe action"
}}

Rules:
- If support_available is "no", social_risk should usually be medium or high.
- If loneliness/family/relationship concerns appear, mention them as factors.
- Do not overstate certainty.
"""

        raw = self.call_llm(prompt)

        return self.parse_json(raw, fallback=fallback)