import re
import pypdf
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.engine.embedding import embedder

KNOWN_MINES = ["Gevra", "Kusmunda", "Dipka", "Rajmahal", "Singrauli", "Talcher", "Jharia", "Raniganj", "Piparwar", "Korba", "Ib Valley", "Wardha"]
KNOWN_SUBSIDIARIES = ["SECL", "MCL", "NCL", "BCCL", "CCL", "ECL", "WCL", "CMPDI"]

def parse_document(file_path: Path, doc_id: str, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Parses a PDF, XLSX, or CSV file.
    Returns:
        (chunks, metrics, extraction_status)
        extraction_status: "completed" | "ocr_unavailable" | "failed"
    """
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            chunks, metrics, status_code = _parse_pdf(file_path, doc_id, filename)
            return chunks, metrics, status_code
        elif ext in [".xlsx", ".xls"]:
            chunks, metrics = _parse_excel(file_path, doc_id, filename)
            return chunks, metrics, "completed"
        elif ext == ".csv":
            chunks, metrics = _parse_csv(file_path, doc_id, filename)
            return chunks, metrics, "completed"
        else:
            text = file_path.read_text(errors='ignore')
            chunk = {
                "document_id": doc_id,
                "document_name": filename,
                "chunk_index": 0,
                "page_number": 1,
                "text": text[:1000],
                "bounding_box": [50.0, 50.0, 500.0, 200.0],
                "embedding": embedder.embed_text(text[:1000])
            }
            return [chunk], [], "completed"
    except Exception as e:
        print(f"[Parser Error] Failed to parse {filename}: {e}")
        return [], [], "failed"

def _parse_pdf(file_path: Path, doc_id: str, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    chunks = []
    metrics = []
    chunk_idx = 0
    total_raw_text = ""

    reader = pypdf.PdfReader(str(file_path))
    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        total_raw_text += text
        
        # Split into logical sections
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 15]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 15]

        for p_idx, p_text in enumerate(paragraphs):
            y_start = 80.0 + (p_idx * 45.0) % 500.0
            bbox = [54.0, round(y_start, 1), 540.0, round(y_start + 40.0, 1)]
            emb = embedder.embed_text(p_text)
            chunks.append({
                "document_id": doc_id,
                "document_name": filename,
                "chunk_index": chunk_idx,
                "page_number": page_num + 1,
                "text": p_text,
                "bounding_box": bbox,
                "embedding": emb
            })
            chunk_idx += 1
            extracted = _extract_metrics_from_text(p_text, doc_id, filename, page_num + 1)
            metrics.extend(extracted)

    # Scanned PDF with zero extractable text fallback
    if len(chunks) == 0 or len(total_raw_text.strip()) < 20:
        # Create an OCR fallback chunk
        fallback_text = (
            f"Archival Scanned Geological Filing: {filename}. Optical character recognition requires "
            f"Tesseract OCR binaries on host. Standard CIL tabular layout cataloged."
        )
        chunks.append({
            "document_id": doc_id,
            "document_name": filename,
            "chunk_index": 0,
            "page_number": 1,
            "text": fallback_text,
            "bounding_box": [50.0, 80.0, 520.0, 180.0],
            "embedding": embedder.embed_text(fallback_text)
        })
        return chunks, metrics, "ocr_unavailable"

    return chunks, metrics, "completed"

def _extract_metrics_from_text(text: str, doc_id: str, filename: str, page_num: int) -> List[Dict[str, Any]]:
    results = []
    
    sub = "SECL"
    for s in KNOWN_SUBSIDIARIES:
        if s.lower() in text.lower():
            sub = s
            break
            
    mine = "Gevra"
    for m in KNOWN_MINES:
        if m.lower() in text.lower():
            mine = m
            break
            
    years_found = re.findall(r'202\d(?:-\d{2,4})?', text)
    year = years_found[0] if years_found else "2023-24"

    # Regex for production figures
    prod_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:MT|Million Tonnes|Million Tons|M\.T\.)', text, re.IGNORECASE)
    if prod_matches:
        val = float(prod_matches[0])
        results.append({
            "document_id": doc_id,
            "subsidiary": sub,
            "mine": mine,
            "year": year,
            "parameter": "Coal Production",
            "value": val,
            "unit": "MT",
            "page_number": page_num,
            "source_doc": filename
        })

    # Regex for OBR
    obr_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:M\.Cum|MCum|M\.Cu\.M|Million Cu\.M)', text, re.IGNORECASE)
    if obr_matches:
        val = float(obr_matches[0])
        results.append({
            "document_id": doc_id,
            "subsidiary": sub,
            "mine": mine,
            "year": year,
            "parameter": "Overburden Removal (OBR)",
            "value": val,
            "unit": "M.Cum",
            "page_number": page_num,
            "source_doc": filename
        })

    # Regex for Stripping Ratio
    strip_matches = re.findall(r'(?:stripping ratio|strip ratio)[^\d]*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if strip_matches:
        results.append({
            "document_id": doc_id,
            "subsidiary": sub,
            "mine": mine,
            "year": year,
            "parameter": "Stripping Ratio",
            "value": float(strip_matches[0]),
            "unit": "ratio",
            "page_number": page_num,
            "source_doc": filename
        })

    return results

def _parse_excel(file_path: Path, doc_id: str, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    df = pd.read_excel(file_path)
    return _process_dataframe(df, doc_id, filename)

def _parse_csv(file_path: Path, doc_id: str, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    df = pd.read_csv(file_path)
    return _process_dataframe(df, doc_id, filename)

def _process_dataframe(df: pd.DataFrame, doc_id: str, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    chunks = []
    metrics = []
    
    col_map = {}
    for col in df.columns:
        c_low = str(col).lower()
        if "mine" in c_low:
            col_map["mine"] = col
        elif "sub" in c_low or "company" in c_low:
            col_map["subsidiary"] = col
        elif "year" in c_low or "period" in c_low:
            col_map["year"] = col
        elif "prod" in c_low or "output" in c_low:
            col_map["production"] = col
        elif "obr" in c_low or "overburden" in c_low:
            col_map["obr"] = col
        elif "strip" in c_low:
            col_map["strip"] = col

    for idx, row in df.iterrows():
        mine = str(row.get(col_map.get("mine", "Mine"), "Gevra")).strip()
        sub = str(row.get(col_map.get("subsidiary", "Subsidiary"), "SECL")).strip()
        year = str(row.get(col_map.get("year", "Year"), "2023-24")).strip()
        
        row_str = f"Mine: {mine} | Subsidiary: {sub} | Financial Year: {year} | "
        for k, v in row.items():
            row_str += f"{k}: {v}, "
            
        emb = embedder.embed_text(row_str)
        y_offset = min(650, 100 + (idx * 25) % 500)
        chunks.append({
            "document_id": doc_id,
            "document_name": filename,
            "chunk_index": idx,
            "page_number": 1,
            "text": row_str,
            "bounding_box": [60.0, float(y_offset), 540.0, float(y_offset + 30.0)],
            "embedding": emb
        })

        if "production" in col_map and pd.notna(row.get(col_map["production"])):
            try:
                prod_val = float(str(row[col_map["production"]]).replace(",", ""))
                metrics.append({
                    "document_id": doc_id,
                    "subsidiary": sub,
                    "mine": mine,
                    "year": year,
                    "parameter": "Coal Production",
                    "value": prod_val,
                    "unit": "MT",
                    "page_number": 1,
                    "source_doc": filename
                })
            except Exception:
                pass

        if "obr" in col_map and pd.notna(row.get(col_map["obr"])):
            try:
                obr_val = float(str(row[col_map["obr"]]).replace(",", ""))
                metrics.append({
                    "document_id": doc_id,
                    "subsidiary": sub,
                    "mine": mine,
                    "year": year,
                    "parameter": "Overburden Removal (OBR)",
                    "value": obr_val,
                    "unit": "M.Cum",
                    "page_number": 1,
                    "source_doc": filename
                })
            except Exception:
                pass

    return chunks, metrics
