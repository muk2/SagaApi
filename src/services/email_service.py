from __future__ import annotations

import logging

import resend

from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Transactional email service with SAGA branding via Resend."""

    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        try:
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            })
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s: %s", to_email, subject)
            return False

    # ── Shared HTML pieces ───────────────────────────────────────────────────

    @staticmethod
    def _header_html() -> str:
        return """
        <div style="text-align:center; padding:24px 0 16px 0; background-color:#1a472a;">
            <h1 style="margin:0; color:#ffffff; font-family:Georgia,serif; font-size:28px; letter-spacing:2px;">
                SAGA
            </h1>
            <p style="margin:6px 0 0 0; color:rgba(255,255,255,0.85); font-family:Arial,sans-serif; font-size:13px; letter-spacing:0.5px;">
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

    # ── Password Reset ────────────────────────────────────────────────────────

    def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset email."""
        inner = f"""
        <h2 style="color:#1a472a; margin:0 0 16px 0;">Password Reset</h2>
        <p style="color:#333;">You requested a password reset. Click the button below to set a new password:</p>
        <div style="text-align:center; margin:24px 0;">
            <a href="{reset_link}" style="display:inline-block; padding:12px 32px; background:#1a472a; color:#fff; text-decoration:none; border-radius:8px; font-weight:600;">
                Reset Password
            </a>
        </div>
        <p style="color:#666; font-size:13px;">This link expires in 1 hour. If you didn't request this, you can ignore this email.</p>
        """

        text_body = f"Click the link to reset your password: {reset_link}\n\nThis link expires in 1 hour."

        return self._send_email(
            to_email,
            "SAGA — Password Reset",
            text_body,
            self._wrap(inner),
        )

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
        """Send event registration confirmation with full price breakdown."""
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
            If you have any questions, reply to this email or contact us at sagaevents@sagagolf.com.
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
            If you have any questions, contact us at sagaevents@sagagolf.com.
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

