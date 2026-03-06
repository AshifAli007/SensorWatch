import { useState, useCallback, useEffect, useRef } from "react";
import useWebSocket from "./hooks/useWebSocket";
import SensorGrid from "./components/SensorGrid";
import LiveChart from "./components/LiveChart";
import AlertFeed from "./components/AlertFeed";
import Filters from "./components/Filters";
import "./App.css";

const MAX_READINGS_PER_SENSOR = 150;

const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_URL = `${wsProtocol}//${window.location.host}/ws/live`;

export default function App() {
  const [sensors, setSensors] = useState([]);
  const [readings, setReadings] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [selectedSensor, setSelectedSensor] = useState("all");
  const [selectedMetric, setSelectedMetric] = useState("temperature");
  const [timeRange, setTimeRange] = useState(120);
  const [connected, setConnected] = useState(false);
  const wsConnected = useRef(false);

  useEffect(() => {
    fetch("/sensors")
      .then((r) => r.json())
      .then((data) => {
        setSensors(data);
        data.forEach((sensor) => {
          fetch(`/readings?sensor_id=${sensor.id}&limit=150`)
            .then((r) => r.json())
            .then((sensorReadings) => {
              setReadings((prev) => ({ ...prev, [sensor.id]: sensorReadings }));
            });
        });
      })
      .catch(() => {});

    fetch("/alerts?limit=20")
      .then((r) => r.json())
      .then(setAlerts)
      .catch(() => {});
  }, []);

  const handleWsMessage = useCallback((data) => {
    if (!wsConnected.current) {
      wsConnected.current = true;
      setConnected(true);
    }

    if (data.readings) {
      setReadings((prev) => {
        const next = { ...prev };
        data.readings.forEach((r) => {
          const arr = [...(next[r.sensor_id] || []), r];
          next[r.sensor_id] = arr.slice(-MAX_READINGS_PER_SENSOR);
        });
        return next;
      });

      setSensors((prev) =>
        prev.map((s) => {
          const update = data.readings.find((r) => r.sensor_id === s.id);
          if (!update) return s;
          return {
            ...s,
            status: update.status,
            latest_reading: {
              temperature: update.temperature,
              pressure: update.pressure,
              flow_rate: update.flow_rate,
              timestamp: update.timestamp,
            },
          };
        })
      );
    }

    if (data.alerts?.length) {
      setAlerts((prev) => [...data.alerts, ...prev].slice(0, 50));
    }
  }, []);

  useWebSocket(WS_URL, handleWsMessage);

  return (
    <div className="app">
      <header className="header">
        <h1>
          <span>Sensor</span>Watch
        </h1>
        <div className="connection-label">
          <span className={`status-dot ${connected ? "connected" : "disconnected"}`} />
          {connected ? "Live" : "Connecting…"}
        </div>
      </header>

      <SensorGrid sensors={sensors} />

      <Filters
        sensors={sensors}
        selectedSensor={selectedSensor}
        selectedMetric={selectedMetric}
        timeRange={timeRange}
        onSensorChange={setSelectedSensor}
        onMetricChange={setSelectedMetric}
        onTimeRangeChange={setTimeRange}
      />

      <div className="main-content">
        <LiveChart
          readings={readings}
          sensors={sensors}
          selectedSensor={selectedSensor}
          selectedMetric={selectedMetric}
          timeRange={timeRange}
        />
        <AlertFeed alerts={alerts} />
      </div>
    </div>
  );
}
