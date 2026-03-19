"""PayPal order endpoints — create orders for the frontend PayPal SDK."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.paypal_service import PayPalError, create_order

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/paypal", tags=["PayPal"])


class CreateOrderRequest(BaseModel):
    amount: float
    description: str = "SAGA Golf Payment"


class CreateOrderResponse(BaseModel):
    id: str


@router.post("/create-order", response_model=CreateOrderResponse)
async def paypal_create_order(data: CreateOrderRequest) -> CreateOrderResponse:
    """Create a PayPal order. Returns the order ID for the frontend SDK."""
    if data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero.",
        )
    try:
        order_id = await create_order(data.amount, data.description)
        return CreateOrderResponse(id=order_id)
    except PayPalError as exc:
        logger.error("PayPal create-order failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
