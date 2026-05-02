# AI Talent Intelligence

AI Data Literacy is a talent intelligence project I built to understand where AI builders are, how they work, and how the ecosystem is changing over time.

I love maps, reports, data, and dashboards, so I wanted to turn public GitHub activity into something decision-ready: monthly scoring, location enrichment, normalized geography, and analytics views you can explore visually.

**Built with AI coding copilots, then rigorously refined through manual validation, SQL testing, and end-to-end pipeline QA.**

## Why I Built This

I started this project to explore talent intelligence end to end:

- Pull data from GitHub at scale  
- Enrich raw activity into usable signals  
- Improve sourcing quality through better weighting logic  
- Build practical TI tools for repeatable analysis  
- Publish clean outputs for maps and dashboards  

This is both a research lab and an operating toolkit.

## What This Project Does

- Ingests 5.87M public GitHub activity records from 2021 to March 2026
- Scores monthly developer AI engagement using event weights and ecosystem multipliers
- Enriches users with public profile location data
- Normalizes messy raw location strings into canonical city, region, country, and analytics-friendly outputs
- Publishes views used by dashboards and geospatial reporting

## Key Findings

- Observable AI talent market expanded from **16,323 users (Jan 2021)** to **2,579,030 users (Mar 2026)** — a **158x** increase
- 5,818,220 total monthly score rows representing AI-engaged developers
- 322,837 users normalized to country/city level for geographic analysis
- US concentration remains strongest in established hubs (Bay Area: 10% of located US users) with growth broadening into mid-tier metros
- Fastest-growing metros since 2025: Raleigh-Durham (+64.7%), Dallas-Fort Worth (+49.3%), Portland (+46.1%)

## Query Reference

- **Canonical query**: `sql/validation/query_github_profiles.sql` — Aggregated monthly scores per user
- **Raw events query**: `sql/seeds/ai_talent_raw_202101_202603.sql` — Unaggregated event-level extraction

## How It Works

### 1. Source
- Query public GitHub Archive data in BigQuery using the canonical query
- Filter to AI-relevant ecosystems and repositories

### 2. Score
- Calculate monthly developer scores using:
  - Event type weight (release=30, PR review=25, deployment=25, etc.)
  - Repository ecosystem multiplier (5×, 3.5×, 2×, 1.5×, 1×)

### 3. Enrich
- Fetch public GitHub profile location strings
- Geocode and stage fast-tier location records

### 4. Normalize
- Reconcile raw locations against curated reference data
- Apply aliasing, metro rollups, and strict-city variants

### 5. Serve
- Publish analytics-ready views for BI and map consumers
- Power reports in Metabase and map exports in Kepler.gl

## Current Snapshot

- 5.87M GitHub activity records processed
- 5,818,220 monthly score rows
- 2,580,505 unique users
- 349,524 users with raw profile locations
- 322,837 normalized locations
- 179,047 strict-city normalized locations

## Tech Stack

| Layer | Tool |
|-------|------|
| Data source | Google BigQuery — GitHub Archive (2021–2026) |
| API enrichment | GitHub REST API (public profiles) |
| VPS | Hetzner CX23 (2 vCPU, 4GB RAM, Ubuntu 24.04) |
| Connectivity | Tailscale |
| Primary DB | PostgreSQL + PostGIS 15 |
| Geocoding | geopy + Nominatim |
| Dashboards | Metabase |
| Visualization | Kepler.gl (time-lapse), Plotly (charts) |
| Queries | DBeaver |

## Network Model

Production network boundaries are intentionally split by purpose.

- Cloudflare is for public web traffic, not arbitrary database or admin ports.
- Tailscale is for administrative access to the Hetzner host.
- PostgreSQL should remain localhost-only on production unless there is a specific operational reason to expose it differently.
- Metabase should default to localhost-only and only be reopened intentionally if a tailnet-only workflow is required.
- UFW on the VPS remains the public ingress control for host-level exposure.

