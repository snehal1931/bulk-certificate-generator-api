"""Tests for individual certificate and ZIP download endpoints."""

import time
from fastapi import status


def test_download_certificate_pdf(client):
    """Test downloading a successfully generated certificate PDF."""
    payload = {
        "event_name": "Success Event",
        "event_date": "2026-10-10",
        "organization_name": "Download Org",
        "recipients": [{"name": "Download User", "email": "down@example.com"}]
    }
    
    # 1. Create job
    response = client.post("/api/v1/jobs", json=payload)
    job_id = response.json()["job_id"]
    
    time.sleep(1)  # wait for bg task
    
    # 2. Get certificate ID
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert_id = certs_res.json()["items"][0]["id"]
    
    # 3. Download certificate PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert pdf_res.status_code == status.HTTP_200_OK
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"] or "inline" in pdf_res.headers["content-disposition"]


def test_download_job_zip(client):
    """Test downloading the ZIP file of all job certificates."""
    payload = {
        "event_name": "ZIP Event",
        "event_date": "2026-10-10",
        "organization_name": "ZIP Org",
        "recipients": [{"name": "ZIP User", "email": "zip@example.com"}]
    }
    
    response = client.post("/api/v1/jobs", json=payload)
    job_id = response.json()["job_id"]
    time.sleep(1)
    
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == status.HTTP_200_OK
    assert zip_res.headers["content-type"] == "application/zip"
    assert "zip" in zip_res.headers["content-disposition"]
