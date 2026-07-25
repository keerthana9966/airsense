<div align="center">

# ◉ AirSense

### Hyper-Local Air Quality Monitoring Platform

**Real-time AQI tracking · AI-powered forecasting · Smart route recommendations**

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org/)
[![Vanilla JS](https://img.shields.io/badge/Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

</div>

---

## 📖 Overview

**AirSense** is a full-stack, hyper-local air quality monitoring platform built for **Hyderabad, India**. It aggregates real-time data from a fleet of ESP32 IoT sensors deployed across the city and presents it through a sleek, modern web dashboard. The platform supports AI-powered AQI forecasting, composite sensor reliability scoring, and smart route recommendations that help commuters minimize pollution exposure.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Live Dashboard** | Real-time AQI, PM2.5, CO, temperature & humidity from all active sensors |
| 🗺️ **Live Map** | Interactive sensor map with colour-coded AQI zones across Hyderabad |
| 🤖 **AI Forecast** | RF/XGBoost ensemble model predicts AQI at NOW, +15 min, +30 min, +1 hr |
| 🛣️ **Smart Routes** | Modified Dijkstra/A\* algorithm finds the cleanest, fastest, and balanced commute routes |
| 📈 **Analytics** | Weekly PM2.5 trends, AQI distribution doughnut, hourly exposure charts |
| 🔬 **Sensor Network** | Full sensor list with live status, uptime, calibration info, and reliability scores |
| 🧮 **Reliability Score** | Composite score (Health · Freshness · Stability · Density) for data trustworthiness |
| 📡 **IoT Ingest** | REST endpoint for ESP32 devices to push readings via MQTT/Wi-Fi/LoRaWAN |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AirSense Platform                   │
│                                                         │
│   ┌─────────────────┐       ┌──────────────────────┐   │
│   │   Frontend      │◄─────►│   Backend (FastAPI)   │   │
│   │  Vanilla HTML   │  REST │   Python 3.10+        │   │
│   │  CSS + JS       │  API  │   SQLite Database     │   │
│   │  Chart.js       │       │                      │   │
│   └─────────────────┘       └──────────┬───────────┘   │
│                                         │               │
│                              ┌──────────▼───────────┐   │
│                              │   IoT Sensor Fleet    │   │
│                              │   ESP32 Nodes         │   │
│                              │   LoRaWAN / Wi-Fi     │   │
│                              │   MQTT                │   │
│                              └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Layer 0–3 Design Pattern

| Layer | Component | Technology |
|---|---|---|
| **Layer 0** | IoT Sensors | ESP32, LoRaWAN, MQTT |
| **Layer 1** | Backend API | FastAPI, Python, SQLite |
| **Layer 2** | Services | Forecast (RF/XGBoost), Reliability, Route (Dijkstra/A\*) |
| **Layer 3** | Frontend | HTML5, CSS3, Vanilla JS, Chart.js |

---

## 📂 Project Structure

```
airsense/
├── airsense/                   # Frontend (static web app)
│   ├── index.html              # Dashboard (main page)
│   ├── css/
│   │   └── main.css            # Design system & all styles
│   ├── js/
│   │   └── main.js             # API calls, charts, interactivity
│   └── pages/
│       ├── map.html            # Live sensor map
│       ├── routes.html         # Smart route finder
│       ├── analytics.html      # Charts & analytics
│       └── sensors.html        # Sensor network overview
│
└── airsense-backend/           # Backend (FastAPI REST API)
    ├── main.py                 # All API endpoints
    ├── models.py               # Pydantic request/response schemas
    ├── database.py             # SQLite connection & schema init
    ├── requirements.txt        # Python dependencies
    └── services/
        ├── forecast.py         # AI AQI prediction logic
        ├── reliability.py      # Composite reliability scoring
        └── route.py            # Dijkstra/A* route algorithm
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A modern web browser (Chrome, Firefox, Edge)

### 1. Clone the repository

```bash
git clone https://github.com/keerthana9966/airsense.git
cd airsense
```

### 2. Set up the backend

```bash
cd airsense-backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at **http://localhost:8000**

> 📄 Interactive API docs: **http://localhost:8000/docs**

### 3. Open the frontend

Simply open `airsense/index.html` in your browser, or serve it with any static file server:

```bash
# Using Python's built-in server (from the airsense/ directory)
cd airsense
python -m http.server 5500
```

Then visit **http://localhost:5500**

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Hero metrics: AQI, PM2.5, CO, temp, humidity |
| `GET` | `/api/sensors` | Full sensor list with latest readings |
| `GET` | `/api/trend?range=24h\|7d\|30d` | AQI time-series for trend chart |
| `GET` | `/api/pollutants` | Breakdown of PM2.5, PM10, CO, NOx, Ozone |
| `GET` | `/api/forecast` | AI-powered AQI predictions (RF/XGBoost) |
| `GET` | `/api/reliability` | Sensor reliability score breakdown |
| `GET` | `/api/analytics` | Analytics stats + chart datasets |
| `POST` | `/api/route` | Smart route recommendation |
| `POST` | `/api/sensor/reading` | Ingest new IoT sensor reading |
| `GET` | `/health` | API health check |

### Example: Ingest a sensor reading

```bash
curl -X POST http://localhost:8000/api/sensor/reading \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "S01",
    "aqi": 72.5,
    "pm25": 34.1,
    "pm10": 51.0,
    "co": 1.2,
    "nox": 38.0,
    "ozone": 42.0,
    "temperature": 31.0,
    "humidity": 62.0
  }'
```

### Example: Find a smart route

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"start": "Banjara Hills", "end": "HITEC City", "mode": "driving"}'
```

---

## 🧠 AI & Algorithm Details

### AQI Forecast — RF/XGBoost Ensemble
- Predicts AQI at **NOW**, **+15 min**, **+30 min**, and **+1 hour**
- Uses historical readings as feature vectors
- Prediction interval: **±8 AQI units**

### Smart Route — Modified Dijkstra/A\*
- Edge weight: `w(e) = 0.4 × distance + 0.6 × air_quality_exposure`
- Returns **3 route options**: Cleanest 🍃 · Fastest ⚡ · Balanced ⚖️

### Reliability Score — Composite Metric
- **Health** (40%): Sensor online/offline ratio
- **Freshness** (30%): Recency of the latest reading
- **Stability** (20%): Variance in recent readings
- **Density** (10%): Coverage density across the zone

---

## 🛠️ Tech Stack

**Frontend**
- HTML5, CSS3 (custom design system)
- Vanilla JavaScript (ES6+)
- [Chart.js](https://chartjs.org/) for data visualization
- Google Fonts: Syne, DM Mono, Inter

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework
- [Pydantic](https://docs.pydantic.dev/) — data validation and serialization
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- SQLite — embedded database (upgradeable to PostgreSQL + TimescaleDB + PostGIS)

**IoT (Hardware Layer)**
- ESP32 microcontroller nodes
- LoRaWAN / Wi-Fi connectivity
- MQTT protocol

---

## 📸 Screenshots

> Dashboard · Live Map · Analytics · Smart Routes · Sensor Network

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is for educational and research purposes as part of the **Google Squad Student Feasibility + Production Design Patterns** initiative.

---

<div align="center">
  <sub>Built with ❤️ for cleaner air · AirSense v2.0 · Layer 0–3 Architecture</sub>
</div>
