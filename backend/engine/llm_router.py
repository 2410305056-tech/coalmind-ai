import json
from typing import Any, Dict, List, Optional, Tuple

import httpx

from backend.config import GEMINI_API_KEY, GROQ_API_KEY
from backend.engine.embedding import embedder
from backend.engine.followup import expand_query
from backend.store.base import BaseStore

SYSTEM = (
    "You are CoalMind AI, a copilot for CMPDI and Coal India reports. "
    "Answer only from the archive excerpts and metrics provided. "
    "Cite document name and page. If the archive does not contain the answer, say so. "
    "Do not invent figures. Be concise. Use Indian financial-year labels when present."
)

GEMINI_MODELS = (
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-pro-latest",
)

GROQ_MODELS = (
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
)


def ai_status() -> Dict[str, Any]:
    if GROQ_API_KEY:
        return {"ai": True, "ai_provider": "groq"}
    if GEMINI_API_KEY:
        return {"ai": True, "ai_provider": "gemini"}
    return {"ai": True, "ai_provider": "grounded"}


def classify_query_intent(query: str) -> str:
    q_low = query.lower()
    sql_triggers = [
        "compare", "production", "chart", "graph", "metric", "trend",
        "between", "versus", "vs", "total", "average", "output", "tonnes",
        "obr", "stripping ratio", "target", "historical", "growth",
    ]
    return "sql" if any(t in q_low for t in sql_triggers) else "rag"


