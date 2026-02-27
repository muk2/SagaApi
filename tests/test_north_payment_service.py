from __future__ import annotations

import logging
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services.north_payment_service import (
    NorthChargeResult,
    NorthPaymentService,
    NorthRefundResult,
    NorthVoidResult,
)


@pytest.fixture
def service() -> NorthPaymentService:
    return NorthPaymentService(
        mid="test-mid-123",
        developer_key="test-dev-key-456",
        password="test-password-789",
        base_url="https://api.north.com/v1/",
        timeout=10,
    )


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    return resp


# ---------- Auth Headers ----------


class TestAuthHeaders:
    def test_auth_headers_contain_required_keys(self, service: NorthPaymentService):
        headers = service._get_auth_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["X-MID"] == "test-mid-123"
        assert headers["X-Developer-Key"] == "test-dev-key-456"

    def test_auth_headers_do_not_contain_password(self, service: NorthPaymentService):
        headers = service._get_auth_headers()
        for value in headers.values():
            assert "test-password-789" not in value


# ---------- Charge ----------


class TestCharge:
    @pytest.mark.asyncio
    async def test_successful_charge(self, service: NorthPaymentService):
        mock_data = {
            "approved": True,
            "transaction_id": "txn-001",
            "token": "reuse-token-abc",
            "card_last_four": "4242",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.charge(token="card-token-xyz", amount=Decimal("49.99"))

        assert isinstance(result, NorthChargeResult)
        assert result.approved is True
        assert result.transaction_id == "txn-001"
        assert result.token == "reuse-token-abc"
        assert result.decline_code is None
        assert result.card_last_four == "4242"
        assert result.raw_response == mock_data

    @pytest.mark.asyncio
    async def test_declined_charge(self, service: NorthPaymentService):
        mock_data = {
            "approved": False,
            "transaction_id": "txn-002",
            "decline_code": "INSUFFICIENT_FUNDS",
            "card_last_four": "1234",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.charge(token="card-token-xyz", amount=Decimal("100.00"))

        assert result.approved is False
        assert result.decline_code == "INSUFFICIENT_FUNDS"
        assert result.transaction_id == "txn-002"

    @pytest.mark.asyncio
    async def test_charge_with_status_approved(self, service: NorthPaymentService):
        """Test that status='approved' is treated as approved even without approved=True."""
        mock_data = {
            "status": "approved",
            "transaction_id": "txn-003",
            "token": "reuse-token-def",
            "card_last_four": "5678",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.charge(token="card-token-xyz", amount=Decimal("25.00"))

        assert result.approved is True

    @pytest.mark.asyncio
    async def test_charge_timeout(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.charge(token="card-token-xyz", amount=Decimal("50.00"))

        assert result.approved is False
        assert result.transaction_id is None
        assert result.decline_code == "TIMEOUT"
        assert "timed out" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_charge_network_error(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.charge(token="card-token-xyz", amount=Decimal("75.00"))

        assert result.approved is False
        assert result.decline_code == "NETWORK_ERROR"
        assert "Connection refused" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_charge_sends_correct_payload(self, service: NorthPaymentService):
        mock_resp = _mock_response({"approved": True, "transaction_id": "txn-004"})

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await service.charge(token="card-token-xyz", amount=Decimal("99.99"), currency="EUR")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.north.com/v1/transactions/charge"
        payload = call_args[1]["json"]
        assert payload["type"] == "sale"
        assert payload["token"] == "card-token-xyz"
        assert payload["amount"] == "99.99"
        assert payload["currency"] == "EUR"
        assert payload["mid"] == "test-mid-123"


# ---------- Refund ----------


class TestRefund:
    @pytest.mark.asyncio
    async def test_successful_refund(self, service: NorthPaymentService):
        mock_data = {
            "approved": True,
            "transaction_id": "ref-001",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.refund(north_token="token-abc", amount=Decimal("25.00"))

        assert isinstance(result, NorthRefundResult)
        assert result.approved is True
        assert result.transaction_id == "ref-001"

    @pytest.mark.asyncio
    async def test_refund_timeout(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.refund(north_token="token-abc", amount=Decimal("25.00"))

        assert result.approved is False
        assert result.transaction_id is None
        assert "timed out" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_refund_network_error(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.refund(north_token="token-abc", amount=Decimal("25.00"))

        assert result.approved is False
        assert "Connection refused" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_refund_sends_correct_payload(self, service: NorthPaymentService):
        mock_resp = _mock_response({"approved": True, "transaction_id": "ref-002"})

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await service.refund(north_token="token-abc", amount=Decimal("10.50"))

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.north.com/v1/transactions/refund"
        payload = call_args[1]["json"]
        assert payload["type"] == "refund"
        assert payload["token"] == "token-abc"
        assert payload["amount"] == "10.50"


# ---------- Void ----------


class TestVoid:
    @pytest.mark.asyncio
    async def test_successful_void(self, service: NorthPaymentService):
        mock_data = {
            "approved": True,
            "transaction_id": "void-001",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.void(north_token="token-abc")

        assert isinstance(result, NorthVoidResult)
        assert result.approved is True
        assert result.transaction_id == "void-001"

    @pytest.mark.asyncio
    async def test_void_timeout(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.void(north_token="token-abc")

        assert result.approved is False
        assert result.transaction_id is None
        assert "timed out" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_void_network_error(self, service: NorthPaymentService):
        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.void(north_token="token-abc")

        assert result.approved is False
        assert "Connection refused" in result.raw_response["error"]

    @pytest.mark.asyncio
    async def test_void_sends_correct_payload(self, service: NorthPaymentService):
        mock_resp = _mock_response({"approved": True, "transaction_id": "void-002"})

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await service.void(north_token="token-abc")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.north.com/v1/transactions/void"
        payload = call_args[1]["json"]
        assert payload["type"] == "void"
        assert payload["token"] == "token-abc"
        assert payload["mid"] == "test-mid-123"


# ---------- Sensitive Data Logging ----------


class TestSensitiveDataNotLogged:
    @pytest.mark.asyncio
    async def test_charge_does_not_log_sensitive_data(
        self, service: NorthPaymentService, caplog: pytest.LogCaptureFixture
    ):
        mock_data = {
            "approved": True,
            "transaction_id": "txn-010",
            "token": "reuse-token",
            "card_last_four": "9999",
        }
        mock_resp = _mock_response(mock_data)

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with caplog.at_level(logging.DEBUG):
                await service.charge(token="card-token-xyz", amount=Decimal("10.00"))

        log_text = caplog.text
        # Ensure sensitive credentials are never logged
        assert "test-password-789" not in log_text
        assert "test-dev-key-456" not in log_text
        assert "card-token-xyz" not in log_text

    @pytest.mark.asyncio
    async def test_refund_does_not_log_sensitive_data(
        self, service: NorthPaymentService, caplog: pytest.LogCaptureFixture
    ):
        mock_resp = _mock_response({"approved": True, "transaction_id": "ref-010"})

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with caplog.at_level(logging.DEBUG):
                await service.refund(north_token="token-secret", amount=Decimal("5.00"))

        log_text = caplog.text
        assert "test-password-789" not in log_text
        assert "token-secret" not in log_text

    @pytest.mark.asyncio
    async def test_void_does_not_log_sensitive_data(
        self, service: NorthPaymentService, caplog: pytest.LogCaptureFixture
    ):
        mock_resp = _mock_response({"approved": True, "transaction_id": "void-010"})

        with patch("src.services.north_payment_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with caplog.at_level(logging.DEBUG):
                await service.void(north_token="token-secret")

        log_text = caplog.text
        assert "test-password-789" not in log_text
        assert "token-secret" not in log_text


# ---------- Base URL Trailing Slash ----------


class TestBaseUrlNormalization:
    def test_trailing_slash_stripped(self):
        svc = NorthPaymentService(
            mid="m",
            developer_key="d",
            password="p",
            base_url="https://api.north.com/v1/",
        )
        assert svc.base_url == "https://api.north.com/v1"

    def test_no_trailing_slash_unchanged(self):
        svc = NorthPaymentService(
            mid="m",
            developer_key="d",
            password="p",
            base_url="https://api.north.com/v1",
        )
        assert svc.base_url == "https://api.north.com/v1"
