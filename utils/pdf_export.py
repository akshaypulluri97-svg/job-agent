"""PDF resume export using reportlab."""
import io
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def resume_to_pdf(resume_text: str) -> bytes:
    """Convert plain-text resume to a clean PDF. Returns raw PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "NameStyle", parent=styles["Normal"],
        fontSize=18, leading=22, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold", spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "ContactStyle", parent=styles["Normal"],
        fontSize=9, leading=12, alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"), spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Normal"],
        fontSize=11, leading=14, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=10, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["Normal"],
        fontSize=10, leading=14,
        textColor=colors.HexColor("#2d2d2d"), spaceAfter=2,
    )
    bullet_style = ParagraphStyle(
        "BulletStyle", parent=styles["Normal"],
        fontSize=10, leading=14, leftIndent=14,
        textColor=colors.HexColor("#2d2d2d"), spaceAfter=2,
    )

    def _escape(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = resume_text.strip().splitlines()
    story = []
    first_line = True
    second_line = False

    for raw in lines:
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue

        if first_line:
            story.append(Paragraph(_escape(line), name_style))
            first_line = False
            second_line = True
            continue

        if second_line:
            story.append(Paragraph(_escape(line), contact_style))
            story.append(HRFlowable(width="100%", thickness=0.75,
                                     color=colors.HexColor("#1a1a2e"), spaceAfter=4))
            second_line = False
            continue

        if line.isupper() or (line.endswith(":") and len(line) < 40):
            story.append(Paragraph(_escape(line.rstrip(":")), heading_style))
            story.append(HRFlowable(width="100%", thickness=0.4,
                                     color=colors.HexColor("#cccccc"), spaceAfter=2))
            continue

        if line.startswith(("•", "–", "-", "*")):
            bullet_text = line.lstrip("•–-* ").strip()
            story.append(Paragraph(f"• {_escape(bullet_text)}", bullet_style))
            continue

        story.append(Paragraph(_escape(line), body_style))

    doc.build(story)
    return buf.getvalue()
