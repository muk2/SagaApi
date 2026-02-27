from __future__ import annotations

import logging
import smtplib
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.services.email_service import EmailService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SMTP_DEFAULTS = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": 587,
    "SMTP_USERNAME": "user@example.com",
    "SMTP_PASSWORD": "secret",
    "SMTP_FROM_NAME": "SAGA Golf",
    "SMTP_FROM_EMAIL": "noreply@sagagolf.com",
    "SMTP_TLS": True,
    "SMTP_SSL": False,
}


def _mock_settings(**overrides):
    """Return a mock settings object with sensible SMTP defaults."""
    values = {**_SMTP_DEFAULTS, **overrides}
    mock = MagicMock()
    for key, value in values.items():
        setattr(mock, key, value)
    return mock


def _patch_settings(**overrides):
    """Return a patch context manager that replaces settings with a mock."""
    return patch("src.services.email_service.settings", new=_mock_settings(**overrides))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

import pytest

@pytest.fixture
def email_service() -> EmailService:
    """Provide a fresh EmailService instance for each test."""
    return EmailService()


# ---------------------------------------------------------------------------
# Event registration receipt tests
# ---------------------------------------------------------------------------


class TestSendEventRegistrationReceipt:
    """Tests for EmailService.send_event_registration_receipt."""

    @patch("src.services.email_service.smtplib")
    def test_sends_correct_email(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            result = email_service.send_event_registration_receipt(
                to_email="golfer@example.com",
                event_name="Spring Open",
                event_date="2026-04-15",
                amount=Decimal("75.00"),
                card_last_four="4242",
                registration_id=101,
            )

        assert result is True
        mock_smtplib.SMTP.assert_called_once_with("smtp.example.com", 587)
        mock_server.login.assert_called_once_with("user@example.com", "secret")
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "golfer@example.com"
        assert "Spring Open" in sent_msg["Subject"]

    @patch("src.services.email_service.smtplib")
    def test_email_content_contains_all_fields(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            email_service.send_event_registration_receipt(
                to_email="golfer@example.com",
                event_name="Spring Open",
                event_date="2026-04-15",
                amount=Decimal("75.00"),
                card_last_four="4242",
                registration_id=101,
            )

        sent_msg = mock_server.send_message.call_args[0][0]
        # The MIMEMultipart message has payloads: plain text part and html part
        payloads = sent_msg.get_payload()
        text_body = payloads[0].get_payload(decode=True).decode()
        html_body = payloads[1].get_payload(decode=True).decode()

        for body in (text_body, html_body):
            assert "Spring Open" in body
            assert "2026-04-15" in body
            assert "$75.00" in body
            assert "4242" in body

        # Registration ID in both bodies
        assert "101" in text_body
        assert "101" in html_body

    @patch("src.services.email_service.smtplib")
    def test_amount_formatting_two_decimals(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            email_service.send_event_registration_receipt(
                to_email="golfer@example.com",
                event_name="Charity Cup",
                event_date="2026-06-01",
                amount=Decimal("100"),
                card_last_four="1234",
                registration_id=200,
            )

        sent_msg = mock_server.send_message.call_args[0][0]
        text_body = sent_msg.get_payload()[0].get_payload()
        assert "$100.00" in text_body

    @patch("src.services.email_service.smtplib")
    def test_smtp_failure_returns_false_and_logs(
        self, mock_smtplib, email_service: EmailService, caplog
    ):
        mock_smtplib.SMTP.side_effect = ConnectionRefusedError("Connection refused")

        with (
            _patch_settings(),
            caplog.at_level(logging.ERROR, logger="src.services.email_service"),
        ):
            result = email_service.send_event_registration_receipt(
                to_email="golfer@example.com",
                event_name="Fall Classic",
                event_date="2026-10-10",
                amount=Decimal("50.00"),
                card_last_four="9999",
                registration_id=300,
            )

        assert result is False
        assert "Failed to send email" in caplog.text


# ---------------------------------------------------------------------------
# Membership receipt tests
# ---------------------------------------------------------------------------


class TestSendMembershipReceipt:
    """Tests for EmailService.send_membership_receipt."""

    @patch("src.services.email_service.smtplib")
    def test_sends_correct_email(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            result = email_service.send_membership_receipt(
                to_email="member@example.com",
                tier_name="Gold",
                season_year=2026,
                amount=Decimal("250.00"),
                card_last_four="5678",
            )

        assert result is True
        mock_server.send_message.assert_called_once()

        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "member@example.com"
        assert "Membership Payment Confirmation" in sent_msg["Subject"]

    @patch("src.services.email_service.smtplib")
    def test_email_content_contains_all_fields(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            email_service.send_membership_receipt(
                to_email="member@example.com",
                tier_name="Gold",
                season_year=2026,
                amount=Decimal("250.00"),
                card_last_four="5678",
            )

        sent_msg = mock_server.send_message.call_args[0][0]
        payloads = sent_msg.get_payload()
        text_body = payloads[0].get_payload(decode=True).decode()
        html_body = payloads[1].get_payload(decode=True).decode()

        for body in (text_body, html_body):
            assert "Gold" in body
            assert "2026" in body
            assert "$250.00" in body
            assert "5678" in body

    @patch("src.services.email_service.smtplib")
    def test_amount_formatting_two_decimals(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings():
            email_service.send_membership_receipt(
                to_email="member@example.com",
                tier_name="Silver",
                season_year=2026,
                amount=Decimal("99.5"),
                card_last_four="0000",
            )

        sent_msg = mock_server.send_message.call_args[0][0]
        text_body = sent_msg.get_payload()[0].get_payload()
        assert "$99.50" in text_body

    @patch("src.services.email_service.smtplib")
    def test_smtp_failure_returns_false_and_logs(
        self, mock_smtplib, email_service: EmailService, caplog
    ):
        mock_smtplib.SMTP.side_effect = ConnectionRefusedError("Connection refused")

        with (
            _patch_settings(),
            caplog.at_level(logging.ERROR, logger="src.services.email_service"),
        ):
            result = email_service.send_membership_receipt(
                to_email="member@example.com",
                tier_name="Platinum",
                season_year=2026,
                amount=Decimal("500.00"),
                card_last_four="1111",
            )

        assert result is False
        assert "Failed to send email" in caplog.text


# ---------------------------------------------------------------------------
# SMTP SSL / TLS mode tests
# ---------------------------------------------------------------------------


class TestSmtpConnectionModes:
    """Verify SSL and TLS connection modes are handled correctly."""

    @patch("src.services.email_service.smtplib")
    def test_ssl_mode_uses_smtp_ssl(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP_SSL.return_value = mock_server

        with _patch_settings(SMTP_SSL=True, SMTP_TLS=False, SMTP_PORT=465):
            result = email_service.send_membership_receipt(
                to_email="ssl@example.com",
                tier_name="Gold",
                season_year=2026,
                amount=Decimal("100.00"),
                card_last_four="1234",
            )

        assert result is True
        mock_smtplib.SMTP_SSL.assert_called_once_with("smtp.example.com", 465)
        mock_smtplib.SMTP.assert_not_called()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("src.services.email_service.smtplib")
    def test_tls_mode_uses_starttls(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings(SMTP_SSL=False, SMTP_TLS=True):
            result = email_service.send_event_registration_receipt(
                to_email="tls@example.com",
                event_name="TLS Event",
                event_date="2026-05-01",
                amount=Decimal("25.00"),
                card_last_four="7777",
                registration_id=400,
            )

        assert result is True
        mock_smtplib.SMTP.assert_called_once_with("smtp.example.com", 587)
        mock_server.ehlo.assert_called()
        mock_server.starttls.assert_called_once()
        # ehlo is called twice: once before starttls and once after
        assert mock_server.ehlo.call_count == 2

    @patch("src.services.email_service.smtplib")
    def test_plain_mode_no_tls_no_ssl(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server

        with _patch_settings(SMTP_SSL=False, SMTP_TLS=False):
            result = email_service.send_membership_receipt(
                to_email="plain@example.com",
                tier_name="Bronze",
                season_year=2026,
                amount=Decimal("50.00"),
                card_last_four="3333",
            )

        assert result is True
        mock_smtplib.SMTP.assert_called_once()
        mock_server.ehlo.assert_called_once()
        mock_server.starttls.assert_not_called()


# ---------------------------------------------------------------------------
# Edge-case: exception never propagates
# ---------------------------------------------------------------------------


class TestExceptionNeverPropagates:
    """Email failures must NEVER raise exceptions to the caller."""

    @patch("src.services.email_service.smtplib")
    def test_login_failure_does_not_raise(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

        with _patch_settings():
            # Must not raise
            result = email_service.send_event_registration_receipt(
                to_email="test@example.com",
                event_name="Fail Test",
                event_date="2026-01-01",
                amount=Decimal("10.00"),
                card_last_four="0000",
                registration_id=999,
            )
        assert result is False

    @patch("src.services.email_service.smtplib")
    def test_send_message_failure_does_not_raise(self, mock_smtplib, email_service: EmailService):
        mock_server = MagicMock()
        mock_smtplib.SMTP.return_value = mock_server
        mock_server.send_message.side_effect = smtplib.SMTPException("Send failed")

        with _patch_settings():
            result = email_service.send_membership_receipt(
                to_email="test@example.com",
                tier_name="Gold",
                season_year=2026,
                amount=Decimal("100.00"),
                card_last_four="0000",
            )
        assert result is False
