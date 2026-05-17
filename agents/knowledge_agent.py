"""
===============================================================================
NeuroSense AI — Knowledge Agent
===============================================================================

Purpose:
- Generate grounded but natural answers from approved mental-health KB only.
- Allow safe greetings / small talk.
- Answer user questions directly, not like a report.
- Uses Ollama if available.
- Falls back to a direct extractive answer if Ollama is unavailable.

Rules:
- Mental health / NeuroSense AI scope only
- No diagnosis
- No medication advice
- No psychiatrist impersonation
- No unsupported claims
===============================================================================
"""

from typing import Any, Dict, List, Optional

from knowledge.retriever import retrieve_knowledge, build_context_from_results
from utils.ollama_client import get_ollama_client, OLLAMA_RESEARCH_MODEL


KNOWLEDGE_AGENT_SYSTEM = """
You are the NeuroSense AI Knowledge Agent.

You are a warm, practical, grounded mental-wellbeing assistant.

You answer ONLY from:
1. Approved NeuroSense AI mental-health knowledge context
2. User-uploaded NeuroSense report context
3. Safe small-talk boundaries

Strict rules:
- Do not diagnose.
- Do not prescribe or recommend medication.
- Do not claim to be a psychiatrist, doctor, psychologist, or emergency service.
- Do not answer unrelated topics.
- Do not make major life/work decisions for the user.
- Help the user think through the decision safely.
- Keep the answer natural and conversational.
- Prefer direct practical guidance over report-style sections.
- If user asks "what should I do", say "I cannot decide for you, but..."
- For crisis/self-harm danger, prioritize immediate human support.
"""


