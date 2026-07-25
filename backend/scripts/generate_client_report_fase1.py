"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 1
(arquitetura de hardware/software, protocolo de dados, esqueleto de
firmware). Linguagem de negócio, não de desenvolvedor — para o relatório
interno de verificação de código, ver generate_phase2_report.py e
generate_phase3_report.py.

Roda: python backend/scripts/generate_client_report_fase1.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-1-arquitetura-protocolo.pdf"


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
    story.append(Paragraph("Relatório de Arquitetura e Protocolo de Dados — Fase 1", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "O Methane &amp; CO2 Tracker é uma solução de monitoramento contínuo "
        "para detecção precoce de vazamento de metano e CO2 em operações de "
        "Óleo &amp; Gás, com foco em conformidade com a Resolução ANP 712, "
        "requisitos EPA e metas ESG. Esta fase definiu a arquitetura ponta a "
        "ponta — do sensor em campo até a nuvem — e o protocolo de dados que "
        "conecta o hardware ao software, base sobre a qual as demais fases "
        "do MVP são construídas.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquitetura da solução", h2))
    story.append(Paragraph(
        "A solução é composta por quatro camadas, projetadas para operar de "
        "forma confiável mesmo em condições adversas de campo:",
        body,
    ))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Sensor de campo</b> — tecnologia TDLAS (espectroscopia a "
            "laser), adequada para detecção de CH4 e CO2 com baixa "
            "manutenção. Modelos avaliados no orçamento preliminar incluem "
            "opções já certificadas para área classificada (Zona 0), "
            "reduzindo o risco de retrabalho de certificação do sensor "
            "isoladamente.", body)),
        ListItem(Paragraph(
            "<b>Conectividade redundante</b> — enlace principal via LoRaWAN "
            "(baixíssimo consumo de energia, alcance longo, ideal para "
            "monitoramento contínuo remoto), com fallback automático para "
            "rede celular (Cat M1/NB-IoT) caso o enlace principal falhe. "
            "Isso garante continuidade dos dados mesmo em cenários de "
            "interferência ou queda de infraestrutura de rádio.", body)),
        ListItem(Paragraph(
            "<b>Segurança em profundidade no alarme</b> — a lógica de alerta "
            "por concentração roda duplicada: uma vez localmente no próprio "
            "dispositivo (alarme sonoro/luminoso imediato, funciona mesmo "
            "sem nenhuma conectividade) e novamente na nuvem, que é a fonte "
            "de verdade para o dashboard e os relatórios de compliance. O "
            "objetivo é que o alarme de segurança nunca dependa de rede "
            "estar disponível.", body)),
        ListItem(Paragraph(
            "<b>Plataforma em nuvem</b> — recebe, decodifica e armazena as "
            "leituras, e é onde a regra de alerta, os relatórios e (nas "
            "próximas fases) o dashboard e as notificações automáticas são "
            "processados.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Protocolo de dados: por que importa", h2))
    story.append(Paragraph(
        "Cada leitura de sensor é transmitida em um pacote binário compacto "
        "de aproximadamente 19 a 25 bytes — muito abaixo do limite de "
        "payload da rede LoRaWAN mesmo no pior cenário de alcance. Essa "
        "escolha não é um detalhe técnico secundário: quanto menos dados "
        "são transmitidos por leitura, menos energia de rádio o sensor "
        "consome, e maior a autonomia de bateria em campo — um fator direto "
        "de custo operacional em instalações remotas onde troca de bateria "
        "exige deslocamento de equipe. O mesmo contrato de dados é "
        "compartilhado entre o firmware do sensor e o backend na nuvem, "
        "eliminando divergência de interpretação entre as duas pontas.",
        body,
    ))
    story.append(Paragraph(
        "Cada pacote carrega: identificação do sensor, timestamp, tipo de "
        "gás medido (CH4 ou CO2 — suporte a múltiplos gases já previsto "
        "desde esta fase), concentração em ppm, temperatura, nível de "
        "bateria e um indicador de alarme local. Leituras fisicamente "
        "implausíveis (ex: bateria fora de 0-100%, relógio do sensor sem "
        "sincronismo) são identificadas e descartadas antes de chegar ao "
        "banco de dados.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Firmware embarcado", h2))
    story.append(Paragraph(
        "O firmware (plataforma STM32L4, sistema operacional de tempo real "
        "FreeRTOS) está em desenvolvimento em repositório dedicado, com as "
        "tarefas centrais definidas: leitura periódica do sensor, avaliação "
        "do alarme local e transmissão. No momento, o desenvolvimento está "
        "em estágio de prototipagem de bancada — a integração com hardware "
        "de campo definitivo (sensor certificado, gateway, gabinete) "
        "acontece em paralelo à validação da certificação de área "
        "classificada, tratada a seguir.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Certificação de área classificada — risco de cronograma", h2))
    story.append(Paragraph(
        "Ponto de atenção para o planejamento do piloto: a certificação "
        "ATEX/IECEx precisa cobrir o <b>conjunto montado</b> (sensor + "
        "gabinete + cabeamento), não apenas o sensor isoladamente. Isso tem "
        "impacto direto em prazo e orçamento:",
        body,
    ))
    risk_table_data = [
        ["Item", "Impacto pro cronograma do piloto"],
        ["Zona de classificação da área", "Precisa ser definida antes da compra de qualquer equipamento — determina qual categoria de proteção (Ex ia, Ex d, Ex e) é exigida."],
        ["Certificação do conjunto (não só do sensor)", "Tipicamente 4 a 12+ semanas com o organismo certificador — maior risco de prazo do projeto, acima até do desenvolvimento de software."],
        ["Gabinete e cabeamento", "Precisam ser certificados Ex e comprados prontos de fabricante certificado — item frequentemente subestimado no orçamento."],
        ["Mitigação disponível", "Se o prazo da certificação de conjunto não fechar a tempo, é possível iniciar prova de conceito em Zona 2 ou área não classificada, migrando depois — desde que formalizado no Termo de Piloto."],
    ]
    risk_table = Table(risk_table_data, colWidths=[6 * cm, 10.5 * cm])
    risk_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 1 (arquitetura e protocolo): <b>concluída</b>.", body)),
        ListItem(Paragraph("Fase 2 (ingestão de dados e motor de alertas): <b>concluída e validada</b> — ver relatório correspondente.", body)),
        ListItem(Paragraph("Fase 3 (API, notificação automática de alertas e primeiro dashboard): <b>em andamento</b>.", body)),
        ListItem(Paragraph("Orçamento formal (cotação de sensores, gateway e certificação) e definição da zona de classificação da área do piloto seguem como pré-requisitos para a fase de campo.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase1.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
