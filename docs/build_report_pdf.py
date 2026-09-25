"""Build an A4 PDF of the prototype report with embedded screenshots."""
from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "SIH26023_CoalMind_AI_Prototype_Report.pdf"
NAVY = colors.HexColor("#1B3A4B")
GOLD = colors.HexColor("#C4A35A")
INK = colors.HexColor("#1b2a32")
MUTED = colors.HexColor("#5c6b73")
LINE = colors.HexColor("#e2ddd4")
CREAM = colors.HexColor("#f4f1ea")


def styles():
    base = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle(
            "cover", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, leading=26, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8,
        ),
        "sub": ParagraphStyle(
            "sub", parent=base["Normal"], fontSize=11, leading=15,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=14, leading=18, textColor=NAVY, spaceBefore=14, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9.5, leading=13,
            textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "cap": ParagraphStyle(
            "cap", parent=base["Normal"], fontSize=8.5, leading=11,
            textColor=MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10,
        ),
        "mono": ParagraphStyle(
            "mono", parent=base["Normal"], fontName="Courier", fontSize=8,
            leading=11, textColor=INK, backColor=CREAM, leftIndent=6, rightIndent=6,
            spaceBefore=4, spaceAfter=8,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontSize=8, leading=11, textColor=INK,
        ),
        "cellh": ParagraphStyle(
            "cellh", parent=base["Normal"], fontSize=8, leading=11,
            textColor=colors.white, fontName="Helvetica-Bold",
        ),
    }


def shot(name, width=170 * mm):
    path = SHOTS / name
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    height = width * (ih / float(iw))
    max_h = 105 * mm
    if height > max_h:
        width = width * (max_h / height)
        height = max_h
    flow = Image(str(path), width=width, height=height)
    flow.hAlign = "CENTER"
    return flow


