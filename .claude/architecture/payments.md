# Payments Architecture – North / Paygrid API

This project uses the North (Paygrid) API as the primary payment processor.

Payments are business-critical.
Correctness, traceability, and reconciliation matter more than speed.

---

## Payment Philosophy (High Level)

Payments are treated as:
- **External events**
- **Asynchronous by nature**
- **Potentially unreliable**

The system must assume:
- Payment requests can fail
- Callbacks/webhooks may arrive late or multiple times
- External references are the source of truth for reconciliation

Never assume a single request = successful payment.

---

## Payment Flow (Conceptual)

1. A user registers for an event
2. A registration record is created with `payment_status = pending`
3. A payment request is initiated via North / Paygrid
4. The system records:
   - Intended amount
   - Payment method
   - External reference (from Paygrid)
5. Payment completion is confirmed asynchronously
6. Registration payment status is updated only after verification

At no point should the system mark a registration as paid
without confirmation from Paygrid.

---

## Mapping to Database Tables

### `payment_method`
Represents allowed methods:
- North / Paygrid
- Zelle
- Admin/manual methods

This allows future expansion without schema changes.

---

### `payment`
Represents a single payment record.

Important fields:
- `registration_id`: what the payment is for
- `method_id`: how it was paid
- `amount`: amount expected/received
- `status`: pending, completed, failed, refunded
- `external_reference`: Paygrid transaction or reference ID
- `marked_paid_by_admin`: manual override flag

Payments are append-only.
Never overwrite historical records.

---

### `event_registration.payment_status`

This is a **derived business state**, not a payment record.

Examples:
- `pending`
- `paid`
- `failed`
- `refunded`

This field summarizes payment outcome but should always be
backed by one or more `payment` records.

---

## External API Considerations (North / Paygrid)

When integrating Paygrid:
- Treat Paygrid as the source of truth for transaction state
- Store all returned identifiers
- Expect retries and duplicate callbacks
- Design idempotent handlers

Never rely on client-side confirmation alone.

---

## Error & Failure Handling

The system must handle:
- Payment created but callback never arrives
- Callback arrives twice
- User closes browser mid-payment
- Admin manually marks payment as completed

In all cases:
- Data integrity must be preserved
- Actions must be auditable
- No silent state changes

---

## Admin Interventions

Admins may:
- Mark payments as paid (e.g. cash, check, Zelle)
- Correct failed or external payments

Admin actions should:
- Set explicit flags
- Leave payment history intact
- Be explainable later

---

## Tradeoffs & Design Choices

### Why not embed payment logic deeply into registrations?
- Payments are external and unreliable
- Separation improves auditability
- Allows multiple payment attempts

### Why allow manual overrides?
- Non-profits often accept offline payments
- Real-world flexibility is required

---

## Guidance for API Design

When exposing payment endpoints:
- Never expose raw payment internals to the frontend
- Return clear, business-level statuses
- Log all external interactions

Always explain payment behavior in plain language.