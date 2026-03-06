import { memo } from "react";

const METRICS = [
  { value: "temperature", label: "Temperature (°F)" },
  { value: "pressure", label: "Pressure (PSI)" },
  { value: "flow_rate", label: "Flow Rate (gal/min)" },
];

const TIME_RANGES = [
  { value: 30, label: "Last 30 sec" },
  { value: 60, label: "Last 1 min" },
  { value: 120, label: "Last 2 min" },
  { value: 300, label: "Last 5 min" },
];

function Filters({
  sensors,
  selectedSensor,
  selectedMetric,
  timeRange,
  onSensorChange,
  onMetricChange,
  onTimeRangeChange,
}) {
  return (
    <div className="filters">
      <label>
        Sensor
        <select value={selectedSensor} onChange={(e) => onSensorChange(e.target.value)}>
          <option value="all">All Sensors</option>
          {sensors.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Metric
        <select value={selectedMetric} onChange={(e) => onMetricChange(e.target.value)}>
          {METRICS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Time Range
        <select
          value={timeRange}
          onChange={(e) => onTimeRangeChange(Number(e.target.value))}
        >
          {TIME_RANGES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export default memo(Filters);
