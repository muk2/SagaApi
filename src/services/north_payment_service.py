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
NORTH_APPSOURCE  = os.getenv("NORTH_APPSOURCE_HEADER", "")
NORTH_TIMEOUT    = int(os.getenv("NORTH_TIMEOUT", "30"))


# ── Response code mapping (from North developer docs) ─────────────────────────
# Codes that indicate an approved transaction
APPROVED_CODES = {"0", "APR", "8", "10", "85"}

# User-friendly messages for decline/error codes (unified across Visa, MC, Discover, Amex, ACH)
RESPONSE_CODE_MESSAGES = {
    # Approved
    "0":   "Approved",
    "APR": "Approved",
    "8":   "Approved (honor with ID)",
    "10":  "Partial approval",
    "85":  "Not declined",
    # Call / Refer
    "1":   "Please contact your card issuer",
    "2":   "Please contact your card issuer",
    "34":  "Please contact your card issuer",
    "59":  "Suspected fraud — please contact your card issuer",
    "70":  "Please contact your card issuer",
    "94":  "Duplicate transaction detected",
    # Terminal / Merchant errors
    "3":   "Invalid merchant configuration",
    "E7":  "Terminal ID error",
    # Pick up card
    "4":   "Card restricted — please contact your card issuer",
    "7":   "Card restricted — please contact your card issuer",
    "41":  "Card reported lost — please contact your card issuer",
    "43":  "Card reported stolen — please contact your card issuer",
    # Decline
    "5":   "Your card was declined. Please try a different card",
    "DCL": "Your card was declined. Please try a different card",
    "ST":  "Payment verification failed. Please try again",
    "N0":  "Your card was declined",
    "N6":  "Your card was declined",
    "93":  "Transaction cannot be completed",
    "100": "Your card was declined",
    # Error
    "6":   "A processing error occurred. Please try again",
    "96":  "System error. Please try again later",
    "RR":  "A processing error occurred. Please try again",
    # Invalid transaction
    "12":  "Invalid transaction",
    "EF":  "Transaction type not allowed",
    # Amount
    "13":  "Invalid amount",
    # Card number
    "14":  "Invalid card number. Please check and try again",
    # Issuer
    "15":  "Card issuer not recognized",
    # Re-enter
    "19":  "Please re-enter your card details and try again",
    # No action
    "21":  "No action taken. Please try again",
    # Unable to locate
    "25":  "Unable to locate record",
    # No reply
    "28":  "Card issuer temporarily unavailable. Please try again later",
    "91":  "Card issuer unavailable. Please try again later",
    "E9":  "Network unavailable. Please try again later",
    "EQ":  "Payment gateway unavailable. Please try again later",
    # Format
    "30":  "A processing error occurred. Please try again",
    "EW":  "A processing error occurred. Please try again",
    # No credit account
    "39":  "No credit account associated with this card",
    # Closed account
    "46":  "This account is closed",
    # Insufficient funds
    "51":  "Insufficient funds. Please try a different card",
    "116": "Insufficient funds. Please try a different card",
    # No checking/savings
    "52":  "No checking account found",
    "53":  "No savings account found",
    # Expired card
    "54":  "Your card is expired. Please use a different card",
    "33":  "Your card is expired",
    "101": "Your card is expired",
    "125": "Invalid effective date",
    # Wrong PIN
    "55":  "Incorrect PIN",
    "75":  "PIN entry tries exceeded",
    "117": "Invalid PIN",
    # Transaction not permitted
    "57":  "This transaction type is not permitted for your card",
    "58":  "This transaction type is not permitted at this terminal",
    "E4":  "Service not allowed",
    "E5":  "Service not allowed",
    "E6":  "Service not allowed",
    "EK":  "Service not allowed",
    # Exceeds limits
    "61":  "Transaction exceeds your card's amount limit",
    "65":  "Transaction exceeds your card's activity limit",
    "121": "Limit exceeded",
    # Restricted card
    "62":  "Restricted card — not valid in this region",
    "EE":  "Card product blocked",
    "78":  "Card blocked by cardholder",
    # Security
    "63":  "Security violation",
    "Q1":  "Card authentication failed",
    "1A":  "Additional authentication required",
    # CVV errors
    "82":  "Incorrect CVV. Please check and try again",
    "N7":  "CVV verification failed",
    "EO":  "CVV mismatch",
    "E3":  "CVV data required",
    # AVS
    "E2":  "Address verification data required",
    # PIN verification
    "83":  "Unable to verify PIN",
    "86":  "Unable to verify PIN",
    "S4":  "PIN processing error",
    # Verification data
    "6P":  "Verification data failed",
    "EL":  "Storage verification failed. Please try again",
    # No card record
    "56":  "No card record found",
    "119": "No card record found",
    # Routing
    "92":  "Unable to route transaction",
    "NR":  "No valid debit network available",
    # Duplicate
    "EV":  "Transaction already captured",
    # Format errors
    "EA":  "Account length error",
    "EB":  "Check digit error",
    "EC":  "CID format error",
    "ED":  "Authorization has expired",
    "EH":  "Invalid card entry method",
    "EI":  "Invalid card ID",
    "ET":  "EMV data required",
    "EX":  "Check number required",
    "EY":  "Please insert your card (contactless not allowed)",
    # Fraud / lifecycle declines
    "ES":  "Transaction not allowed",
    "SA":  "New account information available — contact your card issuer",
    "SB":  "Cannot approve at this time. Please try again later",
    "SC":  "Do not try again",
    "SM":  "Fraud/security concern — contact your card issuer",
    "SN":  "Cannot approve at this time. Please try again later",
    "SO":  "Do not try again",
    # Amex specific
    "109": "Invalid merchant",
    "110": "Invalid amount",
    "111": "Invalid account",
    "115": "Service not permitted",
    "181": "Format error",
    "183": "Invalid currency code",
    "187": "New card issued — please use your new card",
    "189": "Merchant account closed",
    "200": "Card restricted",
    "900": "System error",
    "909": "System malfunction",
    "912": "Issuer not available. Please try again later",
}


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

    print(f"[NORTH DEBUG] base_url={NORTH_BASE_URL}")
    print(f"[NORTH DEBUG] mid={NORTH_MID}")
    print(f"[NORTH DEBUG] dev_key={NORTH_DEV_KEY}")
    print(f"[NORTH DEBUG] password={NORTH_PASSWORD}")
    print(f"[NORTH DEBUG] password length={len(NORTH_PASSWORD)}")
    print(f"[NORTH DEBUG] appsource={NORTH_APPSOURCE}")

    headers = {"Content-Type": "application/json"}
    if NORTH_APPSOURCE:
        headers["x-nabwss-appsource"] = NORTH_APPSOURCE

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/auth",
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException:
        raise NorthGatewayError("Payment gateway timed out during authentication.")
    except httpx.RequestError as exc:
        raise NorthGatewayError(f"Could not reach payment gateway: {exc}")

    print(f"[NORTH DEBUG] auth response: status={resp.status_code} body={resp.text[:300]}")

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

    charge_headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {jwt}",
    }
    if NORTH_APPSOURCE:
        charge_headers["x-nabwss-appsource"] = NORTH_APPSOURCE

    try:
        async with httpx.AsyncClient(timeout=NORTH_TIMEOUT) as client:
            resp = await client.post(
                f"{NORTH_BASE_URL}/mids/{NORTH_MID}/gateways/payment",
                json=payload,
                headers=charge_headers,
            )
    except httpx.TimeoutException:
        raise NorthGatewayError("Payment timed out. Please try again.")
    except httpx.RequestError as exc:
        raise NorthGatewayError(f"Could not reach payment gateway: {exc}")

    print(f"[NORTH DEBUG] charge response: status={resp.status_code} body={resp.text[:500]}")

    data = resp.json()

    if resp.status_code == 401:
        raise NorthGatewayError("Payment gateway session expired. Please try again.")

    if resp.status_code not in (200, 201):
        message = data.get("message") or data.get("detail") or "Payment failed."
        logger.error("North charge failed: status=%s body=%.200s", resp.status_code, str(data))
        raise NorthGatewayError(message)

    # Parse transaction identifier from response
    uniq_id        = data.get("uniq_id") or data.get("transactionUniqueId") or data.get("token") or ""
    transaction_id = uniq_id.replace("ccs_", "") if uniq_id else None

    # Extract the response code — North may return it in different fields
    response_code = (
        data.get("response_code")
        or data.get("responseCode")
        or ""
    ).upper()
    response_text = (data.get("responseText") or "").upper()
    card_last_four = data.get("card_last_four") or data.get("lastFour") or None

    # Determine approval: check response_code against known approved codes,
    # fall back to responseText keywords, then the explicit "approved" flag
    approved = (
        response_code in APPROVED_CODES
        or response_text in ("APPROVAL", "APPROVED", "PARTIAL APPROVED", "HONOR WITH ID", "NOT DECLINED")
        or data.get("approved") is True
    )

    # Get a user-friendly decline message from the response code mapping
    decline_message = None
    if not approved:
        decline_message = (
            RESPONSE_CODE_MESSAGES.get(response_code)
            or RESPONSE_CODE_MESSAGES.get(response_text)
            or response_text
            or "Your card was declined. Please try a different card."
        )

    result = NorthChargeResult(
        approved=approved,
        transaction_id=transaction_id,
        uniq_id=uniq_id,
        account_id=account_id,
        response_text=response_code or response_text,
        card_last_four=card_last_four,
        decline_reason=decline_message,
        raw_response=data,
    )

    if not approved:
        logger.warning(
            "North charge declined: response_code=%s response_text=%s transaction_id=%s",
            response_code, response_text, transaction_id,
        )
        raise NorthDeclinedError(decline_message, result=result)

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