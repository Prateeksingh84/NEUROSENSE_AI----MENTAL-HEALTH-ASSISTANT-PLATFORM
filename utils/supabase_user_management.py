"""
===============================================================================
NeuroSense AI — Supabase User Management
===============================================================================

Purpose:
- User profile management
- Usage limits
- Avatar upload
- Soft delete
- Admin listing
- Safe fallbacks when Supabase schema is missing optional columns

Fixes included:
- get_or_create_profile() accepts name= from app.py
- get_or_create_profile() accepts full_name= and extra kwargs safely
- usage_limits supports knowledge_queries and research_queries
- safe fallback if Supabase schema cache is missing optional columns
===============================================================================
"""

import os
import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from utils.supabase_client import supabase
except Exception:
    supabase = None


SUPABASE_READY = supabase is not None


ALLOWED_USAGE_FIELDS = [
    "daily_messages",
    "monthly_messages",
    "reports_generated",
    "image_uploads",
    "voice_minutes",
    "sign_sessions",
    "research_queries",
    "knowledge_queries",
]


DEFAULT_DAILY_MESSAGE_LIMIT = 100
DEFAULT_MONTHLY_MESSAGE_LIMIT = 2000
DEFAULT_REPORT_LIMIT = 20


def _today() -> str:
    return datetime.date.today().isoformat()


def _month_key() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m")


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


def _safe_execute(builder):
    try:
        return builder.execute()
    except Exception as e:
        print(f"⚠️ Supabase safe execute failed: {e}")
        return None


def _default_usage(user_id: str) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "usage_date": _today(),
        "month_key": _month_key(),
        "daily_messages": 0,
        "monthly_messages": 0,
        "reports_generated": 0,
        "image_uploads": 0,
        "voice_minutes": 0,
        "sign_sessions": 0,
        "research_queries": 0,
        "knowledge_queries": 0,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def _normalize_profile(profile: Dict[str, Any], fallback_name: str = "User") -> Dict[str, Any]:
    """
    Ensure profile always has keys app.py/templates expect.
    """

    profile = profile or {}

    display_name = (
        profile.get("full_name")
        or profile.get("name")
        or profile.get("display_name")
        or fallback_name
        or "User"
    )

    profile.setdefault("full_name", display_name)
    profile.setdefault("name", display_name)
    profile.setdefault("email", "")
    profile.setdefault("phone", "")
    profile.setdefault("role", "user")
    profile.setdefault("preferred_language", "en")
    profile.setdefault("is_active", True)

    return profile


