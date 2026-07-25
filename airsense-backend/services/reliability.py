"""
AirSense — Reliability Score Service
Computes composite sensor reliability:
  composite = 0.4×health + 0.3×freshness + 0.2×stability + 0.1×density
"""

import sqlite3
from datetime import datetime, timedelta
import statistics


def compute_reliability(conn: sqlite3.Connection) -> dict:
    """
    Aggregate reliability components across all *active* sensors.
    Returns individual component scores and composite.
    """

    # ── Health score: fraction of sensors that are online ────────────────────
    rows = conn.execute("SELECT status FROM sensors").fetchall()
    total = len(rows)
    online = sum(1 for r in rows if r["status"] == "online")
    warning = sum(1 for r in rows if r["status"] == "warning")
    health = round((online + 0.5 * warning) / total, 3) if total else 0.0

    # ── Freshness score: how recent are the latest readings? ─────────────────
    now = datetime.now()
    cutoff_good = (now - timedelta(minutes=10)).isoformat(timespec="seconds")
    cutoff_ok   = (now - timedelta(minutes=30)).isoformat(timespec="seconds")

    latest_rows = conn.execute("""
        SELECT sensor_id, MAX(timestamp) as last_ts
        FROM readings GROUP BY sensor_id
    """).fetchall()

    freshness_scores = []
    for r in latest_rows:
        if r["last_ts"] >= cutoff_good:
            freshness_scores.append(1.0)
        elif r["last_ts"] >= cutoff_ok:
            freshness_scores.append(0.6)
        else:
            freshness_scores.append(0.2)
    freshness = round(statistics.mean(freshness_scores), 3) if freshness_scores else 0.0

    # ── Stability score: low stddev of recent readings = stable sensor ────────
    stability_scores = []
    for r in latest_rows:
        recent = conn.execute(
            """SELECT aqi FROM readings
               WHERE sensor_id = ? ORDER BY timestamp DESC LIMIT 12""",
            (r["sensor_id"],)
        ).fetchall()
        aqis = [x["aqi"] for x in recent if x["aqi"] is not None]
        if len(aqis) >= 3:
            std = statistics.stdev(aqis)
            # stddev < 5 → very stable; > 25 → unstable
            score = max(0.0, min(1.0, 1 - (std - 5) / 20))
            stability_scores.append(score)
    stability = round(statistics.mean(stability_scores), 3) if stability_scores else 0.5

    # ── Density score: sensors-per-area proxy (fixed for demo) ───────────────
    density = round(online / 15.0, 3)  # 15 = target node count

    # ── Composite ─────────────────────────────────────────────────────────────
    composite = round(
        0.4 * health +
        0.3 * freshness +
        0.2 * stability +
        0.1 * density,
        3
    )

    return {
        "health":    health,
        "freshness": freshness,
        "stability": stability,
        "density":   density,
        "composite": composite,
    }
