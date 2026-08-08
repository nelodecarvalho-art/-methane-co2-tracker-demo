"""
Gera o relatório voltado a cliente/operadora de O&G sobre a Fase 9
(hardening de produção e preparação pra demo pública). Linguagem de
negócio, não de desenvolvedor — para o relatório técnico, ver
generate_phase9_report.py.

Roda: python backend/scripts/generate_client_report_fase9.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "cliente-fase-9-hardening-producao-demo-publica.pdf"


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
        "Relatório de Hardening de Produção e Preparação pra Demonstração Pública — Fase 9",
        h2,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Resumo executivo", h2))
    story.append(Paragraph(
        "Com o sistema já em produção real (backend e dashboard "
        "publicados), esta fase usou o próprio ambiente ao vivo como "
        "campo de prova, submetendo-o a testes de ponta a ponta "
        "repetidos. Isso revelou e corrigiu três falhas que só se "
        "manifestam em produção real — impossíveis de reproduzir num "
        "ambiente de desenvolvimento local — além de fechar itens de "
        "segurança e limpar todo dado de teste antes da divulgação "
        "pública.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Três falhas reais de produção corrigidas", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Leituras sendo rejeitadas por diferença de relógio</b> "
            "entre o sensor e o servidor — comum quando um servidor "
            "acabou de reiniciar. O sistema agora tolera essa pequena "
            "diferença, evitando descartar dados válidos.", body)),
        ListItem(Paragraph(
            "<b>E-mails de alerta não estavam saindo</b> — o provedor de "
            "hospedagem bloqueia, por padrão de segurança contra spam, o "
            "canal de envio de e-mail tradicionalmente usado (SMTP). "
            "Trocado pelo canal moderno via API do provedor de e-mail, "
            "que não sofre esse bloqueio. Confirmado: e-mail de alerta "
            "chegando normalmente agora.", body)),
        ListItem(Paragraph(
            "<b>Risco de perda de leitura durante períodos de inatividade "
            "do servidor</b> (o plano gratuito de hospedagem \"desliga\" o "
            "serviço após 15 minutos sem uso, uma característica normal "
            "desse tipo de plano) — corrigido fazendo o sistema de "
            "mensageria guardar as leituras não entregues e reenviá-las "
            "automaticamente quando o servidor volta a responder. Nenhuma "
            "leitura real é mais perdida por esse motivo.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Disponibilidade do serviço mais confiável", h2))
    story.append(Paragraph(
        "O mecanismo que mantinha o servidor acordado estava falhando "
        "silenciosamente na grande maioria das vezes — descoberto durante "
        "a investigação desta fase. Substituído por um serviço externo "
        "dedicado a esse propósito, que também avisa automaticamente por "
        "e-mail caso o servidor fique indisponível no futuro — visibilidade "
        "que não existia antes.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Acesso de demonstração mais seguro", h2))
    story.append(Paragraph(
        "A senha da conta de demonstração pública estava escrita "
        "diretamente no código do site — tecnicamente extraível por "
        "qualquer pessoa com conhecimento técnico, mesmo não aparecendo "
        "na tela. Substituída por um botão \"Entrar como Visitante\" que "
        "concede acesso de demonstração sem nenhuma senha trafegando ou "
        "existindo no código do site, com controles adicionais (o acesso "
        "de visitante nunca pode ganhar permissão de administrador, "
        "mesmo em caso de erro de configuração).",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Controle de permissões (base para o futuro)", h2))
    story.append(Paragraph(
        "Adicionada a distinção entre conta administradora e conta "
        "somente-leitura no banco de dados. Hoje o sistema inteiro ainda "
        "é só de consulta (nenhuma ação de edição existe via tela ou "
        "API), então essa distinção não restringe nada agora — mas "
        "garante que qualquer funcionalidade de edição futura já nasça "
        "protegida por padrão, sem depender de alguém lembrar de "
        "configurar isso manualmente na hora.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Validação completa antes da divulgação", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Suíte de testes automatizados do sistema: todos os testes "
            "aplicáveis ao ambiente atual passaram sem falha.", body)),
        ListItem(Paragraph(
            "Fluxo completo testado novamente em produção depois de "
            "todas as correções: leitura, alerta e e-mail de notificação "
            "confirmados funcionando de ponta a ponta.", body)),
        ListItem(Paragraph(
            "Navegação completa testada diretamente no site publicado: "
            "login normal, acesso de visitante, gráfico de leituras, "
            "lista de alertas e geração do relatório de compliance em "
            "PDF — tudo confirmado funcionando, sem nenhum erro.", body)),
        ListItem(Paragraph(
            "Auditoria de segurança do código: nenhuma senha ou segredo "
            "exposto no repositório, nenhuma vulnerabilidade encontrada "
            "nas bibliotecas do painel (frontend). Uma vulnerabilidade "
            "conhecida foi encontrada numa biblioteca de terceiros do "
            "backend (não específica deste projeto) — a correção exige "
            "uma atualização maior de versão, registrada como prioridade "
            "da próxima fase em vez de aplicada às pressas.", body)),
        ListItem(Paragraph(
            "Todo dado de teste (leituras/alertas sintéticos usados só "
            "para validar o sistema) foi removido do banco de produção "
            "antes desta divulgação — a demonstração pública mostra "
            "apenas os dados fictícios de demonstração pretendidos.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Status e próximos passos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Fase 9 (hardening de produção e preparação pra demo pública): <b>concluída e validada</b>.", body)),
        ListItem(Paragraph("Sistema pronto para divulgação pública (ex: LinkedIn) com dados de demonstração limpos e acesso de visitante seguro.", body)),
        ListItem(Paragraph("Próximo passo recomendado: atualizar a versão de uma biblioteca de terceiros do backend para corrigir a vulnerabilidade identificada na auditoria, com teste de regressão dedicado antes do deploy.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_client_report_fase9.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
