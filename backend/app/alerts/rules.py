from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.alerts.notify import notify_alert
from app.db.session import settings
from app.models.orm import Alert, Reading


def evaluate_alert(db: Session, sensor_id: str, gas_type: str, reading_time: datetime) -> None:
    """Avalia a regra de alerta sustentado após uma nova leitura ser
    inserida. Sem estado em memória: reconsulta a janela no banco a cada
    chamada, então é seguro reiniciar o consumer a qualquer momento sem
    perder o estado do alerta.

    Regra: abre/mantém Alert ativo se TODAS as leituras de
    `sensor_id`+`gas_type` dentro da janela [reading_time - window, reading_time]
    estiverem acima do threshold do gás E a janela tiver cobertura completa
    (existe leitura na borda inicial da janela — senão não dá pra afirmar
    que ficou sustentado pelo período todo, pode ser só o sensor começando
    a reportar agora). Fecha o alerta ativo assim que uma leitura cair
    abaixo do threshold.
    """
    threshold = settings.alert_thresholds_ppm.get(gas_type)
    if threshold is None:
        return

    window_start = reading_time - timedelta(seconds=settings.alert_window_seconds)

    window_readings = (
        db.query(Reading)
        .filter(
            Reading.sensor_id == sensor_id,
            Reading.gas_type == gas_type,
            Reading.time >= window_start,
            Reading.time <= reading_time,
        )
        .order_by(Reading.time.asc())
        .all()
    )

    active_alert = (
        db.query(Alert)
        .filter(
            Alert.sensor_id == sensor_id,
            Alert.gas_type == gas_type,
            Alert.status == "active",
        )
        .one_or_none()
    )

    oldest = window_readings[0] if window_readings else None
    window_has_full_coverage = oldest is not None and oldest.time <= window_start + timedelta(
        seconds=1
    )
    all_above_threshold = bool(window_readings) and all(
        r.concentration_ppm >= threshold for r in window_readings
    )

    should_be_active = window_has_full_coverage and all_above_threshold

    if should_be_active and active_alert is None:
        max_ppm = max(r.concentration_ppm for r in window_readings)
        new_alert = Alert(
            sensor_id=sensor_id,
            gas_type=gas_type,
            started_at=oldest.time,
            max_ppm=max_ppm,
            status="active",
        )
        db.add(new_alert)
        db.commit()

        if notify_alert(new_alert):
            new_alert.notified_at = datetime.now(timezone.utc)
            db.commit()
    elif should_be_active and active_alert is not None:
        current_max = max(r.concentration_ppm for r in window_readings)
        if current_max > active_alert.max_ppm:
            active_alert.max_ppm = current_max
            db.commit()
    elif not should_be_active and active_alert is not None:
        active_alert.status = "resolved"
        active_alert.ended_at = reading_time
        db.commit()
