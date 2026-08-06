"""users.role: RBAC mínimo (admin/viewer)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="viewer"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
