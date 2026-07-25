"""
Gera o relatório em PDF da Fase 2 (ingestão MQTT->Protobuf + regra de
alerta) e salva em methane-co2-tracker/relatorios/. Script único, roda uma
vez ao final da fase — não é o módulo de relatório ANP/EPA do produto
(esse vive em app/reports/ e ainda não foi implementado).

Roda: python backend/scripts/generate_phase2_report.py
"""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-2-ingestao-alertas.pdf"


def build_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, textColor=colors.grey)

    doc = SimpleDocTemplate(str(output_path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    story.append(Paragraph("Methane &amp; CO2 Tracker", h1))
    story.append(Paragraph("Relatório da Fase 2 — Ingestão MQTT → Protobuf e Regra de Alerta", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: serviço que assina o(s) tópico(s) MQTT onde o "
        "gateway 4G/LoRaWAN publica leituras dos sensores TDLAS, decodifica "
        "o payload binário Protobuf, valida e grava no TimescaleDB, e avalia "
        "uma regra de alerta por concentração sustentada acima do threshold.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Schema expandido de CH4-only para multi-gás: <b>readings.ppm_ch4</b> "
            "renomeado para <b>concentration_ppm</b>, com nova coluna "
            "<b>gas_type</b> (CH4/CO2) em readings e alerts. Migração 0002, "
            "não altera a 0001 original.", body)),
        ListItem(Paragraph(
            "Contrato Protobuf (<i>proto/sensor_reading.proto</i>) ganhou "
            "enum GasType e o campo gas_type — é a fonte única de verdade "
            "compartilhada com o firmware, atualizado em conjunto com "
            "docs/protocol-spec.md.", body)),
        ListItem(Paragraph(
            "Regra de alerta implementada como <b>sustentada por janela</b> "
            "(default 120s / 500ppm CH4 / 5000ppm CO2, configurável via "
            ".env), não como cruzamento instantâneo — consistente com a "
            "especificação original do produto. Sem estado em memória: "
            "reavalia a janela a partir do banco a cada leitura, então o "
            "serviço pode reiniciar sem perder o estado do alerta.", body)),
        ListItem(Paragraph(
            "Consumer MQTT (paho-mqtt) isola cada mensagem em try/except: "
            "payload malformado é logado e descartado, nunca derruba o "
            "processo. Reconexão ao broker via reconnect_delay_set "
            "(backoff automático).", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["proto/sensor_reading.proto", "Contrato binário sensor -> cloud (atualizado)"],
        ["backend/alembic/versions/0002_multi_gas_schema.py", "Migração multi-gás"],
        ["backend/app/models/orm.py", "ORM atualizado (gas_type, concentration_ppm)"],
        ["backend/app/ingestion/generated/sensor_reading_pb2.py", "Código gerado do .proto"],
        ["backend/app/ingestion/decoder.py", "Bytes Protobuf -> dict (com lookup de sensor)"],
        ["backend/app/ingestion/schemas.py", "Validação Pydantic da leitura decodificada"],
        ["backend/app/ingestion/mqtt_consumer.py", "Serviço de ingestão MQTT"],
        ["backend/app/alerts/rules.py", "Regra de alerta sustentado por janela"],
        ["mosquitto/config/mosquitto.conf", "Config dev-only do broker (allow_anonymous)"],
        ["backend/tests/test_db_connection.py", "Teste standalone — executado, OK"],
        ["backend/tests/test_proto_roundtrip.py", "Teste standalone — executado, OK"],
        ["backend/tests/test_alert_rule.py", "Teste standalone — executado, OK"],
        ["backend/tests/test_mqtt_ingestion.py", "Teste standalone — executado, OK"],
    ]
    files_table = Table(files_table_data, colWidths=[8 * cm, 8.5 * cm])
    files_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    story.append(files_table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status de verificação", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Ambiente subido via <i>docker compose up -d timescaledb "
            "mosquitto</i> (TimescaleDB + Mosquitto 2, config dev-only em "
            "<i>mosquitto/config/mosquitto.conf</i> com allow_anonymous) e "
            "migrations aplicadas com <i>alembic upgrade head</i> (0001 + "
            "0002).", body)),
        ListItem(Paragraph(
            "test_proto_roundtrip.py: <b>executado com sucesso</b> "
            "(serialização/desserialização, 19 bytes/leitura, dentro do "
            "orçamento LoRaWAN).", body)),
        ListItem(Paragraph(
            "test_db_connection.py: <b>executado com sucesso</b> contra o "
            "TimescaleDB real.", body)),
        ListItem(Paragraph(
            "test_alert_rule.py: <b>executado com sucesso</b> — abre "
            "alerta com janela cheia acima do threshold, fecha ao cair "
            "abaixo, e não dispara sem cobertura completa da janela.", body)),
        ListItem(Paragraph(
            "test_mqtt_ingestion.py: <b>executado com sucesso</b> após "
            "corrigir uma condição de corrida no próprio teste (o "
            "publisher publicava antes do consumer confirmar o SUBSCRIBE "
            "no broker, perdendo as mensagens — sem sessão persistente o "
            "Mosquitto não reentrega). Corrigido aguardando o callback "
            "on_subscribe antes de publicar; nenhuma mudança no consumer "
            "de produção. Mensagem malformada foi descartada sem derrubar "
            "o consumer, como esperado.", body)),
        ListItem(Paragraph(
            "Suíte reexecutada uma segunda vez em sequência para confirmar "
            "reprodutibilidade — 4/4 testes OK nas duas rodadas.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Notificação externa do alerta (WhatsApp/Email/SMS) — só o registro em `alerts` foi implementado.", body)),
        ListItem(Paragraph("Detecção de anomalia (Isolation Forest) — módulo app/anomaly ainda vazio.", body)),
        ListItem(Paragraph("Geração de relatório PDF ANP/EPA do produto — módulo app/reports ainda vazio.", body)),
        ListItem(Paragraph("API REST e frontend React — ainda não iniciados.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase2_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
