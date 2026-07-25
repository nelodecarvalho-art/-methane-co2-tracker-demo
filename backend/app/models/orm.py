from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.db.session import Base


class Sensor(Base):
    __tablename__ = "sensors"

    sensor_id = Column(String, primary_key=True)
    sensor_id_short = Column(Integer, nullable=False, unique=True)
    asset_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    location_desc = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    installed_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="active")


class Reading(Base):
    __tablename__ = "readings"

    time = Column(DateTime(timezone=True), primary_key=True)
    sensor_id = Column(String, ForeignKey("sensors.sensor_id"), primary_key=True)
    gas_type = Column(String, nullable=False)
    concentration_ppm = Column(Float, nullable=False)
    temperature_c = Column(Float)
    battery_pct = Column(Float)
    is_anomaly = Column(Boolean, default=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id = Column(String, ForeignKey("sensors.sensor_id"), nullable=False)
    gas_type = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    max_ppm = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")
    notified_at = Column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
