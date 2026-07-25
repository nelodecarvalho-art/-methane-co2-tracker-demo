"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 5
(relatório de compliance ANP/EPA sob demanda). Linguagem de negócio, não de
desenvolvedor — para o relatório interno de verificação de código, ver
generate_phase5_report.py.

Roda: python backend/scripts/generate_client_report_fase5.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-5-relatorio-compliance-anp-epa.pdf"


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
    story.append(Paragraph("Relatório de Compliance ANP/EPA Sob Demanda — Fase 5", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Esta fase entrega a peça que fecha o ciclo de compliance: um "
        "relatório em PDF, gerado sob demanda para qualquer período, "
        "reunindo o histórico de monitoramento e os eventos de alerta "
        "detectados — o documento que a equipe de operação e de meio "
        "ambiente pode anexar ao seu próprio processo de conformidade "
        "regulatória (ANP/EPA), sem precisar extrair e consolidar dados "
        "manualmente.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("O que o relatório contém", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Resumo de monitoramento por sensor e por gás</b> — "
            "quantas leituras foram registradas no período, e as faixas "
            "mínima, média e máxima de concentração observadas.", body)),
        ListItem(Paragraph(
            "<b>Histórico de eventos de alerta</b> — cada vez que um "
            "sensor ficou acima do limite de segurança de forma "
            "sustentada: quando começou, quando terminou, quanto tempo "
            "durou, o pico registrado e se a equipe foi notificada. É o "
            "registro que documenta a resposta da operação a cada evento, "
            "no espírito de um programa de detecção e reparo de vazamento "
            "(LDAR).", body)),
        ListItem(Paragraph(
            "<b>Indicação de leituras anômalas</b> — quantas leituras "
            "fugiram do padrão normal de cada sensor no período (Fase 4), "
            "reforçando o histórico de vigilância contínua.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Disponível sob demanda, para qualquer período", h2))
    story.append(Paragraph(
        "O relatório é gerado na hora, para o intervalo de datas que a "
        "operadora escolher — mês fechado, trimestre, ou uma janela "
        "específica em torno de um evento de interesse — sem depender de "
        "um relatório fixo mensal ou de trabalho manual de exportação e "
        "consolidação de planilhas.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Uma nota importante sobre o escopo", h2))
    story.append(Paragraph(
        "Este relatório documenta <b>concentração de gás monitorada</b> e "
        "a resposta da operação aos eventos de alerta — é uma peça de "
        "apoio ao processo de compliance da operadora, não uma submissão "
        "regulatória pronta para envio, nem um inventário de emissões. "
        "Quantificar a taxa de emissão (em kg/h ou toneladas de CO2 "
        "equivalente) exigiria modelagem adicional de dispersão do gás ou "
        "instrumentação de vazão mássica, que está fora do escopo deste "
        "sistema de sensores de concentração. Por essa razão, e por não "
        "termos ainda confirmação jurídica do enquadramento regulatório "
        "exato aplicável a cada operação, o relatório usa linguagem "
        "regulatória genérica em vez de citar um número de norma "
        "específico — recomendamos validar com a área jurídica/regulatória "
        "da operadora antes de qualquer uso formal em processos externos.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "O gerador de relatório foi testado com dados simulados "
        "(leituras, um evento de alerta e uma leitura anômala) e também "
        "com um período totalmente sem dados, confirmando que o "
        "documento é sempre válido — nunca um erro — mesmo quando não há "
        "nada a reportar naquele intervalo. O acesso é protegido pela "
        "mesma chave de segurança usada no restante da plataforma.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 5 (relatório de compliance sob demanda): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Ainda não incluído: botão dedicado no dashboard para gerar o relatório sem precisar chamar a API diretamente — previsto para uma fase futura.", body)),
        ListItem(Paragraph("Ainda não incluído: notificação automática específica para leituras anômalas.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase5.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
