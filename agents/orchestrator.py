"""
===============================================================================
NeuroSense AI — Agent Orchestrator
===============================================================================
This is the main multi-agent pipeline.

Flow:
1. Safety Agent
2. Emotion Agent
3. Social Agent
4. Therapy Agent
5. Wellness Agent
6. Clinical Escalation Agent
7. Hallucination Checker
8. Final safe response

Use this from app.py instead of direct ai_reply().
===============================================================================
"""

from typing import Any, Dict, List, Optional

from agents.safety_agent import SafetyAgent
from agents.emotion_agent import EmotionAgent
from agents.social_agent import SocialAgent
from agents.therapy_agent import TherapyAgent
from agents.wellness_agent import WellnessAgent
from agents.psychiatrist_agent import PsychiatristAgent
from agents.hallucination_agent import HallucinationAgent


def run_safe_therapy_pipeline(
    user_message: str,
    emotion: str = "neutral",
    wellbeing_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    lang: str = "en",
    include_trace: bool = True,
) -> Dict[str, Any]:
    """
    Main NeuroSense AI agent pipeline.

    Returns:
    {
        "reply": "...",
        "safe": true,
        "risk_level": "...",
        "agents": {...},
        "wellness": {...},
        "referral": {...}
    }
    """

    wellbeing_data = wellbeing_data or {}
    history = history or []

    # -------------------------------------------------------------------------
    # Initialize agents
    # -------------------------------------------------------------------------

    safety_agent = SafetyAgent()
    emotion_agent = EmotionAgent()
    social_agent = SocialAgent()
    therapy_agent = TherapyAgent()
    wellness_agent = WellnessAgent()
    psychiatrist_agent = PsychiatristAgent()
    hallucination_agent = HallucinationAgent()

    trace = {}

    # -------------------------------------------------------------------------
    # 1. Safety
    # -------------------------------------------------------------------------

    safety = safety_agent.run(
        user_message=user_message,
        emotion=emotion,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    trace["safety_agent"] = safety

    if safety.get("risk_level") == "crisis":
        crisis_reply = safety_agent.crisis_response()

        return {
            "reply": crisis_reply,
            "safe": True,
            "risk_level": "crisis",
            "response_type": "crisis",
            "agents": trace if include_trace else {},
            "wellness": {},
            "referral": {
                "needs_professional_referral": True,
                "urgency": "emergency",
                "recommended_professional": "emergency services or crisis helpline",
            },
        }

    # -------------------------------------------------------------------------
    # 2. Emotion Analysis
    # -------------------------------------------------------------------------

    emotion_analysis = emotion_agent.run(
        user_message=user_message,
        detected_emotion=emotion,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    trace["emotion_agent"] = emotion_analysis

    # -------------------------------------------------------------------------
    # 3. Social Wellbeing Analysis
    # -------------------------------------------------------------------------

    social_analysis = social_agent.run(
        user_message=user_message,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    trace["social_agent"] = social_analysis

    # -------------------------------------------------------------------------
    # 4. Wellness Recommendations
    # -------------------------------------------------------------------------

    wellness = wellness_agent.run(
        user_message=user_message,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellbeing_data=wellbeing_data,
    )

    trace["wellness_agent"] = wellness

    # -------------------------------------------------------------------------
    # 5. Clinical Escalation / Professional Help Guidance
    # -------------------------------------------------------------------------

    referral = psychiatrist_agent.run(
        user_message=user_message,
        safety=safety,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    trace["clinical_escalation_agent"] = referral

    # -------------------------------------------------------------------------
    # 6. Therapy Response Draft
    # -------------------------------------------------------------------------

    therapy = therapy_agent.run(
        user_message=user_message,
        safety=safety,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellbeing_data=wellbeing_data,
        history=history,
        lang=lang,
    )

    draft_reply = therapy.get(
        "reply",
        therapy_agent.safe_support_fallback()
    )

    # Add referral message only when needed and not already crisis
    referral_msg = referral.get("user_facing_message", "")

    if referral.get("needs_professional_referral") and referral_msg:
        if referral_msg not in draft_reply:
            draft_reply = draft_reply.strip() + "\n\n" + referral_msg.strip()

    trace["therapy_agent"] = therapy

    # -------------------------------------------------------------------------
    # 7. Hallucination Check
    # -------------------------------------------------------------------------

    hallucination_check = hallucination_agent.run(
        user_message=user_message,
        draft_reply=draft_reply,
        safety=safety,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellness=wellness,
        referral=referral,
        wellbeing_data=wellbeing_data,
    )

    trace["hallucination_agent"] = hallucination_check

    if hallucination_check.get("safe"):
        final_reply = draft_reply
    else:
        final_reply = hallucination_check.get(
            "corrected_reply",
            hallucination_agent.safe_support_fallback()
        )

    # -------------------------------------------------------------------------
    # Final response
    # -------------------------------------------------------------------------

    return {
        "reply": final_reply,
        "safe": True,
        "risk_level": safety.get("risk_level", "none"),
        "response_type": therapy.get("response_type", "supportive"),
        "technique_used": therapy.get("technique_used", "validation"),
        "agents": trace if include_trace else {},
        "wellness": wellness,
        "referral": referral,
    }


# -----------------------------------------------------------------------------
# Lightweight helper for reports
# -----------------------------------------------------------------------------

def run_analysis_only(
    user_message: str,
    emotion: str = "neutral",
    wellbeing_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Runs only analysis agents.
    Useful for report generation.
    """

    wellbeing_data = wellbeing_data or {}
    history = history or []

    safety_agent = SafetyAgent()
    emotion_agent = EmotionAgent()
    social_agent = SocialAgent()
    wellness_agent = WellnessAgent()
    psychiatrist_agent = PsychiatristAgent()

    safety = safety_agent.run(
        user_message=user_message,
        emotion=emotion,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    emotion_analysis = emotion_agent.run(
        user_message=user_message,
        detected_emotion=emotion,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    social_analysis = social_agent.run(
        user_message=user_message,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    wellness = wellness_agent.run(
        user_message=user_message,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellbeing_data=wellbeing_data,
    )

    referral = psychiatrist_agent.run(
        user_message=user_message,
        safety=safety,
        emotion_analysis=emotion_analysis,
        social_analysis=social_analysis,
        wellbeing_data=wellbeing_data,
        history=history,
    )

    return {
        "safety": safety,
        "emotion_analysis": emotion_analysis,
        "social_analysis": social_analysis,
        "wellness": wellness,
        "referral": referral,
    }