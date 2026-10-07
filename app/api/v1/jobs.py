"""API endpoints for bulk certificate generation jobs."""

import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.enums import CertificateStatus
from app.schemas.certificate import PaginatedCertificatesSchema
from app.schemas.job import (
    JobCreateSchema,
    JobCreatedResponseSchema,
    JobStatusResponseSchema,
)
from app.services.certificate_service import CertificateService
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreatedResponseSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a bulk certificate generation job",
    description="Validates request metadata and recipient list, creates job record, and starts asynchronous PDF generation.",
)
def create_job(
    payload: JobCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreatedResponseSchema:
    """Create a certificate generation job."""
    job_service = JobService(db)
    return job_service.create_job(payload, background_tasks)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get job status and progress",
    description="Returns real-time progress metrics, total/successful/failed counts, status, and failure details.",
)
def get_job_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> JobStatusResponseSchema:
    """Get status and progress details of a job."""
    job_service = JobService(db)
    return job_service.get_job_status(job_id)


@router.get(
    "/{job_id}/certificates",
    response_model=PaginatedCertificatesSchema,
    status_code=status.HTTP_200_OK,
    summary="List certificates belonging to a job",
    description="Returns a paginated list of certificates for a specified job ID, with optional status filtering.",
)
def get_job_certificates(
    job_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit size"),
    status: Optional[CertificateStatus] = Query(None, description="Optional status filter"),
    db: Session = Depends(get_db),
) -> PaginatedCertificatesSchema:
    """List certificates belonging to a job."""
    cert_service = CertificateService(db)
    return cert_service.get_certificates_for_job(job_id, skip=skip, limit=limit, status=status)


@router.get(
    "/{job_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download all completed certificates as a ZIP archive",
    description="Bundles all successfully generated PDF certificates for the specified job into a single downloadable ZIP file.",
)
def download_job_certificates_zip(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download all completed certificates for a job in a ZIP archive."""
    job_service = JobService(db)
    zip_file_path = job_service.create_job_zip(job_id)

    return FileResponse(
        path=zip_file_path,
        media_type="application/zip",
        filename=f"certificates_job_{job_id}.zip",
    )
