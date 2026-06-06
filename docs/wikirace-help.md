# Wikirace Help

**Wikirace** compares Wikipedia **daily pageviews** for a group of articles over a date range. See who attracted more attention — and by how much.

Data comes from the [Wikimedia Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs_pageviews/documentation/getting-started.html). StatsWiki resolves articles via [Wikidata](https://www.wikidata.org/) QIDs.

---

## Quick start

1. Open **[Wikirace](/wikirace)** from the site header.
2. **Search** for articles by name or QID (autocomplete uses the StatsWiki catalog).
3. Add **at least two** articles to the group.
4. Set a **start** and **end** date (or use a quick window preset).
5. Click **Compare →**.

You can also pick a **preset group** (elections, sports finals, etc.) to load a ready-made race.

---

## Reading the results

### Chart

Overlaid **daily pageview curves** — one color per article. The time axis runs from your start date to your end date.

### Race% (area under the curve)

**Race%** is each article’s **area under the curve** over the selected period — i.e. the sum of its daily pageviews, expressed as a share of the group total:

```
Race% = sum(daily pageviews for article) ÷ sum(daily pageviews for all articles) × 100
```

On the chart, each colored **shaded band** is that article’s area; a larger band means a higher Race%. The results table is sorted by Race% (highest first).

| Column | Meaning |
|--------|---------|
| **Views** | Total pageviews in the selected period |
| **Race%** | Share of the group’s combined attention |
| **Share** | Visual bar for Race% |

**Example:** Trump 68% · Harris 32% means Trump’s Wikipedia article received about twice as many views as Harris’s over that window.

### Resize buttons

On a race page, **1 month / 3 months / 6 months / 1 year** recalculates the window ending on the current end date (or the day before a preset event). The URL updates with the new dates.

---

## URL format

Every race has a **shareable URL** with three parts:

```
/wikirace/{QID1}+{QID2}+…/{start}/{end}
```

| Part | Format | Example |
|------|--------|---------|
| Group | Wikidata QIDs joined with `+` | `Q22686+Q10853588` |
| Start | `YYYY-MM-DD` | `2024-05-09` |
| End | `YYYY-MM-DD` | `2024-11-04` |

### Examples

| Race | URL |
|------|-----|
| 2024 US President (6 months pre-election) | `/wikirace/Q22686+Q10853588/2024-05-09/2024-11-04` |
| 2020 US President | `/wikirace/Q22686+Q6279/2020-05-07/2020-11-02` |
| 2024 NBA Finals (3 months) | `/wikirace/Q131371+Q132893/2024-03-19/2024-06-16` |

No names or slugs in the URL — only QIDs and dates.

---

## Building a custom group

### Article search

- Type a **name** (e.g. `Trump`, `Biden`, `Chiefs`).
- Or type a **QID** (e.g. `Q22686`) and press Enter.
- Selected articles appear as **chips**; click **×** to remove.
- The catalog lists articles enriched in StatsWiki (~3,700 QIDs). Articles outside the catalog can still be added by QID if they exist on English Wikipedia.

### Dates

- **Quick window** fills start/end relative to yesterday (builder) or relative to the race end date (resize buttons on a race page).
- **Preset groups** use curated ranges anchored to the day **before** the event (election day, final, etc.) to avoid single-day spikes.

---

## Preset groups

Ready-made races for common comparisons:

| Preset | Articles | Default period |
|--------|----------|----------------|
| 2024 US President | Trump · Harris | 6 months before Nov 5, 2024 |
| 2020 US President | Trump · Biden | 6 months before Nov 3, 2020 |
| 2016 US President | Trump · Clinton | 6 months before Nov 8, 2016 |
| 2022 FL Governor | DeSantis · Crist | 6 months before Nov 8, 2022 |
| 2022 PA Senate | Fetterman · Oz | 6 months before Nov 8, 2022 |
| Super Bowl LVIII | Chiefs · 49ers | 3 months before Feb 11, 2024 |
| 2024 NBA Finals | Celtics · Mavericks | 3 months before Jun 17, 2024 |
| 2022 World Cup Final | Argentina · France | 3 months before Dec 18, 2022 |

---

## What Wikirace is — and isn’t

### Good for

- Comparing **relative Wikipedia attention** between candidates, teams, or topics.
- Exploring **attention over time** (trends, spikes, debates, scandals).
- Sharing a **reproducible link** to a specific comparison.

### Not a prediction tool

Higher pageviews reflect **curiosity and media coverage**, not necessarily votes or match outcomes. Incumbents, celebrities, and viral moments can skew the signal. Use Race% as an **attention index**, not a forecast.

---

## For developers

### Regenerate the article catalog

```bash
cd pipeline && pip install -e .
sw-wikirace-catalog
```

Writes `web/public/wikirace/catalog.json` from `web/public/data/q/*.json`.

### Regenerate this help page

```bash
cd web && npm run build:help
```

Source: `docs/wikirace-help.md` → `web/public/wikirace/help.json` (bundled at `npm run build`).

### Local dev

```bash
cd web && npm run dev
# → http://localhost:5173/wikirace
```

---

## License & attribution

Wikipedia pageview data: [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use).

Article metadata: [Wikidata CC0](https://creativecommons.org/publicdomain/zero/1.0/).

StatsWiki code: [MIT](https://github.com/thepriben/StatsWiki/blob/main/LICENSE).
