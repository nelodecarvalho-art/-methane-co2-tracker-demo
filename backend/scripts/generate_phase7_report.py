"""
Gera o relatório em PDF da Fase 7 (autenticação JWT individual,
substituindo a chave de API única compartilhada) e salva em
methane-co2-tracker/relatorios/. Script único.

Reconstrução retroativa (2026-08-08): a Fase 7 nunca teve relatório
gerado na época. Este script foi escrito depois, baseado só em evidência
verificável no repositório — não em memória de sessões passadas:
- Os relatórios reais das Fases 3, 5 e 6 (generate_phase3_report.py etc.,
  já no repo, escritos na época) documentam explicitamente o mecanismo
  anterior (require_api_key / X-API-Key / settings.api_key_secret /
  ApiKeyGate.tsx) como vigente até a Fase 6, e listam repetidamente "login
  individual por usuário" como pendência.
- O código de autenticação foi lido exatamente como existia no commit
  `707028a` ("Initial commit") via `git show 707028a:<path>` — não o
  código atual, que já tem RBAC/demo-login adicionados depois na Fase 9.
Este repositório tem só 16 commits no total; o commit inicial já chega
com as Fases 1-7 inteiras "esmagadas" juntas, então não existe um diff
git isolado só da Fase 7 — daí a reconstrução por leitura direta do
snapshot em vez de comparação de commits.

Roda: python backend/scripts/generate_phase7_report.py
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
OUTPUT_PATH = PROJECT_ROOT / "relatorios" / "fase-7-autenticacao-jwt-individual.pdf"


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
    story.append(Paragraph("Relatório da Fase 7 — Autenticação JWT Individual", h2))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "<i>Nota: relatório reconstruído retroativamente em 2026-08-08 — "
        "a Fase 7 nunca teve PDF gerado na época. Todo o conteúdo abaixo "
        "vem de evidência verificável no repositório (relatórios reais "
        "das Fases 3/5/6 já commitados, e leitura do código de "
        "autenticação exatamente como existia no commit 707028a), não de "
        "memória de sessão. Este repositório tem só 16 commits no total; "
        "o commit inicial já chega com as Fases 1-7 esmagadas juntas, "
        "então não existe diff git isolado só desta fase.</i>",
        small,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Escopo desta fase", h2))
    story.append(Paragraph(
        "Substituir a chave de API única compartilhada (header "
        "<i>X-API-Key</i> validado contra <i>settings.api_key_secret</i>, "
        "sem sessão/cookie — mecanismo descrito explicitamente nos "
        "relatórios das Fases 3, 5 e 6) por autenticação individual por "
        "usuário via JWT (e-mail + senha com hash).",
        body,
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Decisões de arquitetura desta fase", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "<i>backend/alembic/versions/0003_add_users_table.py</i>: "
            "nova tabela <b>users</b> (id autoincrement, email único, "
            "password_hash, created_at com server_default now()) — "
            "revisão 0003, sobre a 0002.", body)),
        ListItem(Paragraph(
            "<i>backend/app/auth/security.py</i>: hash de senha via "
            "bcrypt. Detalhe de segurança notável: <b>verify_password</b> "
            "roda o bcrypt.checkpw contra um hash dummy fixo quando o "
            "e-mail informado não existe no banco — garante tempo de "
            "resposta igual em ambos os casos, para não vazar por timing "
            "se um e-mail está cadastrado ou não. Criação/validação de "
            "JWT via HS256, payload com sub (user id) e exp (expiração).", body)),
        ListItem(Paragraph(
            "<i>backend/app/api/deps.py</i>: <b>require_user</b> — valida "
            "o Bearer token e recarrega o usuário do banco a cada chamada "
            "(stateless-per-call, mesma filosofia do resto do projeto), "
            "401 genérico em qualquer caso de falha (credenciais "
            "ausentes, token inválido, usuário não encontrado), sem "
            "distinguir o motivo exato pro cliente.", body)),
        ListItem(Paragraph(
            "<i>backend/app/api/routers/auth.py</i>: POST /auth/login, "
            "rate limit de 5/minuto.", body)),
        ListItem(Paragraph(
            "Routers readings, devices, alerts e reports migrados de "
            "require_api_key para require_user — confirmado em cada um "
            "via <i>dependencies=[Depends(require_user)]</i> na "
            "declaração do APIRouter.", body)),
        ListItem(Paragraph(
            "<i>main.py</i>: CORS allow_headers trocado para "
            "[\"Authorization\", \"Content-Type\"] (era X-API-Key), "
            "allow_methods ganhou POST (necessário pra /auth/login).", body)),
        ListItem(Paragraph(
            "<i>create_admin_user.py</i>: script não-interativo com "
            "--email e --password como argumentos de linha de comando "
            "nesta versão original. <b>Nota</b>: passar a senha via "
            "--password foi corrigido depois (commit 35239e7, fora do "
            "escopo desta fase) pra usar getpass interativo, evitando "
            "senha salva no histórico do shell.", body)),
        ListItem(Paragraph(
            "Frontend: <i>App.tsx</i> guarda o JWT em localStorage sob a "
            "chave <b>mct_access_token</b>; <i>LoginForm.tsx</i> novo, "
            "com campos de e-mail e senha.", body)),
    ], bulletType="bullet"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Arquivos entregues (snapshot desta fase)", h2))
    files_table_data = [
        ["Arquivo", "Papel"],
        ["backend/alembic/versions/0003_add_users_table.py", "Cria a tabela users"],
        ["backend/app/auth/security.py", "Hash de senha (bcrypt) e criação/validação de JWT"],
        ["backend/app/api/deps.py", "Dependência require_user"],
        ["backend/app/api/routers/auth.py", "Endpoint POST /auth/login"],
        ["backend/app/api/routers/{readings,devices,alerts,reports}.py", "Migrados de require_api_key para require_user"],
        ["backend/app/api/main.py", "CORS ajustado (Authorization, POST)"],
        ["backend/app/api/schemas.py", "LoginRequest / TokenResponse"],
        ["backend/scripts/create_admin_user.py", "Criação de usuário via CLI"],
        ["backend/tests/test_auth.py", "Suíte de testes de autenticação"],
        ["frontend/src/components/LoginForm.tsx", "Formulário de login (e-mail + senha)"],
        ["frontend/src/App.tsx", "Armazenamento do token (mct_access_token)"],
    ]
    files_table = Table(files_table_data, colWidths=[10 * cm, 6.5 * cm])
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
    story.append(Paragraph(
        "<i>backend/tests/test_auth.py</i> cobre, com asserções "
        "explícitas no próprio arquivo: login válido (200), senha errada "
        "(401), e-mail inexistente (401), endpoint protegido chamado sem "
        "token (401), token malformado (401), token expirado (401), e "
        "endpoint protegido com token válido (200) — 7 casos confirmados "
        "no código do teste.",
        body,
    ))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Não incluído nesta fase (próximos passos, conforme registrado na época)", h2))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "A Fase 7 fecha exatamente o item que os relatórios das "
            "Fases 3, 5 e 6 vinham listando repetidamente como pendência "
            "(\"login individual por usuário, hoje: chave única "
            "compartilhada\").", body)),
        ListItem(Paragraph(
            "Nenhum shim de compatibilidade foi mantido — "
            "API_KEY_SECRET foi removido sem retrocompatibilidade.", body)),
    ], bulletType="bullet"))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Gerado automaticamente por backend/scripts/generate_phase7_report.py", small))

    doc.build(story)


def main() -> None:
    build_pdf(OUTPUT_PATH)
    print(f"OK: relatório gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
