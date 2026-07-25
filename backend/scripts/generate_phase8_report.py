"""
Gera o relatório em PDF da Fase 8 (frente de hardware: esqueleto de
firmware, documentação atualizada, BOM, checklist ATEX/IECEx e diagramas de
blocos) e salva em methane-co2-tracker/relatorios/. Script único, roda uma
vez ao final da fase.

Roda: python backend/scripts/generate_phase8_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-8-frente-hardware.pdf"


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
        "Relatório da Fase 8 — Frente de Hardware (Firmware, Documentação, BOM, ATEX, Diagramas)",
        h2,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: até aqui, todo o desenvolvimento das Fases 2-7 "
        "foi do lado de software (backend, ingestão, dashboard, "
        "autenticação). Esta fase trata o lado de hardware do MVP, que "
        "ficou em aberto desde a Fase 1: esqueleto de firmware do "
        "dispositivo de campo, atualização da documentação de integração "
        "hardware↔cloud para refletir o pipeline real (não só o desenho "
        "original), revisão do checklist de certificação ATEX/IECEx, "
        "atualização do BOM para o segundo gás (CO2), e diagramas de "
        "blocos de sistema e de dispositivo.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Novo repositório <b>methane-co2-tracker-firmware</b>, irmão "
            "de <i>methane-co2-tracker</i> (não uma subpasta) — consistente "
            "com a referência que já existia em <i>README.md</i>. Linguagem "
            "e stack (C + nanopb + FreeRTOS em STM32L4) já estavam "
            "decididas em <i>docs/protocol-spec.md</i>, não foi uma escolha "
            "nova desta fase.", body)),
        ListItem(Paragraph(
            "<b>Código Protobuf/nanopb gerado de verdade</b>, não simulado "
            "à mão: rodou-se o pipeline real (protoc via grpc_tools + "
            "nanopb_generator) contra o <i>.proto</i> compartilhado com o "
            "backend, produzindo <i>generated/sensor_reading.pb.{c,h}</i> "
            "válidos (tamanho máximo confirmado: 38 bytes, dentro do "
            "orçamento de payload do LoRaWAN).", body)),
        ListItem(Paragraph(
            "Pipeline de firmware em 3 tasks FreeRTOS conectadas por filas: "
            "<i>task_sample</i> → <i>task_alert</i> → <i>task_transmit</i>. "
            "Decisão de projeto notável: uma falha de comunicação com o "
            "sensor (não apenas uma leitura ruim) ainda é propagada pelo "
            "pipeline com o bit de falha (bit2 do payload) setado, em vez "
            "de ser silenciosamente descartada — evita que o dispositivo "
            "\"desapareça\" silenciosamente do dashboard quando na "
            "verdade está com o sensor com defeito.", body)),
        ListItem(Paragraph(
            "Regra de alerta sustentado duplicada no firmware (janela "
            "circular em memória fixa, sem banco de dados), com os "
            "mesmos limiares default do backend (500ppm CH4 / 5000ppm "
            "CO2 / janela de 120s) — mesma filosofia da Fase 2: o "
            "dispositivo precisa soar alarme local mesmo se toda a "
            "conectividade cair.", body)),
        ListItem(Paragraph(
            "<b>Limitação explícita</b>: o esqueleto de firmware não "
            "compila neste ambiente — faltam o toolchain ARM, o runtime C "
            "do nanopb, o HAL real do STM32CubeMX e as stacks "
            "LoRaWAN/celular, todos fora do escopo por exigirem hardware "
            "físico e bibliotecas de terceiros vendorizadas. Verificação "
            "feita por <b>revisão de código</b>, não por build/flash real "
            "— isso está documentado no <i>README.md</i> do novo "
            "repositório, não escondido.", body)),
        ListItem(Paragraph(
            "Diagramas de blocos (Mermaid, versionável em texto) com nota "
            "explícita de que a norma ABNT NBR 5444 (às vezes citada nesse "
            "contexto) trata de instalações elétricas prediais, não de "
            "diagrama de blocos de sistema eletrônico embarcado — os "
            "diagramas seguem convenções gerais de apresentação técnica "
            "(NBR 10068/8402) e símbolos IEC 60617 onde aplicável, sem "
            "alegar uma conformidade normativa que não existe.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["methane-co2-tracker-firmware/README.md", "Escopo, limitações, como regenerar o nanopb"],
        ["methane-co2-tracker-firmware/proto/sensor_reading.proto", "Cópia idêntica do .proto do backend"],
        ["methane-co2-tracker-firmware/generated/sensor_reading.pb.{c,h}", "Gerado de verdade via protoc+nanopb"],
        ["methane-co2-tracker-firmware/src/task_sample.c", "Amostragem do sensor (10s), forward de falhas de comunicação"],
        ["methane-co2-tracker-firmware/src/task_alert.c", "Janela sustentada local + flags de bateria/falha"],
        ["methane-co2-tracker-firmware/src/task_transmit.c", "Serialização nanopb + fallback LoRaWAN→celular"],
        ["methane-co2-tracker-firmware/src/{sensor,radio,time}_hal.c", "Stubs de HAL, TODOs claros pro hardware real"],
        ["methane-co2-tracker-firmware/Makefile", "Referência de include paths e toolchain esperado"],
        ["docs/hardware-cloud-integration.md", "Atualizado com o pipeline real das Fases 2-6"],
        ["docs/atex-certification-checklist.md", "+ item sobre certificação do sensor de CO2"],
        ["docs/bom.md", "+ sensor TDLAS de CO2 (Cubic GasTDL-3100)"],
        ["docs/block-diagrams.md", "2 diagramas Mermaid (sistema e dispositivo de campo)"],
    ]
    files_table = Table(files_table_data, colWidths=[9 * cm, 7.5 * cm])
    files_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
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
            "Geração do código nanopb <b>executada de verdade</b> (não "
            "simulada) contra o <i>.proto</i> real do backend — confirma "
            "que o contrato binário compartilhado é válido para o "
            "gerador que o firmware real usaria.", body)),
        ListItem(Paragraph(
            "Diagramas de blocos renderizados via Artifact e conferidos "
            "visualmente antes de fechar a fase — sintaxe Mermaid validada, "
            "não apenas escrita e assumida correta.", body)),
        ListItem(Paragraph(
            "Firmware: <b>revisão de código apenas</b>, sem build/flash "
            "(sem toolchain ARM disponível neste ambiente) — declarado "
            "explicitamente, não apresentado como testado.", body)),
        ListItem(Paragraph(
            "Pesquisa feita para fundamentar a citação da Resolução ANP "
            "(ver Fase 5) e para a norma de diagrama de blocos — em ambos "
            "os casos optou-se por linguagem honesta em vez de citar uma "
            "norma que não foi possível confirmar.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Firmware compilável/flashável — exige toolchain ARM real, runtime C do nanopb vendorizado, stack LoRaWAN (ex: LoRaMac-node) e driver real do sensor escolhido.", body)),
        ListItem(Paragraph("Aquisição e cotação formal dos componentes do BOM — os valores continuam sendo estimativas de mercado, não cotações.", body)),
        ListItem(Paragraph("Certificação de conjunto ATEX/IECEx real — processo de 4-12+ semanas com organismo certificador, não iniciado.", body)),
        ListItem(Paragraph("Bring-up em hardware físico (placa STM32 Nucleo LoRa de prototipagem, sensor real) — próximo marco natural da frente de hardware.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase8_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
