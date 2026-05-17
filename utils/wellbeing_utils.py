"""
===============================================================================
NeuroSense AI — Wellbeing Utility
===============================================================================

Purpose:
- Validate and score Mental & Social Wellbeing Check-In.
- Calculate wellbeing score and risk level consistently in backend.
- Generate explanation for reports and dashboard.
- Keep scoring transparent and non-diagnostic.

Important:
This is not a medical or clinical score.
It is a simple wellness indicator for supportive guidance.
===============================================================================
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional


# =============================================================================
# CONSTANTS
# =============================================================================

VALID_MOODS = {
    "happy",
    "calm",
    "neutral",
    "sad",
    "anxious",
    "angry",
    "overwhelmed",
}

VALID_SLEEP_VALUES = {
    "good",
    "okay",
    "poor",
    "very_poor",
}

VALID_SUPPORT_VALUES = {
    "yes",
    "maybe",
    "no",
}

VALID_CONCERNS = {
    "academic_pressure",
    "work_pressure",
    "family_issues",
    "relationship",
    "loneliness",
    "self_doubt",
    "health",
    "sleep",
    "substance_use",
    "grief",
}


# =============================================================================
# SAFE HELPERS
# =============================================================================

def clamp(value: int | float, minimum: int = 0, maximum: int = 100) -> int:
    try:
        value = int(value)
    except Exception:
        value = minimum

    return max(minimum, min(maximum, value))


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def normalize_string(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_concern(value: Any) -> str:
    value = normalize_string(value)
    value = value.replace(" ", "_").replace("-", "_")

    mapping = {
        "academic": "academic_pressure",
        "study": "academic_pressure",
        "studies": "academic_pressure",
        "exam": "academic_pressure",
        "exams": "academic_pressure",
        "work": "work_pressure",
        "job": "work_pressure",
        "family": "family_issues",
        "relationship_stress": "relationship",
        "relationships": "relationship",
        "alone": "loneliness",
        "lonely": "loneliness",
        "confidence": "self_doubt",
        "self_confidence": "self_doubt",
        "health_worries": "health",
        "health_worry": "health",
    }

    return mapping.get(value, value)


# =============================================================================
# CHECK-IN NORMALIZATION
# =============================================================================

def normalize_checkin(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cleans frontend check-in payload before saving or scoring.
    """

    raw = raw or {}

    mood = normalize_string(raw.get("mood"))
    sleep = normalize_string(raw.get("sleep"))
    support_available = normalize_string(raw.get("support_available"))

    if mood not in VALID_MOODS:
        mood = "neutral"

    if sleep not in VALID_SLEEP_VALUES:
        sleep = "okay"

    if support_available not in VALID_SUPPORT_VALUES:
        support_available = "maybe"

    stress = clamp(
        safe_int(raw.get("stress"), 3),
        1,
        5,
    )

    social_connection = clamp(
        safe_int(raw.get("social_connection"), 3),
        1,
        5,
    )

    emotional_safety = clamp(
        safe_int(raw.get("emotional_safety"), 3),
        1,
        5,
    )

    concerns = []

    for item in raw.get("concerns", []) or []:
        concern = normalize_concern(item)

        if concern:
            concerns.append(concern)

    # Remove duplicates while preserving order
    seen = set()
    concerns = [
        c for c in concerns
        if not (c in seen or seen.add(c))
    ]

    current_thoughts = str(
        raw.get("current_thoughts") or ""
    ).strip()

    if len(current_thoughts) > 1200:
        current_thoughts = current_thoughts[:1200]

    created_at = raw.get("created_at") or datetime.datetime.utcnow().isoformat()

    normalized = {
        "mood": mood,
        "stress": stress,
        "social_connection": social_connection,
        "sleep": sleep,
        "concerns": concerns,
        "emotional_safety": emotional_safety,
        "support_available": support_available,
        "current_thoughts": current_thoughts,
        "created_at": created_at,
    }

    score = calculate_wellbeing_score(normalized)
    risk = calculate_risk_level(normalized)

    normalized["wellbeing_score"] = score
    normalized["risk_level"] = risk
    normalized["score_explanation"] = explain_score(normalized)
    normalized["risk_explanation"] = explain_risk(normalized)

    return normalized


# =============================================================================
# WELLBEING SCORE
# =============================================================================

