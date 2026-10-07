"""Tests for PDF Generation."""

import os
import uuid
from datetime import date
from app.services.pdf_generator import PDFGenerator


def test_pdf_generation_creates_file():
    """Verify ReportLab PDF generation creates the physical file."""
    job_id = uuid.uuid4()
    cert_id = uuid.uuid4()
    
    file_path = PDFGenerator.generate_certificate(
        certificate_id=cert_id,
        job_id=job_id,
        recipient_name="Test Recipient",
        organization_name="Test Org",
        event_name="Test Event",
        event_date=date(2026, 10, 10)
    )
    
    assert os.path.exists(file_path)
    assert file_path.endswith(f"cert_{cert_id}.pdf")
    
    # Clean up immediately for this specific direct test
    if os.path.exists(file_path):
        os.remove(file_path)
