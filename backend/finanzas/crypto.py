"""Field-level encryption for sensitive financial data.

Uses AES-256-GCM via the `cryptography` library's Fernet scheme.
Each value is encrypted with the master key from ENCRYPTION_KEY env var.

Encrypted values are stored as base64 strings prefixed with 'enc:' to
distinguish them from plaintext (allows gradual migration).

The module is designed to be transparent:
- encrypt() returns the encrypted string
- decrypt() returns the original value (str or numeric)
- decrypt() handles plaintext gracefully (for migration period)
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

# Derive a valid Fernet key from the ENCRYPTION_KEY env var.
# Fernet requires a 32-byte base64url-encoded key.
_RAW_KEY = os.getenv("ENCRYPTION_KEY", "")
_ENCRYPTION_ENABLED = bool(_RAW_KEY)

if _ENCRYPTION_ENABLED:
    # Derive a 32-byte key from any-length passphrase using SHA-256
    _derived = hashlib.sha256(_RAW_KEY.encode("utf-8")).digest()
    _FERNET_KEY = base64.urlsafe_b64encode(_derived)
    _fernet = Fernet(_FERNET_KEY)
else:
    _fernet = None


# Prefix to identify encrypted values in the database
_ENC_PREFIX = "enc:"


def is_enabled() -> bool:
    """Check if encryption is configured and active."""
    return _ENCRYPTION_ENABLED


def encrypt(value) -> str:
    """Encrypt a value for storage.

    Args:
        value: The value to encrypt (str, int, float, or None).

    Returns:
        Encrypted string prefixed with 'enc:', or empty string if None.
    """
    if value is None:
        return None
    if not _ENCRYPTION_ENABLED:
        return value

    plaintext = str(value)
    encrypted = _fernet.encrypt(plaintext.encode("utf-8"))
    return _ENC_PREFIX + encrypted.decode("utf-8")


def decrypt(value, as_type: type = str):
    """Decrypt a value from storage.

    Args:
        value: The stored value (may be encrypted or plaintext).
        as_type: The desired output type (str, float, int). Default: str.

    Returns:
        The decrypted value cast to as_type, or None if value is None.
    """
    if value is None:
        return None
    if not _ENCRYPTION_ENABLED:
        return _cast(value, as_type)

    value_str = str(value)

    # If it has the encryption prefix, decrypt it
    if value_str.startswith(_ENC_PREFIX):
        token = value_str[len(_ENC_PREFIX):].encode("utf-8")
        try:
            decrypted = _fernet.decrypt(token).decode("utf-8")
            return _cast(decrypted, as_type)
        except InvalidToken:
            # Corrupted token — return as-is (shouldn't happen)
            return _cast(value, as_type)

    # No prefix — it's plaintext (pre-migration data)
    return _cast(value, as_type)


def decrypt_row(row: dict, fields: dict) -> dict:
    """Decrypt multiple fields in a row dict.

    Args:
        row: A dict-like row from the database.
        fields: Dict mapping column_name -> desired_type (str, float, int).

    Returns:
        A new dict with the specified fields decrypted.
    """
    result = dict(row)
    for col, col_type in fields.items():
        if col in result:
            result[col] = decrypt(result[col], col_type)
    return result


def encrypt_fields(data: dict, fields: list) -> dict:
    """Encrypt specified fields in a data dict.

    Args:
        data: Dict with field values.
        fields: List of field names to encrypt.

    Returns:
        A new dict with the specified fields encrypted.
    """
    result = dict(data)
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = encrypt(result[field])
    return result


def _cast(value, as_type: type):
    """Cast a value to the desired type."""
    if value is None:
        return None
    if as_type == float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    if as_type == int:
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    return str(value)
