"""
AirSense — AI Forecast Service
Simulates RF/XGBoost AQI prediction using weighted moving average + trend extrapolation.
In production this would call a trained sklearn/XGBoost model.
"""

import sqlite3
import statistics
import random
from datetime import datetime


def _aqi_label(aqi: float) -> tuple[str, str]:
    """Return (label, hex_color) for a given AQI value."""
    if aqi <= 50:
        return "Good", "#22d3a5"
    elif aqi <= 100:
        return "Moderate", "#fbbf24"
    elif aqi <= 150:
        return "Unhealthy for Sensitive", "#fb923c"
    elif aqi <= 200:
        return "Unhealthy", "#f87171"
    else:
        return "Very Unhealthy", "#c084fc"


def compute_forecast(conn: sqlite3.Connection) -> list[dict]:
    """
    Produces a 4-step forecast: NOW, +15min, +30min, +1hr.
    Uses a weighted moving average of the last 12 readings across active sensors,
    then applies a slight trend to simulate model output.
    """

    # Gather last 12 zone-wide AQI readings (avg across all active sensors)
    rows = conn.execute("""
        SELECT r.timestamp, AVG(r.aqi) as avg_aqi
        FROM readings r
        JOIN sensors s ON s.id = r.sensor_id
        WHERE s.status != 'offline'
        GROUP BY r.timestamp
        ORDER BY r.timestamp DESC
        LIMIT 12
    """).fetchall()

    if not rows:
        # Fallback if DB empty
        base = 73.0
    else:
        aqis = [r["avg_aqi"] for r in rows if r["avg_aqi"]]
        # Weighted moving average (recent readings weighted more)
        weights = list(range(1, len(aqis) + 1))
        base = sum(a * w for a, w in zip(aqis, weights)) / sum(weights)

    # Slight hour-of-day trend
    hour = datetime.now().hour
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        trend = +0.4  # rush hour rising
    elif 1 <= hour <= 5:
        trend = -0.5  # late night falling
    else:
        trend = random.uniform(-0.2, 0.2)

    forecasts = []
    steps = [
        ("NOW",    0),
        ("+15min", 15),
        ("+30min", 30),
        ("+1hr",   60),
    ]
    for label, minutes in steps:
        # Each step extrapolates the trend + adds small Gaussian noise
        predicted = base + (trend * minutes / 5) + random.gauss(0, 2)
        predicted = round(max(10.0, predicted), 1)
        lbl, color = _aqi_label(predicted)
        forecasts.append({
            "time":  label,
            "aqi":   predicted,
            "label": lbl,
            "color": color,
        })

    return forecasts
