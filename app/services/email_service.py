import smtplib
from email.message import EmailMessage
from typing import List

from app.core.config import settings


def send_email(subject: str, body: str, to: List[str]) -> bool:
    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.email_from):
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(to)
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return True



