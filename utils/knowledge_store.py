"""
===============================================================================
NeuroSense AI — Knowledge Chat Store
===============================================================================

Purpose:
- Store Knowledge Chat history locally.
- Compatible with app.py calling:
    append_knowledge_history(user_id=..., entry=..., limit=...)
    append_knowledge_history(user_id=..., query=..., answer=..., ...)
===============================================================================
"""

import os
import json
import datetime
import uuid
from typing import Any, Dict, List, Optional


DATA_DIR = os.path.join(os.getcwd(), "data")
KNOWLEDGE_HISTORY_FILE = os.path.join(DATA_DIR, "knowledge_chat_history.json")


def _ensure_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(KNOWLEDGE_HISTORY_FILE):
        with open(KNOWLEDGE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)


def _read_all() -> Dict[str, List[Dict[str, Any]]]:
    _ensure_file()

    try:
        with open(KNOWLEDGE_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, dict) else {}

    except Exception:
        return {}


def _write_all(data: Dict[str, List[Dict[str, Any]]]) -> None:
    _ensure_file()

    with open(KNOWLEDGE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _safe_user_id(user_id: Optional[str]) -> str:
    return str(user_id or "guest").strip().lower() or "guest"


def get_knowledge_history(
    user_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    user_id = _safe_user_id(user_id)
    data = _read_all()

    items = data.get(user_id, [])

    if not isinstance(items, list):
        return []

    return items[-limit:]


def append_knowledge_history(
    user_id: str,
    entry: Optional[Dict[str, Any]] = None,
    query: str = "",
    question: str = "",
    answer: str = "",
    sources: Optional[List[Dict[str, Any]]] = None,
    scope: Optional[Dict[str, Any]] = None,
    model: str = "",
    used_ollama: bool = False,
    grounded: bool = False,
    report_context: Optional[Dict[str, Any]] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Flexible append function.

    Supports both:
        append_knowledge_history(user_id=..., entry=...)
    and:
        append_knowledge_history(user_id=..., query=..., answer=...)
    """

    user_id = _safe_user_id(user_id)
    data = _read_all()
    data.setdefault(user_id, [])

    if entry and isinstance(entry, dict):
        item = dict(entry)
    else:
        q = query or question

        item = {
            "id": str(uuid.uuid4()),
            "query": str(q or ""),
            "question": str(q or ""),
            "answer": str(answer or ""),
            "sources": sources or [],
            "scope": scope or {},
            "model": model,
            "used_ollama": bool(used_ollama),
            "grounded": bool(grounded),
            "report_context": report_context or {},
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

    item.setdefault("id", str(uuid.uuid4()))
    item.setdefault("created_at", datetime.datetime.utcnow().isoformat())

    if "query" not in item and "question" in item:
        item["query"] = item.get("question", "")

    if "question" not in item and "query" in item:
        item["question"] = item.get("query", "")

    data[user_id].append(item)
    data[user_id] = data[user_id][-limit:]

    _write_all(data)

    return item


def clear_knowledge_history(user_id: str) -> bool:
    user_id = _safe_user_id(user_id)
    data = _read_all()

    data[user_id] = []

    _write_all(data)

    return True


def knowledge_history_summary(user_id: Optional[str] = None) -> Dict[str, Any]:
    data = _read_all()

    if user_id:
        uid = _safe_user_id(user_id)
        items = data.get(uid, [])

        return {
            "ok": True,
            "user_id": uid,
            "count": len(items) if isinstance(items, list) else 0,
            "file": KNOWLEDGE_HISTORY_FILE,
        }

    total = 0

    for items in data.values():
        if isinstance(items, list):
            total += len(items)

    return {
        "ok": True,
        "users": len(data),
        "total_items": total,
        "file": KNOWLEDGE_HISTORY_FILE,
    }


def knowledge_store_status(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Compatibility function expected by app.py.
    """
    return knowledge_history_summary(user_id=user_id)


if __name__ == "__main__":
    print(knowledge_store_status())