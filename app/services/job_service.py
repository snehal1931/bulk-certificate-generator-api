"""Job service layer handling job creation, status calculation, and zip creation."""

import os
import zipfile
import uuid
from typing import List
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import JobNotFoundError, NotFoundError
from app.models.enums import CertificateStatus, JobStatus
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.job import (
    JobCreateSchema,
    JobCreatedResponseSchema,
    JobFailureItemSchema,
    JobStatusResponseSchema,
)
from app.workers.certificate_worker import process_certificate_job


class JobService:
    """Service layer encapsulating job workflow logic."""

    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.cert_repo = CertificateRepository(db)

    def create_job(
        self,
        payload: JobCreateSchema,
        background_tasks: BackgroundTasks,
    ) -> JobCreatedResponseSchema:
        """Create job record, populate certificate entries, and schedule background worker."""
        total_count = len(payload.recipients)

        # 1. Create Job entry
        job = self.job_repo.create(
            event_name=payload.event_name,
            event_date=payload.event_date,
            organization_name=payload.organization_name,
            total_count=total_count,
        )

        # 2. Bulk create initial Pending Certificate entries
        recipients_dicts = [rec.model_dump() for rec in payload.recipients]
        self.cert_repo.create_bulk(job_id=job.id, recipients=recipients_dicts)

        # 3. Queue background task
        background_tasks.add_task(process_certificate_job, job.id)

        return JobCreatedResponseSchema(
            job_id=job.id,
            status=job.status,
            total=job.total_count,
        )

    def get_job_status(self, job_id: uuid.UUID) -> JobStatusResponseSchema:
        """Retrieve current status, progress, and failure list for a job."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(str(job_id))

        # Calculate progress percentage safely
        if job.total_count == 0:
            progress = 100.0
        else:
            processed_count = job.success_count + job.failure_count
            progress = round((processed_count / job.total_count) * 100.0, 2)

        # Get detailed failures
        failed_certs = self.cert_repo.get_failed_certificates_for_job(job_id)
        failure_items = [
            JobFailureItemSchema(
                recipient=f"{cert.recipient_name} ({cert.recipient_email})",
                error=cert.error_message or "Unknown error",
            )
            for cert in failed_certs
        ]

        return JobStatusResponseSchema(
            job_id=job.id,
            status=job.status,
            total=job.total_count,
            successful=job.success_count,
            failed=job.failure_count,
            progress_percentage=progress,
            failures=failure_items,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    def create_job_zip(self, job_id: uuid.UUID) -> str:
        """Bundle all completed certificates for a job into a downloadable ZIP archive."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(str(job_id))

        completed_certs = self.cert_repo.get_completed_certificates_for_job(job_id)
        if not completed_certs:
            raise NotFoundError(f"No completed certificates available to download for job '{job_id}'.")

        job_dir = settings.get_absolute_storage_dir() / str(job_id)
        zip_path = job_dir / f"job_{job_id}_certificates.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for cert in completed_certs:
                if cert.file_path and os.path.exists(cert.file_path):
                    archive_name = f"{cert.recipient_name.replace(' ', '_')}_{cert.id}.pdf"
                    zip_file.write(cert.file_path, arcname=archive_name)

        return str(zip_path)
