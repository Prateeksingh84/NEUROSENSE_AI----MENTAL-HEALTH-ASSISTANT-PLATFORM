"""
===============================================================================
NeuroSense AI — Hallucination Checker Agent
===============================================================================
Purpose:
- Validate final response before showing user.
- Remove diagnosis, medication advice, unsupported claims.
===============================================================================
"""

import json
import re
from typing import Any, Dict, Optional

from agents.base_agent import BaseAgent, GLOBAL_SAFETY_RULES


class HallucinationAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="HallucinationCheckerAgent",
            temperature=0.0,
            max_tokens=800,
        )

    # -------------------------------------------------------------------------

    def safe_support_fallback(self) -> str:
        """
        Safe fallback response used when the draft contains diagnosis,
        medication advice, unsafe crisis guidance, or unsupported medical claims.
        """

        return (
            "I’m here to support you, but I can’t diagnose conditions, prescribe "
            "medication, or replace help from a qualified mental-health professional. "
            "What you’re feeling matters, and it may help to talk to a trusted person "
            "or a licensed professional. If you feel at risk of harming yourself or "
            "someone else, please contact local emergency services or a crisis helpline "
            "immediately."
        )

    # -------------------------------------------------------------------------

    def contains_unsafe_medical_claim(self, text: str) -> bool:
        """
        Deterministically detects unsafe mental-health / medical claims.

        Returns True if the reply:
        - Diagnoses the user
        - Prescribes medication or dosage changes
        - Claims guaranteed cure
        - Discourages professional help
        - Gives unsafe crisis/self-harm advice
        """

        if not text:
            return False

        text_lower = str(text).lower()
        text_lower = re.sub(r"\s+", " ", text_lower).strip()

        unsafe_patterns = [
            # Diagnosis claims
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

            # Medication / prescription advice
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

            # Guaranteed cure / unsupported certainty
            r"\bguaranteed cure\b",
            r"\bthis will cure you\b",
            r"\bthis will definitely cure\b",
            r"\byou will be cured\b",
            r"\b100% effective\b",
            r"\bcompletely safe\b",
            r"\bno side effects\b",
            r"\bthis always works\b",

            # Discouraging professional help
            r"\byou do not need a doctor\b",
            r"\byou don't need a doctor\b",
            r"\byou do not need therapy\b",
            r"\byou don't need therapy\b",
            r"\bavoid seeing a doctor\b",
            r"\bavoid therapy\b",
            r"\bignore your therapist\b",
            r"\bdo not tell anyone\b",
            r"\bdon't tell anyone\b",

            # Unsafe crisis/self-harm guidance
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

        for pattern in unsafe_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    # -------------------------------------------------------------------------

    def deterministic_check(self, draft_reply: str) -> Dict[str, Any]:
        """
        Fast rule-based hallucination and safety check before LLM verification.
        """

        if self.contains_unsafe_medical_claim(draft_reply):
            return {
                "safe": False,
                "issues": [
                    "Unsafe medical or diagnostic claim detected."
                ],
                "corrected_reply": self.safe_support_fallback(),
            }

        return {
            "safe": True,
            "issues": [],
            "corrected_reply": draft_reply,
        }

    # -------------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        draft_reply: str,
        safety: Dict[str, Any],
        emotion_analysis: Dict[str, Any],
        social_analysis: Dict[str, Any],
        wellness: Dict[str, Any],
        referral: Dict[str, Any],
        wellbeing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        wellbeing_data = wellbeing_data or {}

        deterministic = self.deterministic_check(draft_reply)

        if not deterministic["safe"]:
            return deterministic

        prompt = f"""
You are the Hallucination Checker Agent for NeuroSense AI.

Check whether the draft reply is safe and grounded.

{GLOBAL_SAFETY_RULES}

Allowed context:
User message:
{user_message}

Safety:
{json.dumps(safety, ensure_ascii=False)}

Emotion analysis:
{json.dumps(emotion_analysis, ensure_ascii=False)}

Social analysis:
{json.dumps(social_analysis, ensure_ascii=False)}

Wellness:
{json.dumps(wellness, ensure_ascii=False)}

Referral:
{json.dumps(referral, ensure_ascii=False)}

Wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Draft reply:
{draft_reply}

Return ONLY valid JSON:
{{
  "safe": true/false,
  "issues": ["issue1"],
  "corrected_reply": "safe corrected response"
}}

Unsafe if:
- Diagnoses user
- Prescribes or changes medication
- Claims certainty without evidence
- Pretends to be a psychiatrist
- Gives unsafe crisis advice
- Invents facts not present in context
"""

        raw = self.call_llm(prompt)

        parsed = self.parse_json(raw, fallback=deterministic)

        corrected = parsed.get("corrected_reply") or draft_reply

        if self.contains_unsafe_medical_claim(corrected):
            parsed["safe"] = False
            parsed["issues"] = parsed.get("issues", []) + [
                "Corrected reply still contained unsafe medical claim."
            ]
            parsed["corrected_reply"] = self.safe_support_fallback()

        return parsed