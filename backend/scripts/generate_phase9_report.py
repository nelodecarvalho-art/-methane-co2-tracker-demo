"""
Gera o relatório em PDF da Fase 9 (hardening de produção e preparação pra
demo pública: RBAC mínimo, correção de dois bugs reais de produção
descobertos via smoke test, sessão MQTT persistente, troca do keep-alive,
login de visitante sem credencial exposta, limpeza de dados sintéticos, e
auditoria de segurança/teste completo de encerramento) e salva em
methane-co2-tracker/relatorios/. Script único, roda uma vez ao final da
fase.

Roda: python backend/scripts/generate_phase9_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-9-hardening-producao-demo-publica.pdf"


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
        "Relatório da Fase 9 — Hardening de Produção e Preparação pra Demo Pública",
        h2,
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Escopo desta fase", h2))
    story.append(Paragraph(
        "Com o backend já em produção no Render e o frontend no Vercel "
        "(Fase 8/Part C), esta fase usou o próprio ambiente de produção "
        "como banco de testes real via <i>smoke_publish_ch4.py</i> — o que "
        "revelou dois bugs de produção que nenhum teste local com Mailpit/"
        "Mosquitto teria pego, além de uma lacuna arquitetural real "
        "(perda de leitura durante hibernação). Fechou com RBAC mínimo, "
        "login de visitante sem credencial exposta, limpeza de dados "
        "sintéticos e uma auditoria de segurança/teste completo de "
        "encerramento.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Bugs de produção encontrados e corrigidos", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<b>Timestamp \"do futuro\" rejeitando toda leitura</b> — "
            "<i>ReadingIn.time_not_absurd</i> comparava o timestamp do "
            "sensor contra o relógio do próprio processo sem nenhuma "
            "tolerância; um container recém-acordado/redeployado no "
            "Render tem clock skew real contra o publisher. Corrigido com "
            "<i>FUTURE_TOLERANCE = timedelta(minutes=5)</i>.", body)),
        ListItem(Paragraph(
            "<b>Notificação de alerta por e-mail falhando silenciosamente</b> "
            "— <i>Alert.notified_at</i> nunca era preenchido. Diagnóstico "
            "em duas etapas: primeiro suspeitou-se de timeout curto do "
            "SMTP (aumentado de 5s para 15s), mas o traceback completo do "
            "Render revelou que o <i>socket.connect()</i> pra porta 587 "
            "nunca fecha o handshake — bloqueio de saída SMTP comum em "
            "provedores de nuvem, não um problema de lentidão. Corrigido "
            "trocando SMTP pela <b>API HTTP do Resend</b> (porta 443), "
            "reaproveitando a mesma credencial já configurada.", body)),
        ListItem(Paragraph(
            "<b>Leituras perdidas durante hibernação do serviço</b> — "
            "plano free do Render hiberna após 15min sem request HTTP; "
            "MQTT nunca acorda o processo, então qualquer leitura "
            "publicada nesse intervalo simplesmente desaparecia, sem erro "
            "nenhum registrado. Corrigido com sessão MQTT persistente "
            "(<i>clean_session=False</i> + <i>subscribe(qos=1)</i>) — o "
            "HiveMQ Cloud agora enfileira mensagens não entregues e "
            "reentrega ao reconectar. Reentregas duplicadas (semântica "
            "\"at-least-once\" do QoS1) são detectadas pela chave primária "
            "<i>(time, sensor_id)</i> e descartadas silenciosamente "
            "(log de debug, não mais um erro genérico).", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Confiabilidade do keep-alive", h2))
    story.append(Paragraph(
        "O workflow do GitHub Actions que deveria manter o serviço "
        "acordado a cada 10 minutos foi investigado após uma falha real "
        "em produção e revelou dois problemas: seu próprio timeout de "
        "30s no curl era mais curto que o cold-start real do Render "
        "(35-71s medidos), então uma vez adormecido ele nunca conseguia "
        "reacordar o serviço; e o gatilho <i>schedule</i> do GitHub "
        "Actions não tem SLA de execução, tendo falhado ou sido cancelado "
        "em 29 das últimas 30 execuções (confirmado via API pública do "
        "GitHub). Substituído por <b>UptimeRobot</b> (checagem a cada "
        "5min, alerta automático por e-mail em caso de queda) — infra "
        "dedicada a esse propósito, não um cron best-effort.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("RBAC mínimo (admin/viewer)", h2))
    story.append(Paragraph(
        "Coluna <i>role</i> adicionada a <i>users</i> e dependência "
        "<i>require_admin</i> criada — hoje a API é inteiramente somente "
        "leitura (nenhum endpoint de escrita existe ainda), então nada é "
        "restrito por ela no momento; existe como guarda-corrado pronta "
        "pra qualquer rota de mutação futura já nascer restrita a admin, "
        "em vez de depender de alguém lembrar de adicionar o controle na "
        "hora. Conta pessoal promovida a <i>admin</i>, conta de demo "
        "fixada em <i>viewer</i>.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Login de visitante sem credencial exposta", h2))
    story.append(Paragraph(
        "O formulário de login continha o e-mail/senha da conta de demo "
        "escritos diretamente no código-fonte do frontend — o Vite "
        "embute qualquer <i>VITE_*</i> como texto literal no bundle JS "
        "final, então \"esconder\" isso da tela não impedia ninguém de "
        "extrair a senha inspecionando o bundle. Substituído por "
        "<b>POST /auth/demo-login</b>: emite token sem receber nenhuma "
        "credencial, só funciona se a conta apontada por "
        "<i>DEMO_ACCOUNT_EMAIL</i> tiver <i>role=viewer</i> (travado no "
        "servidor, não no cliente), mesmo rate limit de "
        "<i>/auth/login</i>, expiração mais curta (60min) e log de cada "
        "emissão. Verificado: a senha não existe mais em nenhum lugar de "
        "<i>frontend/src</i> nem no <i>dist/</i> gerado.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Limpeza de dados sintéticos", h2))
    story.append(Paragraph(
        "Dados do sensor <i>smoke-test-ch4</i> (leituras, alertas) usados "
        "só pra validação de pipeline foram removidos do banco de "
        "produção antes da divulgação pública, via script dedicado "
        "(<i>cleanup_smoke_test_data.py</i>) com filtro por igualdade "
        "exata de <i>sensor_id</i> — sem risco de alcançar os sensores "
        "<i>demo-sensor-*</i> usados por <i>seed_demo_data.py</i>.",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Teste completo de encerramento", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Suíte automatizada do backend: 7/7 testes independentes de "
            "infraestrutura local passando (auth, API REST, relatório de "
            "compliance, regra de alerta, detecção de anomalia, roundtrip "
            "protobuf, conexão com o banco). 3 testes que dependem de "
            "Mailpit/Mosquitto locais (Docker) falharam por timeout de "
            "conexão — infraestrutura de dev ausente, não regressão.", body)),
        ListItem(Paragraph(
            "Smoke test completo em produção (após o cold-start real do "
            "plano free): leitura, alerta e notificação por e-mail "
            "confirmados ponta a ponta mais uma vez após todas as "
            "correções desta fase.", body)),
        ListItem(Paragraph(
            "Passagem manual pelo frontend real no navegador, contra a "
            "API de produção: login normal, botão \"Entrar como "
            "Visitante\", gráfico de leituras, tabela de eventos de "
            "alerta, e geração do PDF de compliance — todos confirmados "
            "funcionando (respostas HTTP 200 reais capturadas via rede do "
            "navegador), sem nenhum erro de console.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Auditoria de segurança", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Nenhum <i>.env</i> real rastreado pelo git (só os "
            "<i>.env.example</i> com placeholders); a única credencial "
            "real que já esteve em texto no histórico de commits foi a "
            "senha da conta de demo, já corrigida nesta fase.", body)),
        ListItem(Paragraph(
            "Nenhuma query SQL crua em nenhum lugar do backend — 100% via "
            "ORM (SQLAlchemy), risco de injeção de SQL por concatenação "
            "de string não se aplica.", body)),
        ListItem(Paragraph(
            "Nenhum uso de <i>dangerouslySetInnerHTML</i> ou <i>eval</i> "
            "no frontend — sem vetor óbvio de XSS via renderização.", body)),
        ListItem(Paragraph(
            "JWT com algoritmo travado explicitamente na decodificação "
            "(<i>algorithms=[\"HS256\"]</i>) — não vulnerável ao ataque "
            "clássico de confusão de algoritmo (\"alg=none\").", body)),
        ListItem(Paragraph(
            "Rate limiting em duas camadas: 60/min por IP em toda rota "
            "(default do <i>SlowAPIMiddleware</i>) e 5/min específico em "
            "<i>/auth/login</i> e <i>/auth/demo-login</i>.", body)),
        ListItem(Paragraph(
            "CORS restrito a origem configurada (não wildcard) — "
            "confirmado funcionalmente: a origem real de produção no "
            "Vercel completou chamadas cross-origin sem nenhum erro de "
            "CORS no console do navegador.", body)),
        ListItem(Paragraph(
            "<b>Achado real (pip-audit)</b>: <i>starlette</i> (dependência "
            "transitiva do FastAPI 0.111.1) na versão 0.37.2 tem 9 "
            "vulnerabilidades conhecidas no banco de dados consultado, "
            "com correção disponível em versões mais recentes. FastAPI "
            "tem versão 0.141.1 disponível (pinado hoje em 0.111.1) — "
            "salto grande demais pra aplicar no meio desta auditoria sem "
            "teste de regressão dedicado, dado o histórico do projeto com "
            "resolução de dependências instável (ver incidente de OOM no "
            "build do Render). <b>Recomendação: tratar como item "
            "prioritário da próxima fase</b>, não decisão tomada aqui.", body)),
        ListItem(Paragraph(
            "<i>npm audit</i> nas dependências de produção do frontend: "
            "0 vulnerabilidades encontradas.", body)),
        ListItem(Paragraph(
            "Observação fora do repositório: existe um <i>Senhas.txt</i> "
            "em texto puro na pasta pai do projeto (fora do controle de "
            "versão, não vaza pro git) — recomendação de mover pra um "
            "gerenciador de senhas dedicado, especialmente com este "
            "projeto prestes a ganhar visibilidade pública.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos alterados/criados nesta fase", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["backend/app/ingestion/schemas.py", "Tolerância de 5min no validador de timestamp"],
        ["backend/app/email_sender.py", "Novo — envio de e-mail via API HTTP do Resend"],
        ["backend/app/alerts/notify.py, anomaly/notify.py", "Usam email_sender em vez de smtplib direto"],
        ["backend/app/ingestion/mqtt_consumer.py", "Sessão persistente MQTT (QoS1 + clean_session=False)"],
        ["backend/app/models/orm.py, alembic 0004", "Coluna users.role (admin/viewer)"],
        ["backend/app/api/deps.py", "Dependência require_admin"],
        ["backend/app/api/routers/auth.py", "Novo endpoint POST /auth/demo-login"],
        ["backend/scripts/cleanup_smoke_test_data.py", "Novo — limpeza segura de dados de smoke test"],
        [".github/workflows/keep-alive.yml", "Removido — substituído por UptimeRobot"],
        ["frontend/src/components/LoginForm.tsx", "Credencial de demo removida, botão de visitante"],
        ["render.yaml, .env", "USE_RESEND_HTTP_API, DEMO_ACCOUNT_EMAIL, DEMO_LOGIN_EXPIRE_MINUTES"],
    ]
    files_table = Table(files_table_data, colWidths=[8 * cm, 8.5 * cm])
    files_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d2d2d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    story.append(files_table)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph("Atualizar FastAPI/starlette pra resolver as 9 vulnerabilidades encontradas — precisa de teste de regressão dedicado antes do deploy.", body)),
        ListItem(Paragraph("Campo <i>is_demo</i> genérico no banco — hoje a limpeza de dado sintético ainda depende de lista de sensor_id hardcoded por script.", body)),
        ListItem(Paragraph("RBAC ainda sem nenhuma rota de escrita real pra proteger — útil só quando a primeira rota de mutação for criada.", body)),
        ListItem(Paragraph("Rotação do Senhas.txt fora do repositório pra um gerenciador de senhas dedicado.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase9_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
