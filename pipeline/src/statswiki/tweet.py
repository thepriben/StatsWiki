"""Post yesterday's top 5 to @statswiki on X."""

import json
import sys
from datetime import date, timedelta

from statswiki.config import TWEET_LOG, TOP_N, X_CREDENTIALS, X_ENABLED
from statswiki.post_text import build_daily_post, load_lines


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
    body, link = build_daily_post(day, lines, n=n, limit=280)
    return f"{body}\n{link}"[:280]


def post_tweet(text: str) -> None:
    import tweepy

    client = tweepy.Client(
        consumer_key=X_CREDENTIALS["api_key"],
        consumer_secret=X_CREDENTIALS["api_secret"],
        access_token=X_CREDENTIALS["access_token"],
        access_token_secret=X_CREDENTIALS["access_token_secret"],
    )
    response = client.create_tweet(text=text)
    print(f"Tweet posted: {response.data['id']}")


def main():
    import argparse

    p = argparse.ArgumentParser(description="Tweet yesterday's top N articles")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday)")
    p.add_argument("--dry-run", action="store_true", help="Print tweet without posting")
    p.add_argument("--force", action="store_true", help="Post even if already tweeted")
    p.add_argument("--strict", action="store_true", help="Exit 1 if tweet was not posted")
    args = p.parse_args()

    day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    lines = load_lines(day)
    if not lines:
        print(f"No data for {day}")
        sys.exit(1 if args.strict else 0)

    text = build_tweet(day, lines, n=min(args.top, TOP_N))
    if args.dry_run:
        print(text)
        return

    if not args.force and _already_tweeted(day):
        print(f"Already tweeted {day}")
        sys.exit(0 if not args.strict else 1)

    if not X_ENABLED:
        print("X credentials not configured")
        print(text)
        sys.exit(1 if args.strict else 0)

    post_tweet(text)
    _mark_tweeted(day)
    print(text)


if __name__ == "__main__":
    main()