def get_or_create_profile(
    user_id: str,
    email: str = "",
    full_name: str = "",
    name: str = "",
    phone: str = "",
    preferred_language: str = "en",
    role: str = "user",
    **kwargs,
) -> Dict[str, Any]:
    """
    Get or create Supabase user profile.

    Compatibility:
    - app.py may call with name=
    - older code may call with full_name=
    - extra keyword args are accepted safely through **kwargs

    Examples:
        get_or_create_profile(user_id, email="x@y.com", name="Prateek")
        get_or_create_profile(user_id, email="x@y.com", full_name="Prateek")
    """

    display_name = (
        full_name
        or name
        or kwargs.get("display_name")
        or kwargs.get("user_name")
        or kwargs.get("username")
        or "User"
    )

    email = email or kwargs.get("user_email", "") or ""
    phone = phone or kwargs.get("mobile", "") or kwargs.get("phone_number", "") or ""
    preferred_language = (
        preferred_language
        or kwargs.get("lang")
        or kwargs.get("language")
        or "en"
    )
    role = role or kwargs.get("user_role") or "user"

    if not SUPABASE_READY or not user_id:
        return _normalize_profile(
            {
                "id": user_id,
                "email": email,
                "full_name": display_name,
                "name": display_name,
                "phone": phone,
                "role": role,
                "preferred_language": preferred_language,
                "is_active": True,
            },
            fallback_name=display_name,
        )

    try:
        res = (
            supabase.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        if res.data:
            return _normalize_profile(res.data[0], fallback_name=display_name)

        payload = {
            "id": user_id,
            "email": email or "",
            "full_name": display_name or "User",
            "phone": phone or "",
            "role": role or "user",
            "preferred_language": preferred_language or "en",
            "is_active": True,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

        try:
            created = supabase.table("user_profiles").insert(payload).execute()

            if created.data:
                return _normalize_profile(created.data[0], fallback_name=display_name)

            payload["name"] = display_name
            return _normalize_profile(payload, fallback_name=display_name)

        except Exception as insert_error:
            print(f"⚠️ profile insert fallback: {insert_error}")

            # Retry with minimal columns in case schema cache/table does not have optional columns.
            minimal_payload = {
                "id": user_id,
                "email": email or "",
                "full_name": display_name or "User",
            }

            try:
                created = supabase.table("user_profiles").insert(minimal_payload).execute()

                if created.data:
                    profile = created.data[0]
                    profile.setdefault("phone", phone)
                    profile.setdefault("role", role or "user")
                    profile.setdefault("preferred_language", preferred_language or "en")
                    profile.setdefault("is_active", True)
                    return _normalize_profile(profile, fallback_name=display_name)

            except Exception as minimal_error:
                print(f"⚠️ minimal profile insert fallback: {minimal_error}")

            payload["name"] = display_name
            return _normalize_profile(payload, fallback_name=display_name)

    except Exception as e:
        print(f"⚠️ get_or_create_profile fallback: {e}")

        return _normalize_profile(
            {
                "id": user_id,
                "email": email,
                "full_name": display_name or "User",
                "name": display_name or "User",
                "phone": phone,
                "role": role or "user",
                "preferred_language": preferred_language or "en",
                "is_active": True,
            },
            fallback_name=display_name,
        )


def get_today_usage(user_id: str) -> Dict[str, Any]:
    if not SUPABASE_READY or not user_id:
        return _default_usage(user_id)

    today = _today()

    try:
        res = (
            supabase.table("usage_limits")
            .select("*")
            .eq("user_id", user_id)
            .eq("usage_date", today)
            .limit(1)
            .execute()
        )

        if res.data:
            usage = _default_usage(user_id)
            usage.update(res.data[0])
            return usage

        payload = _default_usage(user_id)

        try:
            created = supabase.table("usage_limits").insert(payload).execute()

            if created.data:
                usage = _default_usage(user_id)
                usage.update(created.data[0])
                return usage

        except Exception as insert_error:
            print(f"⚠️ usage_limits insert fallback: {insert_error}")

            # Retry with minimal columns in case schema cache is missing optional columns.
            minimal_payload = {
                "user_id": user_id,
                "usage_date": today,
                "daily_messages": 0,
                "monthly_messages": 0,
            }

            try:
                created = supabase.table("usage_limits").insert(minimal_payload).execute()

                if created.data:
                    usage = _default_usage(user_id)
                    usage.update(created.data[0])
                    return usage

            except Exception as minimal_error:
                print(f"⚠️ usage_limits minimal insert fallback: {minimal_error}")

        return payload

    except Exception as e:
        print(f"⚠️ get_today_usage fallback: {e}")
        return _default_usage(user_id)


def check_usage_allowed(user_id: str) -> Dict[str, Any]:
    usage = get_today_usage(user_id)

    daily = int(usage.get("daily_messages") or 0)
    monthly = int(usage.get("monthly_messages") or 0)
    reports = int(usage.get("reports_generated") or 0)

    allowed = (
        daily < DEFAULT_DAILY_MESSAGE_LIMIT
        and monthly < DEFAULT_MONTHLY_MESSAGE_LIMIT
    )

    return {
        "ok": True,
        "allowed": allowed,
        "usage": usage,
        "limits": {
            "daily_messages": DEFAULT_DAILY_MESSAGE_LIMIT,
            "monthly_messages": DEFAULT_MONTHLY_MESSAGE_LIMIT,
            "reports_generated": DEFAULT_REPORT_LIMIT,
        },
    }


def increment_usage(
    user_id: str,
    field: str = "daily_messages",
    amount: int = 1,
) -> Dict[str, Any]:
    """
    Increment a usage field safely.

    Supports:
    - daily_messages
    - monthly_messages
    - reports_generated
    - image_uploads
    - voice_minutes
    - sign_sessions
    - research_queries
    - knowledge_queries
    """

    if field not in ALLOWED_USAGE_FIELDS:
        raise ValueError(f"Invalid usage field: {field}")

    if not SUPABASE_READY or not user_id:
        return {
            "ok": False,
            "fallback": True,
            "field": field,
            "amount": amount,
        }

    usage = get_today_usage(user_id)
    usage_id = usage.get("id")

    current_value = int(usage.get(field) or 0)
    new_value = current_value + int(amount or 1)

    update_payload = {
        field: new_value,
        "updated_at": _now_iso(),
    }

    try:
        if usage_id:
            res = (
                supabase.table("usage_limits")
                .update(update_payload)
                .eq("id", usage_id)
                .execute()
            )
        else:
            res = (
                supabase.table("usage_limits")
                .update(update_payload)
                .eq("user_id", user_id)
                .eq("usage_date", _today())
                .execute()
            )

        data = getattr(res, "data", None)

        return {
            "ok": True,
            "field": field,
            "amount": amount,
            "new_value": new_value,
            "data": data,
        }

    except Exception as e:
        print(f"⚠️ increment_usage failed for {field}: {e}")

        # If optional field does not exist, do not crash app.
        return {
            "ok": False,
            "field": field,
            "amount": amount,
            "error": str(e),
        }


def get_profile_with_usage(user_id: str) -> Dict[str, Any]:
    profile = {}

    if SUPABASE_READY and user_id:
        try:
            res = (
                supabase.table("user_profiles")
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )

            if res.data:
                profile = _normalize_profile(res.data[0])

        except Exception as e:
            print(f"⚠️ profile load fallback: {e}")

    usage = get_today_usage(user_id)

    return {
        "ok": True,
        "profile": profile or _normalize_profile(
            {
                "id": user_id,
                "full_name": "User",
                "name": "User",
                "role": "user",
                "preferred_language": "en",
                "is_active": True,
            }
        ),
        "usage": usage,
        "limits": {
            "daily_messages": DEFAULT_DAILY_MESSAGE_LIMIT,
            "monthly_messages": DEFAULT_MONTHLY_MESSAGE_LIMIT,
            "reports_generated": DEFAULT_REPORT_LIMIT,
        },
    }


def update_user_profile(
    user_id: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    if not SUPABASE_READY or not user_id:
        return {
            "ok": False,
            "error": "Supabase not available.",
        }

    safe_updates = {}

    allowed = {
        "full_name",
        "name",
        "phone",
        "preferred_language",
        "avatar_url",
        "bio",
    }

    for key, value in (updates or {}).items():
        if key in allowed:
            # Supabase table may not have name column in some schemas.
            # full_name is the primary supported name field.
            if key == "name":
                safe_updates["full_name"] = value
            else:
                safe_updates[key] = value

    safe_updates["updated_at"] = _now_iso()

    try:
        res = (
            supabase.table("user_profiles")
            .update(safe_updates)
            .eq("id", user_id)
            .execute()
        )

        return {
            "ok": True,
            "data": res.data,
        }

    except Exception as e:
        print(f"⚠️ update_user_profile full update failed: {e}")

        # Minimal retry without updated_at if schema cache is missing it.
        minimal_updates = {
            k: v
            for k, v in safe_updates.items()
            if k != "updated_at"
        }

        try:
            res = (
                supabase.table("user_profiles")
                .update(minimal_updates)
                .eq("id", user_id)
                .execute()
            )

            return {
                "ok": True,
                "data": res.data,
            }

        except Exception as e2:
            return {
                "ok": False,
                "error": str(e2),
            }


def upload_avatar(
    user_id: str,
    file_bytes: bytes,
    filename: str = "avatar.png",
) -> Dict[str, Any]:
    """
    Safe avatar upload.

    Keeps app from crashing if storage bucket is not configured.
    """

    if not SUPABASE_READY or not user_id:
        return {
            "ok": False,
            "error": "Supabase not available.",
        }

    try:
        path = f"avatars/{user_id}/{filename}"

        storage = supabase.storage.from_("avatars")
        storage.upload(
            path,
            file_bytes,
            {
                "content-type": "image/png",
                "upsert": "true",
            },
        )

        public_url = storage.get_public_url(path)

        update_user_profile(user_id, {"avatar_url": public_url})

        try:
            increment_usage(user_id, "image_uploads", 1)
        except Exception:
            pass

        return {
            "ok": True,
            "path": path,
            "avatar_url": public_url,
        }

    except Exception as e:
        print(f"⚠️ upload_avatar failed: {e}")
        return {
            "ok": False,
            "error": str(e),
        }


def soft_delete_account(user_id: str) -> Dict[str, Any]:
    if not SUPABASE_READY or not user_id:
        return {
            "ok": False,
            "error": "Supabase not available.",
        }

    try:
        res = (
            supabase.table("user_profiles")
            .update({
                "is_active": False,
                "deleted_at": _now_iso(),
                "updated_at": _now_iso(),
            })
            .eq("id", user_id)
            .execute()
        )

        return {
            "ok": True,
            "data": res.data,
        }

    except Exception as e:
        print(f"⚠️ soft_delete_account full update failed: {e}")

        try:
            res = (
                supabase.table("user_profiles")
                .update({
                    "is_active": False,
                })
                .eq("id", user_id)
                .execute()
            )

            return {
                "ok": True,
                "data": res.data,
            }

        except Exception as e2:
            return {
                "ok": False,
                "error": str(e2),
            }


def list_all_profiles(limit: int = 100) -> Dict[str, Any]:
    if not SUPABASE_READY:
        return {
            "ok": False,
            "profiles": [],
            "error": "Supabase not available.",
        }

    try:
        res = (
            supabase.table("user_profiles")
            .select("*")
            .limit(limit)
            .execute()
        )

        profiles = [
            _normalize_profile(row)
            for row in (res.data or [])
        ]

        return {
            "ok": True,
            "profiles": profiles,
        }

    except Exception as e:
        return {
            "ok": False,
            "profiles": [],
            "error": str(e),
        }


if __name__ == "__main__":
    print("SUPABASE_READY:", SUPABASE_READY)
    print("ALLOWED_USAGE_FIELDS:", ALLOWED_USAGE_FIELDS)

    # Compatibility test for app.py call style
    test_profile = get_or_create_profile(
        user_id="test-user",
        email="test@example.com",
        name="Test User",
        phone="9999999999",
    )
    print("TEST_PROFILE:", test_profile)