"""
===============================================================================
NeuroSense AI — Professional Help Utility
===============================================================================

Purpose:
- Suggest professional help OUTSIDE the app.
- Map different mental health concerns to suitable human support:
  counsellor, psychologist, psychiatrist, emergency/crisis helpline.
- Provide verified/public Indian mental health resources.
- Never diagnose.
- Never prescribe.
- Never pretend NeuroSense AI is a psychiatrist.

IMPORTANT:
This file is for referral guidance only.
It must not be used as medical diagnosis or treatment.
===============================================================================
"""

from __future__ import annotations

import re
import datetime
from typing import Any, Dict, List, Optional


# =============================================================================
# SAFETY DISCLAIMER
# =============================================================================

DISCLAIMER = (
    "NeuroSense AI is not a psychiatrist, doctor, therapist, or emergency service. "
    "It does not diagnose conditions or prescribe medication. The resources below "
    "are referral suggestions to help the user connect with qualified human support."
)


# =============================================================================
# VERIFIED / PUBLIC PROFESSIONAL HELP RESOURCES — INDIA
# =============================================================================

PROFESSIONAL_HELP_RESOURCES: List[Dict[str, Any]] = [
    {
        "id": "tele_manas",
        "name": "Tele MANAS",
        "type": "Government mental health helpline",
        "professional_level": "trained counsellor / mental health professional",
        "best_for": [
            "crisis",
            "self_harm",
            "panic",
            "anxiety",
            "depression",
            "stress",
            "sleep",
            "family_issues",
            "academic_pressure",
            "emotional_distress",
            "loneliness",
            "substance_use",
        ],
        "phone": "14416",
        "alternate_phone": "1800-891-4416",
        "whatsapp": None,
        "email": None,
        "available": "24/7",
        "website": "https://telemanas.mohfw.gov.in/",
        "priority": 1,
        "notes": (
            "Government of India free 24/7 tele-mental health support. "
            "Suitable for immediate emotional support and referral guidance."
        ),
    },
    {
        "id": "icall_tiss",
        "name": "iCALL Psychosocial Helpline",
        "type": "Psychosocial counselling helpline by TISS",
        "professional_level": "trained mental health professionals",
        "best_for": [
            "stress",
            "loneliness",
            "relationship",
            "family_issues",
            "emotional_distress",
            "academic_pressure",
            "self_doubt",
            "grief",
            "work_pressure",
        ],
        "phone": "9152987821",
        "alternate_phone": None,
        "whatsapp": None,
        "email": "icall@tiss.ac.in",
        "available": "Check official website for current timings",
        "website": "https://icallhelpline.org/",
        "priority": 2,
        "notes": (
            "Free telephone and email-based counselling support for emotional "
            "and psychological distress."
        ),
    },
    {
        "id": "vandrevala_foundation",
        "name": "Vandrevala Foundation",
        "type": "Mental health counselling and crisis support",
        "professional_level": "mental health counsellors",
        "best_for": [
            "crisis",
            "self_harm",
            "depression",
            "anxiety",
            "panic",
            "emotional_distress",
            "loneliness",
            "relationship",
            "family_issues",
            "sleep",
        ],
        "phone": "+91 9999 666 555",
        "alternate_phone": None,
        "whatsapp": "+91 9999 666 555",
        "email": "help@vandrevalafoundation.com",
        "available": "24/7",
        "website": "https://www.vandrevalafoundation.com/free-counseling",
        "priority": 1,
        "notes": (
            "Free 24x7 mental health counselling by call or WhatsApp."
        ),
    },
    {
        "id": "ips_directory",
        "name": "Indian Psychiatric Society Directory",
        "type": "Verified psychiatrist directory",
        "professional_level": "psychiatrist directory",
        "best_for": [
            "psychiatrist",
            "medication",
            "diagnosis",
            "persistent_symptoms",
            "severe_distress",
            "substance_use",
            "sleep",
            "panic",
            "depression",
            "anxiety",
        ],
        "phone": None,
        "alternate_phone": None,
        "whatsapp": None,
        "email": None,
        "available": "Online directory",
        "website": "https://indianpsychiatricsociety.org/ips-directory/",
        "priority": 3,
        "notes": (
            "Use this directory to find verified psychiatrists instead of "
            "hardcoding personal doctor numbers or social media IDs."
        ),
    },
]


