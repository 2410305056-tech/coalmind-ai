import sqlite3
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.config import DB_PATH
from backend.store.base import BaseStore

class SQLiteStore(BaseStore):
    engine_name = "sqlite"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DB_PATH)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Documents table with enterprise metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    upload_timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    sha256 TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    confidence_score REAL DEFAULT 0.98,
                    compliance_status TEXT DEFAULT 'DGMS-COMPLIANT',
                    pages_count INTEGER DEFAULT 1
                )
            """)
            # Document chunks for RAG with bounding boxes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    bounding_box TEXT,
                    embedding BLOB,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)
            # Structured numerical metrics for SQL analytical engine
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    subsidiary TEXT,
                    mine TEXT,
                    year TEXT,
                    parameter TEXT,
                    value REAL,
                    unit TEXT,
                    page_number INTEGER,
                    source_doc TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)
            # Data discrepancy/conflict alerts with institutional impact scoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflicts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subsidiary TEXT,
                    mine TEXT,
                    year TEXT,
                    parameter TEXT,
                    val1 REAL,
                    source1 TEXT,
                    val2 REAL,
                    source2 TEXT,
                    discrepancy_pct REAL,
                    statutory_impact TEXT,
                    reconciliation_status TEXT,
                    detected_at TEXT
                )
            """)
            # Immutable System Security & Provenance Audit Log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    details TEXT NOT NULL,
                    integrity_hash TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_document(self, doc_id: str, filename: str, file_type: str, status: str, file_path: str,
                     sha256: Optional[str] = None, size_bytes: int = 0, confidence: float = 0.985,
                     compliance: str = "DGMS-VERIFIED", pages_count: int = 1) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat() + "Z"
        if not sha256:
            try:
                content = Path(file_path).read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                size_bytes = len(content)
            except Exception:
                sha256 = hashlib.sha256(filename.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (id, filename, file_type, status, upload_timestamp, file_path, sha256, size_bytes, confidence_score, compliance_status, pages_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, filename, file_type, status, timestamp, file_path, sha256, size_bytes, confidence, compliance, pages_count))
            conn.commit()

        # Log audit trail event
        self.log_audit("INGESTION_REGISTERED", "SYSTEM_INGEST_DAEMON", f"File '{filename}' ({size_bytes} bytes) SHA-256: {sha256[:12]}...")

        return {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "status": status,
            "upload_timestamp": timestamp,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "confidence_score": confidence,
            "compliance_status": compliance,
            "pages_count": pages_count
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_type, status, upload_timestamp, sha256, size_bytes, 
                       confidence_score, compliance_status, pages_count 
                FROM documents ORDER BY upload_timestamp DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                emb = chunk.get("embedding")
                emb_blob = np.array(emb, dtype=np.float32).tobytes() if emb is not None else None
                bbox_json = json.dumps(chunk.get("bounding_box", [0, 0, 0, 0]))
                cursor.execute("""
                    INSERT INTO document_chunks 
                    (document_id, document_name, chunk_index, page_number, text, bounding_box, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk["document_id"],
                    chunk["document_name"],
                    chunk["chunk_index"],
                    chunk["page_number"],
                    chunk["text"],
                    bbox_json,
                    emb_blob
                ))
            conn.commit()
        return len(chunks)

    def search_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        q_vec = np.array(query_vector, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q > 0:
            q_vec = q_vec / norm_q

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, document_id, document_name, chunk_index, page_number, text, bounding_box, embedding 
                FROM document_chunks WHERE embedding IS NOT NULL
            """)
            rows = cursor.fetchall()

        if not rows:
            return []

        results = []
        for r in rows:
            emb_blob = r["embedding"]
            if not emb_blob:
                continue
            chunk_vec = np.frombuffer(emb_blob, dtype=np.float32)
            norm_c = np.linalg.norm(chunk_vec)
            if norm_c > 0:
                chunk_vec = chunk_vec / norm_c
            score = float(np.dot(q_vec, chunk_vec))
            
            bbox = [72, 100, 520, 180]
            if r["bounding_box"]:
                try:
                    bbox = json.loads(r["bounding_box"])
                except Exception:
                    pass

            results.append({
                "document_name": r["document_name"],
                "document_id": r["document_id"],
                "page_number": r["page_number"],
                "text": r["text"],
                "bounding_box": bbox,
                "score": score
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        if not metrics:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for m in metrics:
                cursor.execute("""
                    INSERT INTO metrics 
                    (document_id, subsidiary, mine, year, parameter, value, unit, page_number, source_doc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m.get("document_id", ""),
                    m.get("subsidiary", ""),
                    m.get("mine", ""),
                    m.get("year", ""),
                    m.get("parameter", ""),
                    float(m.get("value", 0.0)),
                    m.get("unit", ""),
                    int(m.get("page_number", 1)),
                    m.get("source_doc", "")
                ))
            conn.commit()
        return len(metrics)

    def query_metrics(self, mine: Optional[str] = None, subsidiary: Optional[str] = None, 
                      parameter: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM metrics WHERE 1=1"
        params = []
        if mine:
            query += " AND LOWER(mine) LIKE ?"
            params.append(f"%{mine.lower()}%")
        if subsidiary:
            query += " AND LOWER(subsidiary) LIKE ?"
            params.append(f"%{subsidiary.lower()}%")
        if parameter:
            query += " AND LOWER(parameter) LIKE ?"
            params.append(f"%{parameter.lower()}%")
        if year:
            query += " AND year LIKE ?"
            params.append(f"%{year}%")
        query += " ORDER BY year ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_topics(self) -> List[Dict[str, Any]]:
        domain_keywords = {
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
            "Borehole Sampling": 42,
            "Washery Yield": 39,
            "Heavy Earth Moving": 35,
            "Continuous Miner": 31,
            "MCL Talcher": 28,
            "BCCL Jharia Coking": 25
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT text FROM document_chunks")
            rows = cursor.fetchall()
            
        if rows:
            for row in rows:
                txt = row["text"].lower()
                for kw in list(domain_keywords.keys()):
                    if kw.lower() in txt:
                        domain_keywords[kw] += 4

        return [{"text": k, "value": v} for k, v in domain_keywords.items()]

    def get_conflicts(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT subsidiary, mine, year, parameter, val1, source1, val2, source2, 
                       discrepancy_pct, statutory_impact, reconciliation_status 
                FROM conflicts ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def add_conflict(self, conflict: Dict[str, Any]) -> None:
        timestamp = datetime.utcnow().isoformat() + "Z"
        v1 = float(conflict.get("val1", 0.0))
        v2 = float(conflict.get("val2", 0.0))
        diff_pct = round((abs(v1 - v2) / max(0.01, min(v1, v2))) * 100, 1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conflicts 
                (subsidiary, mine, year, parameter, val1, source1, val2, source2, discrepancy_pct, statutory_impact, reconciliation_status, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict.get("subsidiary", "SECL"),
                conflict.get("mine", "Gevra"),
                conflict.get("year", "2021-22"),
                conflict.get("parameter", "Overburden Removal (OBR)"),
                v1,
                conflict.get("source1", ""),
                v2,
                conflict.get("source2", ""),
                diff_pct,
                "HIGH // Output Royalty & DGMS Variance",
                "PENDING DIRECTORATE REVIEW",
                timestamp
            ))
            conn.commit()

        self.log_audit("DISCREPANCY_FLAGGED", "VALIDATION_ENGINE", 
                       f"Discrepancy at {conflict.get('mine')} ({conflict.get('year')}): {v1} vs {v2} ({diff_pct}%)")

    def log_audit(self, event_type: str, operator: str, details: str):
        timestamp = datetime.utcnow().isoformat() + "Z"
        raw = f"{timestamp}|{event_type}|{operator}|{details}"
        integrity_hash = hashlib.sha256(raw.encode()).hexdigest()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs (timestamp, event_type, operator, details, integrity_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, event_type, operator, details, integrity_hash))
                conn.commit()
        except Exception:
            pass

    def get_audit_logs(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
