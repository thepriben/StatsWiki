# Wikirace

Compare **daily English Wikipedia pageviews** for a group of articles over any date range. Each article gets a **Race%** — its share of total group attention, measured as **area under the curve**.

Public user guide: [`wikirace-help.md`](wikirace-help.md) → rendered at `/wikirace/help`.

---

## Routes

| Path | View |
|------|------|
| `/wikirace` | Builder — search catalog, pick articles, set dates |
| `/wikirace/help` | Public help (from markdown) |
| `/wikirace/{QID1}+{QID2}+…/{start}/{end}` | Race — chart, table, shareable URL |

Example:

```
/wikirace/Q22686+Q10853588/2024-05-09/2024-11-04
```

URLs use **Wikidata QIDs and dates only** — no article slugs or labels.

### Abuse limits (client-side)

| Limit | Value | Why |
|-------|-------|-----|
| Max articles | 10 | Chart readability + fewer API calls |
| Max date span | 365 days | Matches longest resize preset |
| Race loads | 6 / minute / tab | Only when uncached API fetches are needed |
| Pageview cache | Per tab session | Re-opening the same race skips repeat API calls |
| Race result cache | Per tab session | Same URL replays instantly without rate-limit hit |

Fetches run in the **visitor’s browser** (not StatsWiki servers). These guards are polite-use quick wins, not a hard anti-DDoS barrier.

---

## Race%

For each article, sum daily pageviews over the selected period. Race% is that total as a fraction of the group sum:

```
Race% = Σ(daily views for article) ÷ Σ(daily views for all articles) × 100
```

This is the discrete integral of the daily curve (area under the curve). **Stacked share** (default chart) stacks daily slices so each band’s area matches Race%. **Daily compare** overlays curves on one scale for peak-day comparison.

Race% is an **attention index**, not a vote or outcome predictor.

---

## Layout

```
web/src/wikirace/
├── lib.js              # URL parsing, API fetch, Race%, catalog search
├── WikiracePage.vue    # Builder, presets, race view, toolbar
├── MultiLineChart.vue  # Overlaid daily curves (SVG)
├── QidPicker.vue       # Chips + autocomplete
└── HelpPage.vue        # Renders help.json

web/public/wikirace/
├── groups.json         # Preset races (politics, sport)
├── catalog.json        # ~3.7k QIDs for autocomplete
└── help.json           # Built from docs/wikirace-help.md

docs/
├── wikirace.md         # This file (maintainer README)
└── wikirace-help.md    # Public help source (English)

pipeline/src/statswiki/wikirace_catalog.py
web/scripts/build-help.mjs
```

Routing is wired in `web/src/App.vue` (`parseWikiracePath` in `lib.js`).

---

## Data sources

| Data | Source | Notes |
|------|--------|-------|
| Daily pageviews | [Wikimedia Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs_pageviews/documentation/getting-started.html) | Fetched live in the browser |
| Article labels / titles | `catalog.json`, `groups.json`, or `data/q/Q*.json` | Catalog from StatsWiki QID exports |
| Preset date ranges | `groups.json` → `defaultRange` | End date = day **before** the event |

### Pageviews API (browser)

- Endpoint: `wikimedia.org/.../per-article/en.wikipedia/all-access/user/daily/{start}/{end}` (human pageviews; default agent)
- **No custom headers** in `fetch()` — custom headers trigger CORS preflight and fail on Wikimedia.
- **Daily data from July 1, 2015** — earlier ranges return HTTP 404; the app clamps the fetch start and shows a note.
- Long ranges are split into monthly chunks.
- Article paths use `encodeURIComponent` on the Wikipedia title (spaces, parentheses).
- Timestamps from the API look like `2024050900`; parse with `parsePvDay()` (first 8 chars → `YYYY-MM-DD`).

---

## Static assets

### `groups.json`

Preset races. Each group:

```json
{
  "slug": "us-president-2024",
  "label": "2024 US Presidential Election",
  "category": "politics",
  "eventDate": "2024-11-05",
  "defaultWindow": "6m",
  "defaultRange": { "start": "2024-05-09", "end": "2024-11-04" },
  "context": "Optional one- or two-sentence note shown on the race page (event + how to read results).",
  "members": [
    { "qid": "Q22686", "label": "Donald Trump", "article": "Donald_Trump" }
  ]
}
```

`article` is the English Wikipedia title (underscores). `defaultRange` avoids ending on election day spikes.

### Autocomplete

Hybrid search in the builder:

1. **Local catalog** (`catalog.json`) — fast, ~3.7k StatsWiki articles.
2. **Wikidata API** (`wbsearchentities` + `wbgetentities`) — fills gaps when the catalog has fewer than 8 hits. Only entities with an **English Wikipedia** sitelink are shown.

No custom headers on Wikidata requests (`origin=*`); CORS is allowed from the browser.

### `catalog.json`

Built from `web/public/data/q/Q*.json`:

```bash
cd pipeline && pip install -e .
sw-wikirace-catalog
```

Articles outside the catalog can also be found via Wikidata search or by typing a QID directly.

### `help.json`

Built from `docs/wikirace-help.md`:

```bash
cd web && npm run build:help
```

Runs automatically on `npm run build`.

---

## Dev

```bash
cd web && npm run dev
# → http://localhost:5173/wikirace
```

Or from repo root: `npm run dev`.

---

## Extending

**New preset race** — add an entry to `web/public/wikirace/groups.json` with members, `eventDate`, and `defaultRange` (typically 6 months or 3 months before the event).

**Choosing members** — prefer articles tied to a single show, event, or product (no spinoff crossovers: e.g. Gus Fring spans Breaking Bad and Better Call Saul, so his pageviews are ambiguous). Avoid overly broad topics (e.g. Bitcoin) where traffic is mostly generic background curiosity, not contextual attention to the headline event. Optional `context` explains the window and any member constraints.

**Refresh autocomplete** — run `sw-wikirace-catalog` after QID exports update.

**Edit public help** — change `docs/wikirace-help.md`, then `npm run build:help`.

**Chart colors** — neutral palette in `CHART_COLORS` (`lib.js`); avoid red/blue as first pair (US party connotation).

---

## Sharing / social previews

Share copies the race URL to the clipboard. There is **no** Open Graph or Twitter Card image yet — link previews show a generic site card, not the chart. OG image generation per race is a possible follow-up.
