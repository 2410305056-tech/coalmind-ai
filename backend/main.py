import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import UPLOADS_DIR, REPORTS_DIR, STORE_TYPE, MAX_UPLOAD_SIZE_MB, PROJECT_ROOT
from backend.store.supabase_store import get_store
from backend.engine.parser import parse_document
from backend.engine.conflict_detector import scan_and_record_conflicts
from backend.engine.llm_router import process_query
from backend.engine.report_generator import generate_executive_pdf
from backend.sample_data.seed_generator import ensure_sample_files

# Store initialization
store = get_store(STORE_TYPE)

# Lifespan startup handler for automatic seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure sample files exist
    pdf_sample, xlsx_sample = ensure_sample_files()
    
    # Auto-seed if database is empty
    docs = store.list_documents()
    if not docs:
        print("[CoalMind AI] Seeding initial CMPDI/CIL repository documents...")
        # Ingest PDF
        pdf_id = str(uuid.uuid4())
        dest_pdf = UPLOADS_DIR / pdf_sample.name
        shutil.copy2(pdf_sample, dest_pdf)
        store.add_document(pdf_id, pdf_sample.name, "pdf", "completed", str(dest_pdf))
        chunks, metrics, *_ = parse_document(dest_pdf, pdf_id, pdf_sample.name)
        store.add_chunks(chunks)
        store.add_metrics(metrics)

        # Ingest Excel
        xlsx_id = str(uuid.uuid4())
        dest_xlsx = UPLOADS_DIR / xlsx_sample.name
        shutil.copy2(xlsx_sample, dest_xlsx)
        store.add_document(xlsx_id, xlsx_sample.name, "xlsx", "completed", str(dest_xlsx))
        chunks_x, metrics_x, *_ = parse_document(dest_xlsx, xlsx_id, xlsx_sample.name)
        store.add_chunks(chunks_x)
        store.add_metrics(metrics_x)

        # Scan for cross-source discrepancies
        scan_and_record_conflicts(store)
        print(f"[CoalMind AI] Seeding complete! Ingested {len(chunks) + len(chunks_x)} chunks, {len(metrics) + len(metrics_x)} metrics.")

    yield
    print("[CoalMind AI] Shutdown cleanup.")

app = FastAPI(
    title="CoalMind AI Core Engine",
    description="SIH26023 AI-Powered Geological, Mining and other Reporting Solution for CMPDI/CIL subsidiaries",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Request & Response Models
# ------------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    subsidiary: str
    reporting_year: str

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------
DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

@app.get("/")
def root():
    index = DIST_DIR / "index.html"
    if index.is_file():
        return FileResponse(index, media_type="text/html")
    return {
        "title": "CoalMind",
        "team": "AGNIVAULT",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health_check():
    """
    GET /health
    Returns: { "status": "ok", "store": "sqlite"|"supabase", "python_ok": true }
    """
    return {
        "status": "ok",
        "store": getattr(store, "engine_name", STORE_TYPE or "sqlite"),
        "python_ok": True,
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    POST /api/upload (Multipart FormData: file <= 25MB)
    Returns: { "document_id": "uuid", "filename": "str", "file_type": "pdf"|"xlsx"|"csv", 
               "status": "completed"|"ocr_unavailable"|"failed", "chunk_count": int, 
               "metrics_count": int, "message": "str" }
    """
    filename = file.filename or "unknown_document"
    ext = Path(filename).suffix.lower().replace(".", "")
    if ext not in ["pdf", "xlsx", "xls", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Please upload .pdf, .xlsx, or .csv"
        )
    
    doc_id = str(uuid.uuid4())
    norm_type = "xlsx" if ext in ["xlsx", "xls"] else ext
    save_path = UPLOADS_DIR / f"{doc_id}_{filename}"
    
    # Save file contents
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB}MB."
        )

    with open(save_path, "wb") as f:
        f.write(content)

    try:
        # Parse document into chunks and metrics
        chunks, metrics, parse_status = parse_document(save_path, doc_id, filename)
        status_label = parse_status if parse_status in ("completed", "ocr_unavailable", "failed") else "completed"
        store.add_document(doc_id, filename, norm_type, status_label, str(save_path))
        chunk_count = store.add_chunks(chunks)
        metrics_count = store.add_metrics(metrics)

        # Trigger conflict detection across historical knowledge base
        scan_and_record_conflicts(store)

        return {
            "document_id": doc_id,
            "filename": filename,
            "file_type": norm_type,
            "status": status_label,
            "chunk_count": chunk_count,
            "metrics_count": metrics_count,
            "message": f"Successfully processed and indexed {chunk_count} semantic blocks and {metrics_count} analytical metrics."
        }
    except Exception as e:
        store.add_document(doc_id, filename, norm_type, "failed", str(save_path))
        return {
            "document_id": doc_id,
            "filename": filename,
            "file_type": norm_type,
            "status": "failed",
            "chunk_count": 0,
            "metrics_count": 0,
            "message": f"Extraction encountered an error: {str(e)}"
        }

@app.get("/api/documents")
def list_documents():
    """
    GET /api/documents
    Returns: Array of { "id": "uuid", "filename": "str", "file_type": "str", "status": "str", "upload_timestamp": "ISO-string" }
    """
    return store.list_documents()

@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: str):
    """
    GET /api/documents/{id}/file
    Returns: Raw PDF binary (application/pdf)
    """
    doc = store.get_document(doc_id)
    if not doc:
        # Check if requested doc_id is in uploaded file names
        for f in UPLOADS_DIR.iterdir():
            if doc_id in f.name:
                return FileResponse(
                    str(f),
                    media_type="application/pdf",
                    filename=f.name
                )
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        # Fallback to sample data PDF if exists
        pdf_sample, _ = ensure_sample_files()
        file_path = pdf_sample

    return FileResponse(
        str(file_path),
        media_type="application/pdf" if file_path.suffix.lower() == ".pdf" else "application/octet-stream",
        filename=doc.get("filename", file_path.name)
    )

@app.post("/api/query")
async def execute_query(req: QueryRequest):
    """
    POST /api/query
    Request: { "query": "str" }
    Returns: { "answer": "str", "intent": "sql"|"rag", "chart_data": {...} | null, "sources": [...] }
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    
    result = await process_query(req.query, store)
    return result

@app.get("/api/topics")
def get_topics():
    """
    GET /api/topics
    Returns: Array of { "text": "str", "value": int }
    """
    return store.get_topics()

@app.get("/api/conflicts")
def get_conflicts():
    """
    GET /api/conflicts
    Returns: Array of { "subsidiary": "str", "mine": "str", "year": "str", 
                        "parameter": "str", "val1": num, "source1": "str", 
                        "val2": num, "source2": "str" }
    """
    return store.get_conflicts()

@app.post("/api/report/generate")
def generate_report(req: ReportRequest):
    """
    POST /api/report/generate
    Request: { "subsidiary": "str", "reporting_year": "str" }
    Returns: PDF Blob download (Content-Disposition: attachment)
    """
    pdf_path = generate_executive_pdf(req.subsidiary, req.reporting_year, store)
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={"Content-Disposition": f'attachment; filename="{pdf_path.name}"'}
    )

_assets = DIST_DIR / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
