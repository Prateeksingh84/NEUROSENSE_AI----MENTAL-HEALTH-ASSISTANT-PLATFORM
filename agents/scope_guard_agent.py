"""
===============================================================================
NeuroSense AI — Scope Guard Agent
===============================================================================

Purpose:
- Keep Knowledge Chat inside mental-health / NeuroSense AI scope.
- Allow friendly small talk.
- Allow real-life wellbeing questions like:
  "I am mentally not well, should I take leave or go for a trip?"
- Block unrelated topics.
- Detect crisis, diagnosis, and medication boundaries.
===============================================================================
"""

import re
from typing import Dict, List


GREETING_KEYWORDS = [
    "hi", "hii", "hiii", "hello", "hey", "heyy",
    "good morning", "good afternoon", "good evening",
    "namaste", "yo", "sup",
]

THANKS_KEYWORDS = [
    "thanks", "thank you", "thankyou", "thx", "appreciate it",
]

BYE_KEYWORDS = [
    "bye", "goodbye", "see you", "see ya", "take care", "talk later",
]

HELP_KEYWORDS = [
    "help", "what can you do", "how can you help",
    "who are you", "what is knowledge chat", "what can i ask",
]

MENTAL_HEALTH_SCOPE_KEYWORDS = [
    # direct mental-health words
    "mental", "mentally", "mental health", "not feeling well mentally",
    "not feeling good mentally", "not okay mentally",
    "health", "wellbeing", "well-being", "wellness",
    "emotion", "emotional", "mood", "feeling low", "feel low",
    "sad", "sadness", "depressed", "depression",

    # stress / overwhelm / burnout
    "stress", "stressed", "stressful", "pressure", "overloaded",
    "overwhelmed", "burnout", "burned out", "exhausted",
    "mentally tired", "mentally exhausted", "drained", "tired mentally",

    # anxiety-like
    "anxiety", "anxious", "panic", "fear", "nervous", "overthinking",

    # sleep
    "sleep", "insomnia", "can't sleep", "tired", "fatigue",

    # social / personal
    "lonely", "loneliness", "alone", "relationship", "social support",

    # coping / support / real-life wellbeing decisions
    "coping", "cope", "grounding", "breathing", "journal", "journaling",
    "break", "take a break", "rest", "leave", "leave work",
    "work break", "trip", "vacation", "travel", "go for a trip",
    "should i go", "should i take leave", "should i rest",

    # work / academic pressure when connected to wellbeing
    "work stress", "office stress", "job stress", "workload",
    "work pressure", "academic", "exam", "study", "college",

    # professional help
    "therapy", "therapist", "counsellor", "counselor",
    "psychologist", "psychiatrist", "professional help",

    # safety
    "crisis", "self harm", "self-harm", "suicide", "unsafe",

    # app/report scope
    "neurosense", "report", "check-in", "checkin", "wellbeing score",
    "mood trend", "emotion detection", "assessment",
    "solution report", "wellness plan", "personalized wellness",
]

OUT_OF_SCOPE_KEYWORDS = [
    "capital of", "stock", "crypto", "movie", "recipe",
    "sports", "football", "cricket score", "programming", "python code",
    "hack", "exploit", "loan", "insurance", "politics", "election",
    "celebrity", "game cheat",
]

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "self harm", "self-harm",
    "hurt myself", "i want to die", "don't want to live", "unsafe",
    "harm myself", "ending it", "no reason to live",
]

DIAGNOSIS_KEYWORDS = [
    "diagnose me", "do i have depression", "do i have anxiety",
    "am i depressed", "am i bipolar", "do i have ptsd",
    "what disorder do i have", "clinical diagnosis",
]

MEDICATION_KEYWORDS = [
    "which medicine", "what medicine", "medication dose", "dosage",
    "should i take medicine", "start medicine", "stop medicine",
    "increase dose", "reduce dose", "antidepressant", "sleeping pill",
]


