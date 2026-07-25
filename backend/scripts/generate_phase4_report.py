"""
Gera o relatório em PDF da Fase 4 (detecção de anomalia via Isolation
Forest) e salva em methane-co2-tracker/relatorios/. Script único, roda uma
vez ao final da fase — não é o módulo de relatório ANP/EPA do produto (esse
vive em app/reports/ e ainda não foi implementado).

Roda: python backend/scripts/generate_phase4_report.py
"""
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-4-deteccao-anomalia.pdf"


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
    story.append(Paragraph("Relatório da Fase 4 — Detecção de Anomalia (Isolation Forest)", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: complementar a regra de alerta por limiar "
        "sustentado (Fase 2) com um classificador estatístico que sinaliza "
        "leituras fora do padrão histórico de cada sensor — incluindo casos "
        "que a regra de limiar não cobre, como picos isolados abaixo do "
        "threshold ou combinações incomuns entre concentração, temperatura "
        "e bateria.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Modelo <b>Isolation Forest</b> (scikit-learn), treinado sob "
            "demanda a cada leitura nova, isolado por par "
            "<i>sensor_id</i>+<i>gas_type</i> — cada sensor tem seu próprio "
            "perfil de normalidade, não um modelo global. Mesma filosofia "
            "sem estado em memória da regra de alerta (Fase 2): reavalia o "
            "histórico do banco a cada chamada, então o serviço pode "
            "reiniciar sem perder nenhum modelo treinado.", body)),
        ListItem(Paragraph(
            "Features: <b>concentration_ppm</b>, <b>temperature_c</b> e "
            "<b>battery_pct</b> — as três colunas já validadas e sempre "
            "presentes na ingestão (Fase 2). Combinar os três sinais "
            "permite detectar, por exemplo, uma leitura de concentração "
            "aparentemente normal acompanhada de uma temperatura "
            "incompatível com a operação normal do sensor.", body)),
        ListItem(Paragraph(
            "Guarda de <i>cold start</i>: um sensor novo, sem histórico "
            "suficiente (mínimo configurável via "
            "<b>ANOMALY_MIN_HISTORY</b>, padrão 50 leituras), nunca é "
            "classificado como anômalo por falta de dado — evita falsos "
            "positivos logo na instalação de um sensor.", body)),
        ListItem(Paragraph(
            "Histórico de treino limitado às leituras mais recentes "
            "(<b>ANOMALY_HISTORY_LIMIT</b>, padrão 500) para manter o "
            "custo de treino previsível e o modelo sensível a mudanças "
            "graduais de comportamento do sensor ao longo do tempo. "
            "Sensibilidade ajustável via <b>ANOMALY_CONTAMINATION</b> "
            "(padrão 2%).", body)),
        ListItem(Paragraph(
            "Nenhuma migração de schema foi necessária — a coluna "
            "<i>readings.is_anomaly</i> já existia desde a "
            "0001_initial_schema, reservada para esta fase.", body)),
        ListItem(Paragraph(
            "Integração no pipeline de ingestão: chamado em "
            "<i>mqtt_consumer.py</i> logo após a avaliação da regra de "
            "alerta, marcando <i>Reading.is_anomaly</i> antes do commit "
            "final da leitura.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["backend/app/anomaly/detector.py", "Classificador Isolation Forest por sensor+gás"],
        ["backend/app/ingestion/mqtt_consumer.py", "Chamada ao detector após cada leitura inserida"],
        ["backend/app/db/session.py", "Novas settings: anomaly_min_history/history_limit/contamination"],
        [".env.example / .env", "Novas variáveis ANOMALY_*"],
        ["backend/app/api/routers/readings.py", "Novo filtro is_anomaly em GET /readings"],
        ["frontend/src/components/ReadingsChart.tsx", "Destaque visual (ponto vermelho) das leituras anômalas"],
        ["frontend/src/index.css", "Estilo da legenda do destaque de anomalia"],
        ["backend/tests/test_anomaly_detection.py", "Teste standalone — executado, OK"],
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
            "test_anomaly_detection.py: <b>executado com sucesso</b> — "
            "cobre três cenários: sensor sem histórico mínimo (não "
            "classifica), leitura dentro do padrão de operação normal "
            "(não marcada) e leitura claramente fora do padrão (marcada "
            "corretamente como anomalia).", body)),
        ListItem(Paragraph(
            "Suíte completa de testes standalone reexecutada após as "
            "mudanças (test_api.py, test_mqtt_ingestion.py, "
            "test_alert_rule.py, test_alert_notifications.py, "
            "test_db_connection.py, test_proto_roundtrip.py) — "
            "<b>nenhuma regressão</b> nos módulos de ingestão, alerta, "
            "notificação e API.", body)),
        ListItem(Paragraph(
            "Build de produção do dashboard (<i>tsc -b &amp;&amp; vite "
            "build</i>) reexecutado com sucesso após o destaque visual de "
            "anomalias.", body)),
        ListItem(Paragraph(
            "scikit-learn precisou ser instalado no ambiente Python do "
            "host para rodar o teste standalone localmente — já constava "
            "em requirements.txt, mas não estava presente no ambiente do "
            "host (só usado dentro do container backend até então).", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Notificação automática ao detectar uma anomalia (hoje: só a flag is_anomaly é gravada, sem e-mail/webhook dedicado como o alerta de limiar tem).", body)),
        ListItem(Paragraph("Geração de relatório PDF ANP/EPA do produto — módulo app/reports ainda vazio.", body)),
        ListItem(Paragraph("Otimização de custo: o modelo é retreinado a cada leitura (aceitável no volume atual); cache de modelo ou retrain periódico ficam como melhoria futura se o volume de sensores crescer.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase4_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
