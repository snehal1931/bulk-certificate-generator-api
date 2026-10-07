"""Job request and response schemas."""

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.config import settings
from app.models.enums import JobStatus
from app.schemas.recipient import RecipientSchema


class JobCreateSchema(BaseModel):
    """Payload for creating a bulk certificate generation job."""

    event_name: str = Field(..., min_length=1, max_length=255, description="Name of event/course")
    event_date: date = Field(..., description="Date of the event (YYYY-MM-DD)")
    organization_name: str = Field(..., min_length=1, max_length=255, description="Issuing organization name")
    recipients: List[RecipientSchema] = Field(
        ...,
        min_length=1,
        description="List of certificate recipients",
    )

    @field_validator("event_name", "organization_name", mode="before")
    @classmethod
    def strip_and_validate_non_empty(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty or whitespace only.")
        return value

    @field_validator("recipients")
    @classmethod
    def validate_max_recipients(cls, recipients: List[RecipientSchema]) -> List[RecipientSchema]:
        if not recipients:
            raise ValueError("Recipient list cannot be empty.")
        if len(recipients) > settings.MAX_RECIPIENTS_PER_JOB:
            raise ValueError(
                f"Recipient count exceeds maximum bulk limit of {settings.MAX_RECIPIENTS_PER_JOB}."
            )
        return recipients


class JobCreatedResponseSchema(BaseModel):
    """Initial response after job creation."""

    job_id: uuid.UUID = Field(..., description="Unique job ID")
    status: JobStatus = Field(..., description="Current job status")
    total: int = Field(..., description="Total recipient count")

    model_config = ConfigDict(from_attributes=True)


class JobFailureItemSchema(BaseModel):
    """Individual certificate failure detail."""

    recipient: str = Field(..., description="Recipient name/email")
    error: str = Field(..., description="Error message")


class JobStatusResponseSchema(BaseModel):
    """Detailed job status response."""

    job_id: uuid.UUID = Field(..., description="Unique job ID")
    status: JobStatus = Field(..., description="Current job status")
    total: int = Field(..., description="Total recipients")
    successful: int = Field(..., description="Count of successfully generated certificates")
    failed: int = Field(..., description="Count of failed certificate generations")
    progress_percentage: float = Field(..., description="Progress percentage (0.0 to 100.0)")
    failures: List[JobFailureItemSchema] = Field(default_factory=list, description="List of individual failures")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")

    model_config = ConfigDict(from_attributes=True)
