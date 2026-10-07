"""Certificate service layer handling certificate queries and file downloads."""

import os
import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import (
    CertificateNotFoundError,
    CertificateNotReadyError,
    JobNotFoundError,
)
from app.models.enums import CertificateStatus
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.certificate import (
    CertificateResponseSchema,
    PaginatedCertificatesSchema,
)


class CertificateService:
    """Service layer encapsulating certificate query and download logic."""

    def __init__(self, db: Session):
        self.db = db
        self.cert_repo = CertificateRepository(db)
        self.job_repo = JobRepository(db)

    def get_certificates_for_job(
        self,
        job_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CertificateStatus] = None,
    ) -> PaginatedCertificatesSchema:
        """Fetch paginated certificates belonging to a specific job."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(str(job_id))

        certs, total = self.cert_repo.get_by_job_id_paginated(
            job_id=job_id,
            skip=skip,
            limit=limit,
            status=status,
        )

        items = [CertificateResponseSchema.model_validate(c) for c in certs]
        return PaginatedCertificatesSchema(
            total=total,
            skip=skip,
            limit=limit,
            items=items,
        )

    def get_certificate_file_path(self, certificate_id: uuid.UUID) -> Tuple[str, str]:
        """Validate certificate existence and return file path and suggested download filename.

        Returns (file_path, filename).
        Raises CertificateNotFoundError or CertificateNotReadyError.
        """
        cert = self.cert_repo.get_by_id(certificate_id)
        if not cert:
            raise CertificateNotFoundError(str(certificate_id))

        if cert.status != CertificateStatus.COMPLETED:
            raise CertificateNotReadyError(str(certificate_id), status=cert.status.value)

        if not cert.file_path or not os.path.exists(cert.file_path):
            raise CertificateNotFoundError(
                f"Certificate file for ID '{certificate_id}' is missing from storage."
            )

        sanitized_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).rstrip()
        filename = f"certificate_{sanitized_name.replace(' ', '_')}_{cert.id}.pdf"

        return cert.file_path, filename
