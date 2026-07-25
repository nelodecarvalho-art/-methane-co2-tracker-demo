"""multi-gas schema: readings.gas_type, concentration_ppm, alerts.gas_type

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # readings é hypertable: precisa dropar o índice que referencia a coluna
    # renomeada antes do rename, e recriar depois.
    op.execute("DROP INDEX IF EXISTS idx_readings_sensor_time;")

    op.alter_column("readings", "ppm_ch4", new_column_name="concentration_ppm")
    op.add_column(
        "readings",
        sa.Column("gas_type", sa.String(), nullable=False, server_default="CH4"),
    )
    op.alter_column("readings", "gas_type", server_default=None)

    op.execute(
        "CREATE INDEX idx_readings_sensor_time ON readings (sensor_id, time DESC);"
    )
    op.create_index(
        "idx_readings_sensor_gas_time", "readings", ["sensor_id", "gas_type", "time"]
    )

    op.add_column(
        "alerts",
        sa.Column("gas_type", sa.String(), nullable=False, server_default="CH4"),
    )
    op.alter_column("alerts", "gas_type", server_default=None)


def downgrade() -> None:
    op.drop_column("alerts", "gas_type")

    op.drop_index("idx_readings_sensor_gas_time", table_name="readings")
    op.execute("DROP INDEX IF EXISTS idx_readings_sensor_time;")
    op.drop_column("readings", "gas_type")
    op.alter_column("readings", "concentration_ppm", new_column_name="ppm_ch4")
    op.execute(
        "CREATE INDEX idx_readings_sensor_time ON readings (sensor_id, time DESC);"
    )
