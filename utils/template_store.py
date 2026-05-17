"""
===============================================================================
NeuroSense AI — Mental Health Template Store
===============================================================================

Purpose:
- Manage pre-built templates.
- Manage user-created custom templates.
- Store custom templates locally in data/custom_templates.json.
- Optional Supabase persistence can be added later.

Safety:
- Templates are support/wellness only.
- No diagnosis templates.
- No medication templates.
===============================================================================
"""

import os
import json
import uuid
import datetime
from typing import Any, Dict, List, Optional


DATA_DIR = os.path.join(os.getcwd(), "data")
CUSTOM_TEMPLATE_FILE = os.path.join(DATA_DIR, "custom_templates.json")


TEMPLATE_CATEGORIES = [
    "stress",
    "anxiety",
    "sleep",
    "loneliness",
    "academic_pressure",
    "relationship",
    "self_doubt",
    "anger",
    "mood_tracking",
    "professional_help",
    "crisis_safety",
    "weekly_reflection",
]


OUTPUT_TYPES = [
    "plan",
    "checklist",
    "reflection",
    "guide",
    "journal_prompt",
    "safety_plan",
]


PREBUILT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "stress_management_plan",
        "title": "Stress Management Plan",
        "category": "stress",
        "description": "Create a safe, practical plan for handling stress.",
        "output_type": "plan",
        "risk_level": "low",
        "prompt": (
            "Create a practical stress management plan using the user's message, "
            "latest wellbeing check-in, and emotional context. Include causes, "
            "body signals, 3 coping actions, and when to seek professional help."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "anxiety_grounding_plan",
        "title": "Anxiety Grounding Plan",
        "category": "anxiety",
        "description": "Generate grounding steps for anxious or overwhelmed feelings.",
        "output_type": "guide",
        "risk_level": "low",
        "prompt": (
            "Create a grounding guide for anxiety-like feelings. Include simple "
            "education, breathing, 5-4-3-2-1 grounding, thought reframing, and "
            "professional help guidance if symptoms persist."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "sleep_improvement_routine",
        "title": "Sleep Improvement Routine",
        "category": "sleep",
        "description": "Build a gentle sleep routine and night wind-down plan.",
        "output_type": "plan",
        "risk_level": "low",
        "prompt": (
            "Create a sleep support routine. Include wind-down habits, screen limits, "
            "thought dumping, relaxation, and when to consult a professional if sleep "
            "problems continue."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "loneliness_support_plan",
        "title": "Loneliness Support Plan",
        "category": "loneliness",
        "description": "Support users who feel alone or disconnected.",
        "output_type": "plan",
        "risk_level": "low",
        "prompt": (
            "Create a loneliness support plan. Include validation, small social steps, "
            "trusted-person message examples, self-kindness, and helpline/professional "
            "support if needed."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "academic_pressure_support",
        "title": "Academic Pressure Support",
        "category": "academic_pressure",
        "description": "Help with exam stress, workload, and study pressure.",
        "output_type": "checklist",
        "risk_level": "low",
        "prompt": (
            "Create an academic pressure support checklist. Include task breakdown, "
            "study blocks, rest, breathing, realistic planning, and emotional support."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "relationship_stress_reflection",
        "title": "Relationship Stress Reflection",
        "category": "relationship",
        "description": "Guide reflection around relationship stress.",
        "output_type": "reflection",
        "risk_level": "low",
        "prompt": (
            "Create a safe relationship stress reflection. Include feelings, needs, "
            "boundaries, communication, and when to seek counsellor support."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "self_doubt_reframing",
        "title": "Self-Doubt Reframing",
        "category": "self_doubt",
        "description": "Help reframe harsh thoughts with kinder alternatives.",
        "output_type": "journal_prompt",
        "risk_level": "low",
        "prompt": (
            "Create a self-doubt reframing exercise. Include identifying a harsh thought, "
            "evidence for/against it, kinder alternative, and small confidence action."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "anger_regulation_plan",
        "title": "Anger Regulation Plan",
        "category": "anger",
        "description": "Create safe anger regulation steps.",
        "output_type": "plan",
        "risk_level": "medium",
        "prompt": (
            "Create an anger regulation plan. Include pause techniques, body awareness, "
            "safe space, communication, and professional help if anger feels uncontrollable."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "mood_journal_template",
        "title": "Mood Journal Template",
        "category": "mood_tracking",
        "description": "Generate a structured mood journal format.",
        "output_type": "journal_prompt",
        "risk_level": "low",
        "prompt": (
            "Create a mood journal template. Include mood, trigger, body sensation, "
            "thought, need, coping step, and one kind sentence."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "professional_help_guidance",
        "title": "Professional Help Guidance",
        "category": "professional_help",
        "description": "Explain what kind of professional help may fit the concern.",
        "output_type": "guide",
        "risk_level": "medium",
        "prompt": (
            "Create professional help guidance. Explain counsellor vs psychologist vs "
            "psychiatrist in simple terms. Do not diagnose. Include India helplines and "
            "when to seek urgent support."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "crisis_safety_plan",
        "title": "Crisis Safety Plan",
        "category": "crisis_safety",
        "description": "Create immediate safety steps for high distress.",
        "output_type": "safety_plan",
        "risk_level": "high",
        "prompt": (
            "Create a crisis safety plan. Include immediate human support, trusted person, "
            "removing access to harm, grounding, helplines, and emergency services. "
            "Do not provide clinical diagnosis."
        ),
        "is_prebuilt": True,
    },
    {
        "id": "weekly_wellness_reflection",
        "title": "Weekly Wellness Reflection",
        "category": "weekly_reflection",
        "description": "Reflect on the week and plan gentle improvements.",
        "output_type": "reflection",
        "risk_level": "low",
        "prompt": (
            "Create a weekly wellness reflection template. Include wins, stressors, emotions, "
            "support, sleep, coping actions, and next week's small goal."
        ),
        "is_prebuilt": True,
    },
]


def _ensure_data_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CUSTOM_TEMPLATE_FILE):
        with open(CUSTOM_TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def _read_custom_templates() -> List[Dict[str, Any]]:
    _ensure_data_file()

    try:
        with open(CUSTOM_TEMPLATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def _write_custom_templates(items: List[Dict[str, Any]]) -> None:
    _ensure_data_file()

    with open(CUSTOM_TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def list_prebuilt_templates() -> List[Dict[str, Any]]:
    return PREBUILT_TEMPLATES


def list_custom_templates(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = _read_custom_templates()

    if not user_id:
        return items

    return [
        item for item in items
        if item.get("user_id") == user_id
    ]


def list_all_templates(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return list_prebuilt_templates() + list_custom_templates(user_id=user_id)


def get_template(template_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    for item in list_all_templates(user_id=user_id):
        if item.get("id") == template_id:
            return item

    return None


def validate_template_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = str(payload.get("title", "")).strip()
    category = str(payload.get("category", "stress")).strip()
    description = str(payload.get("description", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    output_type = str(payload.get("output_type", "plan")).strip()

    if not title:
        raise ValueError("Template title is required.")

    if len(title) > 100:
        raise ValueError("Template title is too long.")

    if category not in TEMPLATE_CATEGORIES:
        raise ValueError("Invalid template category.")

    if output_type not in OUTPUT_TYPES:
        raise ValueError("Invalid output type.")

    if not prompt:
        raise ValueError("Template prompt is required.")

    if len(prompt) > 1500:
        raise ValueError("Template prompt is too long.")

    unsafe_terms = [
        "diagnose me",
        "prescribe",
        "medicine dose",
        "which medicine",
        "clinical diagnosis",
        "replace psychiatrist",
    ]

    lowered = prompt.lower()

    if any(term in lowered for term in unsafe_terms):
        raise ValueError(
            "Template prompt is unsafe. It cannot request diagnosis or medication advice."
        )

    return {
        "title": title,
        "category": category,
        "description": description[:300],
        "prompt": prompt,
        "output_type": output_type,
    }


def create_custom_template(
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    clean = validate_template_payload(payload)

    items = _read_custom_templates()

    template = {
        "id": "custom_" + str(uuid.uuid4()),
        "user_id": user_id or "guest",
        "title": clean["title"],
        "category": clean["category"],
        "description": clean["description"],
        "prompt": clean["prompt"],
        "output_type": clean["output_type"],
        "risk_level": "low",
        "is_prebuilt": False,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
    }

    items.append(template)
    _write_custom_templates(items)

    return template


def delete_custom_template(
    template_id: str,
    user_id: Optional[str] = None,
) -> bool:
    items = _read_custom_templates()

    new_items = []

    deleted = False

    for item in items:
        same_id = item.get("id") == template_id
        same_user = not user_id or item.get("user_id") == user_id

        if same_id and same_user:
            deleted = True
            continue

        new_items.append(item)

    if deleted:
        _write_custom_templates(new_items)

    return deleted


def template_summary() -> Dict[str, Any]:
    custom = _read_custom_templates()

    return {
        "prebuilt_count": len(PREBUILT_TEMPLATES),
        "custom_count": len(custom),
        "categories": TEMPLATE_CATEGORIES,
        "output_types": OUTPUT_TYPES,
    }


if __name__ == "__main__":
    print(template_summary())
    print("Prebuilt templates:", len(list_prebuilt_templates()))