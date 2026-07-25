"""
AirSense Backend — FastAPI Application
Hyper-local air quality monitoring REST API

Endpoints:
  GET  /api/dashboard       → hero metrics (AQI, PM2.5, CO, temp, humidity)
  GET  /api/sensors         → full sensor list with latest readings
  GET  /api/trend           → AQI time-series (?range=24h|7d|30d)
  GET  /api/pollutants      → breakdown of all pollutants
  GET  /api/forecast        → AI-powered AQI predictions (RF/XGBoost simulation)
  GET  /api/reliability     → sensor reliability score breakdown
  GET  /api/analytics       → analytics stats + chart data
  POST /api/route           → smart route recommendation (Dijkstra/A*)
  POST /api/sensor/reading  → ingest new IoT sensor reading

Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import statistics
import math

from database import get_connection, init_db
from models import (
    DashboardOut, SensorOut, TrendOut,
    PollutantsOut, PollutantItem,
    ForecastOut, ReliabilityOut,
    AnalyticsOut, AnalyticsStat, AnalyticsChartData,
    RouteRequest, RouteOut, RouteOption,
    ReadingIn,
)
from services.reliability import compute_reliability
from services.forecast import compute_forecast
from services.route import compute_routes

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AirSense API",
    description="Hyper-local air quality monitoring for Hyderabad · IoT ESP32 Fleet · Layer 0–3",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow the HTML frontend served from any origin
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _aqi_label(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy for Sensitive Groups"
    if aqi <= 200:  return "Unhealthy"
    return "Very Unhealthy"


def _latest_zone_reading(conn) -> dict:
    """Average of the most recent reading per online sensor."""
    row = conn.execute("""
        SELECT
            AVG(r.aqi)         as aqi,
            AVG(r.pm25)        as pm25,
            AVG(r.co)          as co,
            AVG(r.temperature) as temperature,
            AVG(r.humidity)    as humidity,
            MAX(r.timestamp)   as updated_at
        FROM readings r
        JOIN sensors s ON s.id = r.sensor_id
        WHERE s.status != 'offline'
          AND r.timestamp = (
            SELECT MAX(r2.timestamp) FROM readings r2 WHERE r2.sensor_id = r.sensor_id
          )
    """).fetchone()
    return dict(row) if row else {}


# ── GET /api/dashboard ────────────────────────────────────────────────────────

@app.get("/api/dashboard", response_model=DashboardOut, tags=["Dashboard"])
def get_dashboard():
    """Hero panel: current zone-wide AQI and environmental metrics."""
    conn = get_connection()
    try:
        latest = _latest_zone_reading(conn)
        rel    = compute_reliability(conn)

        if not latest.get("aqi"):
            raise HTTPException(500, "No readings available yet.")

        aqi = round(latest["aqi"], 1)
        return DashboardOut(
            aqi=aqi,
            aqi_label=_aqi_label(aqi),
            pm25=round(latest["pm25"], 1),
            co=round(latest["co"], 2),
            temperature=round(latest["temperature"], 1),
            humidity=round(latest["humidity"], 1),
            reliability_score=rel["composite"],
            updated_at=latest["updated_at"],
        )
    finally:
        conn.close()


# ── GET /api/sensors ──────────────────────────────────────────────────────────

@app.get("/api/sensors", response_model=list[SensorOut], tags=["Sensors"])
def get_sensors():
    """Full sensor list with their latest readings and reliability scores."""
    conn = get_connection()
    try:
        sensors = conn.execute("SELECT * FROM sensors ORDER BY id").fetchall()
        result = []
        for s in sensors:
            if s["status"] == "offline":
                result.append(SensorOut(
                    id=s["id"], location=s["location"],
                    lat=s["lat"], lon=s["lon"],
                    status="offline",
                    aqi=None, pm25=None, co=None,
                    reliability=s["reliability"],
                    calibrated=s["calibrated"],
                    uptime=s["uptime"],
                ))
                continue

            reading = conn.execute("""
                SELECT aqi, pm25, co FROM readings
                WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT 1
            """, (s["id"],)).fetchone()

            result.append(SensorOut(
                id=s["id"], location=s["location"],
                lat=s["lat"], lon=s["lon"],
                status=s["status"],
                aqi=round(reading["aqi"], 1) if reading else None,
                pm25=round(reading["pm25"], 1) if reading else None,
                co=round(reading["co"], 2) if reading else None,
                reliability=s["reliability"],
                calibrated=s["calibrated"],
                uptime=s["uptime"],
            ))
        return result
    finally:
        conn.close()


# ── GET /api/trend ────────────────────────────────────────────────────────────

@app.get("/api/trend", response_model=TrendOut, tags=["Analytics"])
def get_trend(range: str = Query("24h", pattern="^(24h|7d|30d)$")):
    """AQI time-series for the trend chart. Supports 24h, 7d, 30d."""
    conn = get_connection()
    try:
        now = datetime.now()

        if range == "24h":
            since = (now - timedelta(hours=24)).isoformat(timespec="seconds")
            rows = conn.execute("""
                SELECT strftime('%H:00', r.timestamp) as label, AVG(r.aqi) as avg_aqi
                FROM readings r
                JOIN sensors s ON s.id = r.sensor_id
                WHERE s.status != 'offline' AND r.timestamp >= ?
                GROUP BY strftime('%H', r.timestamp)
                ORDER BY r.timestamp ASC
            """, (since,)).fetchall()
            labels = [r["label"] for r in rows]
            values = [round(r["avg_aqi"], 1) for r in rows]

        elif range == "7d":
            since = (now - timedelta(days=7)).isoformat(timespec="seconds")
            rows = conn.execute("""
                SELECT strftime('%w', r.timestamp) as dow, AVG(r.aqi) as avg_aqi
                FROM readings r
                JOIN sensors s ON s.id = r.sensor_id
                WHERE s.status != 'offline' AND r.timestamp >= ?
                GROUP BY strftime('%Y-%m-%d', r.timestamp)
                ORDER BY r.timestamp ASC
            """, (since,)).fetchall()
            day_names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
            labels = [day_names[int(r["dow"])] for r in rows] if rows else ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            values = [round(r["avg_aqi"], 1) for r in rows]

        else:  # 30d
            since = (now - timedelta(days=30)).isoformat(timespec="seconds")
            rows = conn.execute("""
                SELECT strftime('%b %d', r.timestamp) as label, AVG(r.aqi) as avg_aqi
                FROM readings r
                JOIN sensors s ON s.id = r.sensor_id
                WHERE s.status != 'offline' AND r.timestamp >= ?
                GROUP BY strftime('%Y-%m-%d', r.timestamp)
                ORDER BY r.timestamp ASC
            """, (since,)).fetchall()
            labels = [r["label"] for r in rows]
            values = [round(r["avg_aqi"], 1) for r in rows]

        return TrendOut(labels=labels, values=values, range=range)
    finally:
        conn.close()


# ── GET /api/pollutants ───────────────────────────────────────────────────────

@app.get("/api/pollutants", response_model=PollutantsOut, tags=["Dashboard"])
def get_pollutants():
    """Latest zone-wide pollutant breakdown."""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT
                AVG(r.pm25)   as pm25,
                AVG(r.pm10)   as pm10,
                AVG(r.co)     as co,
                AVG(r.nox)    as nox,
                AVG(r.ozone)  as ozone,
                AVG(r.humidity) as humidity
            FROM readings r
            JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline'
              AND r.timestamp = (
                SELECT MAX(r2.timestamp) FROM readings r2 WHERE r2.sensor_id = r.sensor_id
              )
        """).fetchone()

        pm25    = round(row["pm25"] or 34.2, 1)
        pm10    = round(row["pm10"] or 51.0, 1)
        co      = round(row["co"]   or 1.2,  2)
        nox     = round(row["nox"]  or 38.5, 1)
        ozone   = round(row["ozone"] or 42.1, 1)
        humidity = round(row["humidity"] or 62.0, 1)

        pollutants = [
            PollutantItem(name="PM2.5",   value=pm25,    unit="µg/m³", max=150, color="#f87171", pct=round(pm25/150*100,1)),
            PollutantItem(name="PM10",    value=pm10,    unit="µg/m³", max=250, color="#fb923c", pct=round(pm10/250*100,1)),
            PollutantItem(name="CO",      value=co,      unit="ppm",   max=10,  color="#fbbf24", pct=round(co/10*100,1)),
            PollutantItem(name="NOx",     value=nox,     unit="ppb",   max=200, color="#a78bfa", pct=round(nox/200*100,1)),
            PollutantItem(name="Ozone",   value=ozone,   unit="ppb",   max=160, color="#60a5fa", pct=round(ozone/160*100,1)),
            PollutantItem(name="Humidity",value=humidity, unit="%",    max=100, color="#22d3a5", pct=humidity),
        ]
        return PollutantsOut(pollutants=pollutants)
    finally:
        conn.close()


