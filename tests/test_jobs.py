"""Tests for job API endpoints."""

from fastapi import status


def test_create_job_success(client):
    """Test job creation returns 202 Accepted and job_id."""
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "organization_name": "Example Organization",
        "recipients": [
            {"name": "Snehal Patil", "email": "snehal@example.com"},
            {"name": "Rahul Sharma", "email": "rahul@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["total"] == 2


def test_get_nonexistent_job(client):
    """Test fetching a non-existent job returns 404."""
    invalid_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/jobs/{invalid_uuid}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["error"].lower()


def test_invalid_job_payload(client):
    """Test missing required fields returns 422 Validation Error."""
    payload = {
        # Missing event_name
        "event_date": "2026-10-10",
        "organization_name": "Example Organization",
        "recipients": [
            {"name": "Snehal Patil", "email": "snehal@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
