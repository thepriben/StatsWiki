from datetime import date, timedelta

from statswiki.config import START
from statswiki.export import export_all
from statswiki.fetch import ingest_range
from statswiki.wikidata import enrich_top


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int)
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--skip-enrich", action="store_true")
    args = p.parse_args()

    yesterday = date.today() - timedelta(days=1)

    if args.year:
        start = date(args.year, 1, 1)
        if args.year == START.year:
            start = START
        end = min(date(args.year, 12, 31), yesterday)
    elif args.start and args.end:
        start = date.fromisoformat(args.start)
        end = min(date.fromisoformat(args.end), yesterday)
    else:
        start, end = START, yesterday

    start = max(start, START)
    print(f"Backfill {start} → {end}")
    n = ingest_range(start, end)
    print(f"Ingested {n} days")

    if not args.skip_enrich:
        enrich_top(1000)

    if args.year:
        export_all(args.year)
    else:
        export_all()


if __name__ == "__main__":
    main()
