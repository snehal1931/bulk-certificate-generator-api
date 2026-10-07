"""Background worker for processing bulk certificate generation jobs."""

import uuid
from datetime import datetime, timezone
from app.core.database import get_db_session_context
from app.core.logging import logger
from app.models.enums import CertificateStatus, JobStatus
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.job_repository import JobRepository
from app.services.pdf_generator import PDFGenerator


def process_certificate_job(job_id: uuid.UUID) -> None:
    """Process all certificates for a job in the background.

    Handles individual certificate failures gracefully without interrupting remaining
    recipients. Updates database state and counters in real time.
    """
    logger.info(f"Starting background processing for Job ID: {job_id}")

    with get_db_session_context() as db:
        job_repo = JobRepository(db)
        cert_repo = CertificateRepository(db)

        job = job_repo.get_by_id(job_id)
        if not job:
            logger.error(f"Worker could not find Job ID: {job_id}")
            return

        # Transition job state to PROCESSING
        job_repo.update_status(
            job_id=job.id,
            status=JobStatus.PROCESSING,
            started_at=datetime.now(timezone.utc),
        )

        # Retrieve all pending certificates
        certificates, _ = cert_repo.get_by_job_id_paginated(
            job_id=job.id,
            skip=0,
            limit=job.total_count + 10,
        )

        for cert in certificates:
            logger.info(f"Processing certificate {cert.id} for '{cert.recipient_name}'")
            cert_repo.update_status(cert.id, CertificateStatus.PROCESSING)

            try:
                # Generate PDF using ReportLab
                output_file_path = PDFGenerator.generate_certificate(
                    certificate_id=cert.id,
                    job_id=job.id,
                    recipient_name=cert.recipient_name,
                    organization_name=job.organization_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                )

                # Record success
                cert_repo.update_certificate_success(
                    certificate_id=cert.id,
                    file_path=output_file_path,
                )
                job_repo.increment_counters(job.id, success=True)
                logger.info(f"Successfully generated certificate {cert.id}")

            except Exception as exc:
                # Record individual failure without stopping next recipients
                error_msg = str(exc)
                logger.error(
                    f"Failed to generate certificate {cert.id} for '{cert.recipient_name}': {error_msg}"
                )
                cert_repo.update_certificate_failure(
                    certificate_id=cert.id,
                    error_message=error_msg,
                )
                job_repo.increment_counters(job.id, success=False)

        # Refresh job state to evaluate final job status
        job = job_repo.get_by_id(job_id)
        if job:
            completed_time = datetime.now(timezone.utc)
            if job.failure_count == 0:
                final_status = JobStatus.COMPLETED
            elif job.success_count == 0 and job.total_count > 0:
                final_status = JobStatus.COMPLETED_WITH_ERRORS
            else:
                final_status = JobStatus.COMPLETED_WITH_ERRORS

            job_repo.update_status(
                job_id=job.id,
                status=final_status,
                completed_at=completed_time,
            )
            logger.info(
                f"Finished Job ID: {job.id} with status '{final_status}'. Success: {job.success_count}, Failed: {job.failure_count}"
            )
