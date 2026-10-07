"""State machine Enums for Jobs and Certificates."""

from enum import Enum


class JobStatus(str, Enum):
    """Job status lifecycle states."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class CertificateStatus(str, Enum):
    """Certificate status lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
