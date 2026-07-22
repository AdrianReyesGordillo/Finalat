"""Standard response builder utilities."""

from typing import Any

from backend.schemas.common import APIResponse, ErrorDetail


def success_response(data: Any = None) -> dict:
    """Build a successful API response.

    Args:
        data: The response payload.

    Returns:
        Dict conforming to the APIResponse envelope.
    """
    return APIResponse(success=True, data=data, error=None).model_dump()


def error_response(
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
) -> dict:
    """Build an error API response.

    Args:
        code: Machine-readable error code (e.g., "VALIDATION_ERROR").
        message: Human-readable error message.
        fields: Optional field-level validation error details.

    Returns:
        Dict conforming to the APIResponse envelope.
    """
    error = ErrorDetail(code=code, message=message, fields=fields)
    return APIResponse(success=False, data=None, error=error).model_dump()


def validation_error_response(message: str, fields: dict[str, str] | None = None) -> dict:
    """Build a validation error response (HTTP 400).

    Args:
        message: Description of the validation failure.
        fields: Field-level error details.

    Returns:
        Dict conforming to the APIResponse envelope with VALIDATION_ERROR code.
    """
    return error_response(code="VALIDATION_ERROR", message=message, fields=fields)


def not_found_response(message: str = "Resource not found.") -> dict:
    """Build a not found error response (HTTP 404).

    Args:
        message: Description of what was not found.

    Returns:
        Dict conforming to the APIResponse envelope with NOT_FOUND code.
    """
    return error_response(code="NOT_FOUND", message=message)


def unauthorized_response(message: str = "Authentication required.") -> dict:
    """Build an unauthorized error response (HTTP 401).

    Args:
        message: Description of the auth failure.

    Returns:
        Dict conforming to the APIResponse envelope with UNAUTHORIZED code.
    """
    return error_response(code="UNAUTHORIZED", message=message)


def forbidden_response(message: str = "Access denied.") -> dict:
    """Build a forbidden error response (HTTP 403).

    Args:
        message: Description of the access denial.

    Returns:
        Dict conforming to the APIResponse envelope with FORBIDDEN code.
    """
    return error_response(code="FORBIDDEN", message=message)


def service_unavailable_response(message: str = "Service temporarily unavailable.") -> dict:
    """Build a service unavailable error response (HTTP 503).

    Args:
        message: Description of the service issue.

    Returns:
        Dict conforming to the APIResponse envelope with SERVICE_UNAVAILABLE code.
    """
    return error_response(code="SERVICE_UNAVAILABLE", message=message)


def rate_limited_response(message: str = "Rate limit exceeded. Try again later.") -> dict:
    """Build a rate limited error response (HTTP 429).

    Args:
        message: Description of the rate limit.

    Returns:
        Dict conforming to the APIResponse envelope with RATE_LIMITED code.
    """
    return error_response(code="RATE_LIMITED", message=message)
