"""Encryption service using Fernet (AES-256) for field-level encryption.

This module provides the EncryptionService class that encrypts and decrypts
sensitive data (monetary amounts, descriptions) before persistence and after
retrieval from the database.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8
"""

import logging
import warnings

from cryptography.fernet import Fernet, InvalidToken

from backend.config import settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption or decryption operations fail.

    This exception intentionally does NOT include plaintext values
    in its message or attributes to prevent data leaks in logs.
    """

    def __init__(self, message: str = "Encryption operation failed."):
        super().__init__(message)


class EncryptionService:
    """Field-level encryption service using Fernet (AES-256-CBC + HMAC-SHA256).

    Provides encrypt/decrypt for individual fields and batch operations
    for processing multiple fields in a dictionary at once.
    """

    def __init__(self, fernet_key: str):
        """Initialize the encryption service with a Fernet key.

        Args:
            fernet_key: A valid Fernet key (URL-safe base64 encoded 32-byte key).

        Raises:
            EncryptionError: If the key is invalid or cannot be used to
                initialize the Fernet cipher.
        """
        if not fernet_key:
            raise EncryptionError("FERNET_KEY is not configured.")
        try:
            self._fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
        except (ValueError, TypeError) as exc:
            raise EncryptionError(
                "FERNET_KEY is invalid. Ensure it is a valid Fernet key."
            ) from exc

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The string value to encrypt.

        Returns:
            The encrypted ciphertext as a URL-safe base64-encoded string.

        Raises:
            EncryptionError: If encryption fails for any reason.
        """
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception:
            raise EncryptionError("Failed to encrypt data.")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string back to plaintext.

        Args:
            ciphertext: The encrypted value (URL-safe base64-encoded string).

        Returns:
            The original plaintext string.

        Raises:
            EncryptionError: If decryption fails due to key mismatch,
                corrupted data, or invalid token. The error message
                intentionally omits any plaintext content.
        """
        try:
            plaintext_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext_bytes.decode("utf-8")
        except InvalidToken:
            raise EncryptionError(
                "Decryption failed: invalid token or key mismatch."
            )
        except Exception:
            raise EncryptionError("Decryption failed.")

    def encrypt_fields(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specified fields in a dictionary.

        Creates a new dictionary with the specified fields encrypted.
        Fields that are None or not present in the data are skipped.

        Args:
            data: The dictionary containing fields to encrypt.
            fields: List of field names whose values should be encrypted.

        Returns:
            A new dictionary with specified fields encrypted, other fields unchanged.

        Raises:
            EncryptionError: If encryption of any field fails.
        """
        result = dict(data)
        for field in fields:
            if field in result and result[field] is not None:
                value = str(result[field])
                result[field] = self.encrypt(value)
        return result

    def decrypt_fields(self, data: dict, fields: list[str]) -> dict:
        """Decrypt specified fields in a dictionary.

        Creates a new dictionary with the specified fields decrypted.
        Fields that are None or not present in the data are skipped.

        Args:
            data: The dictionary containing encrypted field values.
            fields: List of field names whose values should be decrypted.

        Returns:
            A new dictionary with specified fields decrypted, other fields unchanged.

        Raises:
            EncryptionError: If decryption of any field fails.
        """
        result = dict(data)
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.decrypt(result[field])
        return result


def get_encryption_service() -> EncryptionService:
    """Factory function to create an EncryptionService instance.

    Uses the FERNET_KEY from application settings. In development mode,
    if the key is empty, a temporary key is generated with a warning.
    In production, a missing key causes a startup failure.

    Returns:
        A configured EncryptionService instance.

    Raises:
        EncryptionError: If in production and FERNET_KEY is not set or invalid.
    """
    fernet_key = settings.FERNET_KEY

    if not fernet_key:
        if settings.APP_ENV == "development":
            fernet_key = Fernet.generate_key().decode("utf-8")
            warnings.warn(
                "FERNET_KEY is not set. A temporary key has been generated for development. "
                "Data encrypted with this key will NOT be recoverable after restart. "
                "Set FERNET_KEY in your .env file for persistent encryption.",
                UserWarning,
                stacklevel=2,
            )
            logger.warning(
                "Using auto-generated FERNET_KEY for development. "
                "Set FERNET_KEY environment variable for persistent encryption."
            )
        else:
            raise EncryptionError(
                "FERNET_KEY environment variable is required in production. "
                "Application cannot start without a valid encryption key."
            )

    return EncryptionService(fernet_key)


# Module-level singleton instance (initialized on first import)
# This will fail fast at startup if key is invalid in production.
encryption_service = get_encryption_service()
