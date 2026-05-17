"""
===============================================================================
NeuroSense AI — Template Agent
===============================================================================

Purpose:
- Select best mental-health template for a query.
- Validate custom template usage.
- Build final prompt package for Research Agent.

Uses:
- Local logic first
- Optional Ollama classification if needed
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from utils.template_store import (
    list_all_templates,
    get_template,
    TEMPLATE_CATEGORIES,
)
from utils.ollama_client import (
    get_ollama_client,
    OLLAMA_FAST_MODEL,
    parse_json_safely,
)


class TemplateAgent:
    def __init__(self, model: str = OLLAMA_FAST_MODEL):
        self.model = model
        self.client = get_ollama_client()

    # -------------------------------------------------------------------------

    def select_template(
        self,
        query: str,
        user_id: Optional[str] = None,
        requested_template_id: Optional[str] = None,
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Returns selected template dict.
        """

        wellbeing_data = wellbeing_data or {}

        if requested_template_id:
            template = get_template(
                requested_template_id,
                user_id=user_id,
            )

            if template:
                return {
                    "ok": True,
                    "template": template,
                    "selection_method": "explicit",
                }

        templates = list_all_templates(user_id=user_id)

        category = self._detect_category_by_keywords(
            query=query,
            wellbeing_data=wellbeing_data,
        )

        for template in templates:
            if template.get("category") == category:
                return {
                    "ok": True,
                    "template": template,
                    "selection_method": "keyword",
                }

        # fallback to first stress template
        for template in templates:
            if template.get("id") == "stress_management_plan":
                return {
                    "ok": True,
                    "template": template,
                    "selection_method": "fallback",
                }

        return {
            "ok": False,
            "template": {},
            "selection_method": "none",
        }

    # -------------------------------------------------------------------------

    def _detect_category_by_keywords(
        self,
        query: str,
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        text = (query or "").lower()
        wellbeing_data = wellbeing_data or {}

        concerns = wellbeing_data.get("concerns", []) or []
        mood = str(wellbeing_data.get("mood", "")).lower()
        sleep = str(wellbeing_data.get("sleep", "")).lower()

        if any(word in text for word in ["sleep", "insomnia", "tired", "night", "wake up"]) or sleep in ["poor", "very_poor"]:
            return "sleep"

        if any(word in text for word in ["anxiety", "anxious", "panic", "fear", "overthinking", "nervous"]) or mood == "anxious":
            return "anxiety"

        if any(word in text for word in ["stress", "overwhelmed", "pressure", "burnout"]) or mood == "overwhelmed":
            return "stress"

        if any(word in text for word in ["alone", "lonely", "loneliness", "isolated"]) or "loneliness" in concerns:
            return "loneliness"

        if any(word in text for word in ["exam", "study", "college", "assignment", "academic"]) or "academic_pressure" in concerns:
            return "academic_pressure"

        if any(word in text for word in ["relationship", "breakup", "partner", "friendship"]) or "relationship" in concerns:
            return "relationship"

        if any(word in text for word in ["confidence", "self doubt", "worthless", "not good enough"]) or "self_doubt" in concerns:
            return "self_doubt"

        if any(word in text for word in ["anger", "angry", "rage", "irritated"]):
            return "anger"

        if any(word in text for word in ["journal", "mood", "track"]):
            return "mood_tracking"

        if any(word in text for word in ["psychiatrist", "psychologist", "counsellor", "professional", "therapy"]):
            return "professional_help"

        if any(word in text for word in ["suicide", "kill myself", "hurt myself", "self harm", "unsafe"]):
            return "crisis_safety"

        return "stress"

    # -------------------------------------------------------------------------

    def classify_with_ollama(
        self,
        query: str,
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optional model-based template classification.
        """

        wellbeing_data = wellbeing_data or {}

        fallback_category = self._detect_category_by_keywords(
            query,
            wellbeing_data,
        )

        if not self.client.is_available():
            return {
                "category": fallback_category,
                "confidence": "low",
                "reason": "Ollama unavailable; used keyword classifier.",
            }

        prompt = f"""
Classify this NeuroSense AI research request into one category.

Allowed categories:
{json.dumps(TEMPLATE_CATEGORIES)}

User query:
{query}

Wellbeing data:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Return ONLY JSON:
{{
  "category": "one allowed category",
  "confidence": "low | medium | high",
  "reason": "short reason"
}}
"""

        raw = self.client.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.0,
            max_tokens=300,
        )

        parsed = parse_json_safely(
            raw,
            fallback={
                "category": fallback_category,
                "confidence": "low",
                "reason": "Fallback keyword classification.",
            }
        )

        if parsed.get("category") not in TEMPLATE_CATEGORIES:
            parsed["category"] = fallback_category

        return parsed

    # -------------------------------------------------------------------------

    def build_template_context(
        self,
        query: str,
        template: Dict[str, Any],
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        wellbeing_data = wellbeing_data or {}

        return {
            "query": query,
            "template_id": template.get("id"),
            "template_title": template.get("title"),
            "template_category": template.get("category"),
            "template_output_type": template.get("output_type"),
            "template_instruction": template.get("prompt"),
            "wellbeing_context": wellbeing_data,
            "safe_output_rules": [
                "Do not diagnose.",
                "Do not prescribe medication.",
                "Do not pretend to be a psychiatrist.",
                "Give general mental-health education only.",
                "Recommend professional help when needed.",
            ],
        }