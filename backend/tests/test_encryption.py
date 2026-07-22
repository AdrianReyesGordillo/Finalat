"""Unit tests for the Encryption Service.

Tests cover:
- Basic encrypt/decrypt round-trip
- EncryptionError on invalid key
- EncryptionError on corrupted ciphertext
- encrypt_fields / decrypt_fields batch operations
- No plaintext leakage in error messages
- Performance (single field within 50ms)
"""

import time

import pytest
from cryptography.fernet import Fernet

from backend.services.encryption import EncryptionError, EncryptionService


@pytest.fixture
def valid_key() -> str:
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture
def service(valid_key: str) -> EncryptionService:
    """Create an EncryptionService with a valid key."""
    return EncryptionService(valid_key)


class TestEncryptionServiceInit:
    """Tests for EncryptionService initialization."""

    def test_init_with_valid_key(self, valid_key: str):
        svc = EncryptionService(valid_key)
        assert svc is not None

    def test_init_with_empty_key_raises(self):
        with pytest.raises(EncryptionError, match="not configured"):
            EncryptionService("")

    def test_init_with_invalid_key_raises(self):
        with pytest.raises(EncryptionError, match="invalid"):
            EncryptionService("not-a-valid-fernet-key")

    def test_init_with_none_key_raises(self):
        with pytest.raises(EncryptionError):
            EncryptionService(None)  # type: ignore


class TestEncrypt:
    """Tests for the encrypt method."""

    def test_encrypt_returns_string(self, service: EncryptionService):
        result = service.encrypt("123.45")
        assert isinstance(result, str)

    def test_encrypt_differs_from_plaintext(self, service: EncryptionService):
        plaintext = "99999.99"
        ciphertext = service.encrypt(plaintext)
        assert ciphertext != plaintext

    def test_encrypt_empty_string(self, service: EncryptionService):
        # Empty string should still encrypt (produces non-empty ciphertext)
        ciphertext = service.encrypt("")
        assert ciphertext != ""
        assert isinstance(ciphertext, str)


class TestDecrypt:
    """Tests for the decrypt method."""

    def test_decrypt_round_trip(self, service: EncryptionService):
        plaintext = "1234567.89"
        ciphertext = service.encrypt(plaintext)
        result = service.decrypt(ciphertext)
        assert result == plaintext

    def test_decrypt_unicode_round_trip(self, service: EncryptionService):
        plaintext = "Pago de renta - Departamento #5 ñ"
        ciphertext = service.encrypt(plaintext)
        result = service.decrypt(ciphertext)
        assert result == plaintext

    def test_decrypt_corrupted_ciphertext_raises(self, service: EncryptionService):
        with pytest.raises(EncryptionError, match="Decryption failed"):
            service.decrypt("totally-invalid-ciphertext")

    def test_decrypt_wrong_key_raises(self, valid_key: str):
        service1 = EncryptionService(valid_key)
        service2 = EncryptionService(Fernet.generate_key().decode("utf-8"))

        ciphertext = service1.encrypt("sensitive data")
        with pytest.raises(EncryptionError, match="Decryption failed"):
            service2.decrypt(ciphertext)

    def test_decrypt_error_does_not_contain_plaintext(self, service: EncryptionService):
        """Verify that EncryptionError messages never include plaintext."""
        try:
            service.decrypt("corrupted-data-xyz")
        except EncryptionError as e:
            assert "corrupted-data-xyz" not in str(e)


class TestEncryptFields:
    """Tests for the encrypt_fields batch method."""

    def test_encrypt_fields_encrypts_specified_fields(self, service: EncryptionService):
        data = {"amount": "1000.50", "name": "Mi Ahorro", "balance": "500.00"}
        result = service.encrypt_fields(data, ["amount", "balance"])

        # Specified fields should be encrypted (different from original)
        assert result["amount"] != "1000.50"
        assert result["balance"] != "500.00"
        # Unspecified fields should remain unchanged
        assert result["name"] == "Mi Ahorro"

    def test_encrypt_fields_skips_none_values(self, service: EncryptionService):
        data = {"amount": "100.00", "optional_field": None}
        result = service.encrypt_fields(data, ["amount", "optional_field"])

        assert result["amount"] != "100.00"
        assert result["optional_field"] is None

    def test_encrypt_fields_skips_missing_fields(self, service: EncryptionService):
        data = {"amount": "100.00"}
        # Requesting encryption of a field not in data should not raise
        result = service.encrypt_fields(data, ["amount", "nonexistent_field"])
        assert result["amount"] != "100.00"
        assert "nonexistent_field" not in result

    def test_encrypt_fields_does_not_mutate_original(self, service: EncryptionService):
        data = {"amount": "100.00", "name": "Test"}
        original_amount = data["amount"]
        service.encrypt_fields(data, ["amount"])
        assert data["amount"] == original_amount


class TestDecryptFields:
    """Tests for the decrypt_fields batch method."""

    def test_decrypt_fields_round_trip(self, service: EncryptionService):
        original = {"amount": "1234.56", "description": "Pago renta", "id": "abc123"}
        encrypted = service.encrypt_fields(original, ["amount", "description"])
        decrypted = service.decrypt_fields(encrypted, ["amount", "description"])

        assert decrypted["amount"] == "1234.56"
        assert decrypted["description"] == "Pago renta"
        assert decrypted["id"] == "abc123"

    def test_decrypt_fields_skips_none_values(self, service: EncryptionService):
        data = {"amount": None, "name": "Test"}
        result = service.decrypt_fields(data, ["amount"])
        assert result["amount"] is None

    def test_decrypt_fields_raises_on_corrupted_field(self, service: EncryptionService):
        data = {"amount": "not-valid-ciphertext", "name": "Test"}
        with pytest.raises(EncryptionError):
            service.decrypt_fields(data, ["amount"])


class TestPerformance:
    """Tests for performance requirements (single field within 50ms)."""

    def test_single_encrypt_within_50ms(self, service: EncryptionService):
        plaintext = "999999999.99"
        start = time.perf_counter()
        service.encrypt(plaintext)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 50, f"Encryption took {elapsed_ms:.2f}ms, exceeds 50ms limit"

    def test_single_decrypt_within_50ms(self, service: EncryptionService):
        ciphertext = service.encrypt("999999999.99")
        start = time.perf_counter()
        service.decrypt(ciphertext)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 50, f"Decryption took {elapsed_ms:.2f}ms, exceeds 50ms limit"
