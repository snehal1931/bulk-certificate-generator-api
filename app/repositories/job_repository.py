"""Job repository module for DB operations."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.enums import JobStatus
from app.models.job import Job


class JobRepository:
    """Repository handling database interactions for Job entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        event_name: str,
        event_date: datetime.date,
        organization_name: str,
        total_count: int,
    ) -> Job:
        """Create and persist a new Job record."""
        job = Job(
            id=uuid.uuid4(),
            event_name=event_name,
            event_date=event_date,
            organization_name=organization_name,
            status=JobStatus.QUEUED,
            total_count=total_count,
            success_count=0,
            failure_count=0,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Optional[Job]:
        """Fetch job by ID."""
        statement = select(Job).where(Job.id == job_id)
        return self.db.execute(statement).scalar_one_or_none()

    def update_status(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Job]:
        """Update job status and optional timestamp indicators."""
        job = self.get_by_id(job_id)
        if not job:
            return None

        job.status = status
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at

        self.db.commit()
        self.db.refresh(job)
        return job

    def increment_counters(
        self,
        job_id: uuid.UUID,
        success: bool,
    ) -> Optional[Job]:
        """Increment job success or failure count atomically."""
        job = self.get_by_id(job_id)
        if not job:
            return None

        if success:
            job.success_count += 1
        else:
            job.failure_count += 1

        self.db.commit()
        self.db.refresh(job)
        return job
