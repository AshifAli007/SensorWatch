import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const SENSOR_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
];

const METRIC_LABELS = {
  temperature: "Temperature (°F)",
  pressure: "Pressure (PSI)",
  flow_rate: "Flow Rate (gal/min)",
};

function formatTick(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

function cutoffISO(seconds) {
  return new Date(Date.now() - seconds * 1000).toISOString();
}

export default function LiveChart({
  readings,
  sensors,
  selectedSensor,
  selectedMetric,
  timeRange,
}) {
  const chartData = useMemo(() => {
    const cutoff = cutoffISO(timeRange);

    if (selectedSensor === "all") {
      const timeMap = new Map();
      Object.entries(readings).forEach(([sensorId, list]) => {
        const sensor = sensors.find((s) => s.id === Number(sensorId));
        if (!sensor) return;
        list.forEach((r) => {
          if (r.timestamp < cutoff) return;
          const key = r.timestamp;
          if (!timeMap.has(key)) {
            timeMap.set(key, { timestamp: r.timestamp });
          }
          timeMap.get(key)[sensor.name] = r[selectedMetric];
        });
      });
      return Array.from(timeMap.values()).sort((a, b) =>
        a.timestamp.localeCompare(b.timestamp)
      );
    }

    const list = readings[selectedSensor] || [];
    return list
      .filter((r) => r.timestamp >= cutoff)
      .map((r) => ({
        timestamp: r.timestamp,
        [METRIC_LABELS[selectedMetric]]: r[selectedMetric],
      }));
  }, [readings, sensors, selectedSensor, selectedMetric, timeRange]);

  const lineKeys = useMemo(() => {
    if (selectedSensor === "all") {
      return sensors.map((s) => s.name);
    }
    return [METRIC_LABELS[selectedMetric]];
  }, [sensors, selectedSensor, selectedMetric]);

  return (
    <div className="chart-panel">
      <h2>
        Live Readings — {METRIC_LABELS[selectedMetric]}
        {selectedSensor !== "all" && sensors.length > 0 && (
          <span style={{ fontWeight: 400, color: "var(--text-secondary)", marginLeft: 8 }}>
            {sensors.find((s) => s.id === Number(selectedSensor))?.name}
          </span>
        )}
      </h2>

      {chartData.length === 0 ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: 300,
            color: "var(--text-muted)",
            fontSize: "0.9rem",
          }}
        >
          Waiting for readings…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTick}
              stroke="var(--text-muted)"
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
              minTickGap={60}
            />
            <YAxis
              stroke="var(--text-muted)"
              tick={{ fontSize: 11 }}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: "0.82rem",
              }}
              labelFormatter={formatTick}
            />
            <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
            {lineKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={SENSOR_COLORS[i % SENSOR_COLORS.length]}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3 }}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
