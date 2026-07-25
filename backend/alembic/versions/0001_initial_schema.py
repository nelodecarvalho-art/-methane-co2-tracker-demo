"""initial schema: sensors, readings (hypertable), alerts

Revision ID: 0001
Revises:
Create Date: 2026-07-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sensors",
        sa.Column("sensor_id", sa.String(), primary_key=True),
        sa.Column("sensor_id_short", sa.Integer(), nullable=False, unique=True),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location_desc", sa.String()),
        sa.Column("lat", sa.Float()),
        sa.Column("lon", sa.Float()),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )

    op.create_table(
        "readings",
        sa.Column("time", sa.DateTime(timezone=True), primary_key=True),
        sa.Column(
            "sensor_id",
            sa.String(),
            sa.ForeignKey("sensors.sensor_id"),
            primary_key=True,
        ),
        sa.Column("ppm_ch4", sa.Float(), nullable=False),
        sa.Column("temperature_c", sa.Float()),
        sa.Column("battery_pct", sa.Float()),
        sa.Column("is_anomaly", sa.Boolean(), server_default=sa.false()),
    )
    # create_hypertable é específico do TimescaleDB e não tem equivalente
    # direto na API do Alembic, por isso via SQL cru. Em hosts de Postgres
    # gerenciado sem a extensão (ex: Render, Neon — usados no ambiente de
    # demo pública) a tabela some fica uma tabela comum: funciona
    # perfeitamente para o volume pequeno de dados da demo, só perde a
    # otimização de particionamento por tempo que o TimescaleDB dá em
    # produção com volume real.
    conn = op.get_bind()
    timescaledb_available = (
        conn.execute(
            sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'")
        ).scalar()
        is not None
    )
    if timescaledb_available:
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        op.execute("SELECT create_hypertable('readings', 'time');")

    # Índice com ordenação DESC é Postgres padrão, funciona com ou sem
    # TimescaleDB.
    op.execute(
        "CREATE INDEX idx_readings_sensor_time ON readings (sensor_id, time DESC);"
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "sensor_id", sa.String(), sa.ForeignKey("sensors.sensor_id"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("max_ppm", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("notified_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_alerts_sensor_status", "alerts", ["sensor_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_alerts_sensor_status", table_name="alerts")
    op.drop_table("alerts")
    op.execute("DROP INDEX IF EXISTS idx_readings_sensor_time;")
    op.drop_table("readings")
    op.drop_table("sensors")
