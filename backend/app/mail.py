import json
import re
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from app.config import settings

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def mail_configured() -> bool:
    return bool(settings.resend_api_key.strip() or (settings.smtp_user.strip() and settings.smtp_password.strip()))


def _validate_email(value: str) -> str:
    email = value.strip()
    if not _EMAIL.fullmatch(email):
        raise ValueError("Please enter a valid email address.")
    return email


def _body(name: str, email: str, message: str) -> str:
    return (
        f"New message from your portfolio contact form.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"{message}\n"
    )


def _send_resend(name: str, email: str, subject: str, message: str) -> None:
    payload = {
        "from": settings.resend_from_email.strip() or "Portfolio <onboarding@resend.dev>",
        "to": [settings.contact_to_email.strip()],
        "subject": subject,
        "reply_to": email,
        "text": _body(name, email, message),
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key.strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 400:
                raise RuntimeError(f"Resend returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Resend could not send the email: {detail or exc}") from exc


def _send_smtp(name: str, email: str, subject: str, message: str) -> None:
    sender = settings.smtp_from.strip() or settings.smtp_user.strip()
    mail = EmailMessage()
    mail["Subject"] = subject
    mail["From"] = sender
    mail["To"] = settings.contact_to_email.strip()
    mail["Reply-To"] = email
    mail.set_content(_body(name, email, message))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user.strip(), settings.smtp_password.strip())
        smtp.send_message(mail)


def send_contact_email(*, name: str, email: str, subject: str, message: str) -> None:
    clean_name = name.strip()
    clean_email = _validate_email(email)
    clean_subject = subject.strip()
    clean_message = message.strip()
    if not clean_name or not clean_subject or not clean_message:
        raise ValueError("Name, subject, and message are required.")
    if not settings.contact_to_email.strip():
        raise RuntimeError("CONTACT_TO_EMAIL is not set.")
    if settings.resend_api_key.strip():
        _send_resend(clean_name, clean_email, clean_subject, clean_message)
        return
    if settings.smtp_user.strip() and settings.smtp_password.strip():
        _send_smtp(clean_name, clean_email, clean_subject, clean_message)
        return
    raise RuntimeError(
        "Email is not configured. Set RESEND_API_KEY or SMTP_USER and SMTP_PASSWORD in backend/.env."
    )
