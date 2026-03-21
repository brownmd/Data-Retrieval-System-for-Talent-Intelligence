# Test Plan — AI_Data_Literacy Project

## Scope

Tests cover the data pipeline from CSV ingestion through PostgreSQL import,
geocoding, and final query output. No UI testing — Kepler.gl and DBeaver are
read-only visualization tools.

---

## 1. VPS Pipeline Tests

### T1 — CSV integrity check
**What:** Verify no duplicate usernames in final_talent_locations.csv
**How:**
```bash
awk -F',' 'NR>1 {print $1}' final_talent_locations.csv | sort | uniq -d | wc -l
```
**Pass:** Output is 0

### T2 — CSV column structure
**What:** Confirm expected columns exist and are in correct order
**How:**
```bash
head -1 final_talent_locations.csv
```
**Pass:** `username,master_ai_literacy_score,literacy_tier,total_events,raw_location,cleaned_location`

### T3 — rclone sync is current
**What:** Google Drive file is not more than 10 minutes old
**How:**
```bash
rclone lsl gdrive:github-ai-talent/final_talent_locations.csv
```
**Pass:** Timestamp within last 10 minutes (or matches local file mtime)

### T4 — DuckDB import is current
**What:** DuckDB row count matches CSV row count (minus header)
**How:**
```bash
CSV_ROWS=$(( $(wc -l < final_talent_locations.csv) - 1 ))
DB_ROWS=$(duckdb talent.db "SELECT COUNT(*) FROM profiles;")
echo "CSV: $CSV_ROWS | DB: $DB_ROWS"
```
**Pass:** DB row count >= CSV row count (DuckDB may lag by up to 5 min)

### T5 — fetch_locations.py is running in screen
**What:** Exactly one Python process running, and it is a child of screen
**How:**
```bash
pgrep -c python3          # should be 1
pstree -p $(pgrep screen) # should show python3 as descendant
```
**Pass:** Count is 1, pstree shows screen -> bash -> python3

---

## 2. Local PostgreSQL Import Tests

### T6 — PostgreSQL connection
**What:** Can connect to local PostgreSQL with project user
**How:**
```bash
psql -U ai_literacy -d ai_literacy -c "\conninfo"
```
**Pass:** Connected without error

### T7 — profiles table schema
**What:** Table has correct columns, cleaned_location is absent
**How:**
```sql
\d profiles
```
**Pass:** Columns are: username, master_ai_literacy_score, literacy_tier,
total_events, raw_location. No cleaned_location column.

### T8 — row count matches CSV
**What:** PostgreSQL row count equals CSV unique user count
**How:**
```sql
SELECT COUNT(*) FROM profiles;
```
**Pass:** Count matches deduplicated CSV row count

### T9 — no nulls in required fields
**What:** username, master_ai_literacy_score, literacy_tier are never null
**How:**
```sql
SELECT COUNT(*) FROM profiles
WHERE username IS NULL
   OR master_ai_literacy_score IS NULL
   OR literacy_tier IS NULL;
```
**Pass:** Count is 0

### T10 — literacy tier values are valid
**What:** All tier values are within the expected L1-L6 set
**How:**
```sql
SELECT DISTINCT literacy_tier FROM profiles ORDER BY literacy_tier;
```
**Pass:** Only values matching pattern `L[1-6]: *`

---

## 3. Geocoding Tests (geopy/Nominatim)

### T11 — geocoding produces lat/lon
**What:** A sample of raw_location values returns valid coordinates
**How:** Run geocoding on 10 known locations (e.g. "San Francisco", "London", "Berlin")
**Pass:** All 10 return lat/lon within expected bounding boxes

### T12 — geocoding cache works
**What:** Re-geocoding the same address returns cached result (no API call)
**How:** Geocode "San Francisco" twice, verify second call takes < 10ms
**Pass:** Second call is instant (from DB cache, not Nominatim)

### T13 — null handling for empty locations
**What:** Users with empty raw_location get NULL lat/lon, not an error
**How:**
```sql
SELECT COUNT(*) FROM profiles
WHERE raw_location IS NULL AND lat IS NOT NULL;
```
**Pass:** Count is 0

### T14 — PostGIS geometry column is valid
**What:** All non-null lat/lon values produce valid PostGIS geometry
**How:**
```sql
SELECT COUNT(*) FROM profiles
WHERE geom IS NOT NULL AND NOT ST_IsValid(geom);
```
**Pass:** Count is 0

---

## 4. Run Order

Run tests in this order before each major pipeline stage:

| Stage | Tests to run |
|-------|-------------|
| After CSV dedup | T1, T2 |
| After rclone/DuckDB verify | T3, T4, T5 |
| After PostgreSQL import | T6, T7, T8, T9, T10 |
| After geocoding | T11, T12, T13, T14 |
