"""Tests for error isolation and failure handling in background jobs."""

import time
from fastapi import status
from unittest.mock import patch


def mock_generate_certificate_side_effect(*args, **kwargs):
    recipient_name = kwargs.get('recipient_name') or (args[2] if len(args) > 2 else "")
    if "Failure Trigger" in recipient_name:
        raise ValueError(f"Simulated certificate generation failure for '{recipient_name}'")
    return "/fake/path/cert.pdf"


@patch('app.workers.certificate_worker.PDFGenerator.generate_certificate', side_effect=mock_generate_certificate_side_effect)
def test_individual_certificate_failure_isolation(mock_generate, client):
    """
    Test that if one certificate fails,
    the remaining certificates continue processing successfully.
    """
    payload = {
        "event_name": "Failure Handling Workshop",
        "event_date": "2026-10-10",
        "organization_name": "Resilient Org",
        "recipients": [
            {"name": "Valid User 1", "email": "valid1@example.com"},
            {"name": "Failure Trigger", "email": "fail@example.com"},  # Will raise ValueError due to mock
            {"name": "Valid User 2", "email": "valid2@example.com"},
        ]
    }
    
    # Create the job
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
    job_id = response.json()["job_id"]
    
    # Wait briefly for background task to complete
    time.sleep(1)
    
    # Fetch job status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == status.HTTP_200_OK
    
    data = status_res.json()
    assert data["total"] == 3
    assert data["successful"] == 2
    assert data["failed"] == 1
    assert data["status"] == "completed_with_errors"
    
    # Verify failure details
    assert len(data["failures"]) == 1
    assert "Failure Trigger" in data["failures"][0]["recipient"]
    assert "Simulated certificate generation failure" in data["failures"][0]["error"]
    
    # Verify individual certificates via API
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_res.status_code == status.HTTP_200_OK
    certs = certs_res.json()["items"]
    assert len(certs) == 3
    
    # 2 completed, 1 failed
    completed_certs = [c for c in certs if c["status"] == "completed"]
    failed_certs = [c for c in certs if c["status"] == "failed"]
    assert len(completed_certs) == 2
    assert len(failed_certs) == 1
