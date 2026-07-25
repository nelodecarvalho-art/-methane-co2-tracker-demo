"""
Gera o relatório em PDF da Fase 5 (relatório de compliance ANP/EPA via API)
e salva em methane-co2-tracker/relatorios/. Script único, roda uma vez ao
final da fase — não confundir com o relatório de compliance em si, que é
uma funcionalidade do produto gerada sob demanda via GET /reports/compliance
(ver app/reports/compliance_report.py).

Roda: python backend/scripts/generate_phase5_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-5-relatorio-compliance-anp-epa.pdf"


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
    story.append(Paragraph("Relatório da Fase 5 — Relatório de Compliance ANP/EPA", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "Escopo desta fase: expor, como funcionalidade real do produto (não "
        "um script de desenvolvedor), um relatório PDF sob demanda que "
        "resume os dados de monitoramento e os eventos de alerta de um "
        "período — o artefato que o operador usa como trilha de auditoria "
        "no seu próprio processo de compliance regulatório.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Implementado como <b>endpoint da API</b> "
            "(<i>GET /reports/compliance?start=&amp;end=</i>), não como "
            "script standalone: é a primeira funcionalidade em "
            "<i>app/reports/</i>, pensada para ser chamada sob demanda "
            "para qualquer período, inclusive futuramente a partir de um "
            "botão no dashboard. Protegida pela mesma autenticação por "
            "API key das demais rotas.", body)),
        ListItem(Paragraph(
            "Conteúdo do relatório: resumo de leituras por sensor+gás "
            "(contagem, ppm mínimo/médio/máximo, contagem de leituras "
            "marcadas como anomalia pela Fase 4) e uma tabela de eventos "
            "de alerta no espírito de um registro <b>LDAR</b> (Leak "
            "Detection and Repair) — início, fim, duração, ppm máximo, "
            "status e se houve notificação.", body)),
        ListItem(Paragraph(
            "Decisão deliberada de <b>não citar um número de resolução "
            "ANP específico</b>: o README do projeto menciona \"Resolução "
            "712\", mas essa numeração não foi confirmada em pesquisa — "
            "encontramos a Resolução ANP 790/2019 (frequência de "
            "monitoramento) e 791/2019 (metas de redução de GEE no "
            "RenovaBio), e um estudo preliminar de 2025 da ANP propondo "
            "regulação de metano com LDAR e medição direta, mas nada com "
            "o número \"712\" tratando de metano. Optou-se por linguagem "
            "regulatória genérica no relatório em vez de arriscar uma "
            "citação incorreta em um documento de compliance.", body)),
        ListItem(Paragraph(
            "O relatório inclui um <b>disclaimer explícito</b>: é um "
            "artefato de apoio ao processo de compliance do operador "
            "(monitoramento contínuo + trilha de auditoria), não uma "
            "submissão regulatória pronta nem um inventário de emissões — "
            "os sensores medem concentração (ppm), não taxa de emissão "
            "mássica (kg/h ou tCO2e), que exigiria modelagem de dispersão "
            "ou instrumentação de vazão mássica fora do escopo atual.", body)),
        ListItem(Paragraph(
            "Nenhuma migração de schema foi necessária — o relatório "
            "consulta as tabelas <i>readings</i>, <i>alerts</i> e "
            "<i>sensors</i> já existentes.", body)),
        ListItem(Paragraph(
            "Validação de entrada: período com <i>end &lt;= start</i> "
            "retorna 400; período sem nenhum dado ainda gera um PDF "
            "válido (relatório vazio, não erro) — importante para um "
            "operador não ser bloqueado ao consultar um período sem "
            "eventos.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["backend/app/reports/compliance_report.py", "Monta o PDF: resumo de leituras + eventos de alerta"],
        ["backend/app/api/routers/reports.py", "Endpoint GET /reports/compliance"],
        ["backend/app/api/main.py", "Registro do novo router"],
        ["backend/tests/test_compliance_report.py", "Teste standalone — executado, OK"],
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
            "test_compliance_report.py: <b>executado com sucesso</b> — "
            "cobre autenticação obrigatória (401 sem API key), validação "
            "de período (400 com end&lt;=start), PDF válido retornado com "
            "dados seedados (leituras, alerta e leitura anômala) e PDF "
            "válido também para um período vazio.", body)),
        ListItem(Paragraph(
            "PDF gerado inspecionado visualmente em um cenário de exemplo "
            "(10 leituras, 1 anomalia, 1 alerta resolvido) — layout, "
            "tabelas e disclaimer conferidos.", body)),
        ListItem(Paragraph(
            "Suíte completa de testes standalone reexecutada após a "
            "mudança (test_api.py incluído, por registrar um novo router "
            "no app FastAPI) — <b>nenhuma regressão</b>.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Botão no dashboard para gerar o relatório pela UI — hoje só via chamada direta à API.", body)),
        ListItem(Paragraph("Notificação automática dedicada a anomalias (hoje: só a flag is_anomaly, sem e-mail/webhook).", body)),
        ListItem(Paragraph("Confirmação jurídica/regulatória formal do enquadramento ANP/EPA exato aplicável ao cliente final — o relatório é propositalmente genérico até essa validação.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase5_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
