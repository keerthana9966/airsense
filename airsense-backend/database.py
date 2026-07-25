"""
AirSense — SQLite Database
Handles schema creation and seeding of realistic sensor + reading data.
"""

import sqlite3
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "airsense.db"

# ── Sensor definitions (12 Hyderabad IoT nodes) ──────────────────────────────
SENSORS = [
    {"id": "SNS-001", "location": "Banjara Hills, Road No.12",  "lat": 17.4156, "lon": 78.4347, "status": "online",  "reliability": 0.91, "calibrated": "2026-03-25", "uptime": 99.2},
    {"id": "SNS-002", "location": "HITEC City, Cyber Gateway",  "lat": 17.4495, "lon": 78.3808, "status": "warning", "reliability": 0.62, "calibrated": "2026-02-18", "uptime": 87.4},
    {"id": "SNS-003", "location": "Jubilee Hills, Check Post",   "lat": 17.4239, "lon": 78.4073, "status": "online",  "reliability": 0.88, "calibrated": "2026-03-20", "uptime": 97.8},
    {"id": "SNS-004", "location": "Panjagutta, Rly Station",    "lat": 17.4314, "lon": 78.4487, "status": "offline", "reliability": 0.00, "calibrated": "2026-01-10", "uptime": 52.1},
    {"id": "SNS-005", "location": "Ameerpet, Metro Station",    "lat": 17.4374, "lon": 78.4487, "status": "online",  "reliability": 0.79, "calibrated": "2026-03-18", "uptime": 95.5},
    {"id": "SNS-006", "location": "Kukatpally, KPHB Colony",    "lat": 17.4849, "lon": 78.3996, "status": "online",  "reliability": 0.94, "calibrated": "2026-03-27", "uptime": 99.9},
    {"id": "SNS-007", "location": "Madhapur, Durgam Cheruvu",  "lat": 17.4401, "lon": 78.3827, "status": "online",  "reliability": 0.85, "calibrated": "2026-03-22", "uptime": 96.3},
    {"id": "SNS-008", "location": "Gachibowli, Stadium Rd",     "lat": 17.4412, "lon": 78.3499, "status": "online",  "reliability": 0.92, "calibrated": "2026-03-26", "uptime": 98.7},
    {"id": "SNS-009", "location": "Kondapur, Mindspace",        "lat": 17.4615, "lon": 78.3741, "status": "online",  "reliability": 0.89, "calibrated": "2026-03-24", "uptime": 98.1},
    {"id": "SNS-010", "location": "Miyapur, Metro Hub",         "lat": 17.4963, "lon": 78.3688, "status": "online",  "reliability": 0.93, "calibrated": "2026-03-28", "uptime": 99.5},
    {"id": "SNS-011", "location": "LB Nagar, Intersection",    "lat": 17.3445, "lon": 78.5519, "status": "online",  "reliability": 0.77, "calibrated": "2026-03-15", "uptime": 93.2},
    {"id": "SNS-012", "location": "Uppal, Ring Road",           "lat": 17.4051, "lon": 78.5590, "status": "online",  "reliability": 0.81, "calibrated": "2026-03-19", "uptime": 95.0},
]

# Base AQI per sensor (realistic Hyderabad values)
BASE_AQI = {
    "SNS-001": 68, "SNS-002": 95, "SNS-003": 72, "SNS-004": None,
    "SNS-005": 77, "SNS-006": 55, "SNS-007": 81, "SNS-008": 60,
    "SNS-009": 64, "SNS-010": 58, "SNS-011": 88, "SNS-012": 83,
}

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sensors (
            id          TEXT PRIMARY KEY,
            location    TEXT NOT NULL,
            lat         REAL,
            lon         REAL,
            status      TEXT DEFAULT 'online',
            reliability REAL DEFAULT 1.0,
            calibrated  TEXT,
            uptime      REAL DEFAULT 100.0
        );

        CREATE TABLE IF NOT EXISTS readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id   TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            aqi         REAL,
            pm25        REAL,
            pm10        REAL,
            co          REAL,
            nox         REAL,
            ozone       REAL,
            temperature REAL,
            humidity    REAL,
            FOREIGN KEY (sensor_id) REFERENCES sensors(id)
        );

        CREATE INDEX IF NOT EXISTS idx_readings_sensor_ts
            ON readings (sensor_id, timestamp DESC);
    """)
    conn.commit()


def _aqi_to_pm25(aqi: float) -> float:
    """Rough linear conversion for demo purposes."""
    return round(aqi * 0.42 + random.uniform(-2, 2), 1)


def _make_reading(sensor_id: str, base_aqi: float, ts: datetime) -> dict:
    """Generate one realistic reading with diurnal + random variation."""
    hour = ts.hour
    # Traffic-based diurnal factor: peaks at 9am and 6pm
    diurnal = 1.0 + 0.25 * (
        math.exp(-0.5 * ((hour - 9) / 2) ** 2) +
        0.8 * math.exp(-0.5 * ((hour - 18) / 2) ** 2)
    )
    noise = random.gauss(0, 4)
    aqi = max(10.0, round(base_aqi * diurnal + noise, 1))
    pm25 = _aqi_to_pm25(aqi)
    pm10 = round(pm25 * 1.5 + random.uniform(0, 5), 1)
    co   = round(random.uniform(0.7, 2.2), 2)
    nox  = round(random.uniform(20, 55), 1)
    ozone = round(random.uniform(25, 65), 1)
    temp = round(random.uniform(26, 36), 1)
    hum  = round(random.uniform(45, 80), 1)
    return dict(
        sensor_id=sensor_id,
        timestamp=ts.isoformat(timespec="seconds"),
        aqi=aqi, pm25=pm25, pm10=pm10, co=co,
        nox=nox, ozone=ozone, temperature=temp, humidity=hum
    )


def seed_sensors(conn: sqlite3.Connection):
    existing = conn.execute("SELECT COUNT(*) FROM sensors").fetchone()[0]
    if existing == len(SENSORS):
        return  # already seeded
    conn.executemany(
        """INSERT OR REPLACE INTO sensors
           (id, location, lat, lon, status, reliability, calibrated, uptime)
           VALUES (:id,:location,:lat,:lon,:status,:reliability,:calibrated,:uptime)""",
        SENSORS,
    )
    conn.commit()


def seed_readings(conn: sqlite3.Connection, hours: int = 48):
    existing = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    if existing > 0:
        return  # already seeded

    now = datetime.now().replace(second=0, microsecond=0)
    rows = []
    for sensor in SENSORS:
        base = BASE_AQI.get(sensor["id"])
        if base is None:  # offline sensor — no readings
            continue
        # One reading every 5 minutes for `hours` hours
        for minutes_ago in range(hours * 60, -1, -5):
            ts = now - timedelta(minutes=minutes_ago)
            rows.append(_make_reading(sensor["id"], base, ts))

    conn.executemany(
        """INSERT INTO readings
           (sensor_id, timestamp, aqi, pm25, pm10, co, nox, ozone, temperature, humidity)
           VALUES (:sensor_id,:timestamp,:aqi,:pm25,:pm10,:co,:nox,:ozone,:temperature,:humidity)""",
        rows,
    )
    conn.commit()
    print(f"[DB] Seeded {len(rows)} readings across {len(SENSORS)-1} active sensors.")


def init_db():
    """Called once at startup — idempotent."""
    conn = get_connection()
    create_schema(conn)
    seed_sensors(conn)
    seed_readings(conn)
    conn.close()
    print(f"[DB] Ready at {DB_PATH}")