# =============================================================================
# ISSUE → PROFESSIONAL SUPPORT MAPPING
# =============================================================================

ISSUE_TO_PROFESSIONAL: Dict[str, Dict[str, str]] = {
    "academic_pressure": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Academic pressure can often be supported through counselling, "
            "stress management, routine planning, and emotional coping skills."
        ),
    },
    "work_pressure": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Work pressure may benefit from structured stress management and "
            "supportive counselling."
        ),
    },
    "family_issues": {
        "professional": "counsellor, psychologist, or family therapist",
        "urgency": "routine",
        "reason": (
            "Family conflict may benefit from guided communication support "
            "and emotional processing."
        ),
    },
    "relationship": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Relationship stress can be supported through counselling, boundary "
            "work, and emotional regulation strategies."
        ),
    },
    "loneliness": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Persistent loneliness can affect wellbeing and may improve with "
            "supportive counselling and social reconnection planning."
        ),
    },
    "self_doubt": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Self-doubt and low confidence can be supported through therapy-based "
            "coping and self-compassion practices."
        ),
    },
    "health": {
        "professional": "doctor and psychologist",
        "urgency": "routine",
        "reason": (
            "Health worries may need both medical clarification and emotional support."
        ),
    },
    "sleep": {
        "professional": "psychologist or psychiatrist if persistent",
        "urgency": "soon",
        "reason": (
            "Ongoing sleep disturbance may require professional assessment, "
            "especially if it affects daily functioning."
        ),
    },
    "anxiety": {
        "professional": "psychologist or psychiatrist",
        "urgency": "soon",
        "reason": (
            "Persistent anxiety, panic, or overwhelming stress may need structured "
            "therapy or psychiatric evaluation."
        ),
    },
    "panic": {
        "professional": "psychologist or psychiatrist",
        "urgency": "soon",
        "reason": (
            "Panic-like symptoms can be frightening and may benefit from professional support."
        ),
    },
    "depression": {
        "professional": "psychologist or psychiatrist",
        "urgency": "soon",
        "reason": (
            "Persistent sadness, hopelessness, low motivation, or withdrawal should "
            "be discussed with a licensed mental health professional."
        ),
    },
    "grief": {
        "professional": "counsellor or psychologist",
        "urgency": "routine",
        "reason": (
            "Grief can be supported through compassionate counselling and safe processing."
        ),
    },
    "substance_use": {
        "professional": "psychiatrist or de-addiction specialist",
        "urgency": "soon",
        "reason": (
            "Substance use concerns may require specialist support and structured care."
        ),
    },
    "medication": {
        "professional": "psychiatrist or qualified doctor",
        "urgency": "soon",
        "reason": (
            "Medication questions should only be handled by a qualified psychiatrist "
            "or doctor."
        ),
    },
    "severe_distress": {
        "professional": "psychologist or psychiatrist",
        "urgency": "urgent",
        "reason": (
            "Severe distress or impaired daily functioning should be assessed by "
            "a licensed mental health professional."
        ),
    },
    "self_harm": {
        "professional": "emergency services or crisis helpline",
        "urgency": "emergency",
        "reason": (
            "Self-harm thoughts or unsafe feelings require immediate human support."
        ),
    },
    "crisis": {
        "professional": "emergency services or crisis helpline",
        "urgency": "emergency",
        "reason": (
            "Immediate danger or crisis signs require urgent human support."
        ),
    },
}


# =============================================================================
# KEYWORD DETECTION
# =============================================================================

SELF_HARM_PATTERNS = [
    r"\bsuicide\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bi want to die\b",
    r"\bdon'?t want to live\b",
    r"\bno reason to live\b",
    r"\bhurt myself\b",
    r"\bself[- ]?harm\b",
    r"\bcut myself\b",
]

