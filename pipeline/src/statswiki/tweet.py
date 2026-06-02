"""Post yesterday's top 5 to @StatsWiki on X/Twitter."""

import json
import os
from datetime import date, timedelta
from pathlib import Path

from statswiki.config import JSON_OUT, MONTHS, SITE_URL, TOP_N, TWEET_LOG, TWITTER_ENABLED


def _compact_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:,}"


def _day_json(day: date) -> Path:
    return JSON_OUT / "day" / f"{day.year}" / f"{day.month:02d}" / f"{day.day:02d}.json"


def _day_label(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1][:3]} {day.year}"


def _already_tweeted(day: date) -> bool:
    if not TWEET_LOG.exists():
        return False
    try:
        return json.loads(TWEET_LOG.read_text()).get("last") == day.isoformat()
    except (json.JSONDecodeError, OSError):
        return False


def _mark_tweeted(day: date) -> None:
    TWEET_LOG.parent.mkdir(parents=True, exist_ok=True)
    TWEET_LOG.write_text(json.dumps({"last": day.isoformat()}, indent=2) + "\n")


def build_tweet(day: date, lines: list[dict], n: int = 5) -> str:
    header = f"Top {n} English Wikipedia ({_day_label(day)}):\n"
    rows = []
    for line in lines[:n]:
        label = (line.get("label") or line["title"].replace("_", " "))[:40]
        rows.append(f"{line['rank']}. {label} — {_compact_views(line['views'])}")
    link = f"{SITE_URL}/{day.year}/{day.month:02d}/{day.day:02d}"
    text = header + "\n".join(rows) + f"\n{link}"
    if len(text) > 280:
        text = header + "\n".join(rows[:3]) + f"\n…\n{link}"
    return text[:280]


def post_tweet(text: str) -> None:
    import tweepy

    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    response = client.create_tweet(text=text)
    print(f"Tweet posted: {response.data['id']}")


def tweet_yesterday(n: int = 5) -> bool:
    day = date.today() - timedelta(days=1)

    if _already_tweeted(day):
        print(f"Already tweeted {day} — skip")
        return False

    if not TWITTER_ENABLED:
        print("Twitter credentials not configured — skip tweet")
        return False

    path = _day_json(day)
    if not path.exists():
        print(f"No JSON for {day} — skip tweet")
        return False

    payload = json.loads(path.read_text())
    lines = payload.get("lines") or []
    if not lines:
        print(f"Empty ranking for {day} — skip tweet")
        return False

    text = build_tweet(day, lines, n=min(n, TOP_N))
    print(text)
    print("---")
    post_tweet(text)
    _mark_tweeted(day)
    return True


def main():
    import argparse
    import sys

    p = argparse.ArgumentParser(description="Tweet yesterday's top N articles")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday)")
    p.add_argument("--dry-run", action="store_true", help="Print tweet without posting")
    p.add_argument("--force", action="store_true", help="Post even if already tweeted")
    p.add_argument("--strict", action="store_true", help="Exit 1 if tweet was not posted")
    args = p.parse_args()

    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    path = _day_json(day)
    if not path.exists():
        print(f"No data for {day}")
        sys.exit(1 if args.strict else 0)

    payload = json.loads(path.read_text())
    lines = payload.get("lines") or []
    if not lines:
        print(f"Empty ranking for {day}")
        sys.exit(1 if args.strict else 0)

    text = build_tweet(day, lines, n=args.top)
    if args.dry_run:
        print(text)
        return

    if not args.force and _already_tweeted(day):
        print(f"Already tweeted {day}")
        sys.exit(0 if not args.strict else 1)

    if not TWITTER_ENABLED:
        print("Twitter credentials not configured")
        print(text)
        sys.exit(1 if args.strict else 0)

    post_tweet(text)
    _mark_tweeted(day)
    print(text)


if __name__ == "__main__":
    main()
