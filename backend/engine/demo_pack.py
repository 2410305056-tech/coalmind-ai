import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List

from backend.config import UPLOADS_DIR
from backend.engine.conflict_detector import scan_and_record_conflicts
from backend.engine.parser import parse_document
from backend.sample_data.seed_generator import ensure_sample_files
from backend.store.base import BaseStore

SAMPLE_NAMES = (
    "SECL_Annual_Geological_Report_2022_24.pdf",
    "CMPDI_Mine_Master_Register_2024.xlsx",
)


def load_sih_sample(store: BaseStore, force: bool = False) -> Dict[str, Any]:
    pdf_sample, xlsx_sample = ensure_sample_files()
    existing = {str(d.get("filename") or "") for d in store.list_documents()}
    added: List[str] = []

    for path, ftype in ((pdf_sample, "pdf"), (xlsx_sample, "xlsx")):
        if path.name in existing and not force:
            continue
        doc_id = str(uuid.uuid4())
        dest = UPLOADS_DIR / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        store.add_document(doc_id, path.name, ftype, "completed", str(dest))
        chunks, metrics, *_ = parse_document(Path(dest), doc_id, path.name)
        store.add_chunks(chunks)
        store.add_metrics(metrics)
        added.append(path.name)

    if added:
        scan_and_record_conflicts(store)

    return {
        "added": added,
        "already_present": [n for n in SAMPLE_NAMES if n in existing and n not in added],
        "documents": len(store.list_documents()),
        "message": (
            f"Loaded SIH sample: {', '.join(added)}"
            if added
            else "SIH sample (SECL 2022–24) is already in the library."
        ),
    }
