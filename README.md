# AI_Data_Literacy

A talent intelligence project tracking 5.87M monthly activity records across GitHub from 2021–2026 — scoring developers on their AI engagement and complexity to map where AI talent resides worldwide, and visualizing how AI literacy has evolved from the earliest adopters to today.

## Architecture

```
BigQuery (5.87M rows)
    ↓  load_scores.py
PostGIS on Hetzner VPS
    ├── monthly_scores  (username, period, score, ...)
    ├── locations       (username, lat, lon, geo_precision)
    └── profiles VIEW   (joined, single source of truth)
    ↓                          ↓
Kepler.gl (time-lapse map)   Metabase (dashboards)
```

## Pipeline

| Step | Script | What it does |
|------|--------|-------------|
| 1 — Score | BigQuery | Query GitHub Archive (2021–2026), score users across 17 AI repo categories, aggregate monthly |
| 2 — Load | `load_scores.py` | Stream 5.87M rows from BigQuery into PostgreSQL |
| 3 — Enrich | `fetch_locations.py` | Fetch GitHub profile locations via REST API |
| 4 — Geocode | `sync_vps_to_postgres.py` | Geocode raw location strings to lat/lon (cron, every 5 min) |
| 5 — Visualize | `export_kepler.py` / `charts.py` | Export for Kepler.gl time-lapse and Plotly charts |

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

## Schema

```sql
-- Pre-aggregated monthly scores from BigQuery
monthly_scores (username, period DATE, score, total_events, unique_repos, event_variety, efficiency)

-- Geocoded locations from GitHub profiles
locations (username, raw_location, lat, lon, geom GEOMETRY, geo_precision SMALLINT)
-- geo_precision: 0=unknown, 1=country, 2=region, 3=city

-- Joined view — primary query target
profiles VIEW = monthly_scores LEFT JOIN locations ON username
```

## AI Literacy Tier System

Scores are calculated as: **event score × repo multiplier**

### Event Scores

| Event | Score | What it signals |
|-------|-------|-----------------|
| Release | 30 | Shipped production AI software |
| PR Review / Deployment | 25 | Active code review or deployment ownership |
| Pull Request | 20 | Contributing code to AI repos |
| Check Run | 15 | CI/CD engagement |
| Push / Workflow / Member | 10 | Active development and collaboration |
| Issues / Comments | 4–5 | Community engagement |
| Fork | 2 | Exploring AI projects |
| Watch / Star | 1 | Awareness of AI ecosystem |

### Repo Multipliers (by category)

| Tier | Multiplier | Category | Example repos |
|------|-----------|----------|---------------|
| L6 — AI Architect | 5× | Scaling, interpretability, RL | vLLM, DeepSeek-R1, Triton, SAE-Lens, Unsloth |
| L5 — AI Contributor | 3.5× | Agentic orchestration & MCP | LangGraph, CrewAI, DSPy, Pydantic-AI, Mem0 |
| L4 — Agentic Architect | 2× | SDKs & training frameworks | LangChain, HuggingFace, TRL, Axolotl, RAGAS |
| L1–L2 — Explorer/Curious | 1.5× | Local tools & UI | Ollama, Open-WebUI, Cursor, Aider, LM Studio |
| General AI activity | 1× | All other qualifying repos | — |

### 17 Repo Categories Tracked

HuggingFace ecosystem · Agentic & orchestration · AI coding agents · Interpretability & alignment · Synthetic data · Foundation labs & models · Qwen & Zhipu · Training & fine-tuning · Architecture & optimization · Evaluation & observability · Red-teaming & security · Local LLM ecosystem · MCP & tool protocol · Advanced RAG · Vector stores · Multimodal & generative media · MLOps & deployment

## Data Source

All data is sourced from the GitHub Archive public dataset (BigQuery) and public GitHub user profiles via the official GitHub REST API. No private data is collected.
