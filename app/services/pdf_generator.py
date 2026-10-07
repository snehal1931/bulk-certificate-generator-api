"""PDF Certificate Generation Service using ReportLab."""

import os
import uuid
from datetime import date
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from app.core.config import settings
from app.core.logging import logger


class PDFGenerator:
    """Generates professional PDF certificates using ReportLab."""

    @staticmethod
    def generate_certificate(
        certificate_id: uuid.UUID,
        job_id: uuid.UUID,
        recipient_name: str,
        organization_name: str,
        event_name: str,
        event_date: date,
    ) -> str:
        """Generate a single PDF certificate and return its file path."""

        # Storage path preparation
        job_dir = settings.get_absolute_storage_dir() / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"cert_{certificate_id}.pdf"
        output_path = job_dir / file_name

        # Certificate Page Setup (Landscape Letter: 792 x 612 points)
        page_width, page_height = landscape(letter)
        c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

        # Color Palette
        primary_navy = colors.HexColor("#0F2027")
        secondary_blue = colors.HexColor("#2C5364")
        gold_accent = colors.HexColor("#D4AF37")
        dark_gold = colors.HexColor("#B8860B")
        text_dark = colors.HexColor("#1A202C")
        subtext_gray = colors.HexColor("#4A5568")

        # 1. Background Fill (Soft warm white)
        c.setFillColor(colors.HexColor("#FAFAFA"))
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

        # 2. Outer Border (Deep Navy)
        margin = 25
        c.setStrokeColor(primary_navy)
        c.setLineWidth(4)
        c.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)

        # 3. Inner Double Border (Gold Accent)
        inner_margin = 33
        c.setStrokeColor(gold_accent)
        c.setLineWidth(1.5)
        c.rect(
            inner_margin,
            inner_margin,
            page_width - 2 * inner_margin,
            page_height - 2 * inner_margin,
        )

        inner_margin_2 = 37
        c.setLineWidth(0.75)
        c.rect(
            inner_margin_2,
            inner_margin_2,
            page_width - 2 * inner_margin_2,
            page_height - 2 * inner_margin_2,
        )

        # 4. Corner Ornaments (Classic aesthetic)
        corner_size = 20
        c.setLineWidth(2)
        c.setStrokeColor(gold_accent)

        # Top-Left Corner
        c.line(inner_margin_2, page_height - inner_margin_2 - corner_size, inner_margin_2 + corner_size, page_height - inner_margin_2)
        # Top-Right Corner
        c.line(page_width - inner_margin_2 - corner_size, page_height - inner_margin_2, page_width - inner_margin_2, page_height - inner_margin_2 - corner_size)
        # Bottom-Left Corner
        c.line(inner_margin_2, inner_margin_2 + corner_size, inner_margin_2 + corner_size, inner_margin_2)
        # Bottom-Right Corner
        c.line(page_width - inner_margin_2 - corner_size, inner_margin_2, page_width - inner_margin_2, inner_margin_2 + corner_size)

        # 5. Header Section - Organization Name
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(secondary_blue)
        c.drawCentredString(page_width / 2, page_height - 90, organization_name.upper())

        # 6. Main Certificate Title
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(primary_navy)
        c.drawCentredString(page_width / 2, page_height - 140, "CERTIFICATE OF COMPLETION")

        # Decorative Rule below Title
        rule_y = page_height - 155
        c.setStrokeColor(gold_accent)
        c.setLineWidth(2)
        c.line(page_width / 2 - 120, rule_y, page_width / 2 + 120, rule_y)

        # 7. Subheading
        c.setFont("Helvetica", 13)
        c.setFillColor(subtext_gray)
        c.drawCentredString(page_width / 2, page_height - 190, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

        # 8. Recipient Name (Prominent)
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(primary_navy)
        c.drawCentredString(page_width / 2, page_height - 245, recipient_name)

        # Recipient Underline
        c.setStrokeColor(gold_accent)
        c.setLineWidth(1)
        name_width = max(c.stringWidth(recipient_name, "Helvetica-Bold", 28) + 40, 200)
        c.line(page_width / 2 - name_width / 2, page_height - 255, page_width / 2 + name_width / 2, page_height - 255)

        # 9. Body Text & Event Name
        c.setFont("Helvetica", 13)
        c.setFillColor(subtext_gray)
        c.drawCentredString(page_width / 2, page_height - 295, "for successfully participating in and completing the course / workshop")

        c.setFont("Helvetica-BoldOblique", 22)
        c.setFillColor(secondary_blue)
        c.drawCentredString(page_width / 2, page_height - 340, f'"{event_name}"')

        # 10. Date & Authorization Section
        formatted_date = event_date.strftime("%B %d, %Y")
        
        # Left Block: Issue Date
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(text_dark)
        c.drawString(90, 130, "DATE OF ISSUANCE")
        c.setFont("Helvetica", 11)
        c.setFillColor(subtext_gray)
        c.drawString(90, 112, formatted_date)
        c.setStrokeColor(colors.HexColor("#CBD5E0"))
        c.setLineWidth(1)
        c.line(90, 145, 230, 145)

        # Right Block: Authorized Signature
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(text_dark)
        c.drawRightString(page_width - 90, 130, "AUTHORIZED SIGNATURE")
        c.setFont("Helvetica-Oblique", 11)
        c.setFillColor(subtext_gray)
        c.drawRightString(page_width - 90, 112, organization_name)
        c.line(page_width - 230, 145, page_width - 90, 145)

        # Center Graphic: Gold Seal Emblem
        seal_x = page_width / 2
        seal_y = 125
        c.setFillColor(gold_accent)
        c.circle(seal_x, seal_y, 28, fill=True, stroke=False)
        c.setFillColor(dark_gold)
        c.circle(seal_x, seal_y, 24, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.white)
        c.drawCentredString(seal_x, seal_y - 3, "OFFICIAL")

        # 11. Footer Verification Info
        c.setFont("Helvetica", 8)
        c.setFillColor(subtext_gray)
        footer_text = f"Certificate ID: {certificate_id}  |  Verify: https://verify.organization.com/{certificate_id}"
        c.drawCentredString(page_width / 2, 50, footer_text)

        c.save()

        return str(output_path)
