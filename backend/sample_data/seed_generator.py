import os
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.config import SAMPLE_DATA_DIR, UPLOADS_DIR

def create_sample_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#00838f'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []
    story.append(Paragraph("MINISTRY OF COAL • COAL INDIA LIMITED", h2_style))
    story.append(Paragraph("SOUTH EASTERN COALFIELDS LIMITED (SECL) - ANNUAL REPORT", title_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Gevra Opencast Project - Operational Performance", h2_style))
    story.append(Paragraph(
        "Gevra Opencast Project situated in Korba coalfield stands as the single largest opencast coal mine in Asia. "
        "During financial cycle 2021-22, Gevra recorded actual coal production of 48.2 MT. In the subsequent audited "
        "evaluation cycle 2022-23, certified coal production was tabulated at 4.2 MT in primary divisional returns, "
        "supplemented by heavy overburden removal (OBR) of 68.4 M.Cum with an operating stripping ratio of 1.62. "
        "Total geological reserves at Gevra exceed 10,000 million tonnes with continuous seam continuity across seams "
        "Upper Kusum, Lower Kusum and Passang.",
        body_style
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. Kusmunda & Dipka Mine Expansions", h2_style))
    story.append(Paragraph(
        "Kusmunda opencast mine achieved coal production of 41.2 MT in 2022-23 and accelerated to 45.6 MT in 2023-24. "
        "Overburden removal reached 59.2 M.Cum using in-pit crushing and continuous conveyor transport systems. "
        "Dipka expansion recorded 38.4 MT production with stripping ratio of 1.48, fully compliant with Ministry "
        "environmental clearance directives.",
        body_style
    ))
    story.append(Spacer(1, 14))

    # Production Summary Table
    story.append(Paragraph("3. Audited Quantitative Output Table", h2_style))
    table_data = [
        ["Mine Name", "Fiscal Period", "Coal Production (MT)", "OBR (M.Cum)", "Stripping Ratio"],
        ["Gevra OpenCast", "2021-22", "48.2 MT", "62.1 M.Cum", "1.58"],
        ["Gevra OpenCast", "2022-23", "4.2 MT", "65.4 M.Cum", "1.65"],
        ["Gevra OpenCast", "2023-24", "56.8 MT", "72.0 M.Cum", "1.60"],
        ["Kusmunda Mine", "2022-23", "41.2 MT", "55.0 M.Cum", "1.51"],
        ["Kusmunda Mine", "2023-24", "45.6 MT", "59.2 M.Cum", "1.53"],
        ["Dipka Project", "2023-24", "39.5 MT", "52.0 M.Cum", "1.50"]
    ]
    t = Table(table_data, colWidths=[120, 80, 110, 100, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f1f5f9'), colors.white]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t)
    doc.build(story)

def create_sample_excel(output_path: Path):
    data = {
        "Subsidiary": ["SECL", "SECL", "SECL", "SECL", "SECL", "SECL", "SECL", "SECL", "MCL", "NCL"],
        "Mine Name": ["Gevra", "Gevra", "Gevra", "Gevra", "Kusmunda", "Kusmunda", "Dipka", "Dipka", "Talcher", "Singrauli"],
        "Financial Year": ["2021-22", "2022-23", "2023-24", "2024-25", "2022-23", "2023-24", "2022-23", "2023-24", "2023-24", "2023-24"],
        "Coal Production (MT)": [48.2, 4.8, 56.8, 60.5, 41.2, 45.6, 36.8, 39.5, 54.2, 49.8], # Note: 4.8 vs 4.2 in PDF!
        "Overburden Removal (M.Cum)": [62.1, 65.4, 72.0, 78.4, 55.0, 59.2, 48.1, 52.0, 68.9, 64.3],
        "Stripping Ratio": [1.58, 1.65, 1.60, 1.64, 1.51, 1.53, 1.48, 1.50, 1.59, 1.55],
        "Audit Status": ["Audited", "Audited", "Audited", "Provisional", "Audited", "Audited", "Audited", "Audited", "Audited", "Audited"]
    }
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)

def ensure_sample_files() -> tuple[Path, Path]:
    pdf_path = SAMPLE_DATA_DIR / "SECL_Annual_Geological_Report_2022_24.pdf"
    xlsx_path = SAMPLE_DATA_DIR / "CMPDI_Mine_Master_Register_2024.xlsx"
    
    if not pdf_path.exists():
        create_sample_pdf(pdf_path)
    if not xlsx_path.exists():
        create_sample_excel(xlsx_path)
        
    return pdf_path, xlsx_path
