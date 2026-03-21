"""
sync_vps_to_postgres.py
Pulls final_talent_locations.csv from VPS via SCP,
upserts new rows into local PostgreSQL, then runs geocoding on any new locations.
Run every 5 minutes via Task Scheduler.
"""

import subprocess
import csv
import io
import psycopg2
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

VPS_HOST = "root@100.112.67.38"
VPS_KEY = "/c/Users/DavidBrown/.ssh/id_ed25519"
VPS_PATH = "/root/github-ai-talent/final_talent_locations.csv"

DB = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "ai_literacy",
    "user": "ailiteracy",
    "password": "ailiteracy",
}

geolocator = Nominatim(user_agent="ai_literacy_project/1.0 (personal research)")


def fetch_csv_from_vps():
    result = subprocess.run(
        ["ssh", "-i", VPS_KEY, VPS_HOST, f"cat {VPS_PATH}"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"SSH failed: {result.stderr}")
    return result.stdout


def geocode(location):
    try:
        result = geolocator.geocode(location, timeout=10)
        if result:
            return result.latitude, result.longitude
    except (GeocoderTimedOut, GeocoderServiceError):
        time.sleep(5)
    return None, None


def main():
    print("Fetching CSV from VPS...")
    raw = fetch_csv_from_vps()
    rows = list(csv.DictReader(io.StringIO(raw)))
    print(f"  VPS rows: {len(rows)}")

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Upsert all rows, skipping cleaned_location
    inserted = 0
    for row in rows:
        cur.execute("""
            INSERT INTO profiles (username, master_ai_literacy_score, literacy_tier, total_events, raw_location)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (
            row["username"],
            row["master_ai_literacy_score"] or None,
            row["literacy_tier"],
            row["total_events"] or None,
            row["raw_location"] or None,
        ))
        if cur.rowcount:
            inserted += 1

    conn.commit()
    print(f"  New rows inserted: {inserted}")

    # Geocode new rows that have a raw_location but no lat/lon
    cur.execute("""
        SELECT DISTINCT raw_location FROM profiles
        WHERE raw_location IS NOT NULL AND raw_location != ''
          AND lat IS NULL
    """)
    locations = [r[0] for r in cur.fetchall()]
    print(f"  New locations to geocode: {len(locations)}")

    cache = {}
    for loc in locations:
        if loc not in cache:
            lat, lon = geocode(loc)
            cache[loc] = (lat, lon)
            time.sleep(1)

        lat, lon = cache[loc]
        if lat and lon:
            cur.execute("""
                UPDATE profiles SET lat=%s, lon=%s,
                    geom=ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE raw_location=%s AND lat IS NULL
            """, (lat, lon, lon, lat, loc))
        else:
            # No result — send to Null Island
            cur.execute("""
                UPDATE profiles SET lat=0, lon=0,
                    geom=ST_SetSRID(ST_MakePoint(0, 0), 4326)
                WHERE raw_location=%s AND lat IS NULL
            """, (loc,))

    # Also null island any remaining empty locations
    cur.execute("""
        UPDATE profiles SET lat=0, lon=0,
            geom=ST_SetSRID(ST_MakePoint(0, 0), 4326)
        WHERE (raw_location IS NULL OR raw_location = '') AND lat IS NULL
    """)

    conn.commit()
    cur.close()
    conn.close()

    print(f"  Sync complete.")


if __name__ == "__main__":
    main()
