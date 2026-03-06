"""
SensorWatch — FastAPI backend.

Provides REST endpoints for sensors/readings/alerts, a WebSocket for live
streaming, and a background simulator that generates data every 2 seconds.
"""

import asyncio
import datetime
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import SessionLocal, Sensor, Reading, Alert, init_db
from simulator import init_sensors, tick


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, data: dict):
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                self.connections.remove(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Background simulator
# ---------------------------------------------------------------------------
async def simulator_loop():
    await asyncio.sleep(1)
    while True:
        payload = await asyncio.to_thread(tick)
        await manager.broadcast(payload)
        await asyncio.sleep(2)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_sensors()
    task = asyncio.create_task(simulator_loop())
    yield
    task.cancel()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="SensorWatch", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.get("/sensors")
def list_sensors(db: Session = Depends(get_db)):
    sensors = db.query(Sensor).all()
    result = []
    for s in sensors:
        latest = (
            db.query(Reading)
            .filter(Reading.sensor_id == s.id)
            .order_by(Reading.timestamp.desc())
            .first()
        )
        result.append(
            {
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "sensor_type": s.sensor_type,
                "status": s.status,
                "latest_reading": (
                    {
                        "temperature": latest.temperature,
                        "pressure": latest.pressure,
                        "flow_rate": latest.flow_rate,
                        "timestamp": latest.timestamp.isoformat(),
                    }
                    if latest
                    else None
                ),
            }
        )
    return result


@app.get("/readings")
def get_readings(
    sensor_id: int,
    from_ts: Optional[str] = Query(None, alias="from"),
    to_ts: Optional[str] = Query(None, alias="to"),
    limit: int = 200,
    db: Session = Depends(get_db),
):
    query = db.query(Reading).filter(Reading.sensor_id == sensor_id)
    if from_ts:
        query = query.filter(
            Reading.timestamp >= datetime.datetime.fromisoformat(from_ts)
        )
    if to_ts:
        query = query.filter(
            Reading.timestamp <= datetime.datetime.fromisoformat(to_ts)
        )
    readings = query.order_by(Reading.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "sensor_id": r.sensor_id,
            "temperature": r.temperature,
            "pressure": r.pressure,
            "flow_rate": r.flow_rate,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in reversed(readings)
    ]


@app.get("/alerts")
def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .join(Sensor)
        .order_by(Alert.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "sensor_id": a.sensor_id,
            "sensor_name": a.sensor.name,
            "metric": a.metric,
            "value": a.value,
            "mean": a.mean,
            "severity": a.severity,
            "message": a.message,
            "timestamp": a.timestamp.isoformat(),
        }
        for a in alerts
    ]


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------
@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Serve built frontend (production / run.py)
# ---------------------------------------------------------------------------
_frontend_dist = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"
)
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
