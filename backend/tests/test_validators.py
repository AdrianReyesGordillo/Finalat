"""Unit tests for shared validation utilities.

Tests cover:
- Monetary amount validation (bounds, types, edge cases)
- String length validators (names, descriptions)
- SQL injection pattern detection
- XSS pattern detection
- Sanitization helpers (HTML stripping, whitespace trimming)
- Combined validation and sanitization
"""

from decimal import Decimal

import pytest

from backend.utils.validators import (
    ValidationError,
    detect_sql_injection,
    detect_xss,
    sanitize_string,
    strip_html_tags,
    validate_and_sanitize_description,
    validate_and_sanitize_name,
    validate_description,
    validate_monetary_amount,
    validate_name,
    validate_no_injection,
)


class TestValidateMonetaryAmount:
    """Tests for monetary amount validation."""

    def test_accepts_minimum_value(self):
        result = validate_monetary_amount(Decimal("0.01"))
        assert result == Decimal("0.01")

    def test_accepts_maximum_value(self):
        result = validate_monetary_amount(Decimal("999999999.99"))
        assert result == Decimal("999999999.99")

    def test_accepts_typical_amount(self):
        result = validate_monetary_amount(Decimal("1234.56"))
        assert result == Decimal("1234.56")

    def test_accepts_float_input(self):
        result = validate_monetary_amount(1234.56)
        assert result == Decimal("1234.56")

    def test_accepts_int_input(self):
        result = validate_monetary_amount(100)
        assert result == Decimal("100.00")

    def test_accepts_string_input(self):
        result = validate_monetary_amount("5000.50")
        assert result == Decimal("5000.50")

    def test_rejects_zero(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_monetary_amount(Decimal("0.00"))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_monetary_amount(Decimal("-1.00"))

    def test_rejects_below_minimum(self):
        with pytest.raises(ValidationError, match="at least"):
            validate_monetary_amount(Decimal("0.001"))

    def test_rejects_above_maximum(self):
        with pytest.raises(ValidationError, match="must not exceed"):
            validate_monetary_amount(Decimal("1000000000.00"))

    def test_rejects_invalid_string(self):
        with pytest.raises(ValidationError, match="Invalid monetary amount"):
            validate_monetary_amount("not-a-number")

    def test_rounds_to_two_decimals(self):
        result = validate_monetary_amount(Decimal("100.999"))
        assert result == Decimal("101.00")

    def test_custom_field_name_in_error(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_monetary_amount(Decimal("0.00"), field_name="balance")
        assert exc_info.value.field == "balance"

    def test_rejects_invalid_type(self):
        with pytest.raises(ValidationError, match="Invalid type"):
            validate_monetary_amount([100])  # type: ignore


class TestValidateName:
    """Tests for name string validation."""

    def test_accepts_valid_name(self):
        result = validate_name("Mi cuenta de ahorro")
        assert result == "Mi cuenta de ahorro"

    def test_trims_whitespace(self):
        result = validate_name("  Cuenta  ")
        assert result == "Cuenta"

    def test_accepts_max_length(self):
        name = "a" * 100
        result = validate_name(name)
        assert result == name

    def test_rejects_exceeding_max_length(self):
        name = "a" * 101
        with pytest.raises(ValidationError, match="must not exceed 100"):
            validate_name(name)

    def test_rejects_empty_string(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_name("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_name("   ")

    def test_custom_max_length(self):
        result = validate_name("short", max_length=10)
        assert result == "short"

        with pytest.raises(ValidationError, match="must not exceed 10"):
            validate_name("this is too long", max_length=10)

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError, match="Expected a string"):
            validate_name(123)  # type: ignore

    def test_custom_field_name(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_name("", field_name="account_name")
        assert exc_info.value.field == "account_name"


class TestValidateDescription:
    """Tests for description string validation."""

    def test_accepts_valid_description(self):
        result = validate_description("Pago de renta mensual")
        assert result == "Pago de renta mensual"

    def test_accepts_empty_description(self):
        result = validate_description("")
        assert result == ""

    def test_trims_whitespace(self):
        result = validate_description("  Descripción  ")
        assert result == "Descripción"

    def test_accepts_max_length(self):
        desc = "a" * 500
        result = validate_description(desc)
        assert result == desc

    def test_rejects_exceeding_max_length(self):
        desc = "a" * 501
        with pytest.raises(ValidationError, match="must not exceed 500"):
            validate_description(desc)

    def test_custom_max_length(self):
        result = validate_description("short", max_length=200)
        assert result == "short"

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError, match="Expected a string"):
            validate_description(None)  # type: ignore


class TestDetectSqlInjection:
    """Tests for SQL injection pattern detection."""

    def test_detects_union_select(self):
        assert detect_sql_injection("' UNION SELECT * FROM users --") is True

    def test_detects_drop_table(self):
        assert detect_sql_injection("'; DROP TABLE users;") is True

    def test_detects_double_dash_comment(self):
        assert detect_sql_injection("admin'--") is True

    def test_detects_block_comment(self):
        assert detect_sql_injection("admin'/* comment */") is True

    def test_detects_or_equals(self):
        assert detect_sql_injection("' OR 1=1") is True

    def test_detects_semicolon_injection(self):
        assert detect_sql_injection("; DELETE FROM users") is True

    def test_clean_input_passes(self):
        assert detect_sql_injection("Mi cuenta de ahorro") is False

    def test_clean_numeric_input(self):
        assert detect_sql_injection("12345.67") is False

    def test_handles_non_string(self):
        assert detect_sql_injection(123) is False  # type: ignore

    def test_detects_case_insensitive(self):
        assert detect_sql_injection("union select") is True
        assert detect_sql_injection("UNION SELECT") is True
        assert detect_sql_injection("Union Select") is True


class TestDetectXss:
    """Tests for XSS pattern detection."""

    def test_detects_script_tag(self):
        assert detect_xss("<script>alert('xss')</script>") is True

    def test_detects_script_tag_with_spaces(self):
        assert detect_xss("< script >alert('x')</ script>") is True

    def test_detects_javascript_protocol(self):
        assert detect_xss("javascript:alert(1)") is True

    def test_detects_event_handler(self):
        assert detect_xss('<img onerror="alert(1)">') is True

    def test_detects_onclick(self):
        assert detect_xss('<div onclick="steal()">Click</div>') is True

    def test_detects_iframe(self):
        assert detect_xss('<iframe src="evil.com"></iframe>') is True

    def test_detects_vbscript(self):
        assert detect_xss("vbscript:msgbox") is True

    def test_clean_input_passes(self):
        assert detect_xss("Pago de servicios - Luz CFE") is False

    def test_clean_html_entities_pass(self):
        assert detect_xss("&lt;b&gt;bold&lt;/b&gt;") is False

    def test_handles_non_string(self):
        assert detect_xss(None) is False  # type: ignore


class TestValidateNoInjection:
    """Tests for combined injection validation."""

    def test_passes_clean_input(self):
        result = validate_no_injection("Normal text input")
        assert result == "Normal text input"

    def test_raises_on_sql_injection(self):
        with pytest.raises(ValidationError, match="SQL patterns"):
            validate_no_injection("'; DROP TABLE users; --")

    def test_raises_on_xss(self):
        with pytest.raises(ValidationError, match="dangerous content"):
            validate_no_injection("<script>alert(1)</script>")

    def test_custom_field_name(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_no_injection("<script>x</script>", field_name="description")
        assert exc_info.value.field == "description"


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_strips_html_tags(self):
        result = sanitize_string("<b>Hello</b> <i>world</i>")
        assert result == "Hello world"

    def test_trims_whitespace(self):
        result = sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_collapses_multiple_spaces(self):
        result = sanitize_string("hello    world")
        assert result == "hello world"

    def test_handles_script_tags(self):
        result = sanitize_string("<script>alert('x')</script>Safe text")
        assert result == "alert('x')Safe text"

    def test_handles_empty_string(self):
        result = sanitize_string("")
        assert result == ""

    def test_handles_non_string(self):
        result = sanitize_string(123)  # type: ignore
        assert result == ""

    def test_preserves_normal_text(self):
        result = sanitize_string("Pago de renta mensual $5,000.00")
        assert result == "Pago de renta mensual $5,000.00"


class TestStripHtmlTags:
    """Tests for HTML tag stripping."""

    def test_removes_simple_tags(self):
        assert strip_html_tags("<p>Hello</p>") == "Hello"

    def test_removes_nested_tags(self):
        assert strip_html_tags("<div><span>Text</span></div>") == "Text"

    def test_removes_self_closing_tags(self):
        assert strip_html_tags("Line<br/>break") == "Linebreak"

    def test_preserves_text_without_tags(self):
        assert strip_html_tags("No tags here") == "No tags here"

    def test_handles_non_string(self):
        assert strip_html_tags(None) == ""  # type: ignore


class TestValidateAndSanitizeName:
    """Tests for combined name validation and sanitization."""

    def test_sanitizes_and_validates(self):
        result = validate_and_sanitize_name("  <b>Mi Cuenta</b>  ")
        assert result == "Mi Cuenta"

    def test_rejects_injection_after_sanitize(self):
        # Even after stripping HTML, if SQL patterns remain, reject
        with pytest.raises(ValidationError, match="SQL patterns"):
            validate_and_sanitize_name("'; DROP TABLE users;--")

    def test_rejects_empty_after_sanitize(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_and_sanitize_name("<b></b>")

    def test_rejects_too_long_after_sanitize(self):
        long_name = "a" * 101
        with pytest.raises(ValidationError, match="must not exceed 100"):
            validate_and_sanitize_name(long_name)


class TestValidateAndSanitizeDescription:
    """Tests for combined description validation and sanitization."""

    def test_sanitizes_and_validates(self):
        result = validate_and_sanitize_description("  <p>Descripción larga</p>  ")
        assert result == "Descripción larga"

    def test_allows_empty_after_sanitize(self):
        result = validate_and_sanitize_description("")
        assert result == ""

    def test_rejects_too_long(self):
        long_desc = "a" * 501
        with pytest.raises(ValidationError, match="must not exceed 500"):
            validate_and_sanitize_description(long_desc)

    def test_rejects_xss_pattern(self):
        with pytest.raises(ValidationError, match="dangerous content"):
            validate_and_sanitize_description("javascript:alert(1)")
