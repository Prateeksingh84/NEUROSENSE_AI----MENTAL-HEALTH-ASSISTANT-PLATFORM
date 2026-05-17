"""
===============================================================================
NeuroSense AI — Research Agent
===============================================================================

Purpose:
- Generate structured mental-health education/support answers.
- Uses Ollama local models.
- Works with Safety Agent + Hallucination Agent in app.py pipeline.

Important:
- No diagnosis.
- No medication advice.
- No psychiatrist impersonation.
===============================================================================
"""

import json
from typing import Any, Dict, List, Optional

from utils.ollama_client import (
    get_ollama_client,
    OLLAMA_RESEARCH_MODEL,
    STRICT_MENTAL_HEALTH_SYSTEM,
)


RESEARCH_SYSTEM_PROMPT = """
You are the Research Agent for NeuroSense AI.

You provide structured mental-health education and supportive wellness guidance.

Critical rules:
1. You are not a doctor, psychiatrist, therapist, or emergency service.
2. Do not diagnose the user.
3. Do not prescribe medication.
4. Do not say the user has depression, anxiety disorder, PTSD, bipolar disorder, etc.
5. Explain concepts in simple language.
6. Use only the given context.
7. If data is limited, say it is a limited observation.
8. If there is self-harm, suicide, immediate danger, abuse, or crisis, direct the user to urgent human support and crisis resources.
9. Keep the answer practical, calm, and safe.
10. Mention professional help when concerns are persistent, severe, unsafe, or medication-related.
"""


class ResearchAgent:
    def __init__(self, model: str = OLLAMA_RESEARCH_MODEL):
        self.model = model
        self.client = get_ollama_client()

    # -------------------------------------------------------------------------

    def run(
        self,
        query: str,
        wellbeing_data: Optional[Dict[str, Any]] = None,
        emotion: str = "neutral",
        template: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        safety: Optional[Dict[str, Any]] = None,
        professional_help: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        wellbeing_data = wellbeing_data or {}
        template = template or {}
        history = history or []
        safety = safety or {}
        professional_help = professional_help or {}

        if not self.client.is_available():
            return {
                "ok": False,
                "answer": (
                    "Ollama is not running right now. Please start Ollama using "
                    "`ollama serve` and make sure the selected model is installed."
                ),
                "model": self.model,
                "used_ollama": False,
                "sections": [],
            }

        if safety.get("risk_level") == "crisis":
            return {
                "ok": True,
                "answer": (
                    "Your safety matters most right now. I cannot handle crisis support "
                    "alone. Please contact someone you trust immediately or reach a crisis "
                    "helpline such as Tele MANAS 14416, iCALL 9152987821, or Vandrevala "
                    "+91 9999 666 555. If you are in immediate danger, call local emergency services."
                ),
                "model": self.model,
                "used_ollama": False,
                "sections": ["crisis"],
            }

        template_prompt = template.get("prompt", "")
        template_title = template.get("title", "Research Chat")

        prompt = f"""
Research task:
{query}

Selected template:
{template_title}

Template instruction:
{template_prompt}

Detected emotion:
{emotion}

Latest wellbeing check-in:
{json.dumps(wellbeing_data, ensure_ascii=False)}

Safety classification:
{json.dumps(safety, ensure_ascii=False)}

Professional help guidance:
{json.dumps(professional_help, ensure_ascii=False)}

Recent chat history:
{json.dumps(history[-6:], ensure_ascii=False)}

Return a structured answer in this format:

### 1. Simple Explanation
Explain the topic in simple language.

### 2. What May Be Happening
Give non-diagnostic possibilities based only on the context.

### 3. Safe Coping Steps
Give 3 to 5 practical, low-risk steps.

### 4. Reflection Prompt
Give 2 reflection questions.

### 5. When To Seek Professional Help
Explain when to speak with a counsellor, psychologist, psychiatrist, helpline, or emergency support.

### 6. Safety Note
Say clearly that this is not a diagnosis or medical treatment.

Do not diagnose.
Do not prescribe medication.
Do not claim certainty.
"""

        answer = self.client.generate(
            prompt=prompt,
            model=self.model,
            system=RESEARCH_SYSTEM_PROMPT,
            temperature=0.25,
            max_tokens=1500,
        )

        if not answer:
            answer = (
                "I could not generate a research response right now. Please check that "
                "Ollama is running and the selected model is available."
            )

        answer = self._post_filter(answer)

        return {
            "ok": True,
            "answer": answer,
            "model": self.model,
            "used_ollama": True,
            "template_id": template.get("id"),
            "template_title": template_title,
            "sections": [
                "explanation",
                "possible_context",
                "coping_steps",
                "reflection",
                "professional_help",
                "safety_note",
            ],
        }

    # -------------------------------------------------------------------------

    def _post_filter(self, text: str) -> str:
        """
        Simple unsafe phrase cleanup.
        """

        unsafe_replacements = {
            "you have depression": "you may be experiencing low mood",
            "you are depressed": "you may be feeling very low",
            "you have anxiety disorder": "you may be experiencing anxiety-like feelings",
            "you are bipolar": "your mood may feel intense or changeable",
            "take medication": "speak with a qualified doctor or psychiatrist about medication",
            "start medication": "speak with a qualified doctor or psychiatrist about treatment options",
            "stop medication": "speak with your prescribing doctor before making medication changes",
        }

        fixed = text

        for bad, good in unsafe_replacements.items():
            fixed = fixed.replace(bad, good)
            fixed = fixed.replace(bad.capitalize(), good.capitalize())

        return fixed.strip()