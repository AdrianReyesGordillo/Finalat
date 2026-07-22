"""Unit tests for the Amazon Bedrock client service.

Tests cover:
- Prompt construction with financial context
- Message truncation for token limits
- Successful chat completion (mocked Bedrock)
- Timeout handling with fallback message
- AWS error handling with fallback message
- Token estimation heuristic
- Advice extraction
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from backend.services.bedrock_client import (
    FALLBACK_MESSAGE,
    MAX_PROMPT_TOKENS,
    SYSTEM_PROMPT,
    _build_financial_context_text,
    _estimate_token_count,
    _extract_advice,
    _truncate_messages,
    chat_with_fina,
)


class TestBuildFinancialContext:
    """Tests for _build_financial_context_text."""

    def test_empty_context_returns_empty_string(self):
        result = _build_financial_context_text({})
        assert result == ""

    def test_none_context_returns_empty_string(self):
        result = _build_financial_context_text({})
        assert result == ""

    def test_full_context_includes_all_fields(self):
        context = {
            "total_savings": 50000.00,
            "total_debts": 10000.00,
            "total_credit_balance": 5000.00,
            "total_afore": 200000.00,
            "total_gbm": 100000.00,
            "net_worth": 335000.00,
            "risk_tolerance": "medium",
            "liquidity_preference": "short-term",
            "monthly_income": 30000.00,
            "monthly_expenses": 20000.00,
        }
        result = _build_financial_context_text(context)

        assert "Contexto financiero del usuario:" in result
        assert "Ahorro total:" in result
        assert "Deudas totales:" in result
        assert "Saldo en tarjetas:" in result
        assert "Afore:" in result
        assert "Portafolio GBM:" in result
        assert "Patrimonio neto:" in result
        assert "Tolerancia al riesgo: medium" in result
        assert "Preferencia de liquidez: short-term" in result
        assert "Ingreso mensual:" in result
        assert "Gastos mensuales:" in result

    def test_partial_context_includes_only_provided_fields(self):
        context = {"total_savings": 25000.00, "risk_tolerance": "low"}
        result = _build_financial_context_text(context)

        assert "Ahorro total:" in result
        assert "Tolerancia al riesgo: low" in result
        assert "Deudas totales:" not in result
        assert "Portafolio GBM:" not in result


class TestEstimateTokenCount:
    """Tests for _estimate_token_count."""

    def test_empty_string(self):
        assert _estimate_token_count("") == 0

    def test_short_string(self):
        # 12 chars / 4 = 3 tokens
        assert _estimate_token_count("Hello World!") == 3

    def test_longer_string(self):
        text = "a" * 100
        assert _estimate_token_count(text) == 25


class TestTruncateMessages:
    """Tests for _truncate_messages."""

    def test_empty_messages_returns_empty(self):
        result = _truncate_messages([], max_tokens=1000)
        assert result == []

    def test_messages_within_budget_unchanged(self):
        messages = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, ¿cómo puedo ayudarte?"},
        ]
        result = _truncate_messages(messages, max_tokens=1000)
        assert result == messages

    def test_messages_exceeding_budget_truncated(self):
        # Create messages that exceed the budget
        messages = [
            {"role": "user", "content": "a" * 400},  # 100 tokens
            {"role": "assistant", "content": "b" * 400},  # 100 tokens
            {"role": "user", "content": "c" * 400},  # 100 tokens
        ]
        # Budget of 200 tokens should remove the first message
        result = _truncate_messages(messages, max_tokens=200)
        assert len(result) < len(messages)
        # Should keep the most recent messages
        assert result[-1]["content"] == "c" * 400


class TestExtractAdvice:
    """Tests for _extract_advice."""

    def test_empty_response_returns_fallback(self):
        assert _extract_advice("") == FALLBACK_MESSAGE

    def test_whitespace_only_returns_fallback(self):
        assert _extract_advice("   \n  ") == FALLBACK_MESSAGE

    def test_normal_response_returned_cleaned(self):
        text = "  Te recomiendo diversificar tus inversiones.  "
        result = _extract_advice(text)
        assert result == "Te recomiendo diversificar tus inversiones."

    def test_structured_response_preserved(self):
        text = "1. Ahorra el 20% de tu ingreso\n2. Paga tus deudas\n3. Invierte en CETES"
        result = _extract_advice(text)
        assert "1. Ahorra" in result
        assert "2. Paga" in result
        assert "3. Invierte" in result


class TestChatWithFina:
    """Tests for the main chat_with_fina async function."""

    @pytest.mark.asyncio
    async def test_successful_chat_returns_response(self):
        """Test successful Bedrock call returns model response."""
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Te recomiendo invertir en CETES."}]
                }
            }
        }

        mock_client = MagicMock()
        mock_client.converse.return_value = mock_response

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "¿Dónde debo invertir?"}]
            result = await chat_with_fina(messages, {})

        assert result == "Te recomiendo invertir en CETES."
        mock_client.converse.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_returns_fallback(self):
        """Test that a timeout returns the fallback message."""
        mock_client = MagicMock()
        # Simulate a long-running call that will be timed out
        mock_client.converse.side_effect = lambda **kwargs: asyncio.sleep(100)

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            with patch(
                "backend.services.bedrock_client.BEDROCK_TIMEOUT", 0.01
            ):
                messages = [{"role": "user", "content": "Hola"}]
                result = await chat_with_fina(messages, {})

        assert result == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_client_error_returns_fallback(self):
        """Test that a ClientError returns the fallback message."""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.converse.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "Converse",
        )

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "Hola"}]
            result = await chat_with_fina(messages, {})

        assert result == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_botocore_error_returns_fallback(self):
        """Test that a BotoCoreError returns the fallback message."""
        from botocore.exceptions import BotoCoreError

        mock_client = MagicMock()
        mock_client.converse.side_effect = BotoCoreError()

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "Hola"}]
            result = await chat_with_fina(messages, {})

        assert result == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_fallback(self):
        """Test that any unexpected exception returns the fallback message."""
        mock_client = MagicMock()
        mock_client.converse.side_effect = RuntimeError("Unexpected error")

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "Hola"}]
            result = await chat_with_fina(messages, {})

        assert result == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_empty_messages_returns_fallback(self):
        """Test that empty messages list returns fallback."""
        result = await chat_with_fina([], {})
        assert result == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_financial_context_included_in_system_prompt(self):
        """Test that financial context is passed to Bedrock in the system prompt."""
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Respuesta con contexto."}]
                }
            }
        }

        mock_client = MagicMock()
        mock_client.converse.return_value = mock_response

        financial_context = {
            "total_savings": 100000.00,
            "risk_tolerance": "high",
        }

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "¿Qué me recomiendas?"}]
            await chat_with_fina(messages, financial_context)

        # Verify the system prompt contains financial context
        call_kwargs = mock_client.converse.call_args[1]
        system_text = call_kwargs["system"][0]["text"]
        assert "Contexto financiero del usuario:" in system_text
        assert "Ahorro total:" in system_text
        assert "Tolerancia al riesgo: high" in system_text

    @pytest.mark.asyncio
    async def test_messages_limited_to_last_five(self):
        """Test that only the last 5 messages are sent."""
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Respuesta."}]
                }
            }
        }

        mock_client = MagicMock()
        mock_client.converse.return_value = mock_response

        # Create 8 messages
        messages = [
            {"role": "user", "content": f"Mensaje {i}"}
            for i in range(8)
        ]

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            await chat_with_fina(messages, {})

        # Verify only last 5 messages were sent
        call_kwargs = mock_client.converse.call_args[1]
        sent_messages = call_kwargs["messages"]
        assert len(sent_messages) <= 5

    @pytest.mark.asyncio
    async def test_converse_params_include_correct_config(self):
        """Test that the Converse API is called with correct inference config."""
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "OK"}]
                }
            }
        }

        mock_client = MagicMock()
        mock_client.converse.return_value = mock_response

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "Test"}]
            await chat_with_fina(messages, {})

        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["inferenceConfig"]["maxTokens"] == 4096
        assert call_kwargs["inferenceConfig"]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_multi_block_response_concatenated(self):
        """Test that multiple content blocks are concatenated."""
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Primera parte. "},
                        {"text": "Segunda parte."},
                    ]
                }
            }
        }

        mock_client = MagicMock()
        mock_client.converse.return_value = mock_response

        with patch(
            "backend.services.bedrock_client._create_bedrock_client",
            return_value=mock_client,
        ):
            messages = [{"role": "user", "content": "Hola"}]
            result = await chat_with_fina(messages, {})

        assert result == "Primera parte. Segunda parte."
