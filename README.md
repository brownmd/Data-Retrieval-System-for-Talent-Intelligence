# AI_Data_Literacy

Mapping global AI literacy on GitHub — scoring 197k developers by their interactions with AI repositories and visualizing where AI knowledge is concentrated worldwide.

## Pipeline

**Step 1 — Score** (completed)
Query GitHub Archive (`githubarchive.month.202601`) via BigQuery. Score 197k users across 17 AI repo categories using a weighted event system (L1–L6 tiers). Export to `ai_talent_raw_202601.xlsx`.

**Step 2 — Enrich** (running on Hetzner VPS)
`fetch_locations.py` reads the xlsx, hits the GitHub REST API for each user's profile location, and appends results to `final_talent_locations.csv`. Syncs to Google Drive every 5 minutes via rclone. Auto-imports into DuckDB every 5 minutes.

**Step 3 — Analyze** (local)
Download CSV from Google Drive. Import into PostgreSQL + PostGIS (dropping `cleaned_location`). Run geopy/Nominatim to geocode `raw_location` into lat/lon. Query with DBeaver. Visualize with Kepler.gl.

**Step 4 — Publish**
Export maps and charts for blog posts analyzing AI literacy by city, country, and region.

## Tech Stack

| Layer | Tool |
|-------|------|
| Data source | Google BigQuery — GitHub Archive public dataset |
| API enrichment | GitHub REST API (public profiles) |
| VPS | Hetzner (2 vCPU, 4GB RAM) |
| Backup | Google Drive via rclone |
| Temp DB | DuckDB (VPS) |
| Primary DB | PostgreSQL + PostGIS (local) |
| Geocoding | geopy + Nominatim |
| Visualization | Kepler.gl |
| Queries | DBeaver |

## Literacy Tier System

| Tier | Label | Description |
|------|-------|-------------|
| L1 | AI Curious | Starred or watched AI repos |
| L2 | AI Explorer | Forked AI repos |
| L3 | AI Practitioner | Opened issues on AI repos |
| L4 | Agentic Architect | Pull request activity on AI repos |
| L5 | AI Contributor | Merged contributions to AI repos |
| L6 | AI Architect | Release-level contributions to AI repos |

## Data Source

All data is sourced from the GitHub Archive public dataset (BigQuery) and public GitHub user profiles via the official GitHub REST API. No private data is collected.
