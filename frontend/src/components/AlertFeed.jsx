import { memo } from "react";

function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString();
  } catch {
    return iso;
  }
}

function AlertFeed({ alerts }) {
  const visible = alerts.slice(0, 10);

  return (
    <div className="alert-panel">
      <h2>Recent Alerts</h2>
      {visible.length === 0 ? (
        <div className="no-alerts">No anomalies detected yet. Waiting for data…</div>
      ) : (
        visible.map((a, i) => (
          <div className="alert-item" key={a.id ?? `ws-${i}`}>
            <div className={`alert-severity ${a.severity}`} />
            <div className="alert-body">
              <div className="alert-msg">{a.message}</div>
              <div className="alert-meta">
                {a.sensor_name} &middot; {formatTime(a.timestamp)}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default memo(AlertFeed);
