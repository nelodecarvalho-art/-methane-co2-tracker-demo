import smtplib
from email.message import EmailMessage

import httpx

from app.db.session import settings

RESEND_API_URL = "https://api.resend.com/emails"


def send_email(subject: str, body: str) -> None:
    """Ponto único de envio de e-mail pra alertas/anomalia. Usa a API HTTP
    do Resend quando `use_resend_http_api` está ligado (produção); cai para
    SMTP puro (Mailpit local, sem TLS/auth) quando não está — ver o
    comentário em `Settings.use_resend_http_api`.
    """
    if settings.use_resend_http_api:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {settings.smtp_password}"},
            json={
                "from": settings.alert_email_from,
                "to": [settings.alert_email_to],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
        response.raise_for_status()
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.alert_email_from
    msg["To"] = settings.alert_email_to
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
