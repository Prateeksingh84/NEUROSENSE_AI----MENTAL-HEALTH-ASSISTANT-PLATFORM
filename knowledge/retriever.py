"""
===============================================================================
NeuroSense AI — Knowledge Retriever
===============================================================================

Purpose:
- Retrieve approved mental-health knowledge snippets for Knowledge Chat.
- Uses lightweight keyword scoring.
- No external dependency required.
===============================================================================
"""

import re
from typing import Any, Dict, List

from knowledge.mental_health_kb import get_all_kb_items, get_kb_status


def _normalize(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s\-_/']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str) -> List[str]:
    stopwords = {
        "the", "a", "an", "is", "are", "am", "i", "me", "my", "you", "your",
        "and", "or", "to", "for", "of", "in", "on", "with", "about", "what",
        "how", "why", "can", "could", "would", "please", "tell",
        "explain", "give", "need", "want", "that", "this", "it",
        "does", "do", "did", "as", "be", "by", "from",
    }

    return [
        token for token in _normalize(text).split()
        if token and token not in stopwords and len(token) > 1
    ]


def score_kb_item(query: str, item: Dict[str, Any]) -> float:
    q_norm = _normalize(query)
    q_tokens = set(_tokens(query))

    title = _normalize(item.get("title", ""))
    category = _normalize(item.get("category", ""))
    content = _normalize(item.get("content", ""))

    keywords = item.get("keywords", []) or []
    keyword_norms = [_normalize(k) for k in keywords]

    score = 0.0

    # Exact keyword phrase match is strongest.
    for kw in keyword_norms:
        if kw and kw in q_norm:
            score += 6.0

    # Category match.
    if category and category in q_norm:
        score += 3.0

    # Title/category/content token match.
    for token in q_tokens:
        if token in title:
            score += 2.0
        if token in category:
            score += 1.5
        if token in content:
            score += 0.7

    # Keyword token overlap.
    keyword_token_set = set()

    for kw in keyword_norms:
        keyword_token_set.update(_tokens(kw))

    score += len(q_tokens.intersection(keyword_token_set)) * 1.5

    # Boost common real-life wellbeing decision words.
    decision_words = {
        "work", "trip", "leave", "break", "vacation",
        "mentally", "mental", "stress", "stressed", "rest",
        "burnout", "exhausted", "workload",
    }

    score += len(q_tokens.intersection(decision_words)) * 1.8

    return score


def retrieve_knowledge(
    query: str,
    top_k: int = 4,
    min_score: float = 1.0,
) -> List[Dict[str, Any]]:
    query = str(query or "").strip()

    if not query:
        return []

    scored = []

    for item in get_all_kb_items():
        score = score_kb_item(query, item)

        if score >= min_score:
            row = dict(item)
            row["score"] = round(score, 2)
            scored.append(row)

    scored.sort(key=lambda x: x.get("score", 0), reverse=True)

    return scored[:top_k]


def build_context_from_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""

    blocks = []

    for idx, item in enumerate(results, start=1):
        blocks.append(
            f"""
SOURCE {idx}
ID: {item.get("id")}
TITLE: {item.get("title")}
CATEGORY: {item.get("category")}
CONTENT:
{item.get("content")}

SAFETY NOTE:
{item.get("safety_note", "")}
""".strip()
        )

    return "\n\n---\n\n".join(blocks)


def knowledge_retrieval_status() -> Dict[str, Any]:
    status = get_kb_status()

    status.update({
        "retriever": "keyword_weighted_v2",
        "grounding": "approved_internal_kb",
        "hallucination_control": "answers_grounded_in_approved_kb",
    })

    return status


def knowledge_status() -> Dict[str, Any]:
    return knowledge_retrieval_status()


if __name__ == "__main__":
    q = "I am not feeling well mentally should I leave work and go for a trip?"
    results = retrieve_knowledge(q)

    print(knowledge_status())

    for r in results:
        print(r["score"], r["title"])