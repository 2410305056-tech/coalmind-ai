from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from backend.config import SUPABASE_KEY, SUPABASE_URL
from backend.store.base import BaseStore
from backend.store.sqlite_store import SQLiteStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bbox(value: Any) -> List[float]:
    if isinstance(value, list) and len(value) >= 4:
        return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
    if isinstance(value, str):
        try:
            return _bbox(json.loads(value))
        except Exception:
            return [0.0, 0.0, 0.0, 0.0]
    return [0.0, 0.0, 0.0, 0.0]


class SupabaseStore(BaseStore):
    engine_name = "supabase"

    def __init__(self) -> None:
        from supabase import create_client

        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase URL/key missing")
        self._client = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

    def add_document(
        self,
        doc_id: str,
        filename: str,
        file_type: str,
        status: str,
        file_path: str,
        sha256: Optional[str] = None,
        size_bytes: int = 0,
        confidence: float = 0.985,
        compliance: str = "DGMS-VERIFIED",
        pages_count: int = 1,
    ) -> Dict[str, Any]:
        timestamp = _now()
        if not sha256:
            try:
                content = Path(file_path).read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                size_bytes = len(content)
            except Exception:
                sha256 = hashlib.sha256(filename.encode()).hexdigest()
        row = {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "status": status,
            "upload_timestamp": timestamp,
            "file_path": file_path,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "confidence_score": confidence,
            "compliance_status": compliance,
            "pages_count": pages_count,
        }
        self._client.table("documents").upsert(row).execute()
        self.log_audit(
            "INGESTION_REGISTERED",
            "SYSTEM_INGEST_DAEMON",
            f"File '{filename}' ({size_bytes} bytes)",
        )
        return row

    def list_documents(self) -> List[Dict[str, Any]]:
        res = (
            self._client.table("documents")
            .select(
                "id, filename, file_type, status, upload_timestamp, sha256, size_bytes, confidence_score, compliance_status, pages_count"
            )
            .order("upload_timestamp", desc=True)
            .execute()
        )
        return list(res.data or [])

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self._client.table("documents")
            .select("*")
            .eq("id", doc_id)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0
        payload = []
        for chunk in chunks:
            payload.append(
                {
                    "document_id": chunk["document_id"],
                    "document_name": chunk["document_name"],
                    "chunk_index": int(chunk.get("chunk_index", 0)),
                    "page_number": int(chunk.get("page_number", 1)),
                    "text": chunk.get("text") or "",
                    "bounding_box": _bbox(chunk.get("bounding_box")),
                    "embedding": list(chunk.get("embedding") or []),
                }
            )
        for i in range(0, len(payload), 200):
            self._client.table("document_chunks").insert(payload[i : i + 200]).execute()
        return len(payload)

    def search_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        q_vec = np.array(query_vector, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q > 0:
            q_vec = q_vec / norm_q
        res = (
            self._client.table("document_chunks")
            .select("document_id, document_name, page_number, text, bounding_box, embedding")
            .execute()
        )
        results = []
        for r in res.data or []:
            emb = r.get("embedding") or []
            if not emb:
                continue
            chunk_vec = np.array(emb, dtype=np.float32)
            norm_c = np.linalg.norm(chunk_vec)
            if norm_c > 0:
                chunk_vec = chunk_vec / norm_c
            if chunk_vec.shape[0] != q_vec.shape[0]:
                continue
            results.append(
                {
                    "document_name": r.get("document_name"),
                    "document_id": r.get("document_id"),
                    "page_number": r.get("page_number", 1),
                    "text": r.get("text") or "",
                    "bounding_box": _bbox(r.get("bounding_box")),
                    "score": float(np.dot(q_vec, chunk_vec)),
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        if not metrics:
            return 0
        payload = [
            {
                "document_id": m.get("document_id", ""),
                "subsidiary": m.get("subsidiary", ""),
                "mine": m.get("mine", ""),
                "year": m.get("year", ""),
                "parameter": m.get("parameter", ""),
                "value": float(m.get("value", 0.0)),
                "unit": m.get("unit", ""),
                "page_number": int(m.get("page_number", 1)),
                "source_doc": m.get("source_doc", ""),
            }
            for m in metrics
        ]
        for i in range(0, len(payload), 200):
            self._client.table("metrics").insert(payload[i : i + 200]).execute()
        return len(payload)

    def query_metrics(
        self,
        mine: Optional[str] = None,
        subsidiary: Optional[str] = None,
        parameter: Optional[str] = None,
        year: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = self._client.table("metrics").select("*")
        if mine:
            q = q.ilike("mine", f"%{mine}%")
        if subsidiary:
            q = q.ilike("subsidiary", f"%{subsidiary}%")
        if parameter:
            q = q.ilike("parameter", f"%{parameter}%")
        if year:
            q = q.ilike("year", f"%{year}%")
        res = q.order("year").execute()
        return list(res.data or [])

    def get_topics(self) -> List[Dict[str, Any]]:
        domain = {
            "Coal Production": 98,
            "Gevra Mine": 85,
            "Kusmunda OpenCast": 78,
            "Overburden Removal": 72,
            "Stripping Ratio": 68,
            "SECL Performance": 64,
            "Calorific Value": 59,
            "Environmental Clearance": 55,
            "Geological Reserves": 50,
            "Dipka Expansion": 46,
        }
        res = self._client.table("document_chunks").select("text").execute()
        for row in res.data or []:
            txt = (row.get("text") or "").lower()
            for kw in list(domain):
                if kw.lower() in txt:
                    domain[kw] += 4
        return [{"text": k, "value": v} for k, v in domain.items()]

    def get_conflicts(self) -> List[Dict[str, Any]]:
        res = (
            self._client.table("conflicts")
            .select(
                "subsidiary, mine, year, parameter, val1, source1, val2, source2, discrepancy_pct, statutory_impact, reconciliation_status"
            )
            .order("id", desc=True)
            .execute()
        )
        return list(res.data or [])

    def add_conflict(self, conflict: Dict[str, Any]) -> None:
        v1 = float(conflict.get("val1", 0.0))
        v2 = float(conflict.get("val2", 0.0))
        diff_pct = round((abs(v1 - v2) / max(0.01, min(v1, v2))) * 100, 1)
        self._client.table("conflicts").insert(
            {
                "subsidiary": conflict.get("subsidiary", "SECL"),
                "mine": conflict.get("mine", "Gevra"),
                "year": conflict.get("year", "2021-22"),
                "parameter": conflict.get("parameter", "Coal Production"),
                "val1": v1,
                "source1": conflict.get("source1", ""),
                "val2": v2,
                "source2": conflict.get("source2", ""),
                "discrepancy_pct": diff_pct,
                "statutory_impact": "HIGH",
                "reconciliation_status": "PENDING",
                "detected_at": _now(),
            }
        ).execute()
        self.log_audit(
            "DISCREPANCY_FLAGGED",
            "VALIDATION_ENGINE",
            f"Discrepancy at {conflict.get('mine')} ({conflict.get('year')}): {v1} vs {v2}",
        )

    def log_audit(self, event_type: str, operator: str, details: str) -> None:
        timestamp = _now()
        raw = f"{timestamp}|{event_type}|{operator}|{details}"
        try:
            self._client.table("audit_logs").insert(
                {
                    "timestamp": timestamp,
                    "event_type": event_type,
                    "operator": operator,
                    "details": details,
                    "integrity_hash": hashlib.sha256(raw.encode()).hexdigest(),
                }
            ).execute()
        except Exception:
            pass

    def get_audit_logs(self, limit: int = 15) -> List[Dict[str, Any]]:
        res = (
            self._client.table("audit_logs")
            .select("*")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        return list(res.data or [])


def get_store(store_type: str = "sqlite"):
    want = (store_type or "sqlite").strip().lower()
    if want == "supabase" and SUPABASE_URL and SUPABASE_KEY:
        try:
            store = SupabaseStore()
            store.list_documents()
            return store
        except Exception as exc:
            print(f"[CoalMind] Supabase unavailable ({exc}). Using SQLite.")
    return SQLiteStore()