# ── GET /api/forecast ─────────────────────────────────────────────────────────

@app.get("/api/forecast", response_model=ForecastOut, tags=["AI"])
def get_forecast():
    """AI-powered AQI forecast: NOW, +15min, +30min, +1hr (RF/XGBoost simulation)."""
    conn = get_connection()
    try:
        forecasts = compute_forecast(conn)
        return ForecastOut(
            forecasts=forecasts,
            model="RF/XGBoost ensemble",
            interval="±8 AQI units",
        )
    finally:
        conn.close()


# ── GET /api/reliability ──────────────────────────────────────────────────────

@app.get("/api/reliability", response_model=ReliabilityOut, tags=["Sensors"])
def get_reliability():
    """Composite sensor reliability score breakdown."""
    conn = get_connection()
    try:
        rel = compute_reliability(conn)
        return ReliabilityOut(**rel)
    finally:
        conn.close()


# ── GET /api/analytics ────────────────────────────────────────────────────────

@app.get("/api/analytics", response_model=AnalyticsOut, tags=["Analytics"])
def get_analytics():
    """Analytics page data: stat boxes + chart datasets."""
    conn = get_connection()
    try:
        now = datetime.now()
        since_24h = (now - timedelta(hours=24)).isoformat(timespec="seconds")
        since_7d  = (now - timedelta(days=7)).isoformat(timespec="seconds")

        # ── Stats ─────────────────────────────────────────────────────────────
        avg_row = conn.execute("""
            SELECT AVG(r.aqi) as avg_aqi, MAX(r.aqi) as peak_aqi
            FROM readings r
            JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline' AND r.timestamp >= ?
        """, (since_24h,)).fetchone()

        peak_row = conn.execute("""
            SELECT r.aqi, s.location, strftime('%H:00', r.timestamp) as hour
            FROM readings r JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline' AND r.timestamp >= ?
            ORDER BY r.aqi DESC LIMIT 1
        """, (since_24h,)).fetchone()

        sensor_counts = conn.execute("""
            SELECT status, COUNT(*) as cnt FROM sensors GROUP BY status
        """).fetchall()
        status_map = {r["status"]: r["cnt"] for r in sensor_counts}

        data_points = conn.execute(
            "SELECT COUNT(*) as cnt FROM readings WHERE timestamp >= ?",
            (since_24h,)
        ).fetchone()["cnt"]

        stats = AnalyticsStat(
            avg_aqi=round(avg_row["avg_aqi"] or 73, 1),
            peak_aqi=round(avg_row["peak_aqi"] or 95, 1),
            peak_location=peak_row["location"] if peak_row else "HITEC City",
            peak_hour=peak_row["hour"] if peak_row else "09:00",
            active_sensors=status_map.get("online", 0) + status_map.get("warning", 0),
            offline_sensors=status_map.get("offline", 0),
            data_points_24h=data_points,
        )

        # ── PM2.5 weekly bar chart ─────────────────────────────────────────────
        pm25_rows = conn.execute("""
            SELECT strftime('%w', r.timestamp) as dow,
                   strftime('%Y-%m-%d', r.timestamp) as date,
                   AVG(r.pm25) as avg_pm25
            FROM readings r
            JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline' AND r.timestamp >= ?
            GROUP BY date ORDER BY date ASC
        """, (since_7d,)).fetchall()
        day_names = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
        pm25_labels = [day_names[int(r["dow"])] for r in pm25_rows]
        pm25_values = [round(r["avg_pm25"], 1) for r in pm25_rows]

        # ── AQI distribution doughnut ──────────────────────────────────────────
        dist_rows = conn.execute("""
            SELECT
                SUM(CASE WHEN aqi <= 50 THEN 1 ELSE 0 END)  as good,
                SUM(CASE WHEN aqi > 50  AND aqi <= 100 THEN 1 ELSE 0 END) as moderate,
                SUM(CASE WHEN aqi > 100 AND aqi <= 150 THEN 1 ELSE 0 END) as unhealthy,
                SUM(CASE WHEN aqi > 150 THEN 1 ELSE 0 END) as very_unhealthy,
                COUNT(*) as total
            FROM readings r
            JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline' AND r.timestamp >= ?
        """, (since_7d,)).fetchone()
        total = dist_rows["total"] or 1
        aqi_dist = {
            "Good":           round(dist_rows["good"] / total * 100, 1),
            "Moderate":       round(dist_rows["moderate"] / total * 100, 1),
            "Unhealthy":      round(dist_rows["unhealthy"] / total * 100, 1),
            "Very Unhealthy": round(dist_rows["very_unhealthy"] / total * 100, 1),
        }

        # ── Hourly exposure line chart ─────────────────────────────────────────
        exp_rows = conn.execute("""
            SELECT strftime('%H', r.timestamp) as hr, AVG(r.aqi) as avg_aqi
            FROM readings r
            JOIN sensors s ON s.id = r.sensor_id
            WHERE s.status != 'offline' AND r.timestamp >= ?
            GROUP BY hr ORDER BY hr ASC
            LIMIT 12
        """, (since_24h,)).fetchall()
        hourly_labels  = [f"{r['hr']}:00" for r in exp_rows]
        # Exposure ≈ avg_aqi × (time_per_slot_minutes) simplified to AQI·min
        hourly_exposure = [round(r["avg_aqi"] * 5, 1) for r in exp_rows]

        charts = AnalyticsChartData(
            pm25_weekly=pm25_values,
            pm25_labels=pm25_labels,
            aqi_distribution=aqi_dist,
            hourly_exposure=hourly_exposure,
            hourly_labels=hourly_labels,
            reliability_trends={},   # extended in a future version
        )

        return AnalyticsOut(stats=stats, charts=charts)
    finally:
        conn.close()