def calculate_wellbeing_score(data: Dict[str, Any]) -> int:
    """
    Backend version of the frontend scoring formula.

    Starting score = 100

    Deductions:
    - Stress: stress × 8
    - Low social connection: (6 - social_connection) × 6
    - Low emotional safety: (6 - emotional_safety) × 7
    - Poor sleep: -10
    - Very poor sleep: -18
    - Support maybe: -8
    - Support no: -15
    - Concerns: -4 each, max -20
    - Difficult mood: -12

    This is not a clinical score.
    """

    stress = clamp(
        safe_int(data.get("stress"), 3),
        1,
        5,
    )

    social_connection = clamp(
        safe_int(data.get("social_connection"), 3),
        1,
        5,
    )

    emotional_safety = clamp(
        safe_int(data.get("emotional_safety"), 3),
        1,
        5,
    )

    sleep = normalize_string(data.get("sleep"))
    support_available = normalize_string(data.get("support_available"))
    mood = normalize_string(data.get("mood"))

    concerns = data.get("concerns", []) or []

    score = 100

    score -= stress * 8
    score -= (6 - social_connection) * 6
    score -= (6 - emotional_safety) * 7

    if sleep == "poor":
        score -= 10

    if sleep == "very_poor":
        score -= 18

    if support_available == "maybe":
        score -= 8

    if support_available == "no":
        score -= 15

    score -= min(len(concerns) * 4, 20)

    if mood in ["sad", "anxious", "angry", "overwhelmed"]:
        score -= 12

    return clamp(score, 0, 100)


# =============================================================================
# RISK LEVEL
# =============================================================================

def calculate_risk_level(data: Dict[str, Any]) -> str:
    """
    Returns low / medium / high.
    This is a support-risk indicator, not a diagnosis.
    """

    stress = clamp(
        safe_int(data.get("stress"), 3),
        1,
        5,
    )

    social_connection = clamp(
        safe_int(data.get("social_connection"), 3),
        1,
        5,
    )

    emotional_safety = clamp(
        safe_int(data.get("emotional_safety"), 3),
        1,
        5,
    )

    sleep = normalize_string(data.get("sleep"))
    support_available = normalize_string(data.get("support_available"))
    mood = normalize_string(data.get("mood"))
    score = safe_int(data.get("wellbeing_score"), calculate_wellbeing_score(data))

    high_conditions = [
        stress >= 4,
        emotional_safety <= 2,
        support_available == "no",
        mood == "overwhelmed",
        score <= 30,
    ]

    if any(high_conditions):
        return "high"

    medium_conditions = [
        stress >= 3,
        social_connection <= 2,
        sleep in ["poor", "very_poor"],
        mood in ["sad", "anxious", "angry"],
        score <= 60,
    ]

    if any(medium_conditions):
        return "medium"

    return "low"


# =============================================================================
# EXPLANATIONS
# =============================================================================

