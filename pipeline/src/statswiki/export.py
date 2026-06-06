import json
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from statswiki.config import JSON_OUT, MANIFEST, MONTHS, START, TOP_N
from statswiki.filters import skip
from statswiki.mapping import line_from_row, merge_views_by_qid, meta_lookup
from statswiki.store import date_range, load_articles, scan_pageviews


def _aggregate(lf, start: date, end: date) -> pl.DataFrame:
    return (
        lf.filter((pl.col("date") >= start) & (pl.col("date") <= end))
        .group_by("article")
        .agg(pl.col("views").sum())
        .sort("views", descending=True)
    )


def _lines(df: pl.DataFrame, meta: dict) -> list[dict]:
    merged = merge_views_by_qid(df, meta)
    out = []
    seen_qids = set()
    for row in merged.iter_rows(named=True):
        if skip(row["article"]):
            continue
        qid = row.get("qid", "")
        if qid in seen_qids:
            continue
        seen_qids.add(qid)
        out.append(line_from_row(row, meta, len(out) + 1))
        if len(out) >= TOP_N:
            break
    return out


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def export_period(kind: str, year: int = 0, month: int = 0, day: int = 0) -> bool:
    lf = scan_pageviews()
    if lf is None:
        return False
    meta = meta_lookup(load_articles())
    yesterday = date.today() - timedelta(days=1)

    if kind == "alltime":
        start, end = START, yesterday
        path = JSON_OUT / "alltime.json"
        title = "All time"
    elif kind == "year":
        start = date(year, 1, 1) if year > START.year else START
        end = min(date(year, 12, 31), yesterday)
        path = JSON_OUT / "year" / f"{year}.json"
        title = str(year)
    elif kind == "month":
        import calendar
        start = date(year, month, 1)
        end = min(date(year, month, calendar.monthrange(year, month)[1]), yesterday)
        path = JSON_OUT / "month" / f"{year}" / f"{month:02d}.json"
        title = f"{MONTHS[month - 1]} {year}"
    elif kind == "day":
        start = end = date(year, month, day)
        path = JSON_OUT / "day" / f"{year}" / f"{month:02d}" / f"{day:02d}.json"
        title = f"{day} {MONTHS[month - 1]} {year}"
    elif kind == "week":
        week_end = date(year, month, day)
        if week_end.weekday() != 6:
            return False
        week_start = week_end - timedelta(days=6)
        start = max(week_start, START)
        end = week_end
        path = JSON_OUT / "week" / f"{week_end.year}" / f"{week_end.isoformat()}.json"
        from statswiki.post_text import week_range_label

        title = week_range_label(week_start, week_end)
    else:
        return False

    if start > yesterday:
        return False

    df = _aggregate(lf, start, end).collect()
    if df.is_empty():
        return False

    payload = {"period": title, "lines": _lines(df, meta)}

    if kind == "year":
        first_m = START.month if year == START.year else 1
        max_m = yesterday.month if year == yesterday.year else 12
        payload["nav"] = [{"label": MONTHS[m - 1], "path": f"{year}/{m:02d}"} for m in range(first_m, max_m + 1)]

    if kind == "month":
        import calendar
        last = calendar.monthrange(year, month)[1]
        if year == yesterday.year and month == yesterday.month:
            last = yesterday.day
        payload["nav"] = [{"label": f"{d:02d}", "path": f"{year}/{month:02d}/{d:02d}"} for d in range(1, last + 1)]

    _write(path, payload)
    return True


def export_manifest() -> None:
    lo, hi = date_range()
    payload = {
        "start": START.isoformat(),
        "end": hi.isoformat() if hi else None,
        "updated": date.today().isoformat(),
        "language": "en",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n")
    _write(JSON_OUT / "manifest.json", payload)


def export_recent() -> None:
    y = date.today() - timedelta(days=1)
    export_period("day", y.year, y.month, y.day)
    if y.weekday() == 6:
        export_period("week", y.year, y.month, y.day)
    export_period("month", y.year, y.month)
    export_period("year", y.year)
    export_period("alltime")
    export_manifest()
    from statswiki.qid_export import export_qid_stats
    export_qid_stats()


def export_all(year: int | None = None) -> None:
    lf = scan_pageviews()
    if lf is None:
        print("No data")
        return
    lo, hi = date_range()
    if not hi:
        return
    years = [year] if year else range(lo.year, hi.year + 1)
    for y in years:
        export_period("year", y)
        for m in range(1, 13):
            if y == START.year and m < START.month:
                continue
            if export_period("month", y, m):
                import calendar
                for d in range(1, calendar.monthrange(y, m)[1] + 1):
                    tgt = date(y, m, d)
                    if tgt < START or tgt > hi:
                        continue
                    export_period("day", y, m, d)
    export_period("alltime")
    export_manifest()
    from statswiki.qid_export import export_qid_stats
    n = export_qid_stats()
    print(f"Export done — {n} QID series")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int)
    p.add_argument("--recent", action="store_true")
    args = p.parse_args()
    if args.recent:
        export_recent()
    elif args.year:
        export_all(args.year)
    else:
        export_all()


if __name__ == "__main__":
    main()
