import gzip
import time
from collections import defaultdict
from datetime import date, timedelta

import requests

from statswiki.config import DELAY, FETCH_RETRIES, FETCH_RETRY_WAIT, LANG, START, USER_AGENT
from statswiki.store import has_day, write_day

# en + en.m ≈ en.wikipedia/all-access (desktop + mobile web)
_DUMP_PROJECTS = frozenset({"en", "en.m"})
_DUMP_TOP_N = 1000
# dumps.wikimedia.org rate-limits aggressive clients with HTTP 429, so we
# download the 24 hourly files sequentially with a polite delay + backoff.
_DUMP_HOUR_RETRIES = 6
_DUMP_POLITE_DELAY = 1.0


def _dump_hour_url(day: date, hour: int) -> str:
    return (
        f"https://dumps.wikimedia.org/other/pageviews/"
        f"{day.year}/{day.year}-{day.month:02d}/"
        f"pageviews-{day:%Y%m%d}-{hour:02d}0000.gz"
    )


def _fetch_dump_hour(day: date, hour: int) -> dict[str, int] | None:
    """Download and aggregate one hourly dump (en + en.m). None if unavailable."""
    url = _dump_hour_url(day, hour)
    for attempt in range(1, _DUMP_HOUR_RETRIES + 1):
        try:
            with requests.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=180, stream=True
            ) as r:
                if r.status_code == 404:
                    print(f"  dump hour {hour:02d} not published yet (404)")
                    return None
                if r.status_code != 200:
                    print(
                        f"  dump hour {hour:02d} HTTP {r.status_code} "
                        f"(attempt {attempt}/{_DUMP_HOUR_RETRIES})"
                    )
                    time.sleep(10 * attempt)
                    continue
                views: dict[str, int] = {}
                with gzip.open(r.raw, "rt", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        parts = line.rstrip("\n").split(" ")
                        if len(parts) < 3 or parts[0] not in _DUMP_PROJECTS:
                            continue
                        title = parts[1]
                        if title == "-":
                            continue
                        try:
                            views[title] = views.get(title, 0) + int(parts[2])
                        except ValueError:
                            continue
                return views
        except (OSError, requests.RequestException) as exc:
            print(
                f"  dump hour {hour:02d} error "
                f"(attempt {attempt}/{_DUMP_HOUR_RETRIES}): {exc}"
            )
            time.sleep(10 * attempt)
    print(f"  dump hour {hour:02d} gave up after {_DUMP_HOUR_RETRIES} attempts")
    return None


def fetch_day_from_dumps(day: date) -> list[dict] | None:
    """Build the daily top list from 24 hourly dumps when the REST API lags behind."""
    print(f"  REST API unavailable — aggregating {day} from hourly dumps…")
    merged: dict[str, int] = defaultdict(int)
    for hour in range(24):
        hour_views = _fetch_dump_hour(day, hour)
        if hour_views is None:
            print(f"  aborting dump aggregation — hour {hour:02d} unavailable")
            return None
        for title, count in hour_views.items():
            merged[title] += count
        print(f"  dump hour {hour:02d}/23 aggregated ({len(hour_views)} en titles)")
        time.sleep(_DUMP_POLITE_DELAY)

    if not merged:
        return None

    ranked = sorted(merged.items(), key=lambda x: -x[1])[:_DUMP_TOP_N]
    print(f"  dumps: {len(merged)} titles, keeping top {len(ranked)}")
    return [
        {"date": day, "article": article, "views": views, "rank": i + 1}
        for i, (article, views) in enumerate(ranked)
    ]


def fetch_day(day: date) -> list[dict] | None:
    """
    Fetch top articles for one day.
    Returns rows on success, None if the API is unavailable or not ready yet.
    """
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"{LANG}.wikipedia/all-access/{day:%Y/%m/%d}"
    )
    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        except requests.RequestException as exc:
            print(f"  network error for {day} (attempt {attempt}/{FETCH_RETRIES}): {exc}")
            if attempt < FETCH_RETRIES:
                time.sleep(FETCH_RETRY_WAIT * attempt)
            continue

        time.sleep(DELAY)

        if r.status_code == 200:
            try:
                items = r.json()["items"][0]["articles"]
            except (KeyError, IndexError, TypeError):
                print(f"  malformed response for {day}")
                return None
            if not items:
                print(f"  empty top list for {day}")
                return None
            return [
                {"date": day, "article": a["article"], "views": int(a["views"]), "rank": i + 1}
                for i, a in enumerate(items)
            ]

        # 404 = day not published yet; 5xx/429 = transient
        print(f"  HTTP {r.status_code} for {day} (attempt {attempt}/{FETCH_RETRIES})")
        if attempt < FETCH_RETRIES and r.status_code in (404, 429, 500, 502, 503, 504):
            time.sleep(FETCH_RETRY_WAIT * attempt)

    return fetch_day_from_dumps(day)


def ingest_day(day: date) -> str:
    """
    Ingest one day if missing.
    Returns: ingested | skipped | failed
    """
    if has_day(day):
        return "skipped"
    rows = fetch_day(day)
    if rows is None:
        return "failed"
    write_day(day, rows)
    return "ingested"


def ingest_day_with_retry(day: date) -> str:
    """Try ingest; on failure, retry once after a pause (for daily cron)."""
    status = ingest_day(day)
    if status != "failed":
        return status
    print(f"  retrying {day} after {FETCH_RETRY_WAIT}s…")
    time.sleep(FETCH_RETRY_WAIT)
    return ingest_day(day)


def ingest_range(start: date, end: date) -> int:
    """Ingest each day in [start, end]. Returns count of newly ingested days."""
    n = 0
    day = start
    while day <= end:
        status = ingest_day_with_retry(day)
        if status == "ingested":
            n += 1
            print(f"{day}: ingested")
        elif status == "failed":
            print(f"{day}: failed")
        day += timedelta(days=1)
    return n


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday)")
    args = p.parse_args()
    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    status = ingest_day_with_retry(day)
    print(f"{day}: {status}")


if __name__ == "__main__":
    main()
