"""Certificate repository module for DB operations."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.certificate import Certificate
from app.models.enums import CertificateStatus


class CertificateRepository:
    """Repository handling database interactions for Certificate entities."""

    def __init__(self, db: Session):
        self.db = db

    def create_bulk(
        self,
        job_id: uuid.UUID,
        recipients: List[dict],
    ) -> List[Certificate]:
        """Bulk create initial Certificate records for a Job."""
        certificates = [
            Certificate(
                id=uuid.uuid4(),
                job_id=job_id,
                recipient_name=rec["name"],
                recipient_email=str(rec["email"]),
                status=CertificateStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            for rec in recipients
        ]
        self.db.add_all(certificates)
        self.db.commit()
        return certificates

    def get_by_id(self, certificate_id: uuid.UUID) -> Optional[Certificate]:
        """Fetch certificate by ID."""
        statement = select(Certificate).where(Certificate.id == certificate_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_job_id_paginated(
        self,
        job_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CertificateStatus] = None,
    ) -> Tuple[List[Certificate], int]:
        """Fetch paginated list of certificates for a job and total count."""
        base_query = select(Certificate).where(Certificate.job_id == job_id)
        count_query = select(func.count()).select_from(Certificate).where(Certificate.job_id == job_id)

        if status:
            base_query = base_query.where(Certificate.status == status)
            count_query = count_query.where(Certificate.status == status)

        total = self.db.execute(count_query).scalar_one()

        paginated_query = base_query.offset(skip).limit(limit).order_by(Certificate.created_at.asc())
        results = self.db.execute(paginated_query).scalars().all()

        return list(results), total

    def get_failed_certificates_for_job(self, job_id: uuid.UUID) -> Sequence[Certificate]:
        """Fetch all failed certificates for a job to report detailed errors."""
        statement = select(Certificate).where(
            Certificate.job_id == job_id,
            Certificate.status == CertificateStatus.FAILED,
        )
        return self.db.execute(statement).scalars().all()

    def get_completed_certificates_for_job(self, job_id: uuid.UUID) -> Sequence[Certificate]:
        """Fetch all completed certificates for a job."""
        statement = select(Certificate).where(
            Certificate.job_id == job_id,
            Certificate.status == CertificateStatus.COMPLETED,
        )
        return self.db.execute(statement).scalars().all()

    def update_certificate_success(
        self,
        certificate_id: uuid.UUID,
        file_path: str,
    ) -> Optional[Certificate]:
        """Update certificate to COMPLETED state with file_path."""
        cert = self.get_by_id(certificate_id)
        if not cert:
            return None

        cert.status = CertificateStatus.COMPLETED
        cert.file_path = file_path
        cert.error_message = None
        cert.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def update_certificate_failure(
        self,
        certificate_id: uuid.UUID,
        error_message: str,
    ) -> Optional[Certificate]:
        """Update certificate to FAILED state with error message."""
        cert = self.get_by_id(certificate_id)
        if not cert:
            return None

        cert.status = CertificateStatus.FAILED
        cert.error_message = error_message
        cert.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def update_status(
        self,
        certificate_id: uuid.UUID,
        status: CertificateStatus,
    ) -> Optional[Certificate]:
        """Update certificate status."""
        cert = self.get_by_id(certificate_id)
        if not cert:
            return None

        cert.status = status
        self.db.commit()
        self.db.refresh(cert)
        return cert
