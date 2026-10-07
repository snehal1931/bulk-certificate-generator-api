"""Certificate response schemas."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CertificateStatus


class CertificateResponseSchema(BaseModel):
    """Schema representing an individual certificate record."""

    id: uuid.UUID
    job_id: uuid.UUID
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedCertificatesSchema(BaseModel):
    """Paginated list response for certificates."""

    total: int = Field(..., description="Total count of matching certificates")
    skip: int = Field(..., description="Offset pagination skip value")
    limit: int = Field(..., description="Limit pagination limit value")
    items: List[CertificateResponseSchema] = Field(..., description="List of certificate items")