MEDICATION_PATTERNS = [
    r"\bmedicine\b",
    r"\bmedication\b",
    r"\btablet\b",
    r"\bdose\b",
    r"\bantidepressant\b",
    r"\bsleeping pill\b",
    r"\bprescribe\b",
    r"\bpsychiatric medicine\b",
]

SUBSTANCE_PATTERNS = [
    r"\balcohol\b",
    r"\bweed\b",
    r"\bdrug\b",
    r"\bsubstance\b",
    r"\baddiction\b",
    r"\bsmoking\b",
    r"\bdrinking problem\b",
]

PANIC_PATTERNS = [
    r"\bpanic\b",
    r"\bpanic attack\b",
    r"\bheart racing\b",
    r"\bcan'?t breathe\b",
    r"\bbreathing fast\b",
]

ANXIETY_PATTERNS = [
    r"\banxiety\b",
    r"\banxious\b",
    r"\boverthinking\b",
    r"\bworried\b",
    r"\bfear\b",
    r"\bnervous\b",
]

DEPRESSION_PATTERNS = [
    r"\bdepressed\b",
    r"\bdepression\b",
    r"\bhopeless\b",
    r"\bempty\b",
    r"\blow motivation\b",
    r"\bworthless\b",
    r"\bno energy\b",
]

ABUSE_PATTERNS = [
    r"\babuse\b",
    r"\bdomestic violence\b",
    r"\bharassment\b",
    r"\bassault\b",
    r"\bblackmail\b",
    r"\bforced\b",
]


# =============================================================================
# HELPERS
# =============================================================================

def _matches_any(text: str, patterns: List[str]) -> bool:
    text = text or ""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def normalize_issue_tag(tag: str) -> str:
    """
    Normalizes frontend concern values into backend issue tags.
    """

    if not tag:
        return ""

    tag = str(tag).strip().lower().replace(" ", "_").replace("-", "_")

    mapping = {
        "academic": "academic_pressure",
        "academics": "academic_pressure",
        "study": "academic_pressure",
        "studies": "academic_pressure",
        "exam": "academic_pressure",
        "exams": "academic_pressure",
        "work": "work_pressure",
        "career": "work_pressure",
        "family": "family_issues",
        "family_issue": "family_issues",
        "relationships": "relationship",
        "relationship_stress": "relationship",
        "alone": "loneliness",
        "lonely": "loneliness",
        "self_confidence": "self_doubt",
        "confidence": "self_doubt",
        "health_worry": "health",
        "health_worries": "health",
    }

    return mapping.get(tag, tag)


# =============================================================================
# ISSUE DETECTION
# =============================================================================