## Schema

```sql
-- Pre-aggregated monthly scores from BigQuery
monthly_scores (username, period DATE, score, total_events, unique_repos, event_variety, efficiency)

-- Geocoded locations from GitHub profiles
locations (username, raw_location, lat, lon, geom GEOMETRY, geo_precision SMALLINT)
-- geo_precision: 0=unknown, 1=country, 2=region, 3=city

-- Legacy joined view kept for backward compatibility
profiles VIEW = monthly_scores LEFT JOIN locations ON username

-- Active normalized serving layer
profiles_normalized_published
profiles_location_analytics
profiles_location_analytics_city_strict
```

## Deployment Notes

- Production DB name: `ai_talent`
- Production Metabase metadata DB: `metabase`
- Active `reference_version`: `geonames_p_10000_2026_04_08`
- Active production `rules_version`: `spatial_reconcile_geonames_subset_prod_v1`
- Production PostgreSQL and Metabase are bound to `127.0.0.1` on the VPS
- Consumer wrapper views in production: `profiles_location_analytics`, `profiles_location_analytics_city_strict`
- Legacy `profiles` remains present for backward compatibility, but active location consumers have been cut over to wrapper views
- Local Metabase reports can be made production-backed without changing the Metabase database object by tunneling to production and proxying the local wrapper views through [sql/schema/setup_local_metabase_prod_proxy.sql](sql/schema/setup_local_metabase_prod_proxy.sql)
- Use [docs/runbooks/PRODUCTION_MIGRATION_RUNBOOK.md](docs/runbooks/PRODUCTION_MIGRATION_RUNBOOK.md) for the sealed production migration record
- Use [docs/runbooks/RECONCILIATION_RUNBOOK.md](docs/runbooks/RECONCILIATION_RUNBOOK.md) for normalization deployment procedure
- Specs and migration planning docs now live under [docs/specs](docs/specs)

## Scoring Philosophy

The model prioritizes contribution quality over passive activity.

- High-signal actions (releases, pull request reviews, deployments) are weighted more heavily than passive signals
- Ecosystem multipliers reflect technical depth and AI relevance
- Monthly buckets make trends and trajectory easier to compare over time and across cohorts

## Top US Metro Areas by AI-Literate Users

| Rank | Metro Area | AI-Literate Users | Avg AI Score |
|------|-----------|-------------------|--------------|
| 1 | San Francisco-Oakland-Fremont, CA | 5,154 | 365.82 |
| 2 | New York-Newark-Jersey City, NY-NJ | 3,287 | 111.84 |
| 3 | Seattle-Tacoma-Bellevue, WA | 2,598 | 198.83 |
| 4 | Los Angeles-Long Beach-Anaheim, CA | 2,420 | 106.98 |
| 5 | Boston-Cambridge-Newton, MA-NH | 1,909 | 103.34 |
| 6 | San Jose-Sunnyvale-Santa Clara, CA | 1,709 | 293.11 |
| 7 | Chicago-Naperville-Elgin, IL-IN | 1,414 | 206.83 |
| 8 | Austin-Round Rock-San Marcos, TX | 1,221 | 276.78 |
| 9 | Atlanta-Sandy Springs-Roswell, GA | 1,019 | 302.90 |
| 10 | Dallas-Fort Worth-Arlington, TX | 936 | 189.68 |

*Bay Area represents approximately 10% of all located US users, with the highest concentration of sustained high-intensity contributors.*

## Global Country Rankings (All-Time, 2021-2026)

| Rank | Country | AI-Literate Users |
|------|---------|-------------------|
| 1 | United States | 51,913 |
| 2 | China | 48,585 |
| 3 | India | 35,843 |
| 4 | Germany | 14,679 |
| 5 | Brazil | 12,539 |
| 6 | United Kingdom | 11,439 |
| 7 | France | 10,567 |
| 8 | Canada | 9,105 |
| 9 | Japan | 5,678 |
| 10 | South Korea | 5,363 |

