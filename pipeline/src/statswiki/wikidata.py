import time
from datetime import date
from urllib.parse import quote

import polars as pl
import requests

from statswiki.config import DELAY, LANG, USER_AGENT
from statswiki.filters import REDIRECTS
from statswiki.store import load_articles, upsert_articles

BATCH = 50
API = f"https://{LANG}.wikipedia.org/w/api.php"
WDAPI = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": USER_AGENT}

REDIRECTS_BY_TITLE = {k.replace(" ", "_"): v for k, v in REDIRECTS.items()}


def is_real_qid(qid: str) -> bool:
    return bool(qid) and qid.startswith("Q") and qid[1:].isdigit()


def shadow_qid(title: str) -> str:
    return f"Q_en_{title}"


def commons_thumb(filename: str, width: int = 64) -> str:
    if not filename:
        return ""
    name = filename.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(name)}?width={width}"


def _pause():
    time.sleep(DELAY)


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def fetch_qids(titles: list[str]) -> dict[str, str]:
    """Map Wikipedia title → QID via batched pageprops."""
    result = {}
    for batch in _chunks(titles, BATCH):
        r = requests.get(API, params={
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "titles": "|".join(batch),
            "redirects": 1,
        }, headers=HEADERS, timeout=60)
        _pause()
        if r.status_code != 200:
            for t in batch:
                result[t] = REDIRECTS_BY_TITLE.get(t) or shadow_qid(t)
            continue
        for page in r.json().get("query", {}).get("pages", {}).values():
            if "missing" in page:
                continue
            title = page.get("title", "").replace(" ", "_")
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                result[title] = qid
        for t in batch:
            if t not in result:
                result[t] = REDIRECTS_BY_TITLE.get(t) or shadow_qid(t)
    return result


def fetch_entities(qids: list[str]) -> dict[str, dict]:
    """Batch-fetch Wikidata labels, descriptions, P18 images."""
    real = [q for q in qids if is_real_qid(q)]
    result = {}
    for batch in _chunks(real, BATCH):
        r = requests.get(WDAPI, params={
            "action": "wbgetentities",
            "format": "json",
            "ids": "|".join(batch),
            "languages": "en",
            "props": "labels|descriptions|claims",
        }, headers=HEADERS, timeout=60)
        _pause()
        if r.status_code != 200:
            continue
        for qid, entity in r.json().get("entities", {}).items():
            if entity.get("missing"):
                continue
            label = entity.get("labels", {}).get("en", {}).get("value", "")
            desc = entity.get("descriptions", {}).get("en", {}).get("value", "")
            image = ""
            for claim in entity.get("claims", {}).get("P18", []):
                try:
                    if claim["mainsnak"]["snaktype"] == "value":
                        image = claim["mainsnak"]["datavalue"]["value"]
                        break
                except (KeyError, TypeError):
                    pass
            result[qid] = {
                "label": label,
                "description": desc,
                "image": commons_thumb(image),
            }
    return result


def enrich_titles(titles: list[str]) -> list[dict]:
    if not titles:
        return []
    qids = fetch_qids(titles)
    entities = fetch_entities(list(set(qids.values())))
    today = date.today()
    rows = []
    for title in titles:
        qid = qids.get(title, shadow_qid(title))
        meta = entities.get(qid, {}) if is_real_qid(qid) else {}
        rows.append({
            "article": title,
            "qid": qid,
            "label": meta.get("label") or title.replace("_", " "),
            "description": meta.get("description", ""),
            "image": meta.get("image", ""),
            "updated_at": today,
        })
    return rows


def _candidates_new() -> list[str]:
    df = load_articles()
    known = set(df["article"].to_list()) if df.height else set()
    from statswiki.store import unique_articles
    return [t for t in unique_articles() if t not in known]


def _candidates_shadows(limit: int) -> list[str]:
    df = load_articles()
    if df.is_empty():
        return []
    shadows = df.filter(pl.col("qid").str.starts_with("Q_en_"))["article"].to_list()
    return shadows[:limit]


def _candidates_top(limit: int) -> list[str]:
    from statswiki.store import top_articles_by_views
    return top_articles_by_views(limit)


def enrich_batch(titles: list[str]) -> int:
    total = 0
    for batch in _chunks(titles, BATCH):
        rows = enrich_titles(batch)
        total += upsert_articles(rows)
        print(f"  enriched {total}/{len(titles)}")
    return total


def enrich_new(limit: int = 500) -> int:
    titles = _candidates_new()[:limit]
    if not titles:
        return 0
    print(f"Enriching {len(titles)} new articles…")
    return enrich_batch(titles)


def enrich_refresh_shadows(limit: int = 100) -> int:
    titles = _candidates_shadows(limit)
    if not titles:
        return 0
    print(f"Retrying {len(titles)} shadow QIDs…")
    return enrich_batch(titles)


def enrich_top(limit: int = 500) -> int:
    titles = _candidates_top(limit)
    if not titles:
        return 0
    print(f"Enriching top {len(titles)} articles by views…")
    return enrich_batch(titles)


def enrich_daily() -> int:
    from datetime import timedelta
    from statswiki.store import articles_for_day
    yesterday = date.today() - timedelta(days=1)
    day_titles = articles_for_day(yesterday)
    new = set(_candidates_new())
    priority = [t for t in day_titles if t in new]
    rest = [t for t in day_titles if t not in new][:200]
    titles = list(dict.fromkeys(priority + rest))[:300]
    n = enrich_batch(titles) if titles else 0
    n += enrich_refresh_shadows(50)
    return n


def main():
    import argparse
    p = argparse.ArgumentParser(description="Wikidata enrichment (batched)")
    p.add_argument("--new", action="store_true", help="New articles only")
    p.add_argument("--top", type=int, default=0, help="Top N by total views")
    p.add_argument("--refresh-shadows", type=int, default=0, help="Retry shadow QIDs")
    p.add_argument("--titles", nargs="*", help="Specific titles")
    args = p.parse_args()

    if args.titles:
        n = enrich_batch(args.titles)
    elif args.top:
        n = enrich_top(args.top)
    elif args.refresh_shadows:
        n = enrich_refresh_shadows(args.refresh_shadows)
    elif args.new:
        n = enrich_new()
    else:
        n = enrich_daily()
    print(f"Done: {n} articles updated")
