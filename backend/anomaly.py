"""
Anomaly detection using z-score deviation from a rolling window.

Approach: compare each new reading against the mean/stddev of the last
WINDOW_SIZE readings.  A z-score above WARNING_THRESHOLD flags a warning;
above CRITICAL_THRESHOLD flags critical.  We require at least MIN_WINDOW
data points before flagging anything to avoid false positives at startup.
"""

import statistics

WINDOW_SIZE = 30
MIN_WINDOW = 5
WARNING_THRESHOLD = 2.0
CRITICAL_THRESHOLD = 3.0


def detect_anomaly(current_value: float, recent_values: list[float], metric_name: str):
    """Return anomaly dict if the value deviates significantly, else None."""
    if len(recent_values) < MIN_WINDOW:
        return None

    mean = statistics.mean(recent_values)
    std = statistics.stdev(recent_values)

    if std == 0:
        return None

    z_score = abs(current_value - mean) / std

    if z_score >= CRITICAL_THRESHOLD:
        severity = "critical"
    elif z_score >= WARNING_THRESHOLD:
        severity = "warning"
    else:
        return None

    return {
        "metric": metric_name,
        "value": round(current_value, 2),
        "mean": round(mean, 2),
        "std_dev": round(std, 2),
        "severity": severity,
        "message": (
            f"{metric_name} reading {current_value:.2f} is "
            f"{'critically ' if severity == 'critical' else ''}abnormal "
            f"(z-score: {z_score:.2f})"
        ),
    }