class KnowledgeAgent:
    def __init__(self, model: str = OLLAMA_RESEARCH_MODEL):
        self.model = model
        self.client = get_ollama_client()

    def run(
        self,
        query: str,
        scope_result: Optional[Dict[str, Any]] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        scope_result = scope_result or {}
        query = str(query or "").strip()
        response_type = scope_result.get("response_type", "")

        if not query:
            return {
                "ok": False,
                "answer": "Please enter a mental-health or NeuroSense AI related question.",
                "sources": [],
                "used_ollama": False,
                "model": self.model,
                "grounded": False,
                "scope": scope_result,
            }

        if response_type in ["greeting", "thanks", "bye", "help", "smalltalk"]:
            return self._smalltalk_response(
                response_type=response_type,
                scope_result=scope_result,
            )

        if response_type == "crisis":
            return {
                "ok": True,
                "answer": (
                    "I’m really sorry you’re feeling this way. Your safety matters most right now. "
                    "Please contact a trusted person immediately and avoid being alone if possible. "
                    "If you are in immediate danger, call local emergency services. In India, you can contact "
                    "Tele MANAS at 14416 or 1800-891-4416, iCALL at 9152987821, Vandrevala Foundation at "
                    "+91 9999 666 555, KIRAN at 1800-599-0019, or AASRA at 022-27546669.\n\n"
                    "NeuroSense AI cannot provide emergency intervention. Please seek immediate human support."
                ),
                "sources": [{"id": "crisis_safety", "title": "Crisis Safety"}],
                "used_ollama": False,
                "model": self.model,
                "grounded": True,
                "scope": scope_result,
            }

        if response_type == "diagnosis_boundary":
            return {
                "ok": True,
                "answer": (
                    "I can’t diagnose you or confirm whether you have a mental health condition. "
                    "But I can help you reflect on what you’re experiencing and organize your thoughts safely. "
                    "If these feelings are intense, repeated, or affecting daily life, it would be better to speak "
                    "with a licensed psychologist, psychiatrist, counsellor, or qualified mental health professional."
                ),
                "sources": [{"id": "professional_help", "title": "Professional Help Guidance"}],
                "used_ollama": False,
                "model": self.model,
                "grounded": True,
                "scope": scope_result,
            }

        if response_type == "medication_boundary":
            return {
                "ok": True,
                "answer": (
                    "I can’t recommend medicines, dosages, or tell you to start, stop, increase, or reduce medication. "
                    "Medication decisions should only be made with a qualified doctor or psychiatrist. "
                    "I can still help with non-medication support like grounding, journaling, sleep routine, "
                    "stress reduction, and preparing questions for a professional."
                ),
                "sources": [{"id": "professional_help", "title": "Professional Help Guidance"}],
                "used_ollama": False,
                "model": self.model,
                "grounded": True,
                "scope": scope_result,
            }

        results = retrieve_knowledge(query, top_k=top_k)

        if not results:
            return {
                "ok": True,
                "answer": (
                    "I don’t have enough approved NeuroSense AI knowledge to answer that safely. "
                    "You can ask me about stress, anxiety-like feelings, sleep, loneliness, academic pressure, "
                    "mood tracking, assessment reports, wellness plans, professional help, or crisis safety."
                ),
                "sources": [],
                "used_ollama": False,
                "model": self.model,
                "grounded": False,
                "scope": scope_result,
            }

        context = build_context_from_results(results)

        if self.client.is_available():
            answer = self._generate_with_ollama(query, context, scope_result)
            used_ollama = True
        else:
            answer = self._extractive_fallback(query, results)
            used_ollama = False

        answer = self._post_filter(answer)

        sources = [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "score": item.get("score"),
            }
            for item in results
        ]

        return {
            "ok": True,
            "answer": answer,
            "sources": sources,
            "used_ollama": used_ollama,
            "model": self.model,
            "grounded": True,
            "scope": scope_result,
        }

    def _smalltalk_response(
        self,
        response_type: str,
        scope_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        scope_result = scope_result or {}

        if response_type == "greeting":
            answer = (
                "Hi 👋 I’m NeuroSense Knowledge Chat. "
                "You can talk to me about stress, mood, sleep, anxiety-like feelings, burnout, reports, "
                "wellness plans, coping practices, and professional-help guidance."
            )

        elif response_type == "thanks":
            answer = (
                "You’re welcome 😊 I’m here to help with NeuroSense AI and mental-wellbeing questions."
            )

        elif response_type == "bye":
            answer = (
                "Take care 👋 Small consistent steps matter. You can come back anytime for support."
            )

        elif response_type == "help":
            answer = (
                "I’m NeuroSense Knowledge Chat 📚. I answer only from approved NeuroSense AI and mental-health knowledge. "
                "You can ask about stress, sleep, anxiety-like feelings, loneliness, academic pressure, mood tracking, "
                "assessment reports, wellness plans, professional help, and crisis safety."
            )

        else:
            answer = (
                "I’m here with you. Ask me a NeuroSense AI or mental-health related question, "
                "and I’ll answer using approved knowledge only."
            )

        return {
            "ok": True,
            "answer": answer,
            "sources": [{"id": "safe_smalltalk", "title": "Safe Knowledge Chat Interaction"}],
            "used_ollama": False,
            "model": "smalltalk_rule",
            "grounded": True,
            "scope": scope_result,
        }

    def _generate_with_ollama(
        self,
        query: str,
        context: str,
        scope_result: Dict[str, Any],
    ) -> str:
        prompt = f"""
APPROVED KNOWLEDGE CONTEXT:
{context}

SCOPE RESULT:
{scope_result}

USER QUESTION:
{query}

Write a natural, direct, practical answer to the user's question.

Important output rules:
- Do NOT write in report format.
- Do NOT use headings like "1. Direct Answer", "2. Practical Support Steps", or "Source Basis".
- Answer like a supportive chatbot.
- Start by directly responding to the user's actual question.
- If the user asks whether they should leave work, take leave, or go on a trip, do NOT decide for them.
- Say: "I can’t decide for you, but..."
- Give balanced decision support:
  1. pause and check how intense the distress is,
  2. avoid leaving work suddenly if urgent responsibilities are pending,
  3. consider asking for short leave, a lighter day, or a planned break,
  4. a short trip can help if it is for rest and recovery,
  5. if distress is intense, persistent, or unsafe, talk to a trusted person or professional.
- Keep the answer 6-9 sentences.
- Use only the approved context.
- Do not diagnose.
- Do not prescribe medication.
- Do not make major decisions for the user.
- End with a short safety/professional-help note only if relevant.
"""

        answer = self.client.generate(
            prompt=prompt,
            model=self.model,
            system=KNOWLEDGE_AGENT_SYSTEM,
            temperature=0.25,
            max_tokens=500,
        )

        if not answer:
            return self._extractive_fallback(query, retrieve_knowledge(query))

        return answer

    def _extractive_fallback(
        self,
        query: str,
        results: List[Dict[str, Any]],
    ) -> str:
        query_lower = str(query or "").lower()

        if any(word in query_lower for word in ["trip", "leave", "work", "vacation", "break"]):
            return (
                "I can’t decide for you, but since you’re not feeling well mentally, it makes sense to pause "
                "and check what kind of support you need right now. If you feel mentally exhausted or burned out, "
                "a short rest, planned leave, or a small trip may help you recover. But try not to leave work suddenly "
                "if there are urgent responsibilities, financial pressure, or something that may create more stress later. "
                "A safer step could be to take a short break first, breathe, drink water, and then see if you can request "
                "a half-day, one-day leave, or a planned break. If the trip is for rest, sleep, and emotional recovery, "
                "it can be supportive; if it is only to escape a serious ongoing problem, it may not solve the root issue. "
                "If this mental distress feels intense, keeps repeating, or you feel unsafe, please talk to a trusted person "
                "or a mental health professional."
            )

        top = results[0]
        content = str(top.get("content", "")).strip()
        safety = str(top.get("safety_note", "")).strip()

        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        selected = " ".join(paragraphs[:2])

        return (
            f"{selected}\n\n"
            "A safe next step is to pause, notice what you are feeling, and choose one small supportive action "
            "instead of forcing a big decision immediately. If the concern feels severe, repeated, unsafe, or starts "
            "affecting daily life, speaking with a counsellor, psychologist, psychiatrist, or qualified professional "
            f"would be a better step. {safety}"
        )

    def _post_filter(self, text: str) -> str:
        text = str(text or "").strip()

        replacements = {
            "you have depression": "you may be experiencing low mood",
            "you are depressed": "you may be feeling very low",
            "you have anxiety disorder": "you may be experiencing anxiety-like feelings",
            "you are bipolar": "your mood may feel intense or changeable",
            "take medication": "speak with a qualified doctor or psychiatrist about medication",
            "start medication": "speak with a qualified doctor or psychiatrist about treatment options",
            "stop medication": "speak with your prescribing doctor before making medication changes",
            "increase medication": "speak with your prescribing doctor before medication changes",
            "reduce medication": "speak with your prescribing doctor before medication changes",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)
            text = text.replace(bad.capitalize(), good.capitalize())

        # Remove rigid report headings if Ollama still outputs them.
        unwanted = [
            "1. Direct Answer",
            "2. Practical Support Steps",
            "3. When To Seek Professional Help",
            "4. Safety Note",
            "5. Source Basis",
            "### 1. Direct Answer",
            "### 2. Practical Support Steps",
            "### 3. When To Seek Professional Help",
            "### 4. Safety Note",
            "### 5. Source Basis",
        ]

        for item in unwanted:
            text = text.replace(item, "").strip()

        return text