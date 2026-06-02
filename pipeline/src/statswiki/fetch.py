import time
from datetime import date, timedelta

import requests

from statswiki.config import DELAY, LANG, START, USER_AGENT
from statswiki.store import has_day, write_day


def fetch_day(day: date) -> list[dict]:
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"{LANG}.wikipedia/all-access/{day:%Y/%m/%d}"
    )
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    time.sleep(DELAY)
    if r.status_code != 200:
        print(f"  HTTP {r.status_code} for {day}")
        return []
    items = r.json()["items"][0]["articles"]
    return [
        {"date": day, "article": a["article"], "views": int(a["views"]), "rank": i + 1}
        for i, a in enumerate(items)
    ]


def ingest_day(day: date) -> bool:
    if has_day(day):
        return False
    rows = fetch_day(day)
    if rows:
        write_day(day, rows)
        return True
    return False


def ingest_range(start: date, end: date) -> int:
    n = 0
    d = start
    while d <= end:
        if ingest_day(d):
            n += 1
            print(f"  + {d} ({n})")
        d += timedelta(days=1)
    return n


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday)")
    args = p.parse_args()
    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    if ingest_day(day):
        print(f"Fetched {day}")
    else:
        print(f"Skipped {day}")


if __name__ == "__main__":
    main()
