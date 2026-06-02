import time
from datetime import date
from urllib.parse import quote

import polars as pl
import requests

from statswiki.config import DELAY, LANG, USER_AGENT
from statswiki.mapping import (
    is_real_qid,
    manual_qid,
    normalize_title,
    shadow_qid,
)
from statswiki.store import load_articles, top_articles_by_views, upsert_articles

BATCH = 50
API = f"https://{LANG}.wikipedia.org/w/api.php"
WDAPI = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": USER_AGENT}


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


def _get_json(url: str, params: dict) -> dict | None:
    r = requests.get(url, params=params, headers=HEADERS, timeout=60)
    _pause()
    if r.status_code != 200:
        return None
    return r.json()


def _follow_redirects(title: str, redirect_map: dict[str, str]) -> str:
    seen = set()
    current = title
    while current in redirect_map and current not in seen:
        seen.add(current)
        current = redirect_map[current]
    return current


def fetch_qids(titles: list[str]) -> dict[str, dict]:
    """
    Map each pageview title → {qid, resolved_title}.
    Follows Wikipedia redirects and applies manual overrides.
    """
    result: dict[str, dict] = {}
    pending = [normalize_title(t) for t in titles]

    for batch in _chunks(pending, BATCH):
        data = _get_json(API, {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "titles": "|".join(batch),
            "redirects": 1,
        })
        if not data:
            for t in batch:
                override = manual_qid(t)
                result[t] = {
                    "qid": override or shadow_qid(t),
                    "resolved_title": t,
                }
            continue

        query = data.get("query", {})
        redirect_map = {
            normalize_title(r["from"]): normalize_title(r["to"])
            for r in query.get("redirects", [])
        }

        page_qid: dict[str, str] = {}
        for page in query.get("pages", {}).values():
            if "missing" in page:
                continue
            resolved = normalize_title(page.get("title", ""))
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                page_qid[resolved] = qid

        for t in batch:
            override = manual_qid(t)
            if override:
                result[t] = {"qid": override, "resolved_title": t}
                continue

            resolved = _follow_redirects(t, redirect_map)
            qid = page_qid.get(resolved)
            if qid:
                result[t] = {"qid": qid, "resolved_title": resolved}
            else:
                result[t] = {"qid": shadow_qid(t), "resolved_title": resolved}

    return result


def search_qid(title: str) -> str | None:
    """Fallback: Wikidata search, prefer exact enwiki sitelink match."""
    readable = title.replace("_", " ")
    search_data = _get_json(WDAPI, {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": readable,
        "limit": 5,
    })
    if not search_data:
        return None

    normalized = normalize_title(title)
    hits = search_data.get("search", [])
    for hit in hits:
        qid = hit.get("id")
        if not is_real_qid(qid):
            continue
        label = hit.get("label", "").replace(" ", "_")
        if label.lower() == normalized.lower():
            return qid

    qids = [h["id"] for h in hits if is_real_qid(h.get("id", ""))]
    if not qids:
        return None

    entity_data = _get_json(WDAPI, {
        "action": "wbgetentities",
        "format": "json",
        "props": "sitelinks",
        "sites": f"{LANG}wiki",
        "ids": "|".join(qids),
    })
    if entity_data:
        for entity in entity_data.get("entities", {}).values():
            if entity.get("missing"):
                continue
            sitelink = entity.get("sitelinks", {}).get(f"{LANG}wiki", {}).get("title", "")
            if normalize_title(sitelink) == normalized:
                return entity.get("id")

    return qids[0]


def opensearch_title(title: str) -> str | None:
    """Fallback: Wikipedia opensearch for missing pages."""
    data = _get_json(API, {
        "action": "opensearch",
        "format": "json",
        "search": title.replace("_", " "),
        "limit": 1,
        "namespace": 0,
    })
    if not data or len(data) < 2 or not data[1]:
        return None
    found = normalize_title(data[1][0])
    if found.lower() == normalize_title(title).lower():
        return found
    return None


