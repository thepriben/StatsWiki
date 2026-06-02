"""Export per-QID pageview time series for the article stats pages."""

import json
from pathlib import Path

import polars as pl

from statswiki.config import JSON_OUT
from statswiki.mapping import is_real_qid
from statswiki.store import load_articles, scan_pageviews


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def export_qid_stats() -> int:
    """Write web/public/data/q/{QID}.json for each enriched item in catalog."""
    articles = load_articles()
    lf = scan_pageviews()
    if articles.is_empty() or lf is None:
        return 0

    catalog = articles.filter(
        pl.col("qid").str.contains(r"^Q\d+$")
    )
    if catalog.is_empty():
        return 0

    qid_info: dict[str, dict] = {}
    for row in catalog.iter_rows(named=True):
        qid = row["qid"]
        if not is_real_qid(qid):
            continue
        bucket = qid_info.setdefault(qid, {"meta": row, "titles": set()})
        bucket["titles"].add(row["article"])

    pv = lf.collect()
    out_dir = JSON_OUT / "q"
    n = 0

    for qid, info in qid_info.items():
        titles = list(info["titles"])
        sub = pv.filter(pl.col("article").is_in(titles))
        if sub.is_empty():
            continue

        meta = info["meta"]
        total = int(sub["views"].sum())

        monthly_df = (
            sub.with_columns([
                pl.col("date").dt.year().alias("y"),
                pl.col("date").dt.month().alias("m"),
            ])
            .group_by("y", "m")
            .agg(pl.col("views").sum())
            .sort("y", "m")
        )
        yearly_df = (
            sub.with_columns(pl.col("date").dt.year().alias("y"))
            .group_by("y")
            .agg(pl.col("views").sum())
            .sort("y")
        )

        payload = {
            "qid": qid,
            "label": meta.get("label") or titles[0].replace("_", " "),
            "title": meta.get("article") or titles[0],
            "description": meta.get("description", ""),
            "image": meta.get("image", ""),
            "total": total,
            "monthly": [
                {"period": f"{r['y']}-{r['m']:02d}", "views": int(r["views"])}
                for r in monthly_df.iter_rows(named=True)
            ],
            "yearly": [
                {"period": str(r["y"]), "views": int(r["views"])}
                for r in yearly_df.iter_rows(named=True)
            ],
        }
        _write(out_dir / f"{qid}.json", payload)
        n += 1

    return n


def main():
    import argparse
    p = argparse.ArgumentParser(description="Export QID time series JSON")
    p.parse_args()
    count = export_qid_stats()
    print(f"Exported {count} QID series")


if __name__ == "__main__":
    main()