def detect_issue_tags(
    checkin: Optional[Dict[str, Any]] = None,
    message: str = "",
    emotion: str = "neutral",
    safety: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Detect concern tags from:
    - wellbeing check-in
    - current message
    - detected emotion
    - safety agent result

    Returns a sorted list of issue tags.
    """

    checkin = checkin or {}
    safety = safety or {}
    message_lower = (message or "").lower()
    emotion = (emotion or "neutral").lower()

    tags = set()

    # Frontend selected concerns
    for concern in checkin.get("concerns", []) or []:
        normalized = normalize_issue_tag(concern)
        if normalized:
            tags.add(normalized)

    mood = str(checkin.get("mood") or "").lower()
    sleep = str(checkin.get("sleep") or "").lower()
    support_available = str(checkin.get("support_available") or "").lower()

    stress = _safe_int(checkin.get("stress"), 0)
    social_connection = _safe_int(checkin.get("social_connection"), 3)
    emotional_safety = _safe_int(checkin.get("emotional_safety"), 5)
    wellbeing_score = _safe_int(checkin.get("wellbeing_score"), 100)

    # Safety agent signals
    if safety.get("risk_level") in ["crisis", "high"]:
        tags.add("crisis")

    if safety.get("self_harm"):
        tags.add("self_harm")

    if safety.get("medical_advice_requested"):
        tags.add("medication")

    if safety.get("abuse"):
        tags.add("family_issues")

    # Check-in signals
    if mood in ["sad"]:
        tags.add("depression")

    if mood in ["anxious"]:
        tags.add("anxiety")

    if mood in ["overwhelmed"]:
        tags.add("anxiety")
        tags.add("severe_distress")

    if emotion in ["sad"]:
        tags.add("depression")

    if emotion in ["fear", "anxious", "stressed"]:
        tags.add("anxiety")

    if emotion in ["overwhelmed"]:
        tags.add("severe_distress")

    if sleep in ["poor", "very_poor"]:
        tags.add("sleep")

    if stress >= 4:
        tags.add("anxiety")

    if stress >= 5 or wellbeing_score <= 25:
        tags.add("severe_distress")

    if social_connection <= 2 or support_available == "no":
        tags.add("loneliness")

    if emotional_safety <= 2:
        tags.add("crisis")

    # Message keyword signals
    if _matches_any(message_lower, SELF_HARM_PATTERNS):
        tags.add("self_harm")
        tags.add("crisis")

    if _matches_any(message_lower, MEDICATION_PATTERNS):
        tags.add("medication")

    if _matches_any(message_lower, SUBSTANCE_PATTERNS):
        tags.add("substance_use")

    if _matches_any(message_lower, PANIC_PATTERNS):
        tags.add("panic")
        tags.add("anxiety")

    if _matches_any(message_lower, ANXIETY_PATTERNS):
        tags.add("anxiety")

    if _matches_any(message_lower, DEPRESSION_PATTERNS):
        tags.add("depression")

    if _matches_any(message_lower, ABUSE_PATTERNS):
        tags.add("family_issues")

    return sorted(tags)


# =============================================================================
# PROFESSIONAL RECOMMENDATION ENGINE
# =============================================================================

def get_professional_recommendations(issue_tags: List[str]) -> List[Dict[str, str]]:
    """
    Maps detected issue tags to professional support recommendations.
    """

    recommendations = []

    seen = set()

    for tag in issue_tags:
        if tag not in ISSUE_TO_PROFESSIONAL:
            continue

        item = ISSUE_TO_PROFESSIONAL[tag]

        key = (
            tag,
            item["professional"],
            item["urgency"],
        )

        if key in seen:
            continue

        seen.add(key)

        recommendations.append({
            "issue": tag,
            "professional": item["professional"],
            "urgency": item["urgency"],
            "reason": item["reason"],
        })

    urgency_order = {
        "emergency": 0,
        "urgent": 1,
        "soon": 2,
        "routine": 3,
    }

    recommendations.sort(
        key=lambda x: urgency_order.get(x.get("urgency", "routine"), 9)
    )

    return recommendations


def get_matching_resources(issue_tags: List[str]) -> List[Dict[str, Any]]:
    """
    Returns resources best suited for detected issue tags.
    """

    matched = []

    for resource in PROFESSIONAL_HELP_RESOURCES:
        best_for = set(resource.get("best_for", []))

        if any(tag in best_for for tag in issue_tags):
            matched.append(resource)

    if not matched:
        matched = [
            resource
            for resource in PROFESSIONAL_HELP_RESOURCES
            if resource["id"] in [
                "tele_manas",
                "icall_tiss",
                "vandrevala_foundation",
            ]
        ]

    matched.sort(
        key=lambda x: int(x.get("priority", 99))
    )

    return matched[:4]


def get_urgency_level(recommendations: List[Dict[str, str]]) -> str:
    """
    Returns highest urgency across recommendations.
    """

    if not recommendations:
        return "none"

    order = ["emergency", "urgent", "soon", "routine"]

    for level in order:
        if any(r.get("urgency") == level for r in recommendations):
            return level

    return "routine"


def get_user_facing_referral_message(
    urgency: str,
    recommendations: List[Dict[str, str]],
) -> str:
    """
    Creates safe user-facing referral language.
    """

    if urgency == "emergency":
        return (
            "Your safety matters. Based on what you shared, it would be best to "
            "contact immediate human support right now. Please reach out to a "
            "trusted person, emergency services, or a crisis helpline."
        )

    if urgency == "urgent":
        return (
            "Based on the distress indicators, it may be important to speak with "
            "a licensed mental health professional as soon as possible. NeuroSense AI "
            "can support you, but a qualified human professional can assess your "
            "situation more properly."
        )

    if urgency == "soon":
        professional = recommendations[0]["professional"] if recommendations else "mental health professional"

        return (
            f"It may be helpful to speak with a {professional}. I cannot diagnose "
            "or provide medical treatment, but professional support can give you "
            "personalized care."
        )

    if urgency == "routine":
        professional = recommendations[0]["professional"] if recommendations else "counsellor"

        return (
            f"If this concern continues, consider speaking with a {professional}. "
            "This can help you understand your emotions and build healthier coping steps."
        )

    return ""


def recommend_professional_help(
    checkin: Optional[Dict[str, Any]] = None,
    message: str = "",
    emotion: str = "neutral",
    safety: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main function used by app.py, agents, and reports.

    Returns structured professional help guidance.
    """

    checkin = checkin or {}
    safety = safety or {}

    issue_tags = detect_issue_tags(
        checkin=checkin,
        message=message,
        emotion=emotion,
        safety=safety,
    )

    recommendations = get_professional_recommendations(issue_tags)
    resources = get_matching_resources(issue_tags)
    urgency = get_urgency_level(recommendations)

    emergency = urgency == "emergency"

    return {
        "ok": True,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "needs_professional_help": bool(recommendations) or emergency,
        "emergency": emergency,
        "urgency": urgency,
        "issue_tags": issue_tags,
        "recommendations": recommendations,
        "resources": resources,
        "user_facing_message": get_user_facing_referral_message(
            urgency,
            recommendations,
        ),
        "disclaimer": DISCLAIMER,
    }


# =============================================================================
# REPORT-FRIENDLY FORMATTERS
# =============================================================================

def format_resources_for_report(resources: List[Dict[str, Any]]) -> List[str]:
    """
    Converts resource dicts to readable report strings.
    """

    lines = []

    for r in resources:
        parts = [r.get("name", "Resource")]

        if r.get("phone"):
            parts.append(f"Phone: {r['phone']}")

        if r.get("alternate_phone"):
            parts.append(f"Alt: {r['alternate_phone']}")

        if r.get("whatsapp"):
            parts.append(f"WhatsApp: {r['whatsapp']}")

        if r.get("email"):
            parts.append(f"Email: {r['email']}")

        if r.get("website"):
            parts.append(f"Website: {r['website']}")

        if r.get("available"):
            parts.append(f"Availability: {r['available']}")

        lines.append(" | ".join(parts))

    return lines


def compact_professional_help_summary(result: Dict[str, Any]) -> str:
    """
    Creates a short paragraph for dashboards/reports.
    """

    if not result or not result.get("needs_professional_help"):
        return (
            "No urgent professional referral signal was detected from the available data. "
            "The user may still choose to speak with a counsellor or psychologist if they want support."
        )

    urgency = result.get("urgency", "routine")
    tags = ", ".join(result.get("issue_tags", [])) or "general wellbeing concerns"
    msg = result.get("user_facing_message", "")

    return (
        f"Professional help guidance level: {urgency}. "
        f"Detected concern areas: {tags}. {msg}"
    )


# =============================================================================
# EMERGENCY QUICK CHECK
# =============================================================================

def is_emergency_case(
    checkin: Optional[Dict[str, Any]] = None,
    message: str = "",
    safety: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Deterministic emergency check for quick routing.
    """

    result = recommend_professional_help(
        checkin=checkin,
        message=message,
        safety=safety,
    )

    return bool(result.get("emergency"))