def resolve_missing_qids(mappings: dict[str, dict]) -> dict[str, dict]:
    """Try Wikidata search + opensearch for shadow QIDs."""
    for title, info in mappings.items():
        if is_real_qid(info["qid"]):
            continue

        qid = search_qid(title)
        if qid:
            info["qid"] = qid
            continue

        alt = opensearch_title(title)
        if alt and alt != title:
            alt_map = fetch_qids([alt])
            alt_info = alt_map.get(alt)
            if alt_info and is_real_qid(alt_info["qid"]):
                info["qid"] = alt_info["qid"]
                info["resolved_title"] = alt_info["resolved_title"]

    return mappings


def _pick_label(entity: dict, fallback: str) -> str:
    labels = entity.get("labels", {})
    if "en" in labels:
        return labels["en"]["value"]
    sitelink = entity.get("sitelinks", {}).get(f"{LANG}wiki", {}).get("title", "")
    if sitelink:
        return sitelink.replace("_", " ")
    if labels:
        return next(iter(labels.values()))["value"]
    return fallback.replace("_", " ")


def _pick_description(entity: dict) -> str:
    descs = entity.get("descriptions", {})
    if "en" in descs:
        return descs["en"]["value"]
    return ""


def _pick_image(entity: dict) -> str:
    for prop in ("P18", "P154"):
        for claim in entity.get("claims", {}).get(prop, []):
            try:
                if claim["mainsnak"]["snaktype"] == "value":
                    filename = claim["mainsnak"]["datavalue"]["value"]
                    if filename:
                        return commons_thumb(filename)
            except (KeyError, TypeError):
                pass
    return ""


def fetch_entities(qids: list[str]) -> dict[str, dict]:
    """Batch-fetch Wikidata labels, descriptions, images."""
    real = list(dict.fromkeys(q for q in qids if is_real_qid(q)))
    result = {}
    for batch in _chunks(real, BATCH):
        data = _get_json(WDAPI, {
            "action": "wbgetentities",
            "format": "json",
            "ids": "|".join(batch),
            "languages": "en",
            "props": "labels|descriptions|claims|sitelinks",
        })
        if not data:
            continue
        for qid, entity in data.get("entities", {}).items():
            if entity.get("missing"):
                continue
            result[qid] = {
                "label": _pick_label(entity, qid),
                "description": _pick_description(entity),
                "image": _pick_image(entity),
            }
    return result


def enrich_titles(titles: list[str], retry_shadows: bool = True) -> list[dict]:
    if not titles:
        return []

    normalized = [normalize_title(t) for t in titles]
    mappings = fetch_qids(normalized)
    if retry_shadows:
        mappings = resolve_missing_qids(mappings)

    entities = fetch_entities([m["qid"] for m in mappings.values()])
    today = date.today()
    rows = []

    for title in normalized:
        info = mappings.get(title, {"qid": shadow_qid(title), "resolved_title": title})
        qid = info["qid"]
        meta = entities.get(qid, {}) if is_real_qid(qid) else {}
        rows.append({
            "article": title,
            "qid": qid,
            "resolved_title": info.get("resolved_title", title),
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
    shadow_set = set(
        df.filter(pl.col("qid").str.starts_with("Q_en_"))["article"].to_list()
    )
    if not shadow_set:
        return []
    priority = [t for t in top_articles_by_views(5000) if t in shadow_set]
    rest = [t for t in shadow_set if t not in set(priority)]
    return (priority + rest)[:limit]


def _candidates_top(limit: int) -> list[str]:
    return top_articles_by_views(limit)


def enrich_batch(titles: list[str], retry_shadows: bool = True) -> int:
    total = 0
    for batch in _chunks([normalize_title(t) for t in titles], BATCH):
        rows = enrich_titles(batch, retry_shadows=retry_shadows)
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
    return enrich_batch(titles, retry_shadows=True)


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
    day_titles = [normalize_title(t) for t in articles_for_day(yesterday)]
    new = set(_candidates_new())
    priority = [t for t in day_titles if t in new]
    rest = [t for t in day_titles if t not in new][:200]
    titles = list(dict.fromkeys(priority + rest))[:300]
    n = enrich_batch(titles) if titles else 0
    n += enrich_refresh_shadows(100)
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
