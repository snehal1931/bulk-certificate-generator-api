"""Job ORM model definition."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, Enum, Integer, String, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import JobStatus

if TYPE_CHECKING:
    from app.models.certificate import Certificate


class Job(Base):
    """Job table representing a bulk certificate generation request."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", native_enum=False),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )

    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 1-to-Many Relationship
    certificates: Mapped[List["Certificate"]] = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, total={self.total_count})>"
