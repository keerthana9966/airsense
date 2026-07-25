/* AirSense — Dashboard JS (API-connected) */

const API = 'http://localhost:8000/api';

// ── Helpers ─────────────────────────────────────────────────────────────────
function aqiColor(v) {
  if (v === null || v === undefined || v === '--') return '#4a5568';
  if (v <= 50)  return '#22d3a5';
  if (v <= 100) return '#fbbf24';
  if (v <= 150) return '#fb923c';
  return '#f87171';
}

// ── INIT ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  loadSensors();
  loadForecast();
  loadPollutants();
  loadTrend('24h');
  startLiveTicker();
  initTabs();
});

// ── DASHBOARD ───────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const data = await fetch(`${API}/dashboard`).then(r => r.json());
    document.getElementById('heroAqi').textContent  = data.aqi;
    document.getElementById('pm25').textContent     = data.pm25;
    document.getElementById('co').textContent       = data.co;
    document.getElementById('temp').textContent     = `${data.temperature}°C`;
    document.getElementById('hum').textContent      = `${data.humidity}%`;

    const statusEl = document.querySelector('.aqi-status');
    if (statusEl) {
      statusEl.textContent = data.aqi_label;
      statusEl.className = 'aqi-status ' + (
        data.aqi <= 50  ? 'good' :
        data.aqi <= 100 ? 'moderate' : 'unhealthy'
      );
    }

    // Update reliability composite score
    const scoreEl = document.querySelector('.score-val');
    if (scoreEl) scoreEl.textContent = data.reliability_score.toFixed(2);

    loadReliability();
  } catch (e) {
    console.warn('[AirSense] Dashboard API unavailable — using mock values.', e);
  }
}

// ── SENSORS ──────────────────────────────────────────────────────────────────
async function loadSensors() {
  try {
    const sensors = await fetch(`${API}/sensors`).then(r => r.json());
    renderSensors(sensors);
  } catch (e) {
    console.warn('[AirSense] Sensors API unavailable.', e);
    // Fallback mock
    renderSensors([
      { name: "Banjara Hills #1", status: "online",  aqi: 68,  reliability: 0.91 },
      { name: "Jubilee Hills #3", status: "online",  aqi: 72,  reliability: 0.88 },
      { name: "Madhapur #7",      status: "online",  aqi: 81,  reliability: 0.85 },
      { name: "HITEC City #2",    status: "warning", aqi: 95,  reliability: 0.62 },
      { name: "Ameerpet #5",      status: "online",  aqi: 77,  reliability: 0.79 },
      { name: "Panjagutta #4",    status: "offline", aqi: null, reliability: 0.00 },
    ]);
  }
}

function renderSensors(sensors) {
  const el = document.getElementById('sensorList');
  if (!el) return;
  el.innerHTML = sensors.map(s => {
    const aqi   = s.aqi ?? '--';
    const score = s.reliability ?? s.score ?? 0;
    return `
      <div class="sensor-item">
        <div class="sensor-dot ${s.status}"></div>
        <span class="sensor-name">${s.location || s.name}</span>
        <span class="sensor-aqi" style="color:${aqiColor(s.aqi)}">${aqi}</span>
        <span class="sensor-score">${score > 0 ? score.toFixed(2) : 'N/A'}</span>
      </div>`;
  }).join('');
}

// ── FORECAST ─────────────────────────────────────────────────────────────────
async function loadForecast() {
  try {
    const data = await fetch(`${API}/forecast`).then(r => r.json());
    renderForecast(data.forecasts);
    const noteEl = document.querySelector('.forecast-note');
    if (noteEl) noteEl.textContent = `Prediction interval: ${data.interval} · ${data.model}`;
  } catch (e) {
    console.warn('[AirSense] Forecast API unavailable.', e);
    renderForecast([
      { time: "NOW",    aqi: 73, label: "Moderate", color: "#fbbf24" },
      { time: "+15min", aqi: 78, label: "Moderate", color: "#fbbf24" },
      { time: "+30min", aqi: 82, label: "Moderate", color: "#fb923c" },
      { time: "+1hr",   aqi: 69, label: "Moderate", color: "#fbbf24" },
    ]);
  }
}

function renderForecast(forecasts) {
  const el = document.getElementById('forecastRow');
  if (!el) return;
  el.innerHTML = forecasts.map(f => `
    <div class="forecast-item">
      <div class="fc-time">${f.time}</div>
      <div class="fc-aqi" style="color:${f.color}">${f.aqi}</div>
      <div class="fc-label">${f.label}</div>
    </div>`).join('');
}

// ── POLLUTANTS ────────────────────────────────────────────────────────────────
async function loadPollutants() {
  try {
    const data = await fetch(`${API}/pollutants`).then(r => r.json());
    renderPollutants(data.pollutants);
    animateBars();
  } catch (e) {
    console.warn('[AirSense] Pollutants API unavailable.', e);
    renderPollutants([
      { name: "PM2.5",   value: 34.2, unit: "µg/m³", max: 150, color: "#f87171", pct: 23 },
      { name: "PM10",    value: 51.0, unit: "µg/m³", max: 250, color: "#fb923c", pct: 20 },
      { name: "CO",      value: 1.2,  unit: "ppm",   max: 10,  color: "#fbbf24", pct: 12 },
      { name: "NOx",     value: 38.5, unit: "ppb",   max: 200, color: "#a78bfa", pct: 19 },
      { name: "Ozone",   value: 42.1, unit: "ppb",   max: 160, color: "#60a5fa", pct: 26 },
      { name: "Humidity",value: 62,   unit: "%",     max: 100, color: "#22d3a5", pct: 62 },
    ]);
    animateBars();
  }
}