def table(data, col_widths, s):
    rows = []
    for i, row in enumerate(data):
        st = s["cellh"] if i == 0 else s["cell"]
        rows.append([Paragraph(str(c), st) for c in row])
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 10 * mm, A4[0], 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, A4[1] - 11 * mm, A4[0], 1.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(16 * mm, A4[1] - 7 * mm, "CoalMind AI  ·  SIH 26023  ·  AGNIVAULT")
    canvas.drawRightString(A4[0] - 16 * mm, A4[1] - 7 * mm, "CMPDI / CIL prototype")
    canvas.setFillColor(GOLD)
    canvas.rect(0, 0, A4[0], 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(16 * mm, 3 * mm, "Confidential for SIH evaluation")
    canvas.drawRightString(A4[0] - 16 * mm, 3 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main():
    s = styles()
    story = []
    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("CoalMind AI", s["cover"]))
    story.append(Paragraph("Prototype &amp; working report", s["cover"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Smart India Hackathon 2025 · Problem SIH 26023", s["sub"]))
    story.append(Paragraph(
        "AI-Powered Geological, Mining and other Reporting Solution for CMPDI / CIL subsidiaries",
        s["sub"],
    ))
    story.append(Paragraph("Team AGNIVAULT  ·  captured 26 September 2026", s["sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(shot("01-ask-home.png", 150 * mm))
    story.append(Paragraph(
        "Figure 1. Working console — Ask home, Gemini connected, 5 indexed filings.",
        s["cap"],
    ))

    story.append(Paragraph("1. Problem", s["h1"]))
    story.append(Paragraph(
        "CMPDI and Coal India subsidiaries produce large volumes of PDFs, mine registers, "
        "and spreadsheets. Officers still re-type figures, lose the page a number came from, "
        "and miss when two filings disagree on the same mine and year. SIH 26023 asks for an "
        "AI reporting copilot that extracts, retrieves, verifies, and reports — not a chatbot "
        "that invents tonnes.",
        s["body"],
    ))

    story.append(Paragraph("2. What the prototype is", s["h1"]))
    story.append(Paragraph(
        "<b>Upload → Extract → Store → Ask AI → Cite the page → Flag conflicts → Download a brief.</b> "
        "The stack runs on a normal laptop (no CUDA, torch, or FAISS). Gemini is used only as a "
        "language layer on top of indexed archive rows. In this capture: 5 documents, 10 topics, "
        "1 discrepancy, store = Supabase, AI = Gemini.",
        s["body"],
    ))

    story.append(Paragraph("3. How it works", s["h1"]))
    story.append(Paragraph(
        "PDF / XLSX / CSV → parser (pypdf / pandas) → text chunks + mine/year/parameter metrics → "
        "Supabase or SQLite. SQL intent charts structured metrics. RAG intent searches hashed 384-d "
        "chunks. A conflict scan flags the same mine + year + metric in two files when the gap exceeds "
        "5%. Gemini then writes English from those facts only. If the archive has no row, the answer "
        "says so. Short follow-ups such as “Only Gevra” are expanded onto the previous question.",
        s["body"],
    ))

    story.append(Paragraph("4. Ask — working query", s["h1"]))
    story.append(Paragraph(
        "Question: <i>Compare coal production between 2022 and 2024</i>. The thread returns a Gemini "
        "briefing with source file and page, a bar chart from indexed metrics, an officer briefing "
        "card (three bullets, table, citation, Download as note), and a source list with View.",
        s["body"],
    ))
    story.append(shot("02-ask-working.png", 170 * mm))
    story.append(Paragraph(
        "Figure 2. Live Ask result — cited figures, chart, officer note, sources.",
        s["cap"],
    ))

    story.append(Paragraph("5. Mine dashboard", s["h1"]))
    story.append(Paragraph(
        "One jury screenshot: Gevra, Kusmunda, and Dipka with latest production, overburden, "
        "stripping ratio, and last source file.",
        s["body"],
    ))
    story.append(shot("04-mines.png", 170 * mm))
    story.append(Paragraph("Figure 3. Mine dashboard (SECL demo mines).", s["cap"]))
    story.append(table(
        [
            ["Mine", "Production", "OBR", "Last source"],
            ["Gevra", "60.5 MT · 2024-25", "78.4 M.Cum", "Mine master register"],
            ["Kusmunda", "45.6 MT · 2023-24", "59.2 M.Cum", "Mine master register"],
            ["Dipka", "39.5 MT · 2023-24", "52.0 M.Cum", "Mine master register"],
        ],
        [32 * mm, 45 * mm, 40 * mm, 53 * mm],
        s,
    ))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("6. Documents and SIH sample pack", s["h1"]))
    story.append(Paragraph(
        "Officers ingest PDF, Excel, or CSV (25 MB). <b>Load SIH sample (SECL 2022–24)</b> seeds "
        "SECL_Annual_Geological_Report_2022_24.pdf and CMPDI_Mine_Master_Register_2024.xlsx so the "
        "stage demo does not depend on a USB stick. Scanned files without OCR are marked "
        "ocr_unavailable — text is not invented.",
        s["body"],
    ))
    story.append(shot("05-documents.png", 170 * mm))
    story.append(Paragraph("Figure 4. Document library and one-click SIH sample pack.", s["cap"]))

    story.append(Paragraph("7. Review — conflicts and PDF brief", s["h1"]))
    story.append(Paragraph(
        "Gevra · SECL · 2021-22 · Overburden Removal: 68.4 in the annual PDF versus 62.1 in the "
        "mine register (tolerance 5%). Officer actions: Accept, Flag for field check, Ignore. This "
        "capture shows FIELD_CHECK. The right panel builds a one-page executive PDF (ReportLab) "
        "for a subsidiary and financial year.",
        s["body"],
    ))
    story.append(shot("06-review.png", 170 * mm))
    story.append(Paragraph(
        "Figure 5. Conflict control room and executive PDF download.",
        s["cap"],
    ))

    story.append(Paragraph("8. Five-minute jury script", s["h1"]))
    story.append(Paragraph(
        "1. Open http://127.0.0.1:5173 — show AI · gemini and document count.<br/>"
        "2. Documents → Load SIH sample if the library is empty.<br/>"
        "3. Ask: Compare coal production between 2022 and 2024.<br/>"
        "4. Show the chart and Download as note.<br/>"
        "5. Follow-up chip: Only Gevra.<br/>"
        "6. Mines — three tiles.<br/>"
        "7. Review — Gevra OBR 68.4 ≠ 62.1 → Flag for field check.<br/>"
        "8. Download PDF for SECL 2023-24.",
        s["body"],
    ))

    story.append(Paragraph("9. Stack and limits", s["h1"]))
    story.append(table(
        [
            ["Layer", "Choice"],
            ["UI", "React + Vite :5173"],
            ["API", "FastAPI :8000"],
            ["Extract", "pypdf, pandas, regex"],
            ["Vectors", "Hashed / SVD 384-d (no torch)"],
            ["LLM", "Gemini 3.8 Flash via httpx (optional)"],
            ["Data", "Supabase Postgres or SQLite"],
            ["Hosted UI", "GitHub Pages (read-only Ask / library)"],
        ],
        [40 * mm, 130 * mm],
        s,
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Limits (deliberate): no GPU OCR; embeddings are not a large model; GitHub Pages cannot "
        "ingest files; Gemini is optional; officer roles are not full IAM. The product stays up "
        "on an 8 GB laptop.",
        s["body"],
    ))

    story.append(Paragraph("10. Conclusion", s["h1"]))
    story.append(Paragraph(
        "CoalMind AI is a working CMPDI-style console: live Gemini answers, cited metrics, a "
        "three-mine dashboard, a one-click SECL sample pack, and a conflict that must be accepted "
        "or sent for field check. That is the SIH 26023 story — reports you can audit, not "
        "free-form generation.",
        s["body"],
    ))
    story.append(Paragraph(
        "Local UI: http://127.0.0.1:5173 &nbsp;&nbsp; Hosted: https://2410305056-tech.github.io/coalmind-ai/ "
        "&nbsp;&nbsp; Repo: https://github.com/2410305056-tech/coalmind-ai",
        s["sub"],
    ))

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title="CoalMind AI Prototype Report — SIH 26023",
        author="AGNIVAULT",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
