import pytest
from anomaly import detect_anomaly, WARNING_THRESHOLD, CRITICAL_THRESHOLD

STABLE_WINDOW = [75.0, 75.1, 74.9, 75.2, 74.8, 75.0, 75.1]


def test_normal_reading_returns_none():
    result = detect_anomaly(75.05, STABLE_WINDOW, "temperature")
    assert result is None


def test_warning_detected():
    result = detect_anomaly(75.3, STABLE_WINDOW, "temperature")
    assert result is not None
    assert result["severity"] == "warning"
    assert result["metric"] == "temperature"


def test_critical_detected():
    result = detect_anomaly(76.0, STABLE_WINDOW, "temperature")
    assert result is not None
    assert result["severity"] == "critical"


def test_insufficient_data_returns_none():
    result = detect_anomaly(999.0, [75.0, 75.1, 74.9], "temperature")
    assert result is None


def test_zero_stddev_returns_none():
    result = detect_anomaly(100.0, [75.0] * 10, "pressure")
    assert result is None


def test_negative_deviation_detected():
    result = detect_anomaly(74.5, STABLE_WINDOW, "temperature")
    assert result is not None
    assert result["severity"] in ("warning", "critical")


def test_return_shape():
    result = detect_anomaly(76.0, STABLE_WINDOW, "flow_rate")
    assert set(result.keys()) == {"metric", "value", "mean", "std_dev", "severity", "message"}
