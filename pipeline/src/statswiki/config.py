from datetime import date
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PAGEVIEWS = DATA / "pageviews"
ARTICLES = DATA / "articles.parquet"
MANIFEST = DATA / "manifest.json"
TWEET_LOG = DATA / "tweet_log.json"
BSKY_LOG = DATA / "bsky_log.json"
JSON_OUT = ROOT / "web" / "public" / "data"

START = date(2015, 7, 1)
TOP_N = 50
LANG = "en"
SITE_URL = "https://statswiki.info"
USER_AGENT = "StatsWiki/3.0 (https://statswiki.info; https://github.com/thepriben/StatsWiki)"
DELAY = 0.35

# Daily fetch: Wikimedia often needs 24h+; cron at 08:00 and 14:00 UTC
FETCH_RETRIES = 3
FETCH_RETRY_WAIT = 90  # seconds between attempts

def _env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


X_CREDENTIALS = {
    "api_key": _env("X_API_KEY", "TWITTER_API_KEY"),
    "api_secret": _env("X_API_SECRET", "TWITTER_API_SECRET"),
    "access_token": _env("X_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN"),
    "access_token_secret": _env("X_ACCESS_TOKEN_SECRET", "TWITTER_ACCESS_TOKEN_SECRET"),
}
X_ENABLED = all(X_CREDENTIALS.values())
TWITTER_ENABLED = X_ENABLED

BSKY_ENABLED = all(os.environ.get(k) for k in ("BSKY_HANDLE", "BSKY_APP_PASSWORD"))

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
