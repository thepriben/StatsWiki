"""Post week, month, and year summaries to X and Bluesky when period data is complete."""

import sys
from datetime import date, timedelta

from statswiki.bsky import post_to_bsky
from statswiki.config import BSKY_ENABLED, BSKY_LOG, TOP_N, TWEET_LOG, X_ENABLED
from statswiki.post_log import already_posted, mark_posted
from statswiki.post_text import build_period_post, load_period_lines, period_keys
from statswiki.tweet import post_tweet


def _post_period(kind: str, key: str, top: int, dry_run: bool, force: bool) -> bool:
    lines = load_period_lines(kind, key)
    if not lines:
        print(f"No {kind} data for {key}")
        return False

    body, link = build_period_post(kind, key, lines, n=min(top, TOP_N), limit=280)
    text = f"{body}\n{link}"
    bsky_body, bsky_link = build_period_post(kind, key, lines, n=min(top, TOP_N), limit=300)
    bsky_text = f"{bsky_body}\n{bsky_link}"

    if dry_run:
        print(f"=== {kind} {key} (X) ===")
        print(text[:280])
        print(f"=== {kind} {key} (Bluesky) ===")
        print(bsky_text)
        return True

    posted = False

    if not force and already_posted(TWEET_LOG, kind, key):
        print(f"Already tweeted {kind} {key}")
    elif not X_ENABLED:
        print(f"X credentials not configured ({kind} {key})")
        print(text[:280])
    else:
        post_tweet(text[:280])
        mark_posted(TWEET_LOG, kind, key)
        print(f"Tweeted {kind} {key}")
        posted = True

    if not force and already_posted(BSKY_LOG, kind, key):
        print(f"Already posted {kind} {key} to Bluesky")
    elif not BSKY_ENABLED:
        print(f"Bluesky credentials not configured ({kind} {key})")
        print(bsky_text)
    else:
        post_to_bsky(bsky_body, bsky_link)
        mark_posted(BSKY_LOG, kind, key)
        print(f"Bluesky {kind} {key}")
        posted = True

    return posted


def main():
    import argparse

    p = argparse.ArgumentParser(description="Post week/month/year top N when period ends")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--date", help="Last day of period (YYYY-MM-DD). Default: yesterday")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--strict", action="store_true", help="Exit 1 if a due period was not posted")
    args = p.parse_args()

    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    due = period_keys(day)
    if not due:
        print(f"No period posts due for {day}")
        return

    ok = True
    for kind, key in due:
        if not _post_period(kind, key, args.top, args.dry_run, args.force):
            ok = False

    if args.strict and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
