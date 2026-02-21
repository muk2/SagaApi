from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


@dataclass
class NorthChargeResult:
    approved: bool
    transaction_id: str | None
    token: str | None  # Reusable token for refunds/voids
    decline_code: str | None
    card_last_four: str | None
    raw_response: dict


@dataclass
class NorthRefundResult:
    approved: bool
    transaction_id: str | None
    raw_response: dict


@dataclass
class NorthVoidResult:
    approved: bool
    transaction_id: str | None
    raw_response: dict


class NorthPaymentService:
    """Encapsulates all communication with North's payment gateway API."""

    def __init__(
        self,
        mid: str,
        developer_key: str,
        password: str,
        base_url: str,
        timeout: int = 30,
    ):
        self.mid = mid
        self.developer_key = developer_key
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_auth_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-MID": self.mid,
            "X-Developer-Key": self.developer_key,
        }

    async def charge(self, token: str, amount: Decimal, currency: str = "USD") -> NorthChargeResult:
        """Execute a one-time sale using a North card token."""
        payload = {
            "type": "sale",
            "token": token,
            "amount": str(amount),
            "currency": currency,
            "mid": self.mid,
            "password": self.password,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/transactions/charge",
                    headers=self._get_auth_headers(),
                    json=payload,
                )
                data = response.json()

                approved = data.get("approved", False) or data.get("status") == "approved"

                # Log without sensitive data
                logger.info(
                    "North charge: approved=%s, transaction_id=%s, amount=%s",
                    approved,
                    data.get("transaction_id"),
                    amount,
                )

                return NorthChargeResult(
                    approved=approved,
                    transaction_id=data.get("transaction_id"),
                    token=data.get("token"),
                    decline_code=data.get("decline_code") if not approved else None,
                    card_last_four=data.get("card_last_four"),
                    raw_response=data,
                )
        except httpx.TimeoutException:
            logger.error("North charge timeout: amount=%s", amount)
            return NorthChargeResult(
                approved=False,
                transaction_id=None,
                token=None,
                decline_code="TIMEOUT",
                card_last_four=None,
                raw_response={"error": "Request timed out"},
            )
        except httpx.HTTPError as e:
            logger.error("North charge HTTP error: %s", str(e))
            return NorthChargeResult(
                approved=False,
                transaction_id=None,
                token=None,
                decline_code="NETWORK_ERROR",
                card_last_four=None,
                raw_response={"error": str(e)},
            )

    async def refund(self, north_token: str, amount: Decimal) -> NorthRefundResult:
        """Refund a previous transaction using stored token."""
        payload = {
            "type": "refund",
            "token": north_token,
            "amount": str(amount),
            "mid": self.mid,
            "password": self.password,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/transactions/refund",
                    headers=self._get_auth_headers(),
                    json=payload,
                )
                data = response.json()

                approved = data.get("approved", False) or data.get("status") == "approved"

                logger.info(
                    "North refund: approved=%s, transaction_id=%s, amount=%s",
                    approved,
                    data.get("transaction_id"),
                    amount,
                )

                return NorthRefundResult(
                    approved=approved,
                    transaction_id=data.get("transaction_id"),
                    raw_response=data,
                )
        except httpx.TimeoutException:
            logger.error("North refund timeout: amount=%s", amount)
            return NorthRefundResult(
                approved=False,
                transaction_id=None,
                raw_response={"error": "Request timed out"},
            )
        except httpx.HTTPError as e:
            logger.error("North refund HTTP error: %s", str(e))
            return NorthRefundResult(
                approved=False,
                transaction_id=None,
                raw_response={"error": str(e)},
            )

    async def void(self, north_token: str) -> NorthVoidResult:
        """Void a same-day transaction."""
        payload = {
            "type": "void",
            "token": north_token,
            "mid": self.mid,
            "password": self.password,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/transactions/void",
                    headers=self._get_auth_headers(),
                    json=payload,
                )
                data = response.json()

                approved = data.get("approved", False) or data.get("status") == "approved"

                logger.info(
                    "North void: approved=%s, transaction_id=%s",
                    approved,
                    data.get("transaction_id"),
                )

                return NorthVoidResult(
                    approved=approved,
                    transaction_id=data.get("transaction_id"),
                    raw_response=data,
                )
        except httpx.TimeoutException:
            logger.error("North void timeout")
            return NorthVoidResult(
                approved=False,
                transaction_id=None,
                raw_response={"error": "Request timed out"},
            )
        except httpx.HTTPError as e:
            logger.error("North void HTTP error: %s", str(e))
            return NorthVoidResult(
                approved=False,
                transaction_id=None,
                raw_response={"error": str(e)},
            )