# ── POST /api/route ───────────────────────────────────────────────────────────

@app.post("/api/route", response_model=RouteOut, tags=["Routes"])
def find_route(body: RouteRequest):
    """Smart route recommendation using modified Dijkstra/A*."""
    routes_raw = compute_routes(body.start, body.end, body.mode)
    routes = [RouteOption(**r) for r in routes_raw]
    return RouteOut(
        routes=routes,
        algorithm="Modified Dijkstra/A*  w(e) = 0.4·dist + 0.6·exposure",
        start=body.start,
        end=body.end,
        mode=body.mode,
    )


# ── POST /api/sensor/reading ──────────────────────────────────────────────────

@app.post("/api/sensor/reading", status_code=201, tags=["IoT Ingest"])
def ingest_reading(body: ReadingIn):
    """Ingest a new IoT sensor reading (ESP32 push endpoint)."""
    conn = get_connection()
    try:
        sensor = conn.execute(
            "SELECT id FROM sensors WHERE id = ?", (body.sensor_id,)
        ).fetchone()
        if not sensor:
            raise HTTPException(404, f"Sensor '{body.sensor_id}' not found.")

        conn.execute(
            """INSERT INTO readings
               (sensor_id, timestamp, aqi, pm25, pm10, co, nox, ozone, temperature, humidity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                body.sensor_id,
                datetime.now().isoformat(timespec="seconds"),
                body.aqi, body.pm25, body.pm10, body.co,
                body.nox, body.ozone, body.temperature, body.humidity,
            )
        )
        conn.commit()
        return {"status": "ok", "message": f"Reading ingested for {body.sensor_id}"}
    finally:
        conn.close()


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "AirSense API", "version": "2.0.0"}
