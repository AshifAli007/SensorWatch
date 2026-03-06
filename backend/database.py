import datetime
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./sensorwatch.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)
    status = Column(String, default="normal")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    readings = relationship("Reading", back_populates="sensor", lazy="dynamic")
    alerts = relationship("Alert", back_populates="sensor", lazy="dynamic")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    temperature = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    flow_rate = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    sensor = relationship("Sensor", back_populates="readings")

    __table_args__ = (
        Index("ix_readings_sensor_timestamp", "sensor_id", "timestamp"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    reading_id = Column(Integer, ForeignKey("readings.id"), nullable=False)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    mean = Column(Float, nullable=False)
    std_dev = Column(Float, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    sensor = relationship("Sensor", back_populates="alerts")


def init_db():
    Base.metadata.create_all(bind=engine)
