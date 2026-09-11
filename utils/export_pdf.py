import os
import re
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from utils.markdown_parse import parse_markdown

ACCENT = colors.HexColor("#2E3192")
ACCENT_LIGHT = colors.HexColor("#6C6FC4")
INK = colors.HexColor("#1A1A2E")
MUTED = colors.HexColor("#6B7280")
REF_RE = re.compile(r"^\[(\d+)\]\s+(.*)$")


def _runs_to_markup(runs) -> str:
    parts = []
    for text, bold, citation in runs:
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if bold:
            parts.append(f"<b>{text}</b>")
        elif citation:
            parts.append(f'<super><font size=8 color="#2E3192">{text}</font></super>')
        else:
            parts.append(text)
    return "".join(parts)


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1c", parent=ss["Heading1"], textColor=ACCENT, fontSize=19,
                           spaceBefore=6, spaceAfter=8))
    ss.add(ParagraphStyle("H2c", parent=ss["Heading2"], textColor=ACCENT, fontSize=15,
                           spaceBefore=16, spaceAfter=6))
    ss.add(ParagraphStyle("H3c", parent=ss["Heading3"], textColor=ACCENT_LIGHT, fontSize=12,
                           spaceBefore=10, spaceAfter=4))
    ss.add(ParagraphStyle("Bodyc", parent=ss["Normal"], textColor=INK, fontSize=10.5,
                           leading=15, spaceAfter=8))
    ss.add(ParagraphStyle("Bulletc", parent=ss["Bodyc"], leftIndent=16, bulletIndent=4,
                           spaceAfter=4))
    ss.add(ParagraphStyle("Refc", parent=ss["Normal"], textColor=MUTED, fontSize=8.5,
                           leading=12, spaceAfter=3))
    ss.add(ParagraphStyle("TitleBig", parent=ss["Title"], fontSize=26, textColor=INK,
                           alignment=TA_CENTER, spaceAfter=10))
    ss.add(ParagraphStyle("Kicker", parent=ss["Normal"], fontSize=11, textColor=ACCENT_LIGHT,
                           alignment=TA_CENTER, spaceAfter=14))
    ss.add(ParagraphStyle("Meta", parent=ss["Normal"], fontSize=9, textColor=MUTED,
                           alignment=TA_CENTER, fontName="Helvetica-Oblique"))
    ss.add(ParagraphStyle("Caption", parent=ss["Normal"], fontSize=8.5, textColor=MUTED,
                           alignment=TA_CENTER, fontName="Helvetica-Oblique", spaceAfter=14))
    return ss


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2, 0.5 * inch, f"Deep Research Agent  |  Page {doc.page}")
    canvas.restoreState()


def export_pdf(query: str, markdown: str, chart_paths: list[str], image_paths: list[str],
                output_path: str) -> str:
    ss = _styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.9 * inch,
                             bottomMargin=0.8 * inch, leftMargin=0.9 * inch,
                             rightMargin=0.9 * inch)
    story = []

    # ---- Title page ----
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("DEEP RESEARCH REPORT", ss["Kicker"]))
    story.append(Paragraph(query.strip().capitalize(), ss["TitleBig"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="40%", thickness=1.2, color=ACCENT, spaceAfter=10,
                             hAlign="CENTER"))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')} · AI Deep Research Agent",
        ss["Meta"]))
    story.append(PageBreak())

    # ---- Body ----
    blocks = parse_markdown(markdown)
    ref_mode = False
    for block in blocks:
        btype = block["type"]

        if btype == "h1":
            story.append(Paragraph(block["text"], ss["H1c"]))
        elif btype == "h2":
            ref_mode = block["text"].strip().lower() == "references"
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D8D8E8"),
                                     spaceBefore=4, spaceAfter=2))
            story.append(Paragraph(block["text"], ss["H2c"]))
        elif btype == "h3":
            story.append(Paragraph(block["text"], ss["H3c"]))
        elif btype == "bullet":
            story.append(Paragraph(f"•  {_runs_to_markup(block['runs'])}", ss["Bulletc"]))
        elif btype == "numbered":
            story.append(Paragraph(_runs_to_markup(block["runs"]), ss["Bulletc"]))
        elif btype == "table":
            rows = block["rows"]
            if not rows:
                continue
            clean_rows = [[re.sub(r"\*\*(.*?)\*\*", r"\1", c) for c in row] for row in rows]
            wrapped = [[Paragraph(c, ss["Bodyc"]) for c in row] for row in clean_rows]
            table = Table(wrapped, hAlign="CENTER")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D8E8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5FA")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.15 * inch))
        else:
            text = "".join(t for t, _, _ in block["runs"])
            if ref_mode:
                m = REF_RE.match(text.strip())
                if m:
                    num, url = m.group(1), m.group(2)
                    story.append(Paragraph(
                        f'[{num}]&nbsp;&nbsp;<link href="{url}" color="#2E3192">{url}</link>',
                        ss["Refc"]))
                else:
                    story.append(Paragraph(text, ss["Refc"]))
            else:
                story.append(Paragraph(_runs_to_markup(block["runs"]), ss["Bodyc"]))

    # ---- Visuals section ----
    if chart_paths or image_paths:
        story.append(PageBreak())
        story.append(Paragraph("Charts &amp; Visual References", ss["H1c"]))
        story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D8D8E8"),
                                 spaceAfter=10))
        for i, p_path in enumerate(chart_paths):
            if os.path.exists(p_path):
                story.append(RLImage(p_path, width=5.3 * inch, height=3.3 * inch))
                story.append(Paragraph(f"Figure {i + 1} — data derived from research findings",
                                        ss["Caption"]))
        if image_paths:
            story.append(Paragraph("Illustrative Images", ss["H3c"]))
            for p_path in image_paths:
                if os.path.exists(p_path):
                    story.append(RLImage(p_path, width=4.3 * inch, height=2.9 * inch))
                    story.append(Spacer(1, 0.15 * inch))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path
