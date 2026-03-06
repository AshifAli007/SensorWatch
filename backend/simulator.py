"""
Sensor data simulator.

Generates realistic readings for 5 industrial sensors every 2 seconds,
with a configurable probability of injecting abnormal spikes.
"""

import random
import datetime
from database import SessionLocal, Sensor, Reading, Alert
from anomaly import detect_anomaly, WINDOW_SIZE

SENSOR_CONFIGS = [
    {"name": "Sensor-A1", "location": "North Field", "sensor_type": "pressure-temp"},
    {"name": "Sensor-B2", "location": "East Refinery", "sensor_type": "pressure-temp"},
    {"name": "Sensor-C3", "location": "South Pipeline", "sensor_type": "flow-temp"},
    {"name": "Sensor-D4", "location": "West Station", "sensor_type": "pressure-flow"},
    {"name": "Sensor-E5", "location": "Central Hub", "sensor_type": "multi"},
]

BASE = {"temperature": 75.0, "pressure": 150.0, "flow_rate": 200.0}
NOISE = {"temperature": 2.0, "pressure": 5.0, "flow_rate": 10.0}
SPIKE_PROBABILITY = 0.05
SPIKE_MAGNITUDE = (3.5, 6.0)


def init_sensors():
    db = SessionLocal()
    try:
        for cfg in SENSOR_CONFIGS:
            if not db.query(Sensor).filter(Sensor.name == cfg["name"]).first():
                db.add(Sensor(**cfg))
        db.commit()
    finally:
        db.close()


def _generate_value(base: float, noise: float) -> float:
    return round(base + random.gauss(0, noise), 2)


def generate_reading():
    """Return (temperature, pressure, flow_rate) with occasional spikes."""
    temp = _generate_value(BASE["temperature"], NOISE["temperature"])
    pressure = _generate_value(BASE["pressure"], NOISE["pressure"])
    flow = _generate_value(BASE["flow_rate"], NOISE["flow_rate"])

    if random.random() < SPIKE_PROBABILITY:
        target = random.choice(["temperature", "pressure", "flow_rate"])
        magnitude = random.uniform(*SPIKE_MAGNITUDE)
        direction = random.choice([-1, 1])
        if target == "temperature":
            temp = round(BASE["temperature"] + direction * magnitude * NOISE["temperature"], 2)
        elif target == "pressure":
            pressure = round(BASE["pressure"] + direction * magnitude * NOISE["pressure"], 2)
        else:
            flow = round(BASE["flow_rate"] + direction * magnitude * NOISE["flow_rate"], 2)

    return temp, pressure, flow


def tick():
    """
    Run one simulator tick: generate readings for all sensors,
    detect anomalies, persist to DB, and return broadcast payload.
    """
    db = SessionLocal()
    broadcast = {"readings": [], "alerts": []}
    now = datetime.datetime.utcnow()

    try:
        sensors = db.query(Sensor).all()

        for sensor in sensors:
            recent = (
                db.query(Reading)
                .filter(Reading.sensor_id == sensor.id)
                .order_by(Reading.timestamp.desc())
                .limit(WINDOW_SIZE)
                .all()
            )
            recent_temps = [r.temperature for r in recent]
            recent_pressures = [r.pressure for r in recent]
            recent_flows = [r.flow_rate for r in recent]

            temp, pressure, flow = generate_reading()

            reading = Reading(
                sensor_id=sensor.id,
                temperature=temp,
                pressure=pressure,
                flow_rate=flow,
                timestamp=now,
            )
            db.add(reading)
            db.flush()

            new_status = "normal"
            for metric, value, window in [
                ("temperature", temp, recent_temps),
                ("pressure", pressure, recent_pressures),
                ("flow_rate", flow, recent_flows),
            ]:
                anomaly = detect_anomaly(value, window, metric)
                if anomaly:
                    alert = Alert(
                        sensor_id=sensor.id,
                        reading_id=reading.id,
                        metric=anomaly["metric"],
                        value=anomaly["value"],
                        mean=anomaly["mean"],
                        std_dev=anomaly["std_dev"],
                        severity=anomaly["severity"],
                        message=anomaly["message"],
                        timestamp=now,
                    )
                    db.add(alert)
                    broadcast["alerts"].append(
                        {
                            "sensor_name": sensor.name,
                            "sensor_id": sensor.id,
                            **anomaly,
                            "timestamp": now.isoformat(),
                        }
                    )
                    if anomaly["severity"] == "critical":
                        new_status = "critical"
                    elif anomaly["severity"] == "warning" and new_status != "critical":
                        new_status = "warning"

            sensor.status = new_status

            broadcast["readings"].append(
                {
                    "sensor_id": sensor.id,
                    "sensor_name": sensor.name,
                    "temperature": temp,
                    "pressure": pressure,
                    "flow_rate": flow,
                    "status": new_status,
                    "timestamp": now.isoformat(),
                }
            )

        db.commit()
    except Exception as e:
        print(f"Simulator error: {e}")
        db.rollback()
    finally:
        db.close()

    return broadcast
