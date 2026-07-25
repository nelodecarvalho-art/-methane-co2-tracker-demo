"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 6
(relatório de compliance acessível pelo dashboard + notificação dedicada de
anomalia). Linguagem de negócio, não de desenvolvedor — para o relatório
interno de verificação de código, ver generate_phase6_report.py.

Roda: python backend/scripts/generate_client_report_fase6.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-6-dashboard-compliance-notificacao-anomalia.pdf"


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
        "Relatório de Acesso ao Compliance pelo Dashboard e Alerta de Anomalia — Fase 6",
        h2,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Esta fase fecha duas pendências deixadas pelas fases anteriores: "
        "tornar o relatório de compliance (Fase 5) acessível diretamente "
        "pela tela do dashboard, sem depender de uma chamada técnica à "
        "API, e dar à detecção de anomalia (Fase 4) o mesmo tipo de aviso "
        "automático que o alerta de segurança já tinha desde a Fase 3.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Relatório de compliance com um clique", h2))
    story.append(Paragraph(
        "O dashboard agora tem uma seção dedicada onde a equipe de operação "
        "escolhe o período desejado e baixa o relatório de compliance "
        "diretamente, sem precisar de nenhum conhecimento técnico ou "
        "chamada manual a sistemas internos. Testado e confirmado "
        "funcionando pelo próprio usuário no navegador.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Aviso automático de anomalia", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "A partir de agora, quando o sistema identifica uma leitura "
            "fora do padrão normal de um sensor, a equipe recebe um "
            "e-mail automático — com o assunto claramente marcado como "
            "<b>[ANOMALIA]</b>, para não ser confundido com o alerta de "
            "segurança (<b>[ALERTA]</b>), que segue sendo o aviso "
            "prioritário de risco.", body)),
        ListItem(Paragraph(
            "Para evitar excesso de avisos, o sistema notifica apenas uma "
            "vez quando a condição começa — não repete a cada leitura "
            "enquanto o comportamento incomum continuar, o que evitaria "
            "que a equipe passasse a ignorar os avisos por excesso de "
            "volume.", body)),
        ListItem(Paragraph(
            "Suporte opcional a um webhook próprio, separado do webhook do "
            "alerta de segurança — permite, por exemplo, rotear avisos de "
            "anomalia para o sistema de manutenção da operadora, mantendo "
            "o canal de alerta de segurança dedicado só a risco.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "O aviso automático de anomalia foi testado simulando um cenário "
        "de três leituras fora do padrão em sequência, confirmando que "
        "apenas um e-mail e um aviso foram disparados — não três. O botão "
        "de relatório no dashboard foi testado tanto por verificação "
        "automatizada quanto pelo próprio usuário, diretamente no "
        "navegador, confirmando o download correto do documento.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 6 (dashboard de compliance + notificação de anomalia): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Sem pendências conhecidas no momento — todos os itens levantados desde a Fase 2 foram endereçados.", body)),
        ListItem(Paragraph("Possíveis próximos passos: login individual por usuário no dashboard, e validação jurídica formal do enquadramento regulatório ANP/EPA exato aplicável (ver Fase 5).", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase6.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