def explain_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gives transparent score breakdown for reviewer/report.
    """

    stress = clamp(safe_int(data.get("stress"), 3), 1, 5)
    social_connection = clamp(safe_int(data.get("social_connection"), 3), 1, 5)
    emotional_safety = clamp(safe_int(data.get("emotional_safety"), 3), 1, 5)

    sleep = normalize_string(data.get("sleep"))
    support_available = normalize_string(data.get("support_available"))
    mood = normalize_string(data.get("mood"))
    concerns = data.get("concerns", []) or []

    deductions = []

    deductions.append({
        "factor": "stress",
        "value": stress,
        "deduction": stress * 8,
        "reason": "Higher stress reduces wellbeing score.",
    })

    deductions.append({
        "factor": "social_connection",
        "value": social_connection,
        "deduction": (6 - social_connection) * 6,
        "reason": "Lower social connection increases support need.",
    })

    deductions.append({
        "factor": "emotional_safety",
        "value": emotional_safety,
        "deduction": (6 - emotional_safety) * 7,
        "reason": "Lower emotional safety increases concern level.",
    })

    if sleep == "poor":
        deductions.append({
            "factor": "sleep",
            "value": sleep,
            "deduction": 10,
            "reason": "Poor sleep affects emotional wellbeing.",
        })

    if sleep == "very_poor":
        deductions.append({
            "factor": "sleep",
            "value": sleep,
            "deduction": 18,
            "reason": "Very poor sleep strongly affects emotional wellbeing.",
        })

    if support_available == "maybe":
        deductions.append({
            "factor": "support_available",
            "value": support_available,
            "deduction": 8,
            "reason": "Uncertain support availability increases support need.",
        })

    if support_available == "no":
        deductions.append({
            "factor": "support_available",
            "value": support_available,
            "deduction": 15,
            "reason": "No support availability increases concern level.",
        })

    concern_deduction = min(len(concerns) * 4, 20)

    if concern_deduction:
        deductions.append({
            "factor": "concerns",
            "value": concerns,
            "deduction": concern_deduction,
            "reason": "Multiple active concerns increase emotional load.",
        })

    if mood in ["sad", "anxious", "angry", "overwhelmed"]:
        deductions.append({
            "factor": "mood",
            "value": mood,
            "deduction": 12,
            "reason": "Difficult mood state indicates need for support.",
        })

    total_deduction = sum(d["deduction"] for d in deductions)

    return {
        "starting_score": 100,
        "deductions": deductions,
        "total_deduction": total_deduction,
        "final_score": calculate_wellbeing_score(data),
        "note": (
            "This score is a supportive wellbeing indicator, not a medical "
            "or diagnostic score."
        ),
    }


def explain_risk(data: Dict[str, Any]) -> str:
    """
    Gives short explanation for risk level.
    """

    risk = calculate_risk_level(data)

    if risk == "high":
        return (
            "High support need was detected because the check-in shows strong "
            "stress, low emotional safety, low support availability, very low score, "
            "or feeling overwhelmed."
        )

    if risk == "medium":
        return (
            "Medium support need was detected because the check-in shows moderate "
            "stress, low social connection, difficult mood, poor sleep, or reduced score."
        )

    return (
        "Low support need was detected from the available check-in data. "
        "This does not mean the user does not need support; it only reflects the current answers."
    )


# =============================================================================
# WELLNESS SUGGESTIONS
# =============================================================================

def generate_safe_suggestions(
    checkin: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> List[Dict[str, str]]:
    """
    Deterministic safe wellness suggestions based on check-in.
    These are not medical treatment.
    """

    checkin = normalize_checkin(checkin or {})

    mood = checkin["mood"]
    stress = checkin["stress"]
    social_connection = checkin["social_connection"]
    sleep = checkin["sleep"]
    support = checkin["support_available"]
    concerns = checkin["concerns"]
    emotional_safety = checkin["emotional_safety"]
    risk = checkin["risk_level"]

    suggestions = []

    if stress >= 4 or mood in ["anxious", "overwhelmed", "angry"]:
        suggestions.append({
            "title": "Box Breathing",
            "why": "High stress can make the body feel activated.",
            "how_to_do": "Breathe in for 4 seconds, hold for 4, breathe out for 4, and hold again for 4.",
            "frequency": "2–3 rounds when stressed",
            "category": "stress_regulation",
        })

    if mood in ["sad", "overwhelmed"] or "self_doubt" in concerns:
        suggestions.append({
            "title": "Thought Journal",
            "why": "Writing thoughts can reduce emotional overload and improve clarity.",
            "how_to_do": "Write one difficult thought, the feeling linked to it, and one kinder alternative thought.",
            "frequency": "Once daily",
            "category": "reflection",
        })

    if sleep in ["poor", "very_poor"]:
        suggestions.append({
            "title": "Sleep Wind-Down Routine",
            "why": "Poor sleep can affect mood, focus, and emotional regulation.",
            "how_to_do": "Avoid screens 30 minutes before bed, dim lights, and write tomorrow’s tasks before sleeping.",
            "frequency": "Nightly",
            "category": "sleep",
        })

    if social_connection <= 2 or support in ["no", "maybe"] or "loneliness" in concerns:
        suggestions.append({
            "title": "Trusted Person Check-In",
            "why": "Social support can reduce emotional isolation.",
            "how_to_do": "Send one short message to a trusted person saying: 'Can we talk for a few minutes today?'",
            "frequency": "Today or this week",
            "category": "social_support",
        })

    if emotional_safety <= 2 or risk == "high":
        suggestions.append({
            "title": "Professional Support Step",
            "why": "Low emotional safety or high distress is better supported with human help.",
            "how_to_do": "Reach out to a helpline, counsellor, psychologist, psychiatrist, or trusted person.",
            "frequency": "As soon as possible",
            "category": "professional_help",
        })

    # Fill remaining safe suggestions
    fillers = [
        {
            "title": "5-4-3-2-1 Grounding",
            "why": "Grounding helps bring attention back to the present moment.",
            "how_to_do": "Notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.",
            "frequency": "Whenever overwhelmed",
            "category": "grounding",
        },
        {
            "title": "Small Action Plan",
            "why": "Small actions reduce the pressure of big tasks.",
            "how_to_do": "Choose one task that takes less than 5 minutes and complete only that.",
            "frequency": "Once today",
            "category": "activation",
        },
        {
            "title": "Hydration and Movement",
            "why": "Basic body care can support mood and energy.",
            "how_to_do": "Drink water and take a 5-minute walk or stretch break.",
            "frequency": "Daily",
            "category": "body_care",
        },
        {
            "title": "Emotion Naming",
            "why": "Naming emotions can reduce confusion and increase self-awareness.",
            "how_to_do": "Say: 'I am noticing ___ feeling right now, and it makes sense because ___.’",
            "frequency": "When emotions feel intense",
            "category": "emotional_awareness",
        },
    ]

    existing_titles = {
        s["title"] for s in suggestions
    }

    for item in fillers:
        if len(suggestions) >= limit:
            break

        if item["title"] not in existing_titles:
            suggestions.append(item)

    return suggestions[:limit]


# =============================================================================
# CHECK-IN SUMMARY
# =============================================================================

def summarize_checkin(checkin: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates clean report/dashboard summary from latest check-in.
    """

    if not checkin:
        return {
            "available": False,
            "summary": "No wellbeing check-in is available yet.",
            "wellbeing_score": None,
            "risk_level": "unknown",
        }

    normalized = normalize_checkin(checkin)

    concerns = normalized.get("concerns", [])

    concern_text = (
        ", ".join(concerns)
        if concerns else "no specific concerns selected"
    )

    summary = (
        f"The latest check-in shows mood as {normalized['mood']}, "
        f"stress level {normalized['stress']}/5, social connection "
        f"{normalized['social_connection']}/5, emotional safety "
        f"{normalized['emotional_safety']}/5, and sleep quality as "
        f"{normalized['sleep']}. Selected concerns: {concern_text}. "
        f"Calculated wellbeing score is {normalized['wellbeing_score']}/100 "
        f"with {normalized['risk_level']} support need."
    )

    return {
        "available": True,
        "summary": summary,
        "wellbeing_score": normalized["wellbeing_score"],
        "risk_level": normalized["risk_level"],
        "mood": normalized["mood"],
        "stress": normalized["stress"],
        "sleep": normalized["sleep"],
        "concerns": concerns,
        "support_available": normalized["support_available"],
        "score_explanation": normalized["score_explanation"],
        "risk_explanation": normalized["risk_explanation"],
    }