function renderPollutants(pollutants) {
  const el = document.getElementById('pollGrid');
  if (!el) return;
  el.innerHTML = pollutants.map(p => `
    <div class="pollutant-item">
      <div class="poll-name">${p.name}</div>
      <div class="poll-value" style="color:${p.color}">${p.value}</div>
      <div class="poll-unit">${p.unit}</div>
      <div class="poll-bar">
        <div class="poll-fill" style="width:${p.pct}%;background:${p.color}" data-target="${p.pct}"></div>
      </div>
    </div>`).join('');
}

// ── RELIABILITY ───────────────────────────────────────────────────────────────
async function loadReliability() {
  try {
    const rel = await fetch(`${API}/reliability`).then(r => r.json());
    const bars = document.querySelectorAll('.rel-fill');
    const vals = [rel.health, rel.freshness, rel.stability, rel.density];
    bars.forEach((bar, i) => {
      if (vals[i] !== undefined) {
        bar.style.width = `${(vals[i] * 100).toFixed(0)}%`;
      }
    });
    const scoreEl = document.querySelector('.score-val');
    if (scoreEl) scoreEl.textContent = rel.composite.toFixed(2);
  } catch (e) {
    console.warn('[AirSense] Reliability API unavailable.', e);
  }
}

// ── TREND CHART ───────────────────────────────────────────────────────────────
let trendChart = null;

async function loadTrend(range) {
  try {
    const data = await fetch(`${API}/trend?range=${range}`).then(r => r.json());
    renderTrendChart(data.values, data.labels);
  } catch (e) {
    console.warn('[AirSense] Trend API unavailable — using mock data.', e);
    const mock24h = [52,48,44,41,46,55,71,84,90,88,83,78,73,70,72,75,80,77,74,71,68,72,75,73];
    const labels  = Array.from({length: 24}, (_, i) => {
      const h = (new Date().getHours() - 23 + i + 24) % 24;
      return `${String(h).padStart(2,'0')}:00`;
    });
    renderTrendChart(mock24h, labels);
  }
}

function renderTrendChart(data, labels) {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;
  if (trendChart) trendChart.destroy();

  const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, 'rgba(34,211,165,0.18)');
  gradient.addColorStop(1, 'rgba(34,211,165,0.01)');

  trendChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'AQI',
        data,
        borderColor: '#22d3a5',
        borderWidth: 2,
        backgroundColor: gradient,
        tension: 0.4,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#22d3a5',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0d1422',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#8a96a8',
          bodyColor: '#e8edf5',
          titleFont: { family: 'DM Mono', size: 11 },
          bodyFont: { family: 'DM Mono', size: 13 },
          callbacks: { label: ctx => ` AQI: ${ctx.parsed.y}` }
        }
      },
      scales: {
        x: {
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#4a5568', font: { family: 'DM Mono', size: 10 }, maxTicksLimit: 8 }
        },
        y: {
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#4a5568', font: { family: 'DM Mono', size: 10 } },
          min: 20, max: 120
        }
      }
    }
  });
}

// ── TABS ──────────────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadTrend(tab.dataset.range);
    });
  });
}

// ── LIVE TICKER ───────────────────────────────────────────────────────────────
function startLiveTicker() {
  let secs = 0;
  const el = document.getElementById('lastUpdate');
  setInterval(() => {
    secs++;
    if (el) el.textContent = secs < 60 ? `${secs}s ago` : `${Math.floor(secs/60)}m ago`;
    // Refresh dashboard data every 30s
    if (secs % 30 === 0) loadDashboard();
  }, 1000);
}

// ── BAR ANIMATION ─────────────────────────────────────────────────────────────
function animateBars() {
  setTimeout(() => {
    document.querySelectorAll('.rel-fill, .poll-fill').forEach(el => {
      const target = el.style.width;
      el.style.width = '0%';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => { el.style.width = target; });
      });
    });
  }, 200);
}

// ── ROUTE FINDER ──────────────────────────────────────────────────────────────
async function findRoute() {
  const btn   = document.querySelector('.btn-primary');
  const start = document.querySelector('.route-input[placeholder*="Start"]')?.value || 'Banjara Hills';
  const end   = document.querySelector('.route-input[placeholder*="Destination"]')?.value || 'HITEC City';
  const orig  = btn.textContent;

  btn.textContent = '⏳ Calculating...';
  btn.disabled    = true;

  try {
    const data = await fetch(`${API}/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start, end, mode: 'driving' }),
    }).then(r => r.json());

    const el = document.getElementById('routeResult');
    if (el && data.routes) {
      el.innerHTML = data.routes.map((r, i) => `
        <div class="route-card ${i === 0 ? 'active' : 'alt'}">
          <div class="route-label">${r.label}</div>
          <div class="route-path">${r.path}</div>
          <div class="route-stats">
            <span>⏱ ${r.time_min} min</span>
            <span>📏 ${r.distance_km} km</span>
            <span>🌿 Exposure: ${r.exposure} AQI·min</span>
          </div>
        </div>`).join('');
      el.style.animation = 'none';
      void el.offsetWidth;
      el.style.animation = 'fadeUp 0.4s ease both';
    }
  } catch (e) {
    console.warn('[AirSense] Route API unavailable.', e);
  } finally {
    btn.textContent = orig;
    btn.disabled    = false;
  }
}
