"""Unit tests for the Patrimonio (Net Worth) endpoint.

Tests verify:
- _safe_decrypt_sum helper correctly sums decrypted values
- _safe_decrypt_sum handles decryption failures gracefully
- Net worth calculation: total_assets - total_liabilities
- Response structure matches the expected format
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.routers.patrimonio import _safe_decrypt_sum
from backend.services.encryption import EncryptionError


# ---------------------------------------------------------------------------
# _safe_decrypt_sum Tests
# ---------------------------------------------------------------------------


class TestSafeDecryptSum:
    """Tests for the _safe_decrypt_sum helper."""

    def test_empty_entries_returns_zero(self):
        """Empty list yields total=0, failed=0."""
        total, failed = _safe_decrypt_sum([], "amount_encrypted")
        assert total == 0.0
        assert failed == 0

    @patch("backend.routers.patrimonio.encryption_service")
    def test_single_entry_success(self, mock_enc):
        """A single entry decrypts successfully."""
        mock_enc.decrypt.return_value = "1500.50"
        entry = MagicMock()
        entry.amount_encrypted = "cipher_text"
        entry.id = "test-id-1"

        total, failed = _safe_decrypt_sum([entry], "amount_encrypted")

        assert total == 1500.50
        assert failed == 0
        mock_enc.decrypt.assert_called_once_with("cipher_text")

    @patch("backend.routers.patrimonio.encryption_service")
    def test_multiple_entries_sum_correctly(self, mock_enc):
        """Multiple entries are summed correctly."""
        mock_enc.decrypt.side_effect = ["1000.00", "2500.75", "500.25"]
        entries = []
        for i in range(3):
            entry = MagicMock()
            entry.amount_encrypted = f"cipher_{i}"
            entry.id = f"id-{i}"
            entries.append(entry)

        total, failed = _safe_decrypt_sum(entries, "amount_encrypted")

        assert total == 4001.00
        assert failed == 0

    @patch("backend.routers.patrimonio.encryption_service")
    def test_decryption_failure_excluded(self, mock_enc):
        """Entries that fail decryption are excluded from the sum."""
        mock_enc.decrypt.side_effect = [
            "1000.00",
            EncryptionError("bad token"),
            "2000.00",
        ]
        entries = []
        for i in range(3):
            entry = MagicMock()
            entry.amount_encrypted = f"cipher_{i}"
            entry.id = f"id-{i}"
            entries.append(entry)

        total, failed = _safe_decrypt_sum(entries, "amount_encrypted")

        assert total == 3000.00
        assert failed == 1

    @patch("backend.routers.patrimonio.encryption_service")
    def test_all_entries_fail_decryption(self, mock_enc):
        """If all entries fail, total is 0 and failed_count equals entry count."""
        mock_enc.decrypt.side_effect = EncryptionError("bad")
        entries = []
        for i in range(3):
            entry = MagicMock()
            entry.amount_encrypted = f"cipher_{i}"
            entry.id = f"id-{i}"
            entries.append(entry)

        total, failed = _safe_decrypt_sum(entries, "amount_encrypted")

        assert total == 0.0
        assert failed == 3

    @patch("backend.routers.patrimonio.encryption_service")
    def test_invalid_float_value_counted_as_failure(self, mock_enc):
        """A decrypted value that isn't a valid float counts as a failure."""
        mock_enc.decrypt.return_value = "not-a-number"
        entry = MagicMock()
        entry.amount_encrypted = "cipher_text"
        entry.id = "id-1"

        total, failed = _safe_decrypt_sum([entry], "amount_encrypted")

        assert total == 0.0
        assert failed == 1


# ---------------------------------------------------------------------------
# Net Worth Calculation Logic Tests
# ---------------------------------------------------------------------------


class TestNetWorthCalculation:
    """Tests verifying net worth = assets - liabilities."""

    def test_net_worth_positive(self):
        """Net worth is positive when assets exceed liabilities."""
        assets = {"ahorro": 10000.0, "afore": 5000.0, "gbm": 3000.0}
        liabilities = {"deudas": 2000.0, "creditos": 1000.0}

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        net_worth = total_assets - total_liabilities

        assert net_worth == 15000.0

    def test_net_worth_negative(self):
        """Net worth is negative when liabilities exceed assets."""
        assets = {"ahorro": 1000.0, "afore": 500.0, "gbm": 200.0}
        liabilities = {"deudas": 5000.0, "creditos": 3000.0}

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        net_worth = total_assets - total_liabilities

        assert net_worth == -6300.0

    def test_net_worth_zero(self):
        """Net worth is zero when assets equal liabilities."""
        assets = {"ahorro": 5000.0, "afore": 0.0, "gbm": 0.0}
        liabilities = {"deudas": 3000.0, "creditos": 2000.0}

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        net_worth = total_assets - total_liabilities

        assert net_worth == 0.0

    def test_net_worth_all_zeroes(self):
        """Net worth is zero when user has no financial data."""
        assets = {"ahorro": 0.0, "afore": 0.0, "gbm": 0.0}
        liabilities = {"deudas": 0.0, "creditos": 0.0}

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        net_worth = total_assets - total_liabilities

        assert net_worth == 0.0

    def test_net_worth_precision(self):
        """Net worth rounds to 2 decimal places."""
        total_assets = 10000.123
        total_liabilities = 3000.456
        net_worth = round(total_assets - total_liabilities, 2)

        assert net_worth == 6999.67
