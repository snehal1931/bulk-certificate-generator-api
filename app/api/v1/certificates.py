"""API endpoints for individual certificate operations."""

import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve or download an individual generated PDF certificate",
    description="Fetches and returns the generated PDF file for the specified certificate ID.",
)
def get_certificate_pdf(
    certificate_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download an individual certificate PDF."""
    cert_service = CertificateService(db)
    file_path, filename = cert_service.get_certificate_file_path(certificate_id)

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
