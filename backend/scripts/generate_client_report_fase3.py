"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 3
(API de dados, notificação automática de alertas e dashboard visual).
Linguagem de negócio, não de desenvolvedor — para o relatório interno de
verificação de código, ver generate_phase3_report.py.

Roda: python backend/scripts/generate_client_report_fase3.py
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
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-3-api-notificacoes-dashboard.pdf"


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
    story.append(Paragraph("Relatório de Acesso a Dados, Notificação e Dashboard — Fase 3", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Esta fase conecta o motor de detecção construído na Fase 2 às "
        "pessoas que precisam agir sobre ele: a equipe de operação passa a "
        "ser avisada automaticamente quando um alerta é aberto, e ganha uma "
        "tela visual para acompanhar leituras e histórico de eventos sem "
        "depender de acesso direto ao banco de dados.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Acesso aos dados via API", h2))
    story.append(Paragraph(
        "Os dados de leitura e de alerta passam a estar disponíveis por "
        "meio de uma interface de programação (API) protegida por chave de "
        "acesso — permitindo que sistemas internos da operadora (ERP, "
        "central de monitoramento, planilhas de compliance) consultem o "
        "histórico diretamente, com filtros por sensor, tipo de gás e "
        "período, sem depender de exportações manuais.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Notificação automática de alertas", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Quando um alerta é aberto pelo motor da Fase 2, o sistema "
            "agora avisa automaticamente por <b>e-mail</b> a equipe "
            "responsável, sem necessidade de alguém consultar o sistema "
            "ativamente.", body)),
        ListItem(Paragraph(
            "Suporte opcional a <b>webhook</b> — permite integrar o alerta "
            "diretamente a outro sistema da operadora (ex.: central de "
            "monitoramento, SCADA, sistema de tickets), quando configurado.", body)),
        ListItem(Paragraph(
            "Uma falha ao enviar a notificação (ex.: servidor de e-mail "
            "fora do ar) nunca compromete a gravação do alerta em si nem a "
            "recepção contínua dos dados dos sensores — os dois caminhos "
            "são independentes por desenho.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Dashboard visual", h2))
    story.append(Paragraph(
        "Primeira versão de uma tela web para acompanhamento: gráfico das "
        "leituras mais recentes dos sensores e lista dos eventos de "
        "alerta, com atualização sob demanda. O acesso é protegido por "
        "chave — hoje uma chave única compartilhada pela operação; um "
        "controle de usuários individuais (login por pessoa) é previsto "
        "para uma fase futura, quando o número de usuários justificar.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "A API foi testada quanto a controle de acesso (recusa de "
        "requisições sem chave válida), paginação e filtros. O envio de "
        "notificação foi testado de ponta a ponta contra um servidor de "
        "e-mail real (ambiente de testes) e um receptor de webhook, "
        "confirmando que o alerta chega corretamente e fica marcado como "
        "notificado. O dashboard foi compilado em sua versão final de "
        "produção sem erros.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 3 (API, notificação e dashboard): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Ainda não incluído: detecção de anomalia por machine learning e geração automática de relatório de compliance ANP/EPA — previstos para fases seguintes.", body)),
        ListItem(Paragraph("Login individual por usuário no dashboard (hoje: chave única compartilhada) fica como melhoria futura.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase3.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
