import { memo } from "react";

const METRIC_LABELS = {
  temperature: "Temp",
  pressure: "PSI",
  flow_rate: "Flow",
};

const UNITS = {
  temperature: "°F",
  pressure: " PSI",
  flow_rate: " gal/min",
};

function SensorCard({ sensor }) {
  const lr = sensor.latest_reading;
  return (
    <div className={`sensor-card ${sensor.status}`}>
      <div className="name">{sensor.name}</div>
      <div className="location">{sensor.location}</div>
      <span className={`badge ${sensor.status}`}>{sensor.status}</span>
      {lr && (
        <>
          {["temperature", "pressure", "flow_rate"].map((m) => (
            <div className="reading-row" key={m}>
              <span>{METRIC_LABELS[m]}</span>
              <span>
                {lr[m]?.toFixed(1)}
                {UNITS[m]}
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function SensorGrid({ sensors }) {
  if (!sensors.length) {
    return (
      <div className="sensor-grid">
        {[...Array(5)].map((_, i) => (
          <div className="sensor-card normal" key={i} style={{ opacity: 0.4, minHeight: 120 }}>
            <div className="name">Loading…</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="sensor-grid">
      {sensors.map((s) => (
        <SensorCard key={s.id} sensor={s} />
      ))}
    </div>
  );
}

export default memo(SensorGrid);
