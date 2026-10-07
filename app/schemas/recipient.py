"""Recipient request schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientSchema(BaseModel):
    """Recipient data input validation model."""

    name: str = Field(..., min_length=1, max_length=255, description="Recipient full name")
    email: EmailStr = Field(..., description="Valid recipient email address")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Recipient name cannot be empty or whitespace only.")
        return value
