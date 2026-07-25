import logging

from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.db.session import settings
from app.models.orm import Reading

logger = logging.getLogger(__name__)

_FEATURES = ["concentration_ppm", "temperature_c", "battery_pct"]


def is_anomaly(db: Session, sensor_id: str, gas_type: str, reading_time) -> bool:
    """Classifica a leitura em `reading_time` como anômala ou não, usando um
    Isolation Forest treinado sob demanda com o histórico recente do mesmo
    sensor+gás (concentration_ppm, temperature_c, battery_pct).

    Sem estado em memória, no mesmo espírito de `alerts/rules.py`: reavalia
    o histórico do banco a cada chamada, então o consumer pode reiniciar sem
    perder nenhum modelo treinado. Custo: retreina o modelo a cada leitura —
    aceitável no volume atual de sensores, mas um ponto de otimização futura
    (cache de modelo / retrain periódico) se o volume crescer.

    Sem histórico mínimo (`anomaly_min_history`) para o par sensor+gás,
    retorna False — não há dados suficientes para julgar o que é normal.
    """
    history = (
        db.query(Reading)
        .filter(Reading.sensor_id == sensor_id, Reading.gas_type == gas_type, Reading.time <= reading_time)
        .order_by(Reading.time.desc())
        .limit(settings.anomaly_history_limit)
        .all()
    )

    if len(history) < settings.anomaly_min_history:
        return False

    history.reverse()  # ordem cronológica; a leitura avaliada fica na última linha
    features = [[r.concentration_ppm, r.temperature_c, r.battery_pct] for r in history]

    model = IsolationForest(contamination=settings.anomaly_contamination, random_state=42)
    predictions = model.fit_predict(features)

    return bool(predictions[-1] == -1)


def is_new_anomaly_onset(db: Session, sensor_id: str, gas_type: str, reading_time) -> bool:
    """True somente quando a leitura em `reading_time` marca o início de um
    novo episódio de anomalia — ou seja, a leitura anterior do mesmo
    sensor+gás não estava marcada como anômala (ou não existe leitura
    anterior). Usado para notificar uma única vez por episódio, em vez de
    leitura a leitura enquanto a condição persistir.

    Chamar apenas quando a leitura atual já foi classificada como anômala.
    """
    previous = (
        db.query(Reading)
        .filter(Reading.sensor_id == sensor_id, Reading.gas_type == gas_type, Reading.time < reading_time)
        .order_by(Reading.time.desc())
        .first()
    )
    return previous is None or not previous.is_anomaly
