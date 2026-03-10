from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

router = APIRouter(prefix="/api/contact", tags=["Contact"])

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    captcha_token: str


async def verify_recaptcha(token: str) -> bool:
    """Verify reCAPTCHA token with Google."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            RECAPTCHA_VERIFY_URL,
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": token,
            },
        )
        result = response.json()
        return result.get("success", False)


@router.post("/")
async def send_contact_email(data: ContactRequest):
    """Send contact form email to SAGA email address."""

    # Verify reCAPTCHA first
    captcha_valid = await verify_recaptcha(data.captcha_token)
    if not captcha_valid:
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed. Please try again.")

    try:
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587
        SENDER_EMAIL = settings.SMTP_USERNAME
        SENDER_PASSWORD = settings.SMTP_PASSWORD
        RECIPIENT_EMAIL = "sagagolfevents@gmail.com"

        if not SENDER_PASSWORD:
            raise HTTPException(
                status_code=500,
                detail="Email service not configured. Please contact administrator."
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Contact Form: {data.subject}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = data.email

        text_content = f"""
New Contact Form Submission

From: {data.name}
Email: {data.email}
Subject: {data.subject}

Message:
{data.message}
"""

        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; border-radius: 8px;">
        <h2 style="color: #0d9488; border-bottom: 2px solid #0d9488; padding-bottom: 10px;">
            New Contact Form Submission
        </h2>
        <div style="background: white; padding: 20px; border-radius: 6px; margin-top: 20px;">
            <p><strong>From:</strong> {data.name}</p>
            <p><strong>Email:</strong> <a href="mailto:{data.email}">{data.email}</a></p>
            <p><strong>Subject:</strong> {data.subject}</p>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p><strong>Message:</strong></p>
                <p style="white-space: pre-wrap;">{data.message}</p>
            </div>
        </div>
        <p style="margin-top: 20px; font-size: 0.875rem; color: #6b7280;">
            This email was sent from the SAGA Golf Events contact form.
        </p>
    </div>
</body>
</html>
"""

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return {"success": True, "message": "Email sent successfully"}

    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")