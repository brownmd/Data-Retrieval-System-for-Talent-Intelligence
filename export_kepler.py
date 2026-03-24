"""
export_kepler.py
Exports profiles from PostGIS to a Kepler.gl-ready CSV.
Only includes real locations (excludes Null Island).
Run this any time you want a fresh Kepler export.
Output: kepler_export.csv
"""

import psycopg2
import csv

DB = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "ai_literacy",
    "user": "ailiteracy",
    "password": "ailiteracy",
}

OUTPUT_FILE = "kepler_export.csv"

# Tier → numeric level for Kepler color scaling
TIER_LEVEL = {
    "L1: AI Curious":         1,
    "L2: Vibe Coder":         2,
    "L3: Production Builder": 3,
    "L4: Agentic Architect":  4,
    "L5: Frontier Engineer":  5,
    "L6: AI Architect":       6,
}

def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            username,
            literacy_tier,
            master_ai_literacy_score,
            total_events,
            raw_location,
            lat,
            lon,
            first_event,
            last_event
        FROM profiles
        WHERE lat <> 0 AND lon <> 0
        ORDER BY first_event ASC NULLS LAST
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "username", "literacy_tier", "tier_level",
            "master_ai_literacy_score", "total_events",
            "raw_location", "lat", "lon",
            "first_event", "last_event"
        ])
        for row in rows:
            username, tier, score, events, location, lat, lon, first_event, last_event = row
            writer.writerow([
                username, tier, TIER_LEVEL.get(tier, 1),
                score, events, location, lat, lon,
                first_event, last_event
            ])

    print(f"Exported {len(rows):,} profiles to {OUTPUT_FILE}")
    print(f"Load into Kepler.gl: https://kepler.gl/demo — drag and drop the file")
    print(f"Suggested config: lat=lat, lon=lon, color=tier_level, size=master_ai_literacy_score, time=first_event")


if __name__ == "__main__":
    main()
