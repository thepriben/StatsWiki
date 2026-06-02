from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PAGEVIEWS = DATA / "pageviews"
ARTICLES = DATA / "articles.parquet"
MANIFEST = DATA / "manifest.json"
JSON_OUT = ROOT / "web" / "public" / "data"

START = date(2015, 7, 1)
TOP_N = 50
LANG = "en"
USER_AGENT = "StatsWiki/3.0 (https://github.com/thepriben/StatsWiki; github-issues)"
DELAY = 0.35

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
