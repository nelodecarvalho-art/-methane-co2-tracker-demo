"""
Valida o envio de e-mail via Resend usando o MESMO caminho de código do
módulo de alertas — chama app.alerts.notify.send_email_alert diretamente
(STARTTLS + login já implementados lá), não uma implementação SMTP
paralela. Só lê credenciais de os.environ (via app.db.session.settings,
que por sua vez lê o .env carregado abaixo) — nada hardcoded. Não toca no
banco (o Alert de teste é só um objeto em memória, nunca commitado).
Deadline total de 30s.

Roda: python backend/scripts/check_smtp.py
"""
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.alerts.notify import send_email_alert  # noqa: E402
from app.db.session import settings  # noqa: E402
from app.models.orm import Alert  # noqa: E402

TIMEOUT_SECONDS = 30


def main() -> None:
    if not settings.smtp_use_tls:
        print("FAIL: SMTP_USE_TLS não está ativado — o Resend exige STARTTLS na 587")
        sys.exit(1)
    if not settings.smtp_user or not settings.smtp_password:
        print("FAIL: SMTP_USER/SMTP_PASSWORD não configurados no ambiente")
        sys.exit(1)
    if not settings.alert_email_to:
        print("FAIL: ALERT_EMAIL_TO não configurado no ambiente")
        sys.exit(1)

    test_alert = Alert(
        sensor_id="check-smtp-script",
        gas_type="CH4",
        started_at=datetime.now(timezone.utc),
        max_ppm=999.9,
        status="active",
    )

    state: dict = {}
    done = threading.Event()

    def _send() -> None:
        try:
            send_email_alert(test_alert)
        except Exception as exc:  # noqa: BLE001
            state["exc"] = exc
        finally:
            done.set()

    start = time.time()
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    thread.join(timeout=TIMEOUT_SECONDS)

    if not done.is_set():
        print(
            f"FAIL: send_email_alert não retornou em {TIMEOUT_SECONDS}s "
            f"(smtp_host={settings.smtp_host}:{settings.smtp_port})"
        )
        sys.exit(1)
    if "exc" in state:
        exc = state["exc"]
        print(f"FAIL: send_email_alert levantou {exc.__class__.__name__}: {exc}")
        sys.exit(1)

    elapsed = time.time() - start
    print(
        f"PASS: e-mail de teste enviado via {settings.smtp_host}:{settings.smtp_port} "
        f"(STARTTLS) para {settings.alert_email_to} em {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
