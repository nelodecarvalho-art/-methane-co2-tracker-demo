"""
Gera o relatório técnico voltado a cliente/operadora de O&G sobre a Fase 2
(ingestão de dados e motor de alertas). Linguagem de negócio, não de
desenvolvedor — para o relatório interno de verificação de código, ver
generate_phase2_report.py.

Roda: python backend/scripts/generate_client_report_fase2.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-2-ingestao-alertas.pdf"


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
    story.append(Paragraph("Relatório de Ingestão de Dados e Motor de Alertas — Fase 2", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Nesta fase foi implementado e validado, de ponta a ponta, o "
        "caminho que transforma leituras brutas dos sensores em campo em "
        "alertas acionáveis: recepção do dado, verificação de integridade, "
        "armazenamento histórico e avaliação da condição de risco. Esta é a "
        "camada que sustenta os dashboards e relatórios de compliance das "
        "próximas fases.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Pipeline de recepção de dados", h2))
    story.append(Paragraph(
        "Cada leitura enviada por um sensor passa por três etapas antes de "
        "se tornar um dado confiável no sistema:",
        body,
    ))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Decodificação</b> — o pacote binário compacto enviado pelo "
            "sensor (ver relatório da Fase 1) é traduzido para um formato "
            "utilizável pelo sistema.", body)),
        ListItem(Paragraph(
            "<b>Validação</b> — leituras fisicamente implausíveis são "
            "identificadas e descartadas automaticamente: nível de bateria "
            "fora da faixa 0-100%, concentração fora de qualquer faixa "
            "plausível, ou timestamp de um sensor com relógio "
            "dessincronizado (uma falha comum de campo, que sem essa "
            "verificação poderia gerar uma leitura fantasma datada de "
            "1970).", body)),
        ListItem(Paragraph(
            "<b>Armazenamento</b> — a leitura validada é gravada em um "
            "banco de dados de série temporal, otimizado para consultas "
            "rápidas por período e por sensor — a base que vai alimentar os "
            "relatórios de compliance ANP/EPA e o dashboard da Fase 3/4.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Robustez operacional", h2))
    story.append(Paragraph(
        "O sistema foi projetado para que uma falha pontual nunca vire uma "
        "falha geral: uma mensagem corrompida ou um sensor com defeito é "
        "registrado e descartado, sem interromper a recepção dos demais "
        "sensores. Em caso de queda de conexão com a rede de sensores, o "
        "serviço reconecta automaticamente. Isso foi verificado com testes "
        "que simulam falhas reais, incluindo o envio proposital de uma "
        "mensagem corrompida durante a operação normal.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Motor de alertas: por que “sustentado” e não instantâneo", h2))
    story.append(Paragraph(
        "O alerta de concentração elevada só é disparado quando a leitura "
        "permanece acima do limite de segurança por um período sustentado "
        "(padrão: 2 minutos contínuos), configurável por tipo de gás. Essa "
        "é uma decisão deliberada de produto: um pico curto e isolado é "
        "frequentemente ruído de sensor, não um vazamento real — disparar "
        "alerta nesse caso treina a equipe de campo a ignorar alarmes "
        "(“fadiga de alarme”), o que é mais perigoso a longo prazo do que "
        "um atraso de poucos minutos na detecção de um vazamento real e "
        "contínuo. O sistema já suporta dois gases desde esta fase (metano "
        "e CO2), cada um com seu próprio limite configurável, e encerra o "
        "alerta automaticamente assim que a concentração volta a níveis "
        "seguros — sem necessidade de intervenção manual.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação", h2))
    story.append(Paragraph(
        "Toda a lógica descrita acima foi testada contra a infraestrutura "
        "real de banco de dados e de rede de mensagens (não apenas em "
        "simulação isolada), com resultado positivo e reprodutível: "
        "leituras corretas são gravadas, leituras inválidas são "
        "descartadas sem interromper o serviço, e o alerta abre e fecha "
        "corretamente conforme a condição de risco evolui.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 2 (ingestão e motor de alertas): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Fase 3 (em andamento): API para consumo externo dos dados, notificação automática de alertas por e-mail/webhook, e primeira versão do dashboard visual.", body)),
        ListItem(Paragraph("Ainda não incluído: detecção de anomalia por machine learning, relatório automático de compliance ANP/EPA, e aprofundamento do dashboard — previstos para fases seguintes.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase2.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
