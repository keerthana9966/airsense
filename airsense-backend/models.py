"""
AirSense — Pydantic Models
Request/response schemas for all API endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


# ── Sensor ────────────────────────────────────────────────────────────────────

class SensorOut(BaseModel):
    id: str
    location: str
    lat: float
    lon: float
    status: str
    aqi: Optional[float]
    pm25: Optional[float]
    co: Optional[float]
    reliability: float
    calibrated: str
    uptime: float


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardOut(BaseModel):
    aqi: float
    aqi_label: str
    pm25: float
    co: float
    temperature: float
    humidity: float
    reliability_score: float
    updated_at: str


# ── Trend ─────────────────────────────────────────────────────────────────────

class TrendOut(BaseModel):
    labels: List[str]
    values: List[float]
    range: str


# ── Pollutants ────────────────────────────────────────────────────────────────

class PollutantItem(BaseModel):
    name: str
    value: float
    unit: str
    max: float
    color: str
    pct: float


class PollutantsOut(BaseModel):
    pollutants: List[PollutantItem]


# ── Forecast ──────────────────────────────────────────────────────────────────

class ForecastItem(BaseModel):
    time: str
    aqi: float
    label: str
    color: str


class ForecastOut(BaseModel):
    forecasts: List[ForecastItem]
    model: str
    interval: str


# ── Reliability ───────────────────────────────────────────────────────────────

class ReliabilityOut(BaseModel):
    health: float
    freshness: float
    stability: float
    density: float
    composite: float


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsStat(BaseModel):
    avg_aqi: float
    peak_aqi: float
    peak_location: str
    peak_hour: str
    active_sensors: int
    offline_sensors: int
    data_points_24h: int


class AnalyticsChartData(BaseModel):
    pm25_weekly: List[float]
    pm25_labels: List[str]
    aqi_distribution: dict
    hourly_exposure: List[float]
    hourly_labels: List[str]
    reliability_trends: dict


class AnalyticsOut(BaseModel):
    stats: AnalyticsStat
    charts: AnalyticsChartData


# ── Route ─────────────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    start: str
    end: str
    mode: str = "driving"


class RouteOption(BaseModel):
    type: str          # cleanest | fastest | balanced
    label: str
    badge: str
    path: str
    exposure: float    # AQI·min
    time_min: int
    distance_km: float
    color: str


class RouteOut(BaseModel):
    routes: List[RouteOption]
    algorithm: str
    start: str
    end: str
    mode: str


# ── Ingest ────────────────────────────────────────────────────────────────────

class ReadingIn(BaseModel):
    sensor_id: str
    aqi: float
    pm25: float
    pm10: float
    co: float
    nox: float
    ozone: float
    temperature: float
    humidity: float
