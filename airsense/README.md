# AirSense Frontend

Hyper-Local Air Quality Monitoring Dashboard

## How to Open in VS Code

1. Open VS Code
2. `File → Open Folder` → select this `airsense/` folder
3. Install the **Live Server** extension (if not already installed)
   - Extensions panel → search "Live Server" → Install
4. Right-click `index.html` → **Open with Live Server**
5. Browser opens at `http://127.0.0.1:5500`

## Pages

| File | Page |
|------|------|
| `index.html` | Main Dashboard — AQI, trends, sensors, routes |
| `pages/map.html` | Live Heatmap — sensor pins, AQI zones |
| `pages/routes.html` | Smart Route Finder — Dijkstra/A* visualization |
| `pages/analytics.html` | Analytics — PM2.5, distribution, exposure charts |
| `pages/sensors.html` | Sensor Network — full table, health, reliability |

## File Structure

```
airsense/
├── index.html          ← Main dashboard
├── css/
│   └── main.css        ← All shared styles
├── js/
│   └── main.js         ← Dashboard interactivity + Chart.js
└── pages/
    ├── map.html
    ├── routes.html
    ├── analytics.html
    └── sensors.html
```

## Tech Used (Frontend Only)
- Vanilla HTML/CSS/JS — no framework needed
- Chart.js (CDN) — trend, bar, doughnut, line charts
- Google Fonts — Syne + DM Mono + Inter
- Canvas API — route visualization on routes page

## Architecture Shown
Based on AirSense System Architecture v2.0 (12 March 2026):
- Layer 0: IoT ESP32 Fleet (Sensirion SPS30 / DHT22)
- Layer 1: HTTP/REST APIs, WebSocket notifications, Mobile App
- Layer 2: Celery Worker, AI Prediction (RF/XGBoost), Smart Route (Dijkstra/A*), Exposure Estimation
- Layer 3: PostgreSQL + TimescaleDB + PostGIS (Supabase)
