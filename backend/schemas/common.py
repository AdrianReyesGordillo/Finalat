"""Common API response envelope schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail structure for API error responses."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    fields: dict[str, str] | None = Field(
        default=None,
        description="Field-level validation errors.",
    )


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    All API responses follow this structure:
    - success: indicates if the operation succeeded
    - data: the response payload (null on error)
    - error: error details (null on success)

    Exactly one of data or error is non-null.
    """

    success: bool = Field(..., description="Whether the operation succeeded.")
    data: Any = Field(default=None, description="Response payload.")
    error: ErrorDetail | None = Field(default=None, description="Error details if operation failed.")


class PaginatedData(BaseModel, Generic[T]):
    """Paginated data wrapper for list responses."""

    items: list[Any] = Field(default_factory=list, description="List of items.")
    total: int = Field(default=0, description="Total number of items.")
    page: int = Field(default=1, description="Current page number.")
    page_size: int = Field(default=50, description="Number of items per page.")
    has_next: bool = Field(default=False, description="Whether more pages exist.")
