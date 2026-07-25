"""
Relatório de suporte a compliance ANP/EPA — funcionalidade do produto (via
GET /reports/compliance), não um script de fase. Ver
app/api/routers/reports.py para o endpoint.

Este relatório resume, para um período informado, os dados de concentração
coletados, os eventos de alerta (abertura/fechamento, no espírito de um
registro LDAR — Leak Detection and Repair) e as leituras sinalizadas pelo
detector de anomalia. Não citamos aqui um número de resolução ANP/EPA
específico: é um artefato de apoio ao processo de compliance do operador
(monitoramento contínuo e trilha de auditoria de eventos), não uma submissão
regulatória pronta nem um inventário de emissões (que exigiria vazão
mássica/modelagem de dispersão — este sistema mede concentração em ppm, não
taxa de emissão).
"""
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import Integer, cast, func
from sqlalchemy.orm import Session

from app.models.orm import Alert, Reading, Sensor


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def _format_duration(started_at: datetime, ended_at: datetime | None) -> str:
    if ended_at is None:
        return "ainda ativo"
    seconds = int((ended_at - started_at).total_seconds())
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{seconds:02d}s"


def _readings_summary(db: Session, start: datetime, end: datetime) -> list[list[str]]:
    rows = (
        db.query(
            Reading.sensor_id,
            Sensor.name,
            Reading.gas_type,
            func.count(Reading.time).label("count"),
            func.min(Reading.concentration_ppm).label("min_ppm"),
            func.avg(Reading.concentration_ppm).label("avg_ppm"),
            func.max(Reading.concentration_ppm).label("max_ppm"),
            func.sum(cast(Reading.is_anomaly, Integer)).label("anomaly_count"),
        )
        .join(Sensor, Sensor.sensor_id == Reading.sensor_id)
        .filter(Reading.time >= start, Reading.time <= end)
        .group_by(Reading.sensor_id, Sensor.name, Reading.gas_type)
        .order_by(Reading.sensor_id, Reading.gas_type)
        .all()
    )

    table_data = [["Sensor", "Gás", "Leituras", "Mín (ppm)", "Média (ppm)", "Máx (ppm)", "Anomalias"]]
    for row in rows:
        table_data.append([
            f"{row.name} ({row.sensor_id})",
            row.gas_type,
            str(row.count),
            f"{row.min_ppm:.1f}",
            f"{row.avg_ppm:.1f}",
            f"{row.max_ppm:.1f}",
            str(row.anomaly_count or 0),
        ])
    return table_data


def _alert_events(db: Session, start: datetime, end: datetime) -> list[list[str]]:
    alerts = (
        db.query(Alert)
        .filter(Alert.started_at >= start, Alert.started_at <= end)
        .order_by(Alert.started_at.asc())
        .all()
    )

    table_data = [["Sensor", "Gás", "Início", "Fim", "Duração", "Máx (ppm)", "Status", "Notificado"]]
    for alert in alerts:
        table_data.append([
            alert.sensor_id,
            alert.gas_type,
            _format_dt(alert.started_at),
            _format_dt(alert.ended_at),
            _format_duration(alert.started_at, alert.ended_at),
            f"{alert.max_ppm:.1f}",
            alert.status,
            "sim" if alert.notified_at else "não",
        ])
    return table_data


def build_compliance_pdf(db: Session, start: datetime, end: datetime) -> bytes:
    buffer = BytesIO()

    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, textColor=colors.grey)

    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    story.append(Paragraph("Methane &amp; CO2 Tracker", h1))
    story.append(Paragraph("Relatório de Monitoramento e Eventos de Alerta", h2))
    story.append(Paragraph(
        f"Período coberto: {_format_dt(start)} a {_format_dt(end)} — "
        f"gerado em {_format_dt(datetime.now(timezone.utc))}.",
        small,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Este relatório é um artefato de apoio ao processo de compliance "
        "regulatório do operador (monitoramento contínuo de concentração "
        "de gás e trilha de auditoria dos eventos de alerta detectados no "
        "período) — não é uma submissão regulatória pronta nem substitui "
        "verificação independente. As leituras representam "
        "<b>concentração de gás (ppm)</b>, não taxa de emissão mássica "
        "(kg/h ou tCO2e); quantificação de emissão exigiria modelagem de "
        "dispersão ou instrumentação de vazão mássica, fora do escopo "
        "deste sistema de sensores.",
        body,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo de leituras por sensor e gás", h2))
    readings_table_data = _readings_summary(db, start, end)
    if len(readings_table_data) == 1:
        story.append(Paragraph("Nenhuma leitura registrada no período.", body))
    else:
        readings_table = Table(readings_table_data, repeatRows=1)
        readings_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ]))
        story.append(readings_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Eventos de alerta no período", h2))
    alerts_table_data = _alert_events(db, start, end)
    if len(alerts_table_data) == 1:
        story.append(Paragraph("Nenhum evento de alerta no período.", body))
    else:
        alerts_table = Table(alerts_table_data, repeatRows=1)
        alerts_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ]))
        story.append(alerts_table)

    doc.build(story)
    return buffer.getvalue()
