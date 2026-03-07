"""
North Payment Service
Uses the North iFrame JS SDK API spec:
  POST /auth                                  → obtain JWT
  POST /mids/{mid}/gateways/payment           → charge a tokenized card
  POST /accounts/{accountId}/transactions     → refund or void

Required environment variables:
  NORTH_MID                — Merchant ID (e.g. "9999999999999")
  NORTH_DEVELOPER_KEY      — Developer key
  NORTH_PASSWORD           — API password
  NORTH_GATEWAY_PUBLIC_KEY — Gateway public key
  NORTH_BASE_URL           — https://proxy.payanywhere.dev (sandbox)
                             https://proxy.payanywhere.com (production)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)

NORTH_BASE_URL   = os.getenv("NORTH_BASE_URL", "https://proxy.payanywhere.dev").rstrip("/")
NORTH_MID        = os.getenv("NORTH_MID", "")
NORTH_DEV_KEY    = os.getenv("NORTH_DEVELOPER_KEY", "")
NORTH_PASSWORD   = os.getenv("NORTH_PASSWORD", "")
NORTH_GATEWAY_PK = os.getenv("NORTH_GATEWAY_PUBLIC_KEY", "")
NORTH_TIMEOUT    = int(os.getenv("NORTH_TIMEOUT", "30"))


# ── Result dataclasses ──────────────────────────────────────────────────────────

@dataclass
class NorthChargeResult:
    approved:       bool
    transaction_id: str | None        # numeric portion of uniq_id (strip "ccs_" prefix)
    uniq_id:        str | None        # raw uniq_id as returned by North
    account_id:     str | None        # from auth — needed to perform refunds/voids
    response_text:  str | None        # e.g. "APPROVAL"
    card_last_four: str | None
    decline_reason: str | None
    raw_response:   dict = field(default_factory=dict)


@dataclass
class NorthRefundResult:
    approved:       bool
    transaction_id: str | None
    raw_response:   dict = field(default_factory=dict)


@dataclass
class NorthVoidResult:
    approved:       bool
    transaction_id: str | None
    raw_response:   dict = field(default_factory=dict)


# ── Custom exceptions ───────────────────────────────────────────────────────────

class NorthGatewayError(Exception):
    """Raised when the North gateway is unreachable or returns an unexpected error."""
    pass


class NorthDeclinedError(Exception):
    """Raised when the card is explicitly declined."""
    def __init__(self, message: str, result: NorthChargeResult | None = None):
        super().__init__(message)
        self.result = result


# ── Internal: authenticate ──────────────────────────────────────────────────────

async def _authenticate() -> tuple[str, str]:
    """
    POST /auth  →  returns (jwt_token, account_id).
    account_id is required when submitting refunds and voids.
    """
    if not all([NORTH_MID, NORTH_DEV_KEY, NORTH_PASSWORD]):
        raise NorthGatewayError(
            "Payment gateway credentials are not configured. "
            "Set NORTH_MID, NORTH_DEVELOPER_KEY, and NORTH_PASSWORD."
        )

    payload = {
        "mid":          NORTH_MID,
        "developerKey": NORTH_DEV_KEY,
        "password":     NORTH_PASSWORD,
    }

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/auth",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
    except httpx.TimeoutException:
        raise NorthGatewayError("Payment gateway timed out during authentication.")
    except httpx.RequestError as exc:
        raise NorthGatewayError(f"Could not reach payment gateway: {exc}")

    if resp.status_code not in (200, 201):
        logger.error(
            "North auth failed: status=%s body=%.200s",
            resp.status_code, resp.text,
        )
        raise NorthGatewayError("Payment gateway authentication failed. Check credentials.")

    data       = resp.json()
    token      = data.get("token") or data.get("access_token")
    account_id = (
        data.get("accountId")
        or data.get("account_id")
        or data.get("merchantAccountId")
        or ""
    )

    if not token:
        raise NorthGatewayError("Payment gateway returned no auth token.")

    return token, account_id


# ── Charge ──────────────────────────────────────────────────────────────────────

async def charge_card(payment_token: str, amount: float | Decimal) -> NorthChargeResult:
    """
    Charge a card that has been tokenized by the North Collect.js SDK on the frontend.

    Args:
        payment_token: Token string returned by CollectJS callback on the client.
        amount:        Total charge amount, e.g. 75.0

    Returns:
        NorthChargeResult with transaction details.

    Raises:
        NorthDeclinedError  — card was declined
        NorthGatewayError   — network / gateway failure
    """
    jwt, account_id = await _authenticate()

    payload = {
        "token":              payment_token,
        "amount":             f"{float(amount):.2f}",
        "gateway_public_key": NORTH_GATEWAY_PK,
        "transaction_source": "PA-JS-SDK",
    }

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/mids/{NORTH_MID}/gateways/payment",
                json=payload,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {jwt}",
                },
            )
    except httpx.TimeoutException:
        raise NorthGatewayError("Payment timed out. Please try again.")
    except httpx.RequestError as exc:
        raise NorthGatewayError(f"Could not reach payment gateway: {exc}")

    data = resp.json()

    if resp.status_code == 401:
        raise NorthGatewayError("Payment gateway session expired. Please try again.")

    if resp.status_code not in (200, 201):
        message = data.get("message") or data.get("detail") or "Payment failed."
        logger.error("North charge failed: status=%s body=%.200s", resp.status_code, str(data))
        raise NorthGatewayError(message)

    # Parse uniq_id → numeric transaction_id  (format: "ccs_87654321")
    uniq_id        = data.get("uniq_id") or data.get("transactionUniqueId") or ""
    transaction_id = uniq_id.replace("ccs_", "") if uniq_id else None

    response_text  = (data.get("responseText") or "").upper()
    card_last_four = data.get("card_last_four") or data.get("lastFour") or None

    # North may return HTTP 201 with a decline embedded in the body
    approved = response_text in ("APPROVAL", "APPROVED") or data.get("approved") is True

    result = NorthChargeResult(
        approved=approved,
        transaction_id=transaction_id,
        uniq_id=uniq_id,
        account_id=account_id,
        response_text=response_text,
        card_last_four=card_last_four,
        decline_reason=None if approved else (data.get("responseText") or "Declined"),
        raw_response=data,
    )

    if not approved:
        logger.warning(
            "North charge declined: response_text=%s transaction_id=%s",
            response_text, transaction_id,
        )
        raise NorthDeclinedError(
            result.decline_reason or "Your card was declined. Please try a different card.",
            result=result,
        )

    logger.info(
        "North charge approved: transaction_id=%s amount=%s last4=%s",
        transaction_id, amount, card_last_four,
    )
    return result


# ── Refund ──────────────────────────────────────────────────────────────────────

async def refund_transaction(
    account_id:     str,
    transaction_id: int | str,
    amount:         float | Decimal,
    username:       str,
) -> NorthRefundResult:
    """
    Refund a settled transaction (partial or full).

    Args:
        account_id:     Stored from the original charge's auth response.
        transaction_id: Numeric ID — uniq_id with the "ccs_" prefix stripped.
        amount:         Amount to refund.
        username:       Admin email performing the refund (required by North).
    """
    jwt, _ = await _authenticate()

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/accounts/{account_id}/transactions",
                json={
                    "type":               "refund",
                    "ccs_pk":             int(transaction_id),
                    "amount":             f"{float(amount):.2f}",
                    "username":           username,
                    "transaction_source": "PA-JS-SDK",
                },
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {jwt}",
                },
            )
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise NorthGatewayError(f"Refund request failed: {exc}")

    data     = resp.json()
    approved = resp.status_code in (200, 201)
    logger.info("North refund: approved=%s transaction_id=%s amount=%s", approved, transaction_id, amount)

    if not approved:
        raise NorthGatewayError(data.get("message") or "Refund failed.")

    return NorthRefundResult(
        approved=approved,
        transaction_id=str(transaction_id),
        raw_response=data,
    )


# ── Void ────────────────────────────────────────────────────────────────────────

async def void_transaction(
    account_id:     str,
    transaction_id: int | str,
    username:       str,
) -> NorthVoidResult:
    """
    Void an unsettled (same-day) transaction.

    Args:
        account_id:     Stored from the original charge's auth response.
        transaction_id: Numeric ID — uniq_id with the "ccs_" prefix stripped.
        username:       Admin email performing the void.
    """
    jwt, _ = await _authenticate()

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/accounts/{account_id}/transactions",
                json={
                    "type":               "void",
                    "transaction_id":     int(transaction_id),
                    "username":           username,
                    "transaction_source": "PA-JS-SDK",
                },
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {jwt}",
                },
            )
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise NorthGatewayError(f"Void request failed: {exc}")

    data     = resp.json()
    approved = resp.status_code in (200, 201)
    logger.info("North void: approved=%s transaction_id=%s", approved, transaction_id)

    if not approved:
        raise NorthGatewayError(data.get("message") or "Void failed.")

    return NorthVoidResult(
        approved=approved,
        transaction_id=str(transaction_id),
        raw_response=data,
    )