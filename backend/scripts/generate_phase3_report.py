"""
Gera o relatório em PDF da Fase 3 (API REST + notificação de alertas +
dashboard React) e salva em methane-co2-tracker/relatorios/. Script único,
roda uma vez ao final da fase — não é o módulo de relatório ANP/EPA do
produto (esse vive em app/reports/ e ainda não foi implementado).

Roda: python backend/scripts/generate_phase3_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-3-api-notificacoes-dashboard.pdf"


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
    story.append(Paragraph("Relatório da Fase 3 — API REST, Notificação de Alertas e Dashboard", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: expor os dados armazenados (leituras e alertas) "
        "via uma API REST autenticada, notificar automaticamente por e-mail "
        "e webhook quando um alerta é aberto, e entregar a primeira versão "
        "do dashboard visual consumindo essa API.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "API REST em FastAPI (<i>app/api/</i>) com três routers "
            "(readings, alerts, devices), todos protegidos por dependência "
            "<b>require_api_key</b> — header <i>X-API-Key</i> validado "
            "contra <i>settings.api_key_secret</i>. Sem sessão/cookie: "
            "pensado para consumo por dashboard e integrações externas.", body)),
        ListItem(Paragraph(
            "Paginação uniforme via <i>app/api/pagination.py</i> "
            "(offset/limit, resposta envelopada em <b>Page[T]</b> com "
            "total) e filtros por <i>device_id</i>, <i>gas_type</i> e "
            "janela de tempo (<i>start</i>/<i>end</i>) no endpoint de "
            "leituras — mesmos filtros aplicáveis a alertas.", body)),
        ListItem(Paragraph(
            "Notificação de alerta (<i>app/alerts/notify.py</i>) em dois "
            "canais independentes: e-mail via SMTP (Mailpit em dev, "
            "container novo no docker-compose) e webhook HTTP opcional. "
            "<b>notify_alert()</b> isola cada canal em try/except próprio — "
            "uma falha de notificação nunca derruba a ingestão — e marca "
            "<i>Alert.notified_at</i> se pelo menos um canal entregou.", body)),
        ListItem(Paragraph(
            "Dashboard em React 18 + TypeScript + Vite, consumindo a API "
            "via <i>services/api.ts</i>. Autenticação simples por API key "
            "guardada no browser (<i>ApiKeyGate.tsx</i>) — sem fluxo de "
            "login completo, adequado ao estágio atual do produto. "
            "Visualização de leituras recentes (<i>ReadingsChart.tsx</i>, "
            "recharts) e eventos de alerta (<i>AlertsList.tsx</i>).", body)),
        ListItem(Paragraph(
            "Nenhuma migração de schema nova foi necessária nesta fase — "
            "a coluna <i>notified_at</i> já existia desde a "
            "0001_initial_schema.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["backend/app/api/main.py", "App FastAPI, registro dos routers"],
        ["backend/app/api/deps.py", "Autenticação por API key + sessão de DB"],
        ["backend/app/api/pagination.py", "Helper de paginação offset/limit"],
        ["backend/app/api/schemas.py", "Schemas Pydantic de resposta (Page, ReadingOut, AlertOut...)"],
        ["backend/app/api/routers/readings.py", "GET /readings — filtros por sensor/gás/período"],
        ["backend/app/api/routers/alerts.py", "GET /alerts — filtros por sensor/gás/status"],
        ["backend/app/api/routers/devices.py", "GET /devices"],
        ["backend/app/alerts/notify.py", "Notificação por e-mail (SMTP) e webhook"],
        ["docker-compose.yml", "Serviço mailpit (SMTP dev) adicionado"],
        ["frontend/src/pages/Dashboard.tsx", "Página principal do dashboard"],
        ["frontend/src/components/ReadingsChart.tsx", "Gráfico de leituras recentes (recharts)"],
        ["frontend/src/components/AlertsList.tsx", "Lista de eventos de alerta"],
        ["frontend/src/components/ApiKeyGate.tsx", "Gate de autenticação por API key"],
        ["frontend/src/services/api.ts", "Cliente HTTP da API REST"],
        ["backend/tests/test_api.py", "Teste standalone — executado, OK"],
        ["backend/tests/test_alert_notifications.py", "Teste standalone — executado, OK"],
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
            "mosquitto mailpit</i> — os três serviços confirmados "
            "saudáveis.", body)),
        ListItem(Paragraph(
            "test_api.py: <b>executado com sucesso</b> — cobre "
            "autenticação obrigatória (401 sem/incorreta API key), "
            "paginação e filtros por gás, período e status.", body)),
        ListItem(Paragraph(
            "test_alert_notifications.py: <b>executado com sucesso</b> — "
            "alerta disparado notifica por e-mail (capturado no Mailpit) "
            "e por webhook (receptor local de teste), e <i>notified_at</i> "
            "é marcado no banco.", body)),
        ListItem(Paragraph(
            "Dashboard: build de produção (<i>tsc -b &amp;&amp; vite "
            "build</i>) executado com sucesso, sem erros de tipo.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Detecção de anomalia (Isolation Forest) — módulo app/anomaly ainda vazio.", body)),
        ListItem(Paragraph("Geração de relatório PDF ANP/EPA do produto — módulo app/reports ainda vazio.", body)),
        ListItem(Paragraph("Fluxo de login completo no dashboard (hoje: API key única compartilhada) e code-splitting do bundle React (>500kB no build atual).", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase3_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
