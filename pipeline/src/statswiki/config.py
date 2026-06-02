from datetime import date
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PAGEVIEWS = DATA / "pageviews"
ARTICLES = DATA / "articles.parquet"
MANIFEST = DATA / "manifest.json"
TWEET_LOG = DATA / "tweet_log.json"
JSON_OUT = ROOT / "web" / "public" / "data"

START = date(2015, 7, 1)
TOP_N = 50
LANG = "en"
SITE_URL = "https://thepriben.github.io/StatsWiki"
USER_AGENT = "StatsWiki/3.0 (https://github.com/thepriben/StatsWiki; github-issues)"
DELAY = 0.35

# Daily fetch: Wikimedia often needs 24h+; cron at 08:00 and 14:00 UTC
FETCH_RETRIES = 3
FETCH_RETRY_WAIT = 90  # seconds between attempts

TWITTER_ENABLED = all(
    os.environ.get(k)
    for k in (
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    )
)

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
