# AirSense Backend

**FastAPI + SQLite REST API** for the AirSense hyper-local air quality monitoring dashboard.

## Quick Start

### 1. Install Python dependencies

```bash
cd airsense-backend
pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Create `airsense.db` (SQLite) automatically on first run
- Seed 12 Hyderabad sensor locations
- Seed ~48h of realistic AQI readings (diurnal traffic pattern)

### 3. Open the frontend

Open `airsense/index.html` with Live Server (VS Code) or any HTTP server.  
The frontend calls `http://localhost:8000/api/*` — make sure the backend is running.

### 4. Explore the API docs

Swagger UI: **http://localhost:8000/docs**  
ReDoc:       **http://localhost:8000/redoc**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/dashboard` | Hero AQI, PM2.5, CO, temp, humidity |
| `GET`  | `/api/sensors` | Full sensor list with latest readings |
| `GET`  | `/api/trend?range=24h\|7d\|30d` | AQI time-series for charts |
| `GET`  | `/api/pollutants` | PM2.5, PM10, CO, NOx, Ozone, Humidity |
| `GET`  | `/api/forecast` | AI forecast: NOW, +15min, +30min, +1hr |
| `GET`  | `/api/reliability` | Sensor reliability score breakdown |
| `GET`  | `/api/analytics` | Stat boxes + chart datasets for analytics page |
| `POST` | `/api/route` | Smart route recommendation |
| `POST` | `/api/sensor/reading` | Ingest IoT sensor reading (ESP32 push) |
| `GET`  | `/health` | Health check |

### Example: Find a Route

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"start": "Banjara Hills", "end": "HITEC City", "mode": "driving"}'
```

### Example: Ingest a Sensor Reading

```bash
curl -X POST http://localhost:8000/api/sensor/reading \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SNS-001",
    "aqi": 72.5, "pm25": 31.2, "pm10": 48.1,
    "co": 1.3, "nox": 40.2, "ozone": 44.1,
    "temperature": 32.1, "humidity": 65.0
  }'
```

---

## Architecture

```
AirSense Backend (Layer 1–2)
├── main.py              ← FastAPI app, CORS, all routes
├── database.py          ← SQLite schema, seed data, connection helper
├── models.py            ← Pydantic request/response schemas
└── services/
    ├── forecast.py      ← Simulated RF/XGBoost AQI prediction
    ├── route.py         ← Modified Dijkstra/A* route scoring
    └── reliability.py   ← 0.4×health + 0.3×freshness + 0.2×stability + 0.1×density
```

### Reliability Formula

```
composite = 0.4 × health + 0.3 × freshness + 0.2 × stability + 0.1 × density
```

### Route Cost Function

```
w(e) = α·dist_norm + β·exposure_norm    (α=0.4, β=0.6)
```

---

## Upgrading to Production

| Demo | Production |
|------|-----------|
| SQLite | PostgreSQL + TimescaleDB (Supabase) |
| Simulated forecast | Trained RF/XGBoost sklearn model |
| In-process route | Dedicated Celery worker |
| Static seed data | MQTT broker receiving live ESP32 data |
