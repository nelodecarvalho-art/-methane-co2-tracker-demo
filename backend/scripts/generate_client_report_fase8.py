"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 8
(frente de hardware: firmware, documentação, BOM, ATEX, diagramas).
Linguagem de negócio, não de desenvolvedor — para o relatório interno de
verificação de código, ver generate_phase8_report.py.

Roda: python backend/scripts/generate_client_report_fase8.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-8-frente-hardware.pdf"


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
    story.append(Paragraph("Relatório da Frente de Hardware — Fase 8", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Até esta fase, o desenvolvimento avançou principalmente no lado de "
        "software: ingestão de dados, alertas, detecção de anomalia, "
        "relatórios e autenticação. Esta fase equilibra a frente, "
        "endereçando o lado físico do produto — o dispositivo que fica "
        "instalado em campo, no chão de fábrica ou na planta de O&amp;G — "
        "com a estrutura de código do firmware, a documentação técnica "
        "atualizada, a lista de materiais expandida para os dois gases, e "
        "os diagramas de referência do sistema.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("O que foi entregue", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Estrutura de código do firmware</b> — a lógica que vai "
            "rodar no dispositivo de campo (leitura do sensor, alarme "
            "local, transmissão dos dados) foi escrita e documentada, "
            "usando o mesmo contrato de dados binário (Protobuf) já "
            "validado no backend. Isso reduz retrabalho quando o "
            "desenvolvimento de firmware for iniciado com o hardware "
            "físico em mãos.", body)),
        ListItem(Paragraph(
            "<b>Documentação de integração</b> entre o dispositivo de campo "
            "e a nuvem, atualizada para refletir exatamente o que já foi "
            "construído e validado no software (não apenas o plano "
            "original).", body)),
        ListItem(Paragraph(
            "<b>Checklist de certificação ATEX/IECEx</b> revisado, com um "
            "esclarecimento importante: o sensor de CO2 precisa da mesma "
            "certificação para área classificada que o sensor de metano — "
            "um equívoco comum é achar que, por CO2 não ser inflamável, o "
            "equipamento não precisaria de certificação Ex. A exigência "
            "vem do risco da atmosfera do ambiente de instalação, não do "
            "gás que o sensor mede.", body)),
        ListItem(Paragraph(
            "<b>Lista de materiais (BOM)</b> expandida para incluir uma "
            "opção de sensor TDLAS de CO2, complementando o sensor de "
            "metano já listado — refletindo o suporte a dois gases que o "
            "produto já tem no software desde a Fase 2.", body)),
        ListItem(Paragraph(
            "<b>Diagramas de blocos</b> — visão do sistema completo (do "
            "sensor em campo até o dashboard do cliente) e visão do "
            "dispositivo de campo isoladamente, úteis para comunicação "
            "com fornecedores, investidores e a equipe de engenharia que "
            "vier a construir o hardware físico.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Uma nota importante sobre o estágio atual", h2))
    story.append(Paragraph(
        "O firmware entregue nesta fase é uma <b>estrutura de código</b>, "
        "não um dispositivo funcionando — não foi compilado nem testado em "
        "hardware físico, porque isso exige o hardware real em mãos "
        "(placa de microcontrolador, sensor, rádio) e bibliotecas de "
        "terceiros que ainda precisam ser integradas. Isso é esperado "
        "nesta etapa do projeto: o objetivo aqui foi deixar a lógica de "
        "negócio (leitura, alarme local, transmissão) pronta e revisada, "
        "para acelerar o desenvolvimento assim que o hardware físico "
        "estiver disponível — não simular um resultado que ainda não "
        "existe.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "O código que traduz os dados do sensor para o formato binário "
        "compacto (Protobuf) foi gerado executando a ferramenta real do "
        "fabricante do formato, não escrito à mão — confirma que o "
        "contrato de dados compartilhado entre o dispositivo de campo e o "
        "backend é válido. Os diagramas de blocos foram renderizados e "
        "conferidos visualmente antes de considerar a fase concluída.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 8 (frente de hardware — firmware, documentação, BOM, ATEX, diagramas): <b>concluída</b>.", body)),
        ListItem(Paragraph("Próximo marco natural: bring-up em hardware físico de prototipagem (placa STM32 Nucleo LoRa), com o sensor real.", body)),
        ListItem(Paragraph("Ainda pendente: cotação formal dos componentes do BOM e início do processo de certificação de conjunto ATEX/IECEx — este último tem prazo típico de 4 a 12+ semanas e deve ser iniciado com antecedência em relação ao piloto em campo.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase8.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
