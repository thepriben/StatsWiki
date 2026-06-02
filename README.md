# StatsWiki

**Most-read articles on English Wikipedia** — daily rankings from **July 1, 2015** to yesterday.

**Live site:** https://thepriben.github.io/StatsWiki/

MIT license — fork for [another language or project → ADAPT.md](ADAPT.md).

---

## At a glance

| | |
|---|---|
| **Data** | Wikimedia Pageviews API → Parquet → static JSON |
| **Site** | Vue 3 SPA on GitHub Pages (no runtime API calls) |
| **Updates** | Daily cron + manual backfill for history |
| **Enrichment** | Wikidata QID, label, description, image |
| **Rankings** | Top 50 per day, month, year, all-time |

---

## What the site shows

### Home

Three live panels (top 50 each), with fallback to the latest available period when yesterday / this month are not yet ingested:

- **Yesterday** (or latest day)
- **This month** (or latest month)
- **This year**

### Period pages

| View | URL | Content |
|------|-----|---------|
| Day | `/StatsWiki/2026/05/31` | Top 50 that day |
| Month | `/StatsWiki/2026/05` | Top 50 aggregated over the month |
| Year | `/StatsWiki/2026` | Top 50 aggregated over the year |
| All time | `/StatsWiki/alltime` | Top 50 since July 2015 |

Browse via **Year / Month / Day** dropdowns in the header (no date in the page title).

### Article stats (QID)

Click a **Wikidata QID** in any table → `/StatsWiki/q/Q22686` with monthly / yearly view charts, total views, peak period.

*Coming next:* compare several QIDs on a date range (“wiki wars”).

Each row: rank, Wikipedia link, QID, description, thumbnail, view count.

---

## Architecture

```
Wikimedia Pageviews API     one HTTP request per day
         │
         ▼
data/pageviews/             Parquet (date, article, views, rank)
data/articles.parquet       Wikidata catalog
         │
         ▼  aggregate + merge by QID
web/public/data/            static JSON (top 50 per period)
         │
         ▼
Vue 3 SPA                   GitHub Pages CDN
```

**Day → month → year:** months and years are **sums of daily rows**, never fetched separately. See [consolidation](#day--month--year) below.

**Redirects:** old article titles that share a Wikidata item have views merged before ranking.

---

## Quick start (local)

```bash
# Pipeline
cd pipeline && python3 -m venv .venv && source .venv/bin/activate
pip install -e .

sw-fetch --date 2026-05-01          # one day
sw-backfill --year 2026               # full year
sw-daily                              # yesterday + export
sw-export-qids                        # QID time-series JSON

# Frontend
cd web && npm ci && npm run dev
# → http://localhost:5173/StatsWiki/
```

---

## Deployment (GitHub Pages)

1. **Settings → Pages → Source: GitHub Actions** (one-time).
2. Push to `main` — **Deploy Pages** runs when `web/` or `data/` changes.
3. Backfill and daily workflows **commit data, then deploy** in the same run.

| Workflow | Trigger | Role |
|----------|---------|------|
| **Deploy Pages** | Push or manual | Build Vue → publish |
| **Daily update** | 07:00 UTC or manual | Yesterday → commit → deploy |
| **Backfill** | Manual (pick year) | One year of history |
| **Backfill sequence** | Manual | 2025 → 2016 in one job |

### Backfill order (recommended)

1. **Current year** first — homepage needs recent data.
2. **Backfill sequence** (or year-by-year) down to **2015** (July 1 for 2015).
3. Leave **Daily update** enabled.

~5–10 minutes per year on GitHub Actions.

---

## Repository layout

```
StatsWiki/
├── web/                         # Vue 3 frontend
│   ├── src/
│   │   ├── App.vue              # routing, header, home
│   │   ├── QidPage.vue          # article stats + chart
│   │   ├── RankingTable.vue
│   │   └── lib.js
│   └── public/data/             # generated JSON (+ q/Q*.json)
├── data/                        # Parquet source of truth
│   ├── pageviews/year=Y/month=M/
│   ├── articles.parquet
│   └── manifest.json
├── pipeline/src/statswiki/      # Python ETL
└── .github/workflows/
```

---

## Pipeline commands

| Command | Purpose |
|---------|---------|
| `sw-fetch --date YYYY-MM-DD` | Ingest one day |
| `sw-backfill --year YYYY` | Ingest year + Wikidata top 1000 + export |
| `sw-daily` | Yesterday + enrich + export recent |
| `sw-enrich --top 500` | Re-enrich top articles by total views |
| `sw-enrich --refresh-shadows 100` | Retry unresolved QIDs |
| `sw-export --recent` | Rebuild yesterday / month / year / alltime JSON |
| `sw-export --year YYYY` | Export all periods for one year |
| `sw-export-qids` | Export `data/q/Q*.json` time series for charts |

All ingest is **idempotent** — existing days are skipped.

---

## Data model

### Pageviews (`data/pageviews/`)

| Column | Description |
|--------|-------------|
| `date` | Day |
| `article` | Title with underscores (as in API) |
| `views` | View count |
| `rank` | Position in daily top ~1000 |

### Articles catalog (`data/articles.parquet`)

| Column | Description |
|--------|-------------|
| `article` | Pageview title |
| `qid` | Wikidata QID (e.g. Q22686) |
| `resolved_title` | Canonical title after Wikipedia redirects |
| `label`, `description`, `image` | From Wikidata |
| `updated_at` | Last enrichment |

### Export JSON (`web/public/data/`)

Each file has `period`, `lines` (array of ranked articles), and optionally `nav` (sub-links on year/month views).

| Field | Description |
|-------|-------------|
| `rank` | 1–50 |
| `title` | Wikipedia title (`Article_Name`) |
| `label` | Display name from Wikidata |
| `description` | Short Wikidata description |
| `views` | View count for the period |
| `qid` | Wikidata ID (e.g. `Q12345`) |
| `image` | Commons thumbnail URL |

`manifest.json` — `start`, `end`, `updated`, `language`.

---

## Day → month → year

```
1 API call / day  →  Parquet row per (date, article)
                         │
                         ├─ SUM(days in month)  →  month/YYYY/MM.json
                         ├─ SUM(days in year)   →  year/YYYY.json
                         └─ SUM(all days)       →  alltime.json
```

---

## Wikidata

Batched enrichment (50 titles / request):

1. **QID** — Wikipedia `pageprops`, follows redirects
2. **Fallbacks** — Wikidata search + opensearch
3. **Entity** — label, description, image (P18 / P154)
4. **Export** — merge views by QID before top-50 ranking

Manual overrides in `filters.py` for edge cases. Shadow QIDs (`Q_en_…`) retried on high-traffic articles.

Modules: `wikidata.py`, `mapping.py`, `qid_export.py`.

---

## Fork for another language

This repo tracks **English Wikipedia only**. To run StatsWiki for French, German, Japanese, etc.:

→ **[ADAPT.md](ADAPT.md)** — step-by-step fork guide (config, Pages URL, Wikidata language, backfill).

Multi-language in a **single** site is not implemented yet; one fork per language is the intended model for now.

---

## License

**Code:** [MIT](LICENSE)

**Data** (Wikipedia / Wikidata content shown on the site): [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), [Wikidata CC0](https://creativecommons.org/publicdomain/zero/1.0/) (Commons images retain their own licenses).
