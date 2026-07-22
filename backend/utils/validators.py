"""Shared validation utilities for all CRUD routers.

Provides reusable validators for:
- Monetary amount bounds (0.01–999,999,999.99)
- String length constraints (names: 100 chars, descriptions: 500 chars)
- SQL injection pattern detection
- XSS pattern detection
- Input sanitization (HTML stripping, whitespace trimming)

These validators can be used standalone or integrated with Pydantic v2
field_validator functions.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Union


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MONETARY_MIN: Decimal = Decimal("0.01")
MONETARY_MAX: Decimal = Decimal("999999999.99")

MAX_NAME_LENGTH: int = 100
MAX_DESCRIPTION_LENGTH: int = 500

# SQL injection patterns (case-insensitive)
_SQL_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bUNION\b", re.IGNORECASE),
    re.compile(r"\bSELECT\b", re.IGNORECASE),
    re.compile(r"\bINSERT\b", re.IGNORECASE),
    re.compile(r"\bUPDATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\b", re.IGNORECASE),
    re.compile(r"\bDROP\b", re.IGNORECASE),
    re.compile(r"\bALTER\b", re.IGNORECASE),
    re.compile(r"\bEXEC\b", re.IGNORECASE),
    re.compile(r"\bEXECUTE\b", re.IGNORECASE),
    re.compile(r"--", re.IGNORECASE),
    re.compile(r"/\*", re.IGNORECASE),
    re.compile(r"\*/", re.IGNORECASE),
    re.compile(r"\bOR\b\s+\d+=\d+", re.IGNORECASE),
    re.compile(r"\bAND\b\s+\d+=\d+", re.IGNORECASE),
    re.compile(r";\s*(DROP|ALTER|DELETE|INSERT|UPDATE|SELECT)", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+'", re.IGNORECASE),
]

# XSS patterns (case-insensitive)
_XSS_PATTERNS: list[re.Pattern] = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"</\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onerror=, onclick=, onload=, etc.
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*link", re.IGNORECASE),
    re.compile(r"<\s*img[^>]+src\s*=", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
]

# HTML tag stripping pattern
_HTML_TAG_PATTERN: re.Pattern = re.compile(r"<[^>]*>")


# ---------------------------------------------------------------------------
# Validation Error
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when a validation check fails."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# ---------------------------------------------------------------------------
# Monetary Validation
# ---------------------------------------------------------------------------

def validate_monetary_amount(
    value: Union[Decimal, float, int, str],
    field_name: str = "amount",
) -> Decimal:
    """Validate that a monetary amount is within the accepted range.

    Accepts Decimal, float, int, or numeric string representations.
    Returns a Decimal rounded to 2 decimal places.

    Args:
        value: The monetary value to validate.
        field_name: Name of the field for error messages.

    Returns:
        Decimal value rounded to 2 decimal places.

    Raises:
        ValidationError: If the value is not a valid number or outside [0.01, 999999999.99].
    """
    try:
        if isinstance(value, float):
            # Convert float to string first to avoid floating point issues
            decimal_value = Decimal(str(value))
        elif isinstance(value, (int, str)):
            decimal_value = Decimal(str(value))
        elif isinstance(value, Decimal):
            decimal_value = value
        else:
            raise ValidationError(
                field=field_name,
                message=f"Invalid type for monetary amount: {type(value).__name__}. Expected a numeric value.",
            )
    except (InvalidOperation, ValueError):
        raise ValidationError(
            field=field_name,
            message="Invalid monetary amount. Must be a valid number.",
        )

    # Round to 2 decimal places
    decimal_value = decimal_value.quantize(Decimal("0.01"))

    if decimal_value < MONETARY_MIN:
        raise ValidationError(
            field=field_name,
            message=f"Amount must be at least {MONETARY_MIN}. Got: {decimal_value}",
        )

    if decimal_value > MONETARY_MAX:
        raise ValidationError(
            field=field_name,
            message=f"Amount must not exceed {MONETARY_MAX}. Got: {decimal_value}",
        )

    return decimal_value


# ---------------------------------------------------------------------------
# String Length Validation
# ---------------------------------------------------------------------------

def validate_name(
    value: str,
    field_name: str = "name",
    max_length: int = MAX_NAME_LENGTH,
) -> str:
    """Validate a name field (trimmed, non-empty, within length limit).

    Args:
        value: The string to validate.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed length (default: 100).

    Returns:
        The trimmed string value.

    Raises:
        ValidationError: If the string is empty or exceeds max_length.
    """
    if not isinstance(value, str):
        raise ValidationError(
            field=field_name,
            message=f"Expected a string value, got {type(value).__name__}.",
        )

    trimmed = value.strip()

    if not trimmed:
        raise ValidationError(
            field=field_name,
            message="Field cannot be empty.",
        )

    if len(trimmed) > max_length:
        raise ValidationError(
            field=field_name,
            message=f"Field must not exceed {max_length} characters. Got: {len(trimmed)}",
        )

    return trimmed


def validate_description(
    value: str,
    field_name: str = "description",
    max_length: int = MAX_DESCRIPTION_LENGTH,
) -> str:
    """Validate a description field (trimmed, within length limit, allows empty).

    Args:
        value: The string to validate.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed length (default: 500).

    Returns:
        The trimmed string value.

    Raises:
        ValidationError: If the string exceeds max_length.
    """
    if not isinstance(value, str):
        raise ValidationError(
            field=field_name,
            message=f"Expected a string value, got {type(value).__name__}.",
        )

    trimmed = value.strip()

    if len(trimmed) > max_length:
        raise ValidationError(
            field=field_name,
            message=f"Field must not exceed {max_length} characters. Got: {len(trimmed)}",
        )

    return trimmed


# ---------------------------------------------------------------------------
# Security Pattern Detection
# ---------------------------------------------------------------------------

def detect_sql_injection(value: str) -> bool:
    """Check if a string contains common SQL injection patterns.

    Args:
        value: The input string to check.

    Returns:
        True if a SQL injection pattern is detected, False otherwise.
    """
    if not isinstance(value, str):
        return False

    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True

    return False


def detect_xss(value: str) -> bool:
    """Check if a string contains common XSS patterns.

    Args:
        value: The input string to check.

    Returns:
        True if an XSS pattern is detected, False otherwise.
    """
    if not isinstance(value, str):
        return False

    for pattern in _XSS_PATTERNS:
        if pattern.search(value):
            return True

    return False


def validate_no_injection(
    value: str,
    field_name: str = "input",
) -> str:
    """Validate that a string does not contain SQL injection or XSS patterns.

    Args:
        value: The input string to validate.
        field_name: Name of the field for error messages.

    Returns:
        The original string if no patterns detected.

    Raises:
        ValidationError: If SQL injection or XSS patterns are found.
    """
    if detect_sql_injection(value):
        raise ValidationError(
            field=field_name,
            message="Input contains potentially dangerous SQL patterns.",
        )

    if detect_xss(value):
        raise ValidationError(
            field=field_name,
            message="Input contains potentially dangerous content.",
        )

    return value


# ---------------------------------------------------------------------------
# Sanitization Helpers
# ---------------------------------------------------------------------------

def sanitize_string(value: str) -> str:
    """Sanitize a user-provided string by stripping HTML tags and trimming whitespace.

    Args:
        value: The input string to sanitize.

    Returns:
        The sanitized string with HTML tags removed and whitespace trimmed.
    """
    if not isinstance(value, str):
        return ""

    # Strip HTML tags
    cleaned = strip_html_tags(value)

    # Trim leading/trailing whitespace
    cleaned = cleaned.strip()

    # Collapse multiple spaces into single space
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned


def strip_html_tags(value: str) -> str:
    """Remove all HTML tags from a string.

    Args:
        value: The input string.

    Returns:
        The string with all HTML tags removed.
    """
    if not isinstance(value, str):
        return ""

    return _HTML_TAG_PATTERN.sub("", value)


# ---------------------------------------------------------------------------
# Combined Validation (for use in Pydantic validators)
# ---------------------------------------------------------------------------

def validate_and_sanitize_name(
    value: str,
    field_name: str = "name",
    max_length: int = MAX_NAME_LENGTH,
) -> str:
    """Validate and sanitize a name field: sanitize, check length, check injection.

    This is designed to be used within a Pydantic field_validator.

    Args:
        value: The input string.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed length.

    Returns:
        Sanitized and validated string.

    Raises:
        ValidationError: If validation fails.
    """
    sanitized = sanitize_string(value)
    validate_no_injection(sanitized, field_name)
    validated = validate_name(sanitized, field_name, max_length)
    return validated


def validate_and_sanitize_description(
    value: str,
    field_name: str = "description",
    max_length: int = MAX_DESCRIPTION_LENGTH,
) -> str:
    """Validate and sanitize a description field: sanitize, check length, check injection.

    This is designed to be used within a Pydantic field_validator.

    Args:
        value: The input string.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed length.

    Returns:
        Sanitized and validated string.

    Raises:
        ValidationError: If validation fails.
    """
    sanitized = sanitize_string(value)
    validate_no_injection(sanitized, field_name)
    validated = validate_description(sanitized, field_name, max_length)
    return validated
