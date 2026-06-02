"""Ingest and export any missing days from START through yesterday."""
from datetime import date, timedelta

from statswiki.config import JSON_OUT, START
from statswiki.export import export_period, export_manifest
from statswiki.fetch import ingest_day_with_retry
from statswiki.store import has_day


def _iter_days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _day_json(d: date):
    return JSON_OUT / "day" / f"{d.year}" / f"{d.month:02d}" / f"{d.day:02d}.json"


def missing_days(start: date, end: date) -> list[date]:
    return [d for d in _iter_days(start, end) if not has_day(d)]


def fill_gaps(skip_enrich: bool = True) -> int:
    yesterday = date.today() - timedelta(days=1)
    gaps = missing_days(START, yesterday)
    print(f"Missing in parquet: {len(gaps)} days")
    if not gaps:
        print("Parquet complete — checking day JSON exports…")
    else:
        ingested = failed = 0
        for d in gaps:
            status = ingest_day_with_retry(d)
            if status == "ingested":
                ingested += 1
                print(f"{d}: ingested")
            elif status == "failed":
                failed += 1
                print(f"{d}: failed")
            else:
                print(f"{d}: {status}")
        print(f"Ingested {ingested}, failed {failed}")

    affected_years = {d.year for d in gaps}
    affected_months = {(d.year, d.month) for d in gaps}
    exported_days = 0
    for d in _iter_days(START, yesterday):
        if not has_day(d):
            continue
        if not _day_json(d).exists():
            if export_period("day", d.year, d.month, d.day):
                exported_days += 1
    print(f"Exported {exported_days} day pages")

    import calendar
    for y in sorted(affected_years):
        export_period("year", y)
        for m in range(1, 13):
            if y == START.year and m < START.month:
                continue
            if y == yesterday.year and m > yesterday.month:
                continue
            export_period("month", y, m)

    export_period("alltime")
    export_manifest()

    if not skip_enrich:
        from statswiki.wikidata import enrich_top
        enrich_top(1000)

    from statswiki.qid_export import export_qid_stats
    n = export_qid_stats()
    print(f"Done — {n} QID series")
    return len(missing_days(START, yesterday))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--enrich", action="store_true", help="Run Wikidata enrichment")
    args = p.parse_args()
    remaining = fill_gaps(skip_enrich=not args.enrich)
    if remaining:
        raise SystemExit(f"{remaining} days still missing in parquet")


if __name__ == "__main__":
    main()
