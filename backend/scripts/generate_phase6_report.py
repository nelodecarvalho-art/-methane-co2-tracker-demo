"""
Gera o relatório em PDF da Fase 6 (botão de relatório de compliance no
dashboard + notificação dedicada de anomalia) e salva em
methane-co2-tracker/relatorios/. Script único, roda uma vez ao final da
fase.

Roda: python backend/scripts/generate_phase6_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-6-dashboard-compliance-notificacao-anomalia.pdf"


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
    story.append(Paragraph(
        "Relatório da Fase 6 — Botão de Relatório no Dashboard e Notificação Dedicada de Anomalia",
        h2,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: dois follow-ups pendentes das fases anteriores. "
        "Primeiro, expor o relatório de compliance (Fase 5) diretamente no "
        "dashboard, sem exigir chamada manual à API. Segundo, dar à "
        "detecção de anomalia (Fase 4) um canal de notificação próprio, "
        "assim como o alerta de segurança já tem desde a Fase 3.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Parte 1 — Botão de relatório de compliance no dashboard", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Novo componente <i>ComplianceReportPanel.tsx</i>: formulário "
            "com datas \"De\"/\"Até\" e botão \"Gerar relatório PDF\", "
            "adicionado como nova seção do <i>Dashboard.tsx</i>.", body)),
        ListItem(Paragraph(
            "Nova função <i>fetchComplianceReportPdf()</i> em "
            "<i>services/api.ts</i> — busca o PDF como <i>blob</i> (não "
            "JSON, diferente das demais chamadas da API) e dispara o "
            "download no navegador via URL de objeto temporária.", body)),
        ListItem(Paragraph(
            "Tratamento de erro no cliente: 401 (chave inválida), 400 "
            "(período com fim anterior ao início) e falha de rede, cada um "
            "com mensagem própria.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Parte 2 — Notificação dedicada de anomalia", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Novo módulo <i>app/anomaly/notify.py</i> — mesma estrutura do "
            "<i>alerts/notify.py</i> (e-mail sempre tentado, webhook "
            "opcional, exceções isoladas por canal, nunca propaga falha "
            "para a ingestão). Assunto de e-mail <b>[ANOMALIA]</b>, "
            "distinto de <b>[ALERTA]</b>, para a equipe não confundir "
            "severidades.", body)),
        ListItem(Paragraph(
            "Nova configuração <b>ANOMALY_WEBHOOK_URL</b>, deliberadamente "
            "separada de <b>ALERT_WEBHOOK_URL</b> — anomalia é sinal de "
            "menor severidade que o alerta de segurança, e pode fazer "
            "sentido rotear para um sistema diferente (ex: manutenção, não "
            "escalonamento de risco).", body)),
        ListItem(Paragraph(
            "Desenho anti-spam: <i>detector.is_new_anomaly_onset()</i> só "
            "considera uma leitura como início de um novo episódio de "
            "anomalia quando a leitura imediatamente anterior do mesmo "
            "sensor+gás não estava marcada como anômala. Notifica uma "
            "única vez por episódio, não leitura a leitura enquanto a "
            "condição persistir — sem exigir nenhuma coluna ou migração "
            "nova, derivado inteiramente do histórico de <i>is_anomaly</i> "
            "já existente.", body)),
        ListItem(Paragraph(
            "Integrado em <i>mqtt_consumer.py</i> logo após o cálculo do "
            "flag <i>is_anomaly</i> de cada leitura.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["frontend/src/components/ComplianceReportPanel.tsx", "Formulário + botão de geração do relatório"],
        ["frontend/src/services/api.ts", "fetchComplianceReportPdf() — busca PDF como blob"],
        ["frontend/src/pages/Dashboard.tsx", "Nova seção do relatório de compliance"],
        ["frontend/src/index.css", "Estilo do formulário de datas"],
        ["backend/app/anomaly/notify.py", "Notificação de anomalia (e-mail + webhook)"],
        ["backend/app/anomaly/detector.py", "is_new_anomaly_onset() — guarda anti-spam"],
        ["backend/app/ingestion/mqtt_consumer.py", "Chamada à notificação de anomalia"],
        ["backend/app/db/session.py", "Nova setting anomaly_webhook_url"],
        [".env.example / .env", "Nova variável ANOMALY_WEBHOOK_URL"],
        ["backend/tests/test_anomaly_notifications.py", "Teste standalone — executado, OK"],
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
            "test_anomaly_notifications.py: <b>executado com sucesso</b> "
            "— simula um episódio de 3 leituras anômalas seguidas e "
            "confirma exatamente 1 e-mail (Mailpit) e 1 webhook (receptor "
            "local), não 3. Reexecutado uma segunda vez em sequência para "
            "confirmar reprodutibilidade.", body)),
        ListItem(Paragraph(
            "Durante a escrita do teste, identificado que o campo "
            "<i>total</i>/<i>unread</i> da API de busca do Mailpit reflete "
            "a caixa inteira, não a busca filtrada — a contagem filtrada "
            "correta é <i>messages_count</i>. Corrigido no teste antes de "
            "confiar no resultado.", body)),
        ListItem(Paragraph(
            "Botão de relatório no dashboard: build de produção do "
            "frontend verificado, preflight CORS e chamada real contra a "
            "API local confirmados via linha de comando, e "
            "<b>testado interativamente pelo usuário no navegador</b> "
            "— confirmou funcionamento de ponta a ponta.", body)),
        ListItem(Paragraph(
            "Suíte completa de testes standalone reexecutada — "
            "<b>nenhuma regressão</b> nos módulos de ingestão, alerta, "
            "detecção de anomalia, API e relatório de compliance.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Sem pendências conhecidas no momento — todos os itens levantados nas fases 2 a 5 foram endereçados.", body)),
        ListItem(Paragraph("Possíveis próximos passos de produto: frontend com login individual por usuário, code-splitting do bundle React, e confirmação jurídica formal do enquadramento ANP/EPA (ver Fase 5).", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase6_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