# =============================================================================
# TREND UTILITIES
# =============================================================================

def summarize_wellbeing_trend(
    checkins: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Summarizes trend from multiple check-ins.
    """

    checkins = checkins or []

    if not checkins:
        return {
            "available": False,
            "trend": "limited_data",
            "average_score": None,
            "latest_score": None,
            "summary": "No wellbeing check-ins are available yet.",
        }

    normalized = [
        normalize_checkin(item)
        for item in checkins
    ]

    scores = [
        item["wellbeing_score"]
        for item in normalized
    ]

    average_score = round(
        sum(scores) / len(scores),
        1
    )

    latest_score = scores[-1]

    if len(scores) < 2:
        trend = "limited_data"
    elif latest_score > scores[0] + 5:
        trend = "improving"
    elif latest_score < scores[0] - 5:
        trend = "declining"
    else:
        trend = "stable"

    high_count = sum(
        1 for item in normalized
        if item["risk_level"] == "high"
    )

    medium_count = sum(
        1 for item in normalized
        if item["risk_level"] == "medium"
    )

    summary = (
        f"{len(scores)} check-in(s) available. Average score is "
        f"{average_score}/100, latest score is {latest_score}/100, "
        f"and trend is {trend}. High-risk check-ins: {high_count}, "
        f"medium-risk check-ins: {medium_count}."
    )

    return {
        "available": True,
        "trend": trend,
        "average_score": average_score,
        "latest_score": latest_score,
        "high_count": high_count,
        "medium_count": medium_count,
        "summary": summary,
    }


# =============================================================================
# BACKEND API RESPONSE HELPER
# =============================================================================

def build_checkin_response(
    raw: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Normalizes check-in and returns API-friendly response.
    """

    normalized = normalize_checkin(raw)

    suggestions = generate_safe_suggestions(
        normalized,
        limit=5,
    )

    return {
        "ok": True,
        "checkin": normalized,
        "wellbeing_score": normalized["wellbeing_score"],
        "risk_level": normalized["risk_level"],
        "suggestions": suggestions,
        "summary": summarize_checkin(normalized),
        "disclaimer": (
            "This is not a diagnosis. It is a supportive wellbeing indicator "
            "based on the user's current check-in answers."
        ),
    }