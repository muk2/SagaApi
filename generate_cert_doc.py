"""
Generate North certification document from actual sandbox transaction logs.

Usage:
  1. Run test transactions through the app (charge, refund, void)
  2. The payment service saves real request/response pairs to north_transaction_log.json
  3. Run this script:  python3 generate_cert_doc.py
  4. Submit the generated Word doc to North
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

LOG_FILE = Path(__file__).parent / "north_transaction_log.json"
OUTPUT_FILE = Path(__file__).parent / "North_Certification_Samples.docx"

OPERATION_TITLES = {
    "auth": "Authentication — POST /auth",
    "charge": "Payment (Charge) — POST /mids/{mid}/gateways/payment",
    "refund": "Refund — POST /accounts/{accountId}/transactions",
    "void": "Void — POST /accounts/{accountId}/transactions",
}


def redact_sensitive(obj, keys_to_redact=("token", "password", "access_token")):
    """Redact sensitive values in a dict for the document."""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k.lower() in keys_to_redact and isinstance(v, str) and len(v) > 20:
                result[k] = v[:20] + "...[REDACTED]"
            else:
                result[k] = redact_sensitive(v, keys_to_redact)
        return result
    elif isinstance(obj, list):
        return [redact_sensitive(item, keys_to_redact) for item in obj]
    return obj


def add_code_block(doc, text):
    """Add a formatted code block paragraph."""
    p = doc.add_paragraph()
    p.style = doc.styles["Normal"]
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    return p


def build_document(log_entries):
    doc = Document()

    # Title
    title = doc.add_heading("North iFrame JS SDK — Certification Samples", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(
        "Merchant: SAGA Golf Events\n"
        "Integration Type: iFrame JavaScript SDK (PayNow)\n"
        "All samples below are from actual sandbox test transactions."
    )
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph()  # spacer

    # Group entries by operation, keep order of first appearance
    seen_ops = []
    grouped = {}
    for entry in log_entries:
        op = entry["operation"]
        if op not in grouped:
            grouped[op] = []
            seen_ops.append(op)
        grouped[op].append(entry)

    section_num = 1
    for op in seen_ops:
        entries = grouped[op]
        title_text = OPERATION_TITLES.get(op, op)
        doc.add_heading(f"{section_num}. {title_text}", level=2)

        for i, entry in enumerate(entries):
            req = entry["request"]
            resp = entry["response"]

            label = ""
            if op == "charge":
                # Determine if approved or declined from response
                resp_body = resp["body"]
                response_code = (resp_body.get("response_code") or resp_body.get("responseCode") or "").upper()
                approved_codes = {"0", "APR", "8", "10", "85"}
                response_text = (resp_body.get("responseText") or "").upper()
                is_approved = (
                    response_code in approved_codes
                    or response_text in ("APPROVAL", "APPROVED")
                    or resp_body.get("approved") is True
                )
                label = " (Approved)" if is_approved else " (Declined)"

            if len(entries) > 1:
                doc.add_heading(f"Sample {i + 1}{label} — {entry['timestamp'][:19]}Z", level=3)
            else:
                suffix = f"{label} — {entry['timestamp'][:19]}Z" if label else f" — {entry['timestamp'][:19]}Z"
                doc.add_heading(f"Transaction{suffix}", level=3)

            # Request
            doc.add_heading("Request", level=4)
            req_body = redact_sensitive(req["body"])
            headers_text = ""
            if req.get("headers"):
                for k, v in req["headers"].items():
                    headers_text += f"{k}: {v}\n"

            request_text = f"{req['method']} {req['url']}\n"
            if headers_text:
                request_text += headers_text
            request_text += f"\n{json.dumps(req_body, indent=4)}"
            add_code_block(doc, request_text)

            # Response
            status = resp["status_code"]
            status_label = "Success" if status in (200, 201) else f"Error {status}"
            doc.add_heading(f"Response (HTTP {status} — {status_label})", level=4)

            resp_body = redact_sensitive(resp["body"])
            add_code_block(doc, json.dumps(resp_body, indent=4))

        section_num += 1

    # Application overview
    doc.add_heading(f"{section_num}. Application Overview", level=2)
    doc.add_paragraph(
        "SAGA Golf Events uses the North iFrame JS SDK to securely collect card data "
        "on the frontend. Card numbers, CVV, and billing information are entered directly "
        "into North-hosted iFrame fields — sensitive card data never touches our server."
    )

    doc.add_heading("Payment Flow:", level=3)
    flow_steps = [
        "User enters card details into North PayNow iFrame fields on our payment form",
        "The PayNow SDK tokenizes the card client-side",
        "Our backend receives only the token and calls POST /auth to authenticate",
        "Our backend submits the token to POST /mids/{mid}/gateways/payment",
        "The response code is validated against North's documented response codes",
        "Registration is saved to our database upon approval",
    ]
    for step in flow_steps:
        doc.add_paragraph(step, style="List Number")

    doc.add_heading("Supported Card Types:", level=3)
    for card in ["Visa", "Mastercard", "American Express", "Discover"]:
        doc.add_paragraph(card, style="List Bullet")

    doc.add_heading("Response Code Handling:", level=3)
    doc.add_paragraph(
        "All response codes from North's Transaction Response Codes documentation are mapped "
        "to user-friendly messages in our backend, covering Visa, Mastercard, Discover, "
        "American Express, and ACH codes. Declined transactions display a clear message to "
        "the user and do not create a registration record."
    )

    return doc


def main():
    if not LOG_FILE.exists():
        print(f"No transaction log found at {LOG_FILE}")
        print("Run test transactions through the app first, then re-run this script.")
        sys.exit(1)

    log_entries = json.loads(LOG_FILE.read_text())
    if not log_entries:
        print("Transaction log is empty. Run some test transactions first.")
        sys.exit(1)

    print(f"Found {len(log_entries)} logged transaction(s):")
    for entry in log_entries:
        print(f"  - {entry['operation']} at {entry['timestamp']} (HTTP {entry['response']['status_code']})")

    doc = build_document(log_entries)
    doc.save(str(OUTPUT_FILE))
    print(f"\nCertification document saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