## Interactive Maps and Reports

Explore the talent intelligence dataset visually through Metabase dashboards and Kepler.gl interactive maps.

### Public Reports Hub

| Report | Description | Access |
|--------|-------------|--------|
| Talent Intelligence Master Dashboard | Combined overview of global AI engagement | [Open](docs/reports/talent_intelligence_master_dashboard.html) |
| AI Developer Density Dashboard | Geographic distribution and density analysis | [Open](docs/reports/ai_dev_density_full_dashboard.html) |
| Talent Intelligence Overview Card | Executive one-page summary | [Open](docs/reports/talent_intelligence_overview_card.html) |
| US AI Market Battle Card | US market scale, momentum, and sourcing strategy | [Open](docs/reports/us_ai_market_battle_card.html) |

### Featured Maps

#### City User Points by Location

<iframe src="docs/reports/kepler_map_1.html" title="Kepler Map 1 - City User Points" width="100%" height="680" loading="lazy" allowfullscreen style="border:1px solid #d9e1ec; border-radius:8px; margin: 20px 0;"></iframe>

#### Global AI Activity by Country

<iframe src="docs/reports/kepler_map_7.html" title="Kepler Map 7 - Country AI Activity" width="100%" height="680" loading="lazy" allowfullscreen style="border:1px solid #d9e1ec; border-radius:8px; margin: 20px 0;"></iframe>

#### Global AI Activity Heatmap

<iframe src="docs/reports/kepler_map_13.html" title="Kepler Map 13 - Global Heatmap" width="100%" height="680" loading="lazy" allowfullscreen style="border:1px solid #d9e1ec; border-radius:8px; margin: 20px 0;"></iframe>

## Leaderboards

### Global Top Performers (2021-2026)

| Rank | Username | Total Score | Interaction Months | Country |
|------|----------|-------------|---------------------|---------|
| 1 | Ilikectrlmusic | 4,797,581 | 21 | — |
| 2 | skotrla | 1,778,310 | — | — |
| 3 | DarkLight1337 | 1,650,087 | — | Hong Kong |

*Full worldwide top-1,000 available in [leaderboard_worldwide_top1000_alltime.csv](docs/reports/leaderboard_worldwide_top1000_alltime.csv)*

### US Top Performers (2021-2026)

| Rank | Username | Total Score | City | State |
|------|----------|-------------|------|-------|
| 1 | WoosukKwon | 629,696 | San Francisco | CA |
| 2 | AndreasKaratzas | 581,759 | Austin | TX |
| 3 | Jokeren | 438,177 | Fairfax | VA |

*Full US top-1,000 available in [leaderboard_usa_top1000_alltime.csv](docs/reports/leaderboard_usa_top1000_alltime.csv)*

## Data Exports

Complete datasets and leaderboards are available as CSV files:

| File | Description | Records |
|------|-------------|---------|
| `leaderboard_worldwide_top1000_alltime.csv` | Global top 1,000 users by all-time score | 1,000 |
| `leaderboard_usa_top1000_alltime.csv` | US top 1,000 users with city/state | 1,000 |
| `leaderboard_usa_top100_by_year.csv` | US top 100 performers per year (2021-2026) | 600 |
| `usa_metro_report.csv` | All 621 US metros ranked by AI-literate users | 621 |
| `usa_metro_growth_falloff_since_2025.csv` | Metro growth metrics 2024 vs 2025+ | 105 |
| `usa_ai_literacy_yoy_change.csv` | Year-over-year adoption and score trends | 6 |

All files include normalized geographic fields and activity metrics.

---

*Data sourced from GitHub public activity records, January 2021 - March 2026. AI activity scoring reflects engagement with AI/ML repositories weighted by contribution type. Geographic normalization applied to 92.4% of self-reported locations. All figures reflect post-quality-review production dataset after bot and spam account removal.*
