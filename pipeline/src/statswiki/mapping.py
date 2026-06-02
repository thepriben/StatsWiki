"""Title normalization and QID-based view merging for export."""

from statswiki.filters import REDIRECTS

REDIRECTS_BY_TITLE = {k.replace(" ", "_"): v for k, v in REDIRECTS.items()}


def normalize_title(title: str) -> str:
    return title.replace(" ", "_").strip()


def is_real_qid(qid: str) -> bool:
    return bool(qid) and qid.startswith("Q") and qid[1:].isdigit()


def shadow_qid(title: str) -> str:
    return f"Q_en_{normalize_title(title)}"


def manual_qid(title: str) -> str | None:
    return REDIRECTS_BY_TITLE.get(normalize_title(title))


def resolve_qid(article: str, meta: dict) -> str:
    title = normalize_title(article)
    override = manual_qid(title)
    if override:
        return override
    row = meta.get(title) or meta.get(article) or {}
    qid = row.get("qid")
    if qid and is_real_qid(qid):
        return qid
    if qid and qid.startswith("Q_en_"):
        return qid
    return shadow_qid(title)


def meta_lookup(articles) -> dict[str, dict]:
    """Index catalog rows by article title and by QID."""
    if articles.is_empty():
        return {}
    lookup = {}
    for row in articles.iter_rows(named=True):
        title = normalize_title(row["article"])
        lookup[title] = row
        qid = row.get("qid")
        if qid and is_real_qid(qid) and qid not in lookup:
            lookup[qid] = row
    return lookup


def pick_canonical_title(titles: list[str], meta: dict) -> str:
    """Prefer Wikidata label match, then highest-traffic title string."""
    for title in titles:
        row = meta.get(normalize_title(title), {})
        if row.get("label"):
            return normalize_title(title)
    return normalize_title(titles[0])


def merge_views_by_qid(df, meta: dict):
    """Sum views for all pageview titles that share the same Wikidata item."""
    import polars as pl

    groups: dict[str, dict] = {}
    shadows: dict[str, int] = {}

    for row in df.iter_rows(named=True):
        title = normalize_title(row["article"])
        views = int(row["views"])
        qid = resolve_qid(title, meta)

        if is_real_qid(qid):
            bucket = groups.setdefault(qid, {"views": 0, "titles": []})
            bucket["views"] += views
            bucket["titles"].append(title)
        else:
            shadows[title] = shadows.get(title, 0) + views

    rows = []
    for qid, bucket in groups.items():
        canon = pick_canonical_title(bucket["titles"], meta)
        row = meta.get(canon) or meta.get(qid, {})
        article = row.get("article") or canon
        rows.append({"article": normalize_title(article), "views": bucket["views"], "qid": qid})

    for title, views in shadows.items():
        rows.append({"article": title, "views": views, "qid": shadow_qid(title)})

    if not rows:
        return pl.DataFrame(schema={"article": pl.String, "views": pl.Int64})
    return pl.DataFrame(rows).sort("views", descending=True)


def line_from_row(row: dict, meta: dict, rank: int) -> dict:
    title = normalize_title(row["article"])
    qid = row.get("qid") or resolve_qid(title, meta)
    m = meta.get(title) or (meta.get(qid, {}) if is_real_qid(qid) else {})
    return {
        "rank": rank,
        "title": title,
        "label": m.get("label") or title.replace("_", " "),
        "description": m.get("description", ""),
        "views": row["views"],
        "qid": qid,
        "image": m.get("image", ""),
    }
