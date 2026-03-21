"""
geocode_profiles.py
Reads raw_location from PostgreSQL profiles table, geocodes via Nominatim,
writes lat/lon/geom back. Skips already-geocoded rows and empty locations.
Rate limit: 1 request/second (Nominatim TOS).
"""

import time
import psycopg2
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

DB = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "ai_literacy",
    "user": "ailiteracy",
    "password": "ailiteracy",
}

geolocator = Nominatim(user_agent="ai_literacy_project/1.0 (personal research)")


def geocode(location: str):
    try:
        result = geolocator.geocode(location, timeout=10)
        if result:
            return result.latitude, result.longitude
    except (GeocoderTimedOut, GeocoderServiceError):
        time.sleep(5)
    return None, None


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # Get unique locations not yet geocoded
    cur.execute("""
        SELECT DISTINCT raw_location
        FROM profiles
        WHERE raw_location IS NOT NULL
          AND raw_location != ''
          AND lat IS NULL
        ORDER BY raw_location
    """)
    locations = [row[0] for row in cur.fetchall()]
    total = len(locations)
    print(f"Locations to geocode: {total}")

    cache = {}
    done = 0
    skipped = 0

    for loc in locations:
        if loc in cache:
            lat, lon = cache[loc]
        else:
            lat, lon = geocode(loc)
            cache[loc] = (lat, lon)
            time.sleep(1)  # Nominatim rate limit: 1 req/sec

        if lat and lon:
            cur.execute("""
                UPDATE profiles
                SET lat = %s,
                    lon = %s,
                    geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE raw_location = %s
                  AND lat IS NULL
            """, (lat, lon, lon, lat, loc))
            done += 1
        else:
            skipped += 1

        if (done + skipped) % 50 == 0:
            conn.commit()
            print(f"  Progress: {done + skipped}/{total} — geocoded: {done}, no result: {skipped}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Geocoded: {done}, no result: {skipped}, total processed: {done + skipped}/{total}")


if __name__ == "__main__":
    main()