async def process_query(
    query: str,
    store: BaseStore,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    expanded = expand_query(query, history)
    intent = classify_query_intent(expanded)
    if intent == "sql":
        result = await _handle_sql_intent(expanded, store)
    else:
        result = await _handle_rag_intent(expanded, store)
    result["query"] = expanded
    return result


async def _handle_sql_intent(query: str, store: BaseStore) -> Dict[str, Any]:
    q_low = query.lower()
    mine_target = None
    for m in ["gevra", "kusmunda", "dipka", "rajmahal", "singrauli", "talcher", "jharia", "raniganj", "piparwar"]:
        if m in q_low:
            mine_target = m.capitalize()
            break

    sub_target = None
    for s in ["secl", "mcl", "ncl", "bccl", "ccl", "ecl", "wcl", "cmpdi"]:
        if s in q_low:
            sub_target = s.upper()
            break

    param_target = "Coal Production"
    if "obr" in q_low or "overburden" in q_low:
        param_target = "Overburden Removal (OBR)"
    elif "stripping" in q_low:
        param_target = "Stripping Ratio"

    records = store.query_metrics(mine=mine_target, subsidiary=sub_target, parameter=param_target)
    if not records:
        records = store.query_metrics(parameter=param_target)
    if not records:
        records = store.query_metrics()

    deduped: Dict[str, Dict[str, Any]] = {}
    sources: List[Dict[str, Any]] = []
    seen_sources = set()

    for r in sorted(records, key=lambda x: str(x.get("year", ""))):
        key = f"{r.get('mine', 'Mine')}_{r.get('year', 'FY')}"
        if key not in deduped:
            deduped[key] = r
        src_key = f"{r.get('source_doc')}:{r.get('page_number')}"
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            sources.append({
                "document_name": r.get("source_doc", "CIL_Annual_Report.pdf"),
                "page_number": int(r.get("page_number", 1) or 1),
                "bounding_box": [72.0, 140.0, 520.0, 220.0],
            })

    labels = []
    values = []
    fact_rows = []
    for r in list(deduped.values())[:8]:
        labels.append(f"{r.get('mine', 'Mine')} ({r.get('year', 'FY')})")
        values.append(float(r.get("value", 0.0) or 0.0))
        fact_rows.append({
            "mine": r.get("mine"),
            "year": r.get("year"),
            "parameter": r.get("parameter"),
            "value": r.get("value"),
            "unit": r.get("unit"),
            "source": r.get("source_doc"),
            "page": r.get("page_number"),
        })

    unit = "MT" if "Production" in param_target else ("M.Cum" if "OBR" in param_target else "ratio")

    conflicts = store.get_conflicts()
    relevant_conflict = None
    for c in conflicts:
        if (not mine_target or str(c.get("mine", "")).lower() == mine_target.lower()) and param_target.lower() in str(c.get("parameter", "")).lower():
            relevant_conflict = c
            break

    context = "INDEXED METRICS (JSON):\n" + json.dumps(fact_rows, ensure_ascii=False, indent=2)
    if relevant_conflict:
        context += "\n\nFLAGGED DISCREPANCY:\n" + json.dumps(relevant_conflict, ensure_ascii=False, indent=2)

    answer, provider = await _complete(
        f"{context}\n\nQuestion: {query}\nWrite a short briefing with the figures above."
    )
    if not answer:
        answer = _grounded_sql(query, param_target, mine_target, fact_rows, unit, relevant_conflict)
        provider = "grounded"

    chart_data = {
        "type": "bar",
        "unit": unit,
        "labels": labels,
        "values": values,
    }

    return {
        "answer": answer,
        "intent": "sql",
        "chart_data": chart_data if labels else None,
        "sources": sources,
        "ai": True,
        "ai_provider": provider,
    }


async def _handle_rag_intent(query: str, store: BaseStore) -> Dict[str, Any]:
    q_vec = embedder.embed_text(query)
    chunks = store.search_chunks(q_vec, top_k=4)

    sources = []
    excerpts = []
    for c in chunks:
        sources.append({
            "document_name": c["document_name"],
            "page_number": c["page_number"],
            "bounding_box": c.get("bounding_box") or [55.0, 80.0, 540.0, 160.0],
        })
        excerpts.append({
            "document": c["document_name"],
            "page": c["page_number"],
            "text": (c.get("text") or "")[:1200],
        })

    context = "ARCHIVE EXCERPTS:\n" + json.dumps(excerpts, ensure_ascii=False, indent=2)
    answer, provider = await _complete(
        f"{context}\n\nQuestion: {query}\nAnswer from these excerpts only. Quote briefly."
    )
    if not answer:
        answer = _grounded_rag(query, excerpts)
        provider = "grounded"

    return {
        "answer": answer,
        "intent": "rag",
        "chart_data": None,
        "sources": sources,
        "ai": True,
        "ai_provider": provider,
    }


def _grounded_sql(query, param, mine, rows, unit, conflict) -> str:
    if not rows:
        return (
            f"CoalMind AI searched indexed metrics for “{query}” and found no matching rows. "
            "Upload a production register or annual report, then ask again."
        )
    parts = [
        f"CoalMind AI reviewed {len(rows)} indexed figures for **{param}**"
        + (f" at **{mine}**" if mine else "")
        + "."
    ]
    bullets = []
    for r in rows:
        bullets.append(
            f"- {r.get('mine') or 'Mine'} ({r.get('year') or 'FY'}): "
            f"{r.get('value')} {r.get('unit') or unit} — {r.get('source') or 'archive'}"
        )
    if len(rows) >= 2:
        try:
            start = float(rows[0]["value"])
            end = float(rows[-1]["value"])
            pct = round(((end - start) / max(0.01, abs(start))) * 100, 1)
            direction = "up" if pct >= 0 else "down"
            parts.append(
                f"Across the series, values move {direction} {abs(pct)}% "
                f"from {rows[0]['value']} to {rows[-1]['value']} {unit}."
            )
        except (TypeError, ValueError, KeyError):
            pass
    parts.append("Cited metrics:\n" + "\n".join(bullets))
    if conflict:
        parts.append(
            f"Integrity flag: {conflict.get('mine')} {conflict.get('year')} "
            f"{conflict.get('parameter')} is {conflict.get('val1')} in {conflict.get('source1')} "
            f"vs {conflict.get('val2')} in {conflict.get('source2')}."
        )
    return "\n\n".join(parts)


def _grounded_rag(query, excerpts) -> str:
    if not excerpts:
        return (
            f"CoalMind AI found no matching passages for “{query}”. "
            "Ingest a PDF or spreadsheet and retry."
        )
    top = excerpts[0]
    quote = " ".join(str(top.get("text") or "").split())[:420]
    more = ""
    if len(excerpts) > 1:
        names = ", ".join(f"{e['document']} p.{e['page']}" for e in excerpts[1:3])
        more = f" Also consulted: {names}."
    return (
        f"CoalMind AI (grounded on the archive):\n\n"
        f"From **{top.get('document')}** (page {top.get('page')}):\n\n"
        f"> {quote}\n\n"
        f"This is the closest passage to “{query}”.{more}"
    )


async def _complete(user_text: str) -> Tuple[Optional[str], str]:
    if GROQ_API_KEY:
        text = await _call_groq(user_text)
        if text:
            return text, "groq"
    if GEMINI_API_KEY:
        text = await _call_gemini(user_text)
        if text:
            return text, "gemini"
    return None, "grounded"


async def _call_groq(user_text: str) -> Optional[str]:
    for model in GROQ_MODELS:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM},
                            {"role": "user", "content": user_text},
                        ],
                        "temperature": 0.2,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            continue
    return None


def _gemini_text(data: dict) -> Optional[str]:
    for cand in data.get("candidates") or []:
        parts = ((cand.get("content") or {}).get("parts")) or []
        bits = [p.get("text", "") for p in parts if p.get("text")]
        if bits:
            return "\n".join(bits).strip()
    return None


async def _call_gemini(user_text: str) -> Optional[str]:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in GEMINI_MODELS:
            try:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={GEMINI_API_KEY}"
                )
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    continue
                text = _gemini_text(resp.json())
                if text:
                    return text
            except Exception:
                continue
    return None
