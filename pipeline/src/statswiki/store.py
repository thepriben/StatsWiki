from datetime import date
from pathlib import Path

import polars as pl

from statswiki.config import ARTICLES, PAGEVIEWS


def _part(day: date) -> Path:
    return PAGEVIEWS / f"year={day.year}" / f"month={day.month:02d}" / "data.parquet"


def has_day(day: date) -> bool:
    p = _part(day)
    if not p.exists():
        return False
    return pl.read_parquet(p).filter(pl.col("date") == day).height > 0


def write_day(day: date, rows: list[dict]) -> None:
    if not rows:
        return
    p = _part(day)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = pl.DataFrame(rows, schema={
        "date": pl.Date, "article": pl.String, "views": pl.Int64, "rank": pl.Int16,
    })
    if p.exists():
        old = pl.read_parquet(p).filter(pl.col("date") != day)
        new = pl.concat([old, new], how="vertical_relaxed")
    new.write_parquet(p, compression="zstd")


def scan_pageviews():
    if not PAGEVIEWS.exists():
        return None
    if not list(PAGEVIEWS.glob("**/*.parquet")):
        return None
    return pl.scan_parquet(PAGEVIEWS / "**" / "*.parquet")


def date_range() -> tuple[date | None, date | None]:
    lf = scan_pageviews()
    if lf is None:
        return None, None
    df = lf.select("date").collect()
    return df["date"].min(), df["date"].max()


ARTICLE_SCHEMA = {
    "article": pl.String,
    "qid": pl.String,
    "label": pl.String,
    "description": pl.String,
    "image": pl.String,
    "updated_at": pl.Date,
}


def load_articles() -> pl.DataFrame:
    if ARTICLES.exists():
        df = pl.read_parquet(ARTICLES)
        for col, dtype in ARTICLE_SCHEMA.items():
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).cast(dtype).alias(col))
        return df.select(list(ARTICLE_SCHEMA.keys()))
    return pl.DataFrame(schema=ARTICLE_SCHEMA)


def save_articles(df: pl.DataFrame) -> None:
    ARTICLES.parent.mkdir(parents=True, exist_ok=True)
    df.select(list(ARTICLE_SCHEMA.keys())).write_parquet(ARTICLES, compression="zstd")


def upsert_articles(rows: list[dict]) -> int:
    if not rows:
        return 0
    df = load_articles()
    titles = [r["article"] for r in rows]
    df = df.filter(~pl.col("article").is_in(titles))
    save_articles(pl.concat([df, pl.DataFrame(rows)], how="vertical_relaxed"))
    return len(rows)


def unique_articles(limit: int | None = None) -> list[str]:
    lf = scan_pageviews()
    if lf is None:
        return []
    q = lf.select("article").unique()
    if limit:
        q = q.head(limit)
    return q.collect()["article"].to_list()


def top_articles_by_views(limit: int = 500) -> list[str]:
    lf = scan_pageviews()
    if lf is None:
        return []
    return (
        lf.group_by("article")
        .agg(pl.col("views").sum().alias("views"))
        .sort("views", descending=True)
        .head(limit)
        .collect()["article"]
        .to_list()
)


def articles_for_day(day: date) -> list[str]:
    lf = scan_pageviews()
    if lf is None:
        return []
    return (
        lf.filter(pl.col("date") == day)
        .select("article")
        .collect()["article"]
        .to_list()
    )
