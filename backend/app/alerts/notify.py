import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.db.session import settings
from app.models.orm import Alert

logger = logging.getLogger(__name__)


def _subject(alert: Alert) -> str:
    return f"[ALERTA] {alert.gas_type} sustentado acima do limite — sensor {alert.sensor_id}"


def _body(alert: Alert) -> str:
    return (
        f"Sensor: {alert.sensor_id}\n"
        f"Gas: {alert.gas_type}\n"
        f"Concentracao maxima na janela: {alert.max_ppm} ppm\n"
        f"Inicio do alerta: {alert.started_at.isoformat()}\n"
    )


def send_email_alert(alert: Alert) -> None:
    msg = EmailMessage()
    msg["Subject"] = _subject(alert)
    msg["From"] = settings.alert_email_from
    msg["To"] = settings.alert_email_to
    msg.set_content(_body(alert))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def send_webhook_alert(alert: Alert) -> bool:
    """Retorna False (sem tentar enviar) se nenhuma URL de webhook estiver
    configurada — isso não é uma falha, o webhook é opcional."""
    if not settings.alert_webhook_url:
        return False

    payload = {
        "device_id": alert.sensor_id,
        "gas_type": alert.gas_type,
        "value_ppm": alert.max_ppm,
        "timestamp": alert.started_at.isoformat(),
    }
    response = httpx.post(settings.alert_webhook_url, json=payload, timeout=5)
    response.raise_for_status()
    return True


def notify_alert(alert: Alert) -> bool:
    """Envia notificações para um alerta recém aberto: e-mail sempre,
    webhook se configurado. Nunca propaga exceção — uma falha de
    notificação não pode derrubar a ingestão. Retorna True se pelo menos um
    canal entregou com sucesso (usado para decidir se `notified_at` é
    marcado).
    """
    delivered = False

    try:
        send_email_alert(alert)
        delivered = True
    except Exception:
        logger.exception("falha ao enviar e-mail de alerta (sensor=%s)", alert.sensor_id)

    try:
        if send_webhook_alert(alert):
            delivered = True
    except Exception:
        logger.exception("falha ao enviar webhook de alerta (sensor=%s)", alert.sensor_id)

    return delivered
