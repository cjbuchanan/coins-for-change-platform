"""Common Pydantic schemas and validation utilities."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")
    sort: Optional[str] = Field(None, description="Sort field")
    order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    page: int
    size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Optional[Dict[str, str]] = Field(None, description="Detailed health checks")


class UserSummary(BaseModel):
    """User summary for references in other models."""
    id: UUID
    name: str
    email: str


def validate_uuid(v: str) -> UUID:
    """Validate and convert string to UUID."""
    try:
        return UUID(v)
    except ValueError:
        raise ValueError("Invalid UUID format")


def validate_non_empty_string(v: str) -> str:
    """Validate string is not empty after stripping whitespace."""
    if not v or not v.strip():
        raise ValueError("String cannot be empty")
    return v.strip()


def validate_email_format(v: str) -> str:
    """Basic email format validation."""
    import re
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, v):
        raise ValueError("Invalid email format")
    return v.lower()