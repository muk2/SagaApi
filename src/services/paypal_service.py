"""PayPal REST API service for order creation and capture.

Uses the PayPal Orders v2 API:
  - Sandbox: https://api-m.sandbox.paypal.com
  - Production: https://api-m.paypal.com
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class PayPalError(Exception):
    """Raised when a PayPal API call fails."""


class PayPalCaptureDeclined(PayPalError):
    """Raised when PayPal capture is declined."""


@dataclass
class PayPalCaptureResult:
    order_id: str
    status: str  # COMPLETED, DECLINED, etc.
    payer_email: Optional[str] = None
    capture_id: Optional[str] = None
    amount: Optional[str] = None


async def _get_access_token() -> str:
    """Obtain an OAuth 2.0 access token from PayPal using client credentials."""
    url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"

    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET


    if not client_id or not client_secret:
        raise PayPalError("PayPal credentials not configured (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET)")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            headers={"Accept": "application/json"},
            timeout=settings.PAYPAL_TIMEOUT_SECONDS,
        )


    if resp.status_code != 200:
        logger.error("PayPal auth failed: %s %s", resp.status_code, resp.text)
        raise PayPalError(f"PayPal authentication failed (HTTP {resp.status_code})")

    data = resp.json()
    return data["access_token"]


async def create_order(amount: float, description: str = "SAGA Golf Payment") -> str:
    """Create a PayPal order and return the order ID.

    The order is created with intent=CAPTURE so it can be captured after
    buyer approval.
    """
    token = await _get_access_token()
    url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}",
                },
                "description": description,
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    logger.info("[PayPal] Creating order: amount=$%.2f description=%s", amount, description)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.PAYPAL_TIMEOUT_SECONDS,
        )

    if resp.status_code not in (200, 201):
        logger.error("PayPal create order failed: %s %s", resp.status_code, resp.text)
        raise PayPalError(f"Failed to create PayPal order (HTTP {resp.status_code})")

    data = resp.json()
    order_id = data["id"]
    logger.info("[PayPal] Order created: %s", order_id)
    return order_id


async def capture_order(order_id: str) -> PayPalCaptureResult:
    """Capture a previously approved PayPal order.

    Returns a PayPalCaptureResult with the capture details.
    Raises PayPalCaptureDeclined if the capture was not completed.
    """
    token = await _get_access_token()
    url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    logger.info("[PayPal] Capturing order: %s", order_id)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={},
            headers=headers,
            timeout=settings.PAYPAL_TIMEOUT_SECONDS,
        )

    if resp.status_code not in (200, 201):
        logger.error("PayPal capture failed: %s %s", resp.status_code, resp.text)
        raise PayPalError(f"PayPal capture failed (HTTP {resp.status_code})")

    data = resp.json()
    order_status = data.get("status", "UNKNOWN")

    # Extract capture details from the response
    payer_email = None
    capture_id = None
    amount = None

    payer = data.get("payer", {})
    payer_email = payer.get("email_address")

    purchase_units = data.get("purchase_units", [])
    if purchase_units:
        captures = purchase_units[0].get("payments", {}).get("captures", [])
        if captures:
            capture_id = captures[0].get("id")
            amount = captures[0].get("amount", {}).get("value")

    result = PayPalCaptureResult(
        order_id=order_id,
        status=order_status,
        payer_email=payer_email,
        capture_id=capture_id,
        amount=amount,
    )

    if order_status != "COMPLETED":
        logger.warning("[PayPal] Order %s not completed: status=%s", order_id, order_status)
        raise PayPalCaptureDeclined(
            f"Payment was not completed. Status: {order_status}"
        )

    logger.info(
        "[PayPal] Order captured: order_id=%s capture_id=%s amount=%s payer=%s",
        order_id, capture_id, amount, payer_email,
    )
    return result
