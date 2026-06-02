import time
from datetime import date, timedelta

import requests

from statswiki.config import DELAY, FETCH_RETRIES, FETCH_RETRY_WAIT, LANG, START, USER_AGENT
from statswiki.store import has_day, write_day


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

    return None


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
