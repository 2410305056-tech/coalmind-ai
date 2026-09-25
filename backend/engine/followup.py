from typing import Dict, List, Optional

FOLLOW_HINTS = (
    "only",
    "show",
    "just",
    "now",
    "also",
    "same",
    "what about",
    "and ",
    "for ",
    "filter",
    "instead",
    "that mine",
    "this year",
)


def expand_query(query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    q = (query or "").strip()
    if not q or not history:
        return q
    last_user = ""
    for turn in reversed(history):
        if turn.get("role") == "user" and turn.get("content"):
            last_user = str(turn["content"]).strip()
            break
    if not last_user:
        return q
    low = q.lower()
    short = len(q.split()) <= 8
    hinted = any(low.startswith(h) or f" {h.strip()} " in f" {low} " for h in FOLLOW_HINTS)
    if short or hinted:
        return f"{last_user}. Follow-up constraint: {q}"
    return q
