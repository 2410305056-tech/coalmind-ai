"""Apply anon-read policies and seed sample filings into Supabase."""
from pathlib import Path
import json
import os
import shutil
import sys
import uuid
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from backend.database.link_supabase import parse_env, run_sql, statements  # noqa: E402


def apply_policies() -> None:
    src = parse_env(ROOT / ".env")
    token, ref = src.get("SUPABASE_ACCESS_TOKEN", ""), src.get("SUPABASE_PROJECT_REF", "")
    sql = (Path(__file__).with_name("anon_read.sql")).read_text(encoding="utf-8")
    ok = fail = 0
    for stmt in statements(sql):
        code = run_sql(token, ref, stmt)
        if 200 <= code < 300:
            ok += 1
        else:
            fail += 1
    print("policies_ok", ok, "policies_fail", fail)


def write_frontend_env() -> None:
    src = parse_env(Path(r"C:\Users\YASHS\MonkeyCode\supabase-app\.env"))
    url = src.get("SUPABASE_URL", "")
    anon = src.get("SUPABASE_ANON_KEY", "")
    dest = ROOT / "frontend" / ".env.production"
    dest.write_text(
        f"VITE_SUPABASE_URL={url}\nVITE_SUPABASE_ANON_KEY={anon}\n",
        encoding="utf-8",
    )
    print("wrote frontend .env.production (anon key only)")


def seed() -> None:
    from backend.store.supabase_store import get_store
    from backend.engine.parser import parse_document
    from backend.engine.conflict_detector import scan_and_record_conflicts
    from backend.sample_data.seed_generator import ensure_sample_files
    from backend.config import UPLOADS_DIR, STORE_TYPE

    store = get_store("supabase")
    if getattr(store, "engine_name", "") != "supabase":
        raise SystemExit("not on supabase")
    existing = store.list_documents()
    if existing:
        print("already_seeded", len(existing))
        return
    pdf_sample, xlsx_sample = ensure_sample_files()
    pdf_id = str(uuid.uuid4())
    dest_pdf = UPLOADS_DIR / pdf_sample.name
    shutil.copy2(pdf_sample, dest_pdf)
    store.add_document(pdf_id, pdf_sample.name, "pdf", "completed", str(dest_pdf))
    chunks, metrics, *_ = parse_document(dest_pdf, pdf_id, pdf_sample.name)
    store.add_chunks(chunks)
    store.add_metrics(metrics)

    xlsx_id = str(uuid.uuid4())
    dest_xlsx = UPLOADS_DIR / xlsx_sample.name
    shutil.copy2(xlsx_sample, dest_xlsx)
    store.add_document(xlsx_id, xlsx_sample.name, "xlsx", "completed", str(dest_xlsx))
    chunks_x, metrics_x, *_ = parse_document(dest_xlsx, xlsx_id, xlsx_sample.name)
    store.add_chunks(chunks_x)
    store.add_metrics(metrics_x)
    n = scan_and_record_conflicts(store)
    print(
        "seeded",
        "chunks",
        len(chunks) + len(chunks_x),
        "metrics",
        len(metrics) + len(metrics_x),
        "new_conflicts",
        n,
    )


if __name__ == "__main__":
    apply_policies()
    write_frontend_env()
    seed()
