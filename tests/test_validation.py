"""Tests for payload validation rules."""

import pytest
from pydantic import ValidationError
from app.schemas.job import JobCreateSchema


def test_valid_job_schema():
    """Test valid payload parses correctly."""
    data = {
        "event_name": "Test Event",
        "event_date": "2026-10-10",
        "organization_name": "Test Org",
        "recipients": [
            {"name": "Snehal Patil", "email": "snehal@example.com"}
        ],
    }
    job = JobCreateSchema(**data)
    assert job.event_name == "Test Event"
    assert len(job.recipients) == 1


def test_empty_event_name_fails():
    """Test empty event name triggers validation error."""
    with pytest.raises(ValidationError) as exc_info:
        JobCreateSchema(
            event_name="   ",
            event_date="2026-10-10",
            organization_name="Test Org",
            recipients=[{"name": "Snehal Patil", "email": "snehal@example.com"}],
        )
    assert "cannot be empty or whitespace" in str(exc_info.value).lower()


def test_invalid_email_fails():
    """Test invalid email format triggers validation error."""
    with pytest.raises(ValidationError) as exc_info:
        JobCreateSchema(
            event_name="Test Event",
            event_date="2026-10-10",
            organization_name="Test Org",
            recipients=[{"name": "Snehal Patil", "email": "not-an-email"}],
        )
    assert "value is not a valid email address" in str(exc_info.value).lower()


def test_empty_recipient_list_fails():
    """Test providing 0 recipients fails validation."""
    with pytest.raises(ValidationError) as exc_info:
        JobCreateSchema(
            event_name="Test Event",
            event_date="2026-10-10",
            organization_name="Test Org",
            recipients=[],
        )
    assert "list should have at least 1 item" in str(exc_info.value).lower() or "recipient list cannot be empty" in str(exc_info.value).lower()


def test_exceeding_max_recipients_fails():
    """Test providing too many recipients triggers custom validation error."""
    # settings.MAX_RECIPIENTS_PER_JOB is 1000
    recipients = [{"name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1001)]
    with pytest.raises(ValidationError) as exc_info:
        JobCreateSchema(
            event_name="Test Event",
            event_date="2026-10-10",
            organization_name="Test Org",
            recipients=recipients,
        )
    assert "exceeds maximum bulk limit" in str(exc_info.value).lower()
