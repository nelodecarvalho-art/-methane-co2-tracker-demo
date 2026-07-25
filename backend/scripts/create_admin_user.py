"""
Cria o primeiro usuário (email + senha) — não é um endpoint público de
cadastro, é um script rodado uma vez manualmente. Recusa se o e-mail já
existir (idempotente, não duplica).

Roda: python backend/scripts/create_admin_user.py --email a@b.com --password ...
(Do host, sem estar dentro do container: DB_HOST=localhost python ...)
"""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.orm import User  # noqa: E402


def create_user(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).one_or_none()
        if existing is not None:
            print(f"ERRO: já existe um usuário com o e-mail {email}")
            sys.exit(1)

        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"OK: usuário criado (id={user.id}, email={user.email})")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário para login na API/dashboard")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    if len(args.password) < 8:
        print("ERRO: senha precisa ter pelo menos 8 caracteres")
        sys.exit(1)

    create_user(args.email, args.password)


if __name__ == "__main__":
    main()
