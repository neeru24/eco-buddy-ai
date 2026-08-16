"""Sustainability milestone certificate generator using ReportLab."""

import logging
import os
import tempfile
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


def generate_certificate(
    username: str,
    achievement_title: str,
    achievement_description: str,
    eco_score: Optional[float],
    date_achieved: str,
    output_path: Optional[str] = None
) -> Optional[str]:
    """Generate a PDF certificate for an unlocked achievement."""
    
    if not output_path:
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"certificate_{uuid.uuid4().hex[:8]}.pdf"
        )

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    try:
        # Font registration
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "assets", "fonts", "DejaVuSans.ttf")
        
        font_name = "Helvetica"
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
                font_name = "DejaVuSans"
            except Exception as e:
                logger.warning("Failed to register DejaVuSans, falling back to Helvetica: %s", e)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(letter),
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Typography
        brand_style = ParagraphStyle(
            "Brand",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=16,
            textColor=colors.HexColor("#2E7D32"),
            alignment=1,
            spaceAfter=30
        )
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=36,
            textColor=colors.HexColor("#2E7D32"),
            alignment=1,
            spaceAfter=20
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=14,
            textColor=colors.gray,
            alignment=1,
            spaceAfter=20
        )
        recipient_style = ParagraphStyle(
            "Recipient",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=28,
            textColor=colors.black,
            alignment=1,
            spaceAfter=30
        )
        achievement_style = ParagraphStyle(
            "Achievement",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=22,
            textColor=colors.HexColor("#2E7D32"),
            alignment=1,
            spaceAfter=15
        )
        desc_style = ParagraphStyle(
            "Description",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=16,
            textColor=colors.darkgray,
            alignment=1,
            spaceAfter=30
        )
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            textColor=colors.gray,
            alignment=1,
            spaceBefore=40
        )

        content = []
        
        # Clean input strings
        safe_username = str(username).replace("<", "&lt;").replace(">", "&gt;")
        safe_title = str(achievement_title).replace("<", "&lt;").replace(">", "&gt;")
        safe_desc = str(achievement_description).replace("<", "&lt;").replace(">", "&gt;")

        # Content elements
        content.append(Paragraph("<b>EcoBuddy AI</b>", brand_style))
        content.append(Paragraph("Certificate of Achievement", title_style))
        content.append(Paragraph("This is to certify that", subtitle_style))
        content.append(Paragraph(f"<b>{safe_username}</b>", recipient_style))
        content.append(Paragraph("has successfully achieved", subtitle_style))
        content.append(Paragraph(f"<b>{safe_title}</b>", achievement_style))
        content.append(Paragraph(safe_desc, desc_style))
        
        if eco_score is not None:
            content.append(Paragraph(f"Eco Score: {eco_score:.0f}/100", subtitle_style))
            
        content.append(Paragraph(f"Awarded on {date_achieved}", subtitle_style))
        
        cert_id = uuid.uuid4().hex[:8].upper()
        content.append(Paragraph(f"Certificate ID: {cert_id}", footer_style))
        
        # Create a single-cell table for the border
        table_data = [[content]]
        table = Table(table_data, colWidths=[9 * inch])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 4, colors.HexColor("#2E7D32")),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5 * inch),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 * inch),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.5 * inch),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.5 * inch),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        doc.build([table])
        return output_path
    except Exception as e:
        logger.error("Certificate generation failed: %s", e)
        return None
