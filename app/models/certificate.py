"""Certificate ORM model definition."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum, ForeignKey, String, Text, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import CertificateStatus

if TYPE_CHECKING:
    from app.models.job import Job


class Certificate(Base):
    """Certificate table representing an individual recipient certificate."""

    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[CertificateStatus] = mapped_column(
        Enum(CertificateStatus, name="certificate_status_enum", native_enum=False),
        default=CertificateStatus.PENDING,
        nullable=False,
        index=True,
    )

    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship back to Job
    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="certificates",
    )

    def __repr__(self) -> str:
        return f"<Certificate(id={self.id}, recipient={self.recipient_name}, status={self.status})>"
