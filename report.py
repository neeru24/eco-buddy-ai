import os
import tempfile
import uuid
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from notifications import error

def generate_pdf(total, eco_score, insight):
    try:
        file_name = os.path.join(tempfile.gettempdir(), f"eco_report_{uuid.uuid4().hex}.pdf")
        doc = SimpleDocTemplate(file_name)
        styles = getSampleStyleSheet()

        content = [
            Paragraph("EcoBuddy AI Report", styles["Title"]),
            Paragraph(f"Carbon Footprint: {total:.2f} kg CO₂", styles["Normal"]),
            Paragraph(f"Eco Score: {eco_score}/100", styles["Normal"]),
            Paragraph("Key Insight:", styles["Heading2"]),
            Paragraph(insight, styles["Normal"])
        ]

        doc.build(content)
        return file_name
    except Exception:
        error("Could not generate the PDF report. Please check disk space and permissions, then try again.")
        return None
