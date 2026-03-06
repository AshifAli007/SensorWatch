# SensorWatch — Real-Time Field Monitoring System

A full-stack application that simulates 500+ industrial sensors, ingests time-series data, detects anomalies in real time, and displays everything on a live dashboard.

## Quick Start

### Option A — Docker (recommended)

```bash
docker-compose up --build
```

Open **http://localhost:3000** in your browser.

### Option B — Local Python + Node

```bash
python run.py
```

This installs dependencies, builds the frontend, and starts the server at **http://localhost:8000**.

### Option C — Development (hot reload)

Terminal 1 — Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Terminal 2 — Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** (Vite dev server proxies API calls to the backend).

---

## Architecture

```
┌────────────────┐      WebSocket        ┌──────────────────┐
│  React + Vite  │◄────────────────────►  │  FastAPI Backend  │
│  (Recharts)    │      REST API          │  + Simulator      │
└────────────────┘                        │  + Anomaly Detect │
                                          └────────┬─────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │   SQLite DB  │
                                            └─────────────┘
```

### Data Layer

- **SQLite** chosen for zero-config local setup. Schema has three tables:
  - `sensors` — metadata (name, location, type, status)
  - `readings` — time-series data (temperature, pressure, flow_rate per sensor)
  - `alerts` — detected anomalies with severity and context
- Composite index on `(sensor_id, timestamp)` for efficient time-range queries.
- The simulator inserts all 5 sensor readings in a single transaction per tick, reducing write overhead.

### Anomaly Detection

- **Z-score method**: each new reading is compared against the mean and standard deviation of the last 30 readings for that sensor/metric.
- Thresholds: **|z| ≥ 2** → warning, **|z| ≥ 3** → critical.
- Requires at least 5 historical readings before flagging (avoids false positives during startup).
- Trade-off: z-score is simple and effective for stationary data. A production system might use exponential moving averages or a model that accounts for drift/seasonality.

### Real-Time Flow

1. Background async task calls `simulator.tick()` every 2 seconds.
2. Each tick generates readings for all sensors (with ~5% spike probability).
3. Anomaly detection runs per-metric before the reading is committed.
4. New readings + alerts are broadcast to all connected WebSocket clients.
5. The React dashboard appends new data points to its in-memory buffer and re-renders the chart.

### Frontend

- **Recharts** for the live time-series chart (lightweight, React-native).
- Sensor status grid uses color-coded cards (green/yellow/red).
- Alert feed shows the 10 most recent anomalies with severity bars.
- Filters: sensor, metric, and time range — all applied client-side from the in-memory buffer.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/sensors` | GET | List all sensors with current status and latest reading |
| `/readings?sensor_id=X&from=Y&to=Z` | GET | Fetch readings for a sensor in a time range |
| `/alerts?limit=N` | GET | List detected anomalies (default 50) |
| `/ws/live` | WebSocket | Stream real-time readings and alerts |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest test_anomaly.py -v
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, uvicorn |
| Frontend | React 18, Vite, Recharts |
| Database | SQLite |
| Deployment | Docker, nginx, docker-compose |
