"""Post yesterday's top 5 to StatsWiki on Bluesky."""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import requests

from statswiki.config import BSKY_LOG, BSKY_ENABLED, TOP_N
from statswiki.post_text import build_daily_post, load_lines

BSKY_PDS = "https://bsky.social"


def _already_posted(day: date) -> bool:
    if not BSKY_LOG.exists():
        return False
    try:
        return json.loads(BSKY_LOG.read_text()).get("last") == day.isoformat()
    except (json.JSONDecodeError, OSError):
        return False


def _mark_posted(day: date) -> None:
    BSKY_LOG.parent.mkdir(parents=True, exist_ok=True)
    BSKY_LOG.write_text(json.dumps({"last": day.isoformat()}, indent=2) + "\n")


def _link_facet(text: str, url: str) -> dict:
    start = text.index(url)
    prefix = text[:start].encode("utf-8")
    uri = url.encode("utf-8")
    return {
        "index": {"byteStart": len(prefix), "byteEnd": len(prefix) + len(uri)},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
    }


def _normalize_handle(raw: str) -> str:
    handle = raw.strip().lstrip("@")
    if "." not in handle:
        handle = f"{handle}.bsky.social"
    return handle


def _session() -> tuple[str, str]:
    handle = _normalize_handle(os.environ["BSKY_HANDLE"])
    password = os.environ["BSKY_APP_PASSWORD"].strip()
    r = requests.post(
        f"{BSKY_PDS}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
        timeout=30,
    )
    if not r.ok:
        detail = r.text[:300]
        raise RuntimeError(f"Bluesky login failed for {handle} ({r.status_code}): {detail}")
    data = r.json()
    return data["accessJwt"], data["did"]


def post_to_bsky(body: str, link: str) -> str:
    text = f"{body}\n{link}"
    token, did = _session()
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "facets": [_link_facet(text, link)],
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    r = requests.post(
        f"{BSKY_PDS}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {token}"},
        json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
        timeout=30,
    )
    r.raise_for_status()
    uri = r.json()["uri"]
    print(f"Bluesky post created: {uri}")
    return uri


def main():
    import argparse

    p = argparse.ArgumentParser(description="Post yesterday's top N to Bluesky")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday)")
    p.add_argument("--dry-run", action="store_true", help="Print post without publishing")
    p.add_argument("--force", action="store_true", help="Post even if already posted")
    p.add_argument("--strict", action="store_true", help="Exit 1 if post was not published")
    args = p.parse_args()

    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    lines = load_lines(day)
    if not lines:
        print(f"No data for {day}")
        sys.exit(1 if args.strict else 0)

    body, link = build_daily_post(day, lines, n=min(args.top, TOP_N))
    text = f"{body}\n{link}"
    if args.dry_run:
        print(text)
        return

    if not args.force and _already_posted(day):
        print(f"Already posted {day} to Bluesky")
        sys.exit(0 if not args.strict else 1)

    if not BSKY_ENABLED:
        print("Bluesky credentials not configured")
        print(text)
        sys.exit(1 if args.strict else 0)

    post_to_bsky(body, link)
    _mark_posted(day)
    print(text)


if __name__ == "__main__":
    main()
