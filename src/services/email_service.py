from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings

logger = logging.getLogger(__name__)

# SAGA logo hosted on the frontend's public directory
LOGO_URL = f"{settings.FRONTEND_URL}/sagalogo.png"


class EmailService:
    """Transactional email service with SAGA branding.

    Failures are logged but never raised — email should never block
    the payment response.
    """

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            if settings.SMTP_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.ehlo()
                if settings.SMTP_TLS:
                    server.starttls()
                    server.ehlo()

            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s: %s", to_email, subject)
            return False

    # ── Shared HTML pieces ───────────────────────────────────────────────────

    @staticmethod
    def _header_html() -> str:
        return f"""
        <div style="text-align:center; padding:24px 0 16px 0; background-color:#1a472a;">
            <img src="{LOGO_URL}" alt="SAGA" style="height:60px; margin-bottom:8px;" />
            <h1 style="margin:0; color:#ffffff; font-family:Georgia,serif; font-size:22px; letter-spacing:1px;">
                SAGA
            </h1>
            <p style="margin:4px 0 0 0; color:#0d94873b; font-family:Arial,sans-serif; font-size:12px;">
                South Asian Golf Association
            </p>
        </div>
        """

    @staticmethod
    def _footer_html() -> str:
        return """
        <div style="padding:16px 32px; background-color:#f8f8f8; text-align:center; color:#999; font-size:12px;">
            &copy; SAGA &mdash; South Asian Golf Association
        </div>
        """

    def _wrap(self, inner: str) -> str:
        return f"""
        <html>
        <body style="margin:0; padding:0; background-color:#f4f4f4; font-family:Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4; padding:20px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff; border-radius:8px; overflow:hidden;
                              box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <tr><td>{self._header_html()}</td></tr>
                    <tr><td style="padding:24px 32px 32px 32px;">{inner}</td></tr>
                    <tr><td>{self._footer_html()}</td></tr>
                </table>
            </td></tr>
            </table>
        </body>
        </html>
        """

    # ── Event Registration Confirmation ──────────────────────────────────────

    def send_event_registration_email(
        self,
        to_email: str,
        registrant_name: str,
        event_name: str,
        event_date: str,
        confirmation_id: str,
        base_price: float,
        additional_golfers: list[dict] | None = None,
        sponsor_amount: float | None = None,
        total: float = 0.0,
    ) -> bool:
        """Send event registration confirmation with full price breakdown.

        additional_golfers: list of {"name": str, "price": float}
        """
        # Build price breakdown rows
        rows_html = f"""
        <tr>
            <td style="padding:8px 0; border-bottom:1px solid #eee;">{registrant_name} (You)</td>
            <td style="padding:8px 0; border-bottom:1px solid #eee; text-align:right;">${base_price:.2f}</td>
        </tr>
        """
        rows_text = f"  {registrant_name} (You): ${base_price:.2f}\n"

        if additional_golfers:
            for g in additional_golfers:
                name = g.get("name", "Additional Golfer")
                price = g.get("price", 0)
                rows_html += f"""
                <tr>
                    <td style="padding:8px 0; border-bottom:1px solid #eee;">{name}</td>
                    <td style="padding:8px 0; border-bottom:1px solid #eee; text-align:right;">${price:.2f}</td>
                </tr>
                """
                rows_text += f"  {name}: ${price:.2f}\n"

        if sponsor_amount and sponsor_amount > 0:
            rows_html += f"""
            <tr>
                <td style="padding:8px 0; border-bottom:1px solid #eee;">Sponsorship</td>
                <td style="padding:8px 0; border-bottom:1px solid #eee; text-align:right;">${sponsor_amount:.2f}</td>
            </tr>
            """
            rows_text += f"  Sponsorship: ${sponsor_amount:.2f}\n"

        inner = f"""
        <h2 style="color:#1a472a; margin:0 0 16px 0;">Event Registration Confirmed</h2>
        <p style="color:#333;">Hi {registrant_name},</p>
        <p style="color:#333;">You are registered for the following event:</p>

        <table width="100%" style="margin:16px 0; border-collapse:collapse;">
            <tr>
                <td style="padding:10px 12px; background:#f0f7f0; font-weight:bold;">Event</td>
                <td style="padding:10px 12px; background:#f0f7f0; text-align:right;">{event_name}</td>
            </tr>
            <tr>
                <td style="padding:10px 12px; background:#f8f8f8;">Date</td>
                <td style="padding:10px 12px; background:#f8f8f8; text-align:right;">{event_date}</td>
            </tr>
            <tr>
                <td style="padding:10px 12px; background:#f0f7f0;">Confirmation #</td>
                <td style="padding:10px 12px; background:#f0f7f0; text-align:right;">{confirmation_id}</td>
            </tr>
        </table>

        <h3 style="color:#1a472a; margin:20px 0 8px 0;">Price Breakdown</h3>
        <table width="100%" style="border-collapse:collapse;">
            {rows_html}
            <tr>
                <td style="padding:10px 0; font-weight:bold; font-size:16px;">Total</td>
                <td style="padding:10px 0; font-weight:bold; font-size:16px; text-align:right; color:#1a472a;">${total:.2f}</td>
            </tr>
        </table>

        <p style="color:#666; margin-top:24px; font-size:13px;">
            If you have any questions, reply to this email or contact us at {settings.SMTP_FROM_EMAIL}.
        </p>
        """

        text_body = (
            f"Event Registration Confirmed\n\n"
            f"Hi {registrant_name},\n\n"
            f"Event: {event_name}\n"
            f"Date: {event_date}\n"
            f"Confirmation #: {confirmation_id}\n\n"
            f"Price Breakdown:\n{rows_text}"
            f"  Total: ${total:.2f}\n"
        )

        return self._send_email(
            to_email,
            f"SAGA Event Registration — {event_name}",
            text_body,
            self._wrap(inner),
        )

    # ── Membership Signup Confirmation ───────────────────────────────────────

    def send_membership_confirmation_email(
        self,
        to_email: str,
        member_name: str,
        membership_type: str,
        price: float,
    ) -> bool:
        """Send membership signup confirmation email."""
        inner = f"""
        <h2 style="color:#1a472a; margin:0 0 16px 0;">Welcome to SAGA!</h2>
        <p style="color:#333;">Hi {member_name},</p>
        <p style="color:#333;">Thank you for joining the South Asian Golf Association. Your membership is now active.</p>

        <table width="100%" style="margin:16px 0; border-collapse:collapse;">
            <tr>
                <td style="padding:10px 12px; background:#f0f7f0; font-weight:bold;">Membership</td>
                <td style="padding:10px 12px; background:#f0f7f0; text-align:right;">{membership_type}</td>
            </tr>
            <tr>
                <td style="padding:10px 12px; background:#f8f8f8; font-weight:bold;">Amount Paid</td>
                <td style="padding:10px 12px; background:#f8f8f8; text-align:right; color:#1a472a; font-weight:bold;">${price:.2f}</td>
            </tr>
        </table>

        <p style="color:#333;">You now have access to member pricing for all SAGA events. We look forward to seeing you on the course!</p>

        <p style="color:#666; margin-top:24px; font-size:13px;">
            If you have any questions, reply to this email or contact us at {settings.SMTP_FROM_EMAIL}.
        </p>
        """

        text_body = (
            f"Welcome to SAGA!\n\n"
            f"Hi {member_name},\n\n"
            f"Thank you for joining the South Asian Golf Association.\n\n"
            f"Membership: {membership_type}\n"
            f"Amount Paid: ${price:.2f}\n\n"
            f"You now have access to member pricing for all SAGA events.\n"
        )

        return self._send_email(
            to_email,
            "Welcome to SAGA — Membership Confirmed",
            text_body,
            self._wrap(inner),
        )
