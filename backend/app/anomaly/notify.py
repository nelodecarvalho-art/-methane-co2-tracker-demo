import logging

import httpx

from app.db.session import settings
from app.email_sender import send_email
from app.models.orm import Reading

logger = logging.getLogger(__name__)


def _subject(reading: Reading) -> str:
    return f"[ANOMALIA] leitura fora do padrão — sensor {reading.sensor_id} ({reading.gas_type})"


def _body(reading: Reading) -> str:
    return (
        f"Sensor: {reading.sensor_id}\n"
        f"Gas: {reading.gas_type}\n"
        f"Concentracao: {reading.concentration_ppm} ppm\n"
        f"Temperatura: {reading.temperature_c} C\n"
        f"Bateria: {reading.battery_pct}%\n"
        f"Horario: {reading.time.isoformat()}\n\n"
        "Esta leitura foi sinalizada pelo detector de anomalia (Isolation "
        "Forest) por fugir do padrao historico deste sensor. Isto NAO e um "
        "alerta de seguranca (que segue a regra de limiar sustentado) -- e "
        "um aviso de possivel desvio de comportamento do sensor ou do "
        "processo monitorado, para investigacao."
    )


def send_email_anomaly(reading: Reading) -> None:
    send_email(_subject(reading), _body(reading))


def send_webhook_anomaly(reading: Reading) -> bool:
    """Retorna False (sem tentar enviar) se nenhuma URL de webhook estiver
    configurada — isso não é uma falha, o webhook é opcional. Separado do
    webhook de alerta de segurança (settings.alert_webhook_url)."""
    if not settings.anomaly_webhook_url:
        return False

    payload = {
        "device_id": reading.sensor_id,
        "gas_type": reading.gas_type,
        "value_ppm": reading.concentration_ppm,
        "temperature_c": reading.temperature_c,
        "battery_pct": reading.battery_pct,
        "timestamp": reading.time.isoformat(),
        "type": "anomaly",
    }
    response = httpx.post(settings.anomaly_webhook_url, json=payload, timeout=5)
    response.raise_for_status()
    return True


def notify_anomaly(reading: Reading) -> bool:
    """Envia notificações para uma leitura recém marcada como anômala:
    e-mail sempre, webhook se configurado. Nunca propaga exceção — uma
    falha de notificação não pode derrubar a ingestão. Retorna True se pelo
    menos um canal entregou com sucesso.

    Diferente de `alerts/notify.notify_alert`, aqui não há campo
    `notified_at` para marcar: a deduplicação de notificações repetidas
    (para não notificar leitura a leitura durante um mesmo episódio de
    anomalia) é responsabilidade de quem chama esta função — ver
    `anomaly/detector.is_new_anomaly_onset`.
    """
    delivered = False

    try:
        send_email_anomaly(reading)
        delivered = True
    except Exception:
        logger.exception("falha ao enviar e-mail de anomalia (sensor=%s)", reading.sensor_id)

    try:
        if send_webhook_anomaly(reading):
            delivered = True
    except Exception:
        logger.exception("falha ao enviar webhook de anomalia (sensor=%s)", reading.sensor_id)

    return delivered
