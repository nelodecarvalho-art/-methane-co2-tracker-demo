"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 4
(detecção de anomalia). Linguagem de negócio, não de desenvolvedor — para o
relatório interno de verificação de código, ver generate_phase4_report.py.

Roda: python backend/scripts/generate_client_report_fase4.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-4-deteccao-anomalia.pdf"


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
    story.append(Paragraph("Relatório de Detecção de Anomalia — Fase 4", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "O motor de alerta da Fase 2 avisa quando a concentração de gás "
        "ultrapassa um limite de segurança de forma sustentada — é a "
        "proteção contra o risco mais crítico, um vazamento real. Esta "
        "fase adiciona uma segunda camada, complementar: um modelo "
        "estatístico de machine learning que aprende o comportamento "
        "normal de cada sensor individualmente e sinaliza leituras fora "
        "desse padrão, mesmo quando não chegam a cruzar o limite de "
        "segurança. É uma ferramenta de detecção precoce e de saúde do "
        "equipamento, não um substituto do alerta de segurança.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Por que isso complementa o alerta de limiar", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Um pico de concentração isolado, que sobe e desce rápido "
            "demais para acionar o alerta sustentado, ainda assim pode "
            "indicar um problema começando (ex.: falha intermitente) — o "
            "novo detector consegue sinalizar esse tipo de evento.", body)),
        ListItem(Paragraph(
            "O modelo também considera temperatura e nível de bateria do "
            "sensor junto com a concentração, o que ajuda a distinguir um "
            "sensor com comportamento estranho (possível defeito ou "
            "necessidade de manutenção) de uma leitura genuína, mesmo "
            "quando o valor de concentração isoladamente não parece "
            "alarmante.", body)),
        ListItem(Paragraph(
            "Cada sensor é avaliado contra o próprio histórico — o que é "
            "\"normal\" para um sensor instalado perto de um equipamento "
            "mais quente não precisa ser o mesmo padrão de outro em local "
            "diferente.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Segurança contra falsos positivos em sensores novos", h2))
    story.append(Paragraph(
        "Um sensor recém-instalado, ainda sem histórico suficiente, nunca "
        "é classificado como anômalo por falta de dado — o sistema exige "
        "um número mínimo de leituras antes de começar a avaliar aquele "
        "sensor, evitando alarmes indevidos logo após a instalação.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Onde aparece", h2))
    story.append(Paragraph(
        "As leituras marcadas como anômalas ficam disponíveis via API "
        "(com filtro dedicado) e são destacadas visualmente no dashboard, "
        "junto ao gráfico de leituras recentes, para a equipe de operação "
        "identificar rapidamente pontos que merecem atenção — sem "
        "necessidade de análise manual dos dados brutos.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "O classificador foi testado com três cenários: um sensor sem "
        "histórico suficiente (corretamente não avaliado), leituras dentro "
        "do padrão normal de operação (corretamente não sinalizadas) e uma "
        "leitura claramente fora do padrão (corretamente sinalizada como "
        "anomalia). Toda a suíte de testes das fases anteriores foi "
        "reexecutada para confirmar que a nova funcionalidade não afeta a "
        "ingestão de dados, o alerta de segurança, as notificações nem a "
        "API existentes.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 4 (detecção de anomalia): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Ainda não incluído: notificação automática (e-mail/webhook) especificamente para anomalias detectadas — hoje elas ficam registradas e visíveis, mas não disparam aviso como o alerta de segurança.", body)),
        ListItem(Paragraph("Ainda não incluído: geração automática de relatório de compliance ANP/EPA — previsto para fase seguinte.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase4.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
