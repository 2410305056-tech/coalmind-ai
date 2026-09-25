from typing import Any, Dict, List, Optional

from backend.store.base import BaseStore

FOCUS_MINES = ["Gevra", "Kusmunda", "Dipka"]


def _latest(rows: List[Dict[str, Any]], needle: str) -> Optional[Dict[str, Any]]:
    hits = [r for r in rows if needle in str(r.get("parameter") or "").lower()]
    hits.sort(key=lambda r: str(r.get("year") or ""), reverse=True)
    return hits[0] if hits else None


def mine_snapshot(store: BaseStore) -> List[Dict[str, Any]]:
    rows = store.query_metrics() or []
    out = []
    for mine in FOCUS_MINES:
        mine_rows = [r for r in rows if str(r.get("mine") or "").lower().startswith(mine.lower())]
        prod = _latest(mine_rows, "production")
        obr = _latest(mine_rows, "overburden") or _latest(mine_rows, "obr")
        strip = _latest(mine_rows, "stripping")
        last = prod or obr or strip or (mine_rows[-1] if mine_rows else None)
        out.append({
            "mine": mine,
            "subsidiary": (last or {}).get("subsidiary") or "SECL",
            "production": prod,
            "obr": obr,
            "stripping": strip,
            "last_source": (last or {}).get("source_doc"),
            "last_year": (last or {}).get("year"),
        })
    return out
