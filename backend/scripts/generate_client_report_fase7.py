"""
Gera o relatório voltado a cliente/operadora de O&G sobre a Fase 7
(autenticação individual, substituindo a chave de acesso única
compartilhada). Linguagem de negócio, não de desenvolvedor — para o
relatório técnico, ver generate_phase7_report.py.

Reconstrução retroativa (2026-08-08) — ver nota de fonte no relatório
técnico irmão.

Roda: python backend/scripts/generate_client_report_fase7.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-7-autenticacao-individual.pdf"


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
    story.append(Paragraph("Relatório de Autenticação Individual — Fase 7", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "<i>Relatório reconstruído em 2026-08-08 a partir de evidência "
        "verificável no código e nos relatórios das fases anteriores — "
        "esta fase, por uma falha de processo, não teve seu relatório "
        "gerado na época.</i>",
        small,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Até esta fase, todas as pessoas que acessavam o painel usavam a "
        "mesma chave de acesso compartilhada pela operação — não havia "
        "como saber individualmente quem tinha entrado. Esta fase "
        "introduz login individual por e-mail e senha, encerrando uma "
        "pendência que já vinha sendo registrada desde os primeiros "
        "relatórios do projeto.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("O que mudou na prática", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Cada pessoa passa a ter sua própria conta (e-mail + senha), "
            "em vez de uma chave única compartilhada por toda a equipe.", body)),
        ListItem(Paragraph(
            "A senha nunca é armazenada em texto — apenas um \"hash\" "
            "criptográfico irreversível, prática padrão de segurança da "
            "indústria.", body)),
        ListItem(Paragraph(
            "O sistema recusa uma tentativa de login incorreta sem "
            "revelar se o problema foi o e-mail (não cadastrado) ou a "
            "senha (errada) — proteção contra tentativas de descobrir "
            "quais contas existem por tentativa e erro.", body)),
        ListItem(Paragraph(
            "O acesso concedido tem prazo de validade; passado esse "
            "tempo, a pessoa precisa entrar novamente — reduz o risco de "
            "uma sessão esquecida aberta indefinidamente.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "Testado e confirmado: login com credenciais corretas funciona; "
        "login com senha errada ou e-mail inexistente é recusado; "
        "tentativa de acessar dados sem estar logado é bloqueada; e um "
        "acesso expirado deixa de funcionar automaticamente, exigindo "
        "novo login.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 7 (autenticação individual): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Resolve a pendência de \"login individual por usuário\" registrada desde a Fase 3.", body)),
        ListItem(Paragraph("Nenhuma ação de acompanhamento pendente para esta fase especificamente.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase7.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
