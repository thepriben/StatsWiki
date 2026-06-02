# Adapting StatsWiki

This guide explains how to fork StatsWiki for **another Wikipedia language** (e.g. French, German, Japanese) or reuse the architecture for a **related Wikimedia rankings project**.

The codebase is MIT-licensed — fork freely, rename the project, deploy your own instance.

---

## Quick checklist

| Step | What to change |
|------|----------------|
| 1 | Fork repo → rename (e.g. `StatsWiki-fr`) |
| 2 | `pipeline/src/statswiki/config.py` — `LANG`, `START`, `USER_AGENT` |
| 3 | `web/vite.config.js` — `base` path for GitHub Pages |
| 4 | `web/src/lib.js` — `REPO_URL`, routing base if needed |
| 5 | GitHub → Settings → Pages → **GitHub Actions** |
| 6 | Backfill current year, then history (see [README](README.md)) |
| 7 | Optional: UI strings, month names, tagline in `App.vue` / `config.py` |

---

## 1. Choose your scope

### A — Another Wikipedia language (most common)

Same APIs, same pipeline. Examples:

| Language | `LANG` | Pageviews API segment |
|----------|--------|------------------------|
| French | `fr` | `fr.wikipedia` |
| German | `de` | `de.wikipedia` |
| Japanese | `ja` | `ja.wikipedia` |
| Spanish | `es` | `es.wikipedia` |

Wikidata labels and descriptions should follow the wiki language (see §4).

### B — Another Wikimedia project

The [Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/) also exposes other projects, e.g.:

```
/metrics/pageviews/top/{project}/{access}/{year}/{month}/{day}
```

Examples: `fr.wiktionary`, `commons.wikimedia`, `www.wikidata` (where available).

To support a non-`*.wikipedia` project you will need to:

1. Generalise `fetch.py` — replace `{LANG}.wikipedia` with a `PROJECT` config (e.g. `fr.wiktionary`).
2. Generalise `wikidata.py` — Wikipedia `pageprops` may not apply; enrichment strategy depends on the project.
3. Review `filters.py` — namespace prefixes differ by project.

This path is more work; start with another Wikipedia language unless you know you need it.

---

## 2. Pipeline configuration

Edit `pipeline/src/statswiki/config.py`:

```python
LANG = "fr"                    # ISO 639-1 wiki language code
START = date(2015, 7, 1)       # Pageviews API start (July 2015 for most wikis)
TOP_N = 50                     # Rankings size on the website
USER_AGENT = "StatsWiki-fr/1.0 (https://github.com/you/StatsWiki-fr; contact@you)"
DELAY = 0.35                   # Seconds between API calls — keep ≥ 0.2
```

| Variable | Purpose |
|----------|---------|
| `LANG` | Wikipedia subdomain + Wikidata sitelink (`frwiki`, `dewiki`, …) |
| `START` | First day to ingest (API limit is usually 2015-07-01) |
| `TOP_N` | Number of rows exported per period (site shows top 50 by default) |
| `USER_AGENT` | **Required** by Wikimedia — include a URL and contact |
| `DELAY` | Rate limiting between HTTP requests |

---

## 3. Frontend and GitHub Pages

### Base URL

If your repo is `https://github.com/you/StatsWiki-fr`, Pages serves at:

```
https://you.github.io/StatsWiki-fr/
```

Set the Vite base path in `web/vite.config.js`:

```js
export default defineConfig({
  base: '/StatsWiki-fr/',
  // ...
});
```

Update routing in `web/src/App.vue` — the `parseRoute` function uses a hardcoded base:

```js
const base = '/StatsWiki-fr'.replace(/\/$/, '');
```

Update the repo link in `web/src/lib.js`:

```js
export const REPO_URL = 'https://github.com/you/StatsWiki-fr';
```

### UI language

StatsWiki UI strings are in English in `web/src/App.vue`. For a full localisation:

- Header tagline, button labels, home section titles
- `MONTHS` in `config.py` (export period titles) and `web/src/lib.js` (date picker)
- Error messages (`No data yet.`, etc.)

The ranking **article labels** come from Wikidata in the wiki language once enrichment uses `LANG` (§4).

---

## 4. Wikidata enrichment for your language

Most of the pipeline already reads `LANG` from config for:

- Wikipedia API host (`{LANG}.wikipedia.org`)
- Pageviews path (`{LANG}.wikipedia`)
- Wikidata sitelinks (`{LANG}wiki`)

**Still hardcoded to English today** — change these when forking:

| File | What to update |
|------|----------------|
| `wikidata.py` | `_pick_label` / `_pick_description` — use `LANG` instead of `"en"` |
| `wikidata.py` | `wbgetentities` `languages` parameter |
| `wikidata.py` | `wbsearchentities` `language` parameter |
| `mapping.py` | Shadow QID prefix `Q_en_` → e.g. `Q_fr_` (or `Q_{LANG}_`) |
| `export.py` | `manifest.json` `"language"` field |

Suggested shadow QID helper:

```python
def shadow_qid(title: str) -> str:
    return f"Q_{LANG}_{normalize_title(title)}"
```

If you adapt the code for another language, keep your changes in **your fork** — pull requests to [thepriben/StatsWiki](https://github.com/thepriben/StatsWiki) are **not accepted**.

---

## 5. Filters and manual redirects

`pipeline/src/statswiki/filters.py`:

- **`FILTERS`** — skip namespaces (`Special:`, `File:`, …). Adjust if your wiki uses different high-traffic namespaces.
- **`REDIRECTS`** — manual title → QID map for renamed articles, election pages, pandemic titles, etc. Start empty; add entries when you see duplicate top-50 rows.

---

## 6. GitHub setup

1. **Fork** (or create a new repo and push this code).
2. **Pages** → Build and deployment → **GitHub Actions**.
3. **Secrets** — none required for public Wikimedia APIs.
4. **Backfill** (Actions → Backfill or Backfill sequence):
   - Run **current year** first (homepage needs recent data).
   - Then **2025 → 2015** (2015 from July 1).
5. **Daily update** — enable schedule (07:00 UTC) or run manually.

Workflows commit data with `github-actions[bot]` and deploy automatically.

---

## 7. Local development

```bash
# Pipeline
cd pipeline && python3 -m venv .venv && source .venv/bin/activate
pip install -e .
sw-backfill --year 2026          # or sw-fetch --date 2026-05-01
sw-export --recent
sw-export-qids                   # QID time-series for chart pages

# Frontend
cd web && npm ci && npm run dev
# → http://localhost:5173/YourRepoName/
```

---

## 8. What you do *not* need to change

- Parquet layout (`data/pageviews/year=Y/month=M/`)
- JSON export shape (`lines`, `nav`, `manifest`)
- GitHub Actions workflow structure
- Vue app architecture (home → period pages → QID stats)
- Day → month → year consolidation logic

---

## 9. Naming and branding

| Item | Suggestion |
|------|------------|
| Repo name | `StatsWiki-fr`, `LecturesWiki`, … |
| Site title | `App.vue` → `.brand` text |
| `USER_AGENT` | Include your repo URL |
| License | Keep MIT `LICENSE` file; attribute original if you wish |

---

## 10. Upstream policy

- **Fork:** MIT license — copy, modify, deploy your own instance freely.
- **Pull requests:** not accepted on the upstream repo. Maintain your changes in your fork.
- **Issues:** use your own tracker; upstream is not actively seeking contributions.
- **API docs:** [Analytics API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/), [Wikidata API](https://www.wikidata.org/wiki/Wikidata:Data_access)