class ScopeGuardAgent:
    def __init__(self):
        self.greeting_keywords = GREETING_KEYWORDS
        self.thanks_keywords = THANKS_KEYWORDS
        self.bye_keywords = BYE_KEYWORDS
        self.help_keywords = HELP_KEYWORDS
        self.scope_keywords = MENTAL_HEALTH_SCOPE_KEYWORDS
        self.out_of_scope_keywords = OUT_OF_SCOPE_KEYWORDS
        self.crisis_keywords = CRISIS_KEYWORDS
        self.diagnosis_keywords = DIAGNOSIS_KEYWORDS
        self.medication_keywords = MEDICATION_KEYWORDS

    def run(self, query: str) -> Dict:
        return self.analyze(query)

    def analyze(self, query: str) -> Dict:
        text = str(query or "").strip()
        lowered = " ".join(text.lower().split())

        if not text:
            return {
                "allowed": False,
                "scope": "empty",
                "risk_level": "none",
                "reason": "Empty question.",
                "response_type": "empty",
                "matched": [],
            }

        matched_crisis = self._matches_any(lowered, self.crisis_keywords)

        if matched_crisis:
            return {
                "allowed": True,
                "scope": "crisis_safety",
                "risk_level": "crisis",
                "reason": "Crisis or self-harm related wording detected.",
                "response_type": "crisis",
                "matched": matched_crisis,
            }

        matched_greeting = self._matches_any(lowered, self.greeting_keywords)
        matched_thanks = self._matches_any(lowered, self.thanks_keywords)
        matched_bye = self._matches_any(lowered, self.bye_keywords)
        matched_help = self._matches_any(lowered, self.help_keywords)

        if self._is_short_smalltalk(
            lowered,
            matched_greeting,
            matched_thanks,
            matched_bye,
            matched_help,
        ):
            response_type = "smalltalk"

            if matched_greeting:
                response_type = "greeting"
            elif matched_thanks:
                response_type = "thanks"
            elif matched_bye:
                response_type = "bye"
            elif matched_help:
                response_type = "help"

            return {
                "allowed": True,
                "scope": "safe_smalltalk",
                "risk_level": "none",
                "reason": "Safe greeting/small-talk allowed.",
                "response_type": response_type,
                "matched": matched_greeting + matched_thanks + matched_bye + matched_help,
            }

        matched_scope = self._matches_any(lowered, self.scope_keywords)
        matched_out = self._matches_any(lowered, self.out_of_scope_keywords)
        matched_diagnosis = self._matches_any(lowered, self.diagnosis_keywords)
        matched_medication = self._matches_any(lowered, self.medication_keywords)

        if matched_medication:
            return {
                "allowed": True,
                "scope": "mental_health_medication_boundary",
                "risk_level": "medium",
                "reason": "Medication-related question detected.",
                "response_type": "medication_boundary",
                "matched": matched_medication,
            }

        if matched_diagnosis:
            return {
                "allowed": True,
                "scope": "mental_health_diagnosis_boundary",
                "risk_level": "medium",
                "reason": "Diagnosis request detected.",
                "response_type": "diagnosis_boundary",
                "matched": matched_diagnosis,
            }

        # If out-of-scope words appear but the user also has mental-health context,
        # allow it because the wellbeing context is the actual intent.
        if matched_out and not matched_scope:
            return {
                "allowed": False,
                "scope": "out_of_scope",
                "risk_level": "none",
                "reason": "Question is outside NeuroSense AI mental-health scope.",
                "response_type": "refusal",
                "matched": matched_out,
            }

        if matched_scope:
            return {
                "allowed": True,
                "scope": "mental_health",
                "risk_level": "low",
                "reason": "Question is within approved mental-health/wellbeing scope.",
                "response_type": "knowledge_answer",
                "matched": matched_scope[:10],
            }

        return {
            "allowed": False,
            "scope": "unclear",
            "risk_level": "none",
            "reason": "Question does not clearly match approved mental-health scope.",
            "response_type": "refusal",
            "matched": [],
        }

    def _is_short_smalltalk(
        self,
        text: str,
        greetings: List[str],
        thanks: List[str],
        byes: List[str],
        helps: List[str],
    ) -> bool:
        words = text.split()

        if greetings and len(words) <= 6:
            return True

        if thanks and len(words) <= 8:
            return True

        if byes and len(words) <= 8:
            return True

        if helps and len(words) <= 10:
            return True

        return False

    def _matches_any(self, text: str, phrases: List[str]) -> List[str]:
        matched = []

        for phrase in phrases:
            p = phrase.lower().strip()

            if not p:
                continue

            if " " in p:
                if p in text:
                    matched.append(phrase)
            else:
                # Allow soft matching for these real-life wellbeing terms.
                if p in ["mental", "mentally", "stress", "stressed", "trip", "break", "leave", "work"]:
                    if p in text:
                        matched.append(phrase)
                else:
                    if re.search(rf"\b{re.escape(p)}\b", text):
                        matched.append(phrase)

        return matched

    def refusal_message(self) -> str:
        return (
            "I can only answer questions related to NeuroSense AI and mental-health/wellbeing areas "
            "such as stress, anxiety-like feelings, sleep, loneliness, emotions, mood tracking, "
            "coping skills, professional help, crisis safety, reports, and app usage. "
            "Please ask a question within those areas."
        )

    def crisis_message(self) -> str:
        return (
            "Your safety matters most right now. I cannot support a crisis alone. "
            "Please contact a trusted person immediately, move away from anything that could be used for harm, "
            "and call local emergency services if you are in immediate danger. In India, you can contact "
            "Tele MANAS at 14416 or 1800-891-4416, iCALL at 9152987821, Vandrevala Foundation at "
            "+91 9999 666 555, KIRAN at 1800-599-0019, or AASRA at 022-27546669."
        )

    def diagnosis_boundary_message(self) -> str:
        return (
            "I cannot diagnose you or confirm whether you have a mental health condition. "
            "I can explain common signs in general terms and help you reflect safely. "
            "For a diagnosis or clinical assessment, please speak with a licensed psychologist, "
            "psychiatrist, or qualified mental health professional."
        )

    def medication_boundary_message(self) -> str:
        return (
            "I cannot recommend medicines, dosages, or tell you to start, stop, increase, or reduce medication. "
            "Medication decisions should only be made with a qualified doctor or psychiatrist. "
            "I can still share general wellness support and coping practices that do not involve medication."
        )


if __name__ == "__main__":
    agent = ScopeGuardAgent()

    tests = [
        "hi",
        "I am not feeling well mentally should I leave work and go for a trip?",
        "I am stressed at work should I take a break?",
        "Should I go for vacation because I feel burned out?",
        "What is capital of France?",
    ]

    for q in tests:
        print(q, "=>", agent.analyze(q))