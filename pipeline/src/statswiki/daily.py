from datetime import date, timedelta
import os
import sys

from statswiki.export import export_recent
from statswiki.fetch import ingest_day_with_retry
from statswiki.store import has_day
from statswiki.wikidata import enrich_daily


def _set_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main():
    yesterday = date.today() - timedelta(days=1)
    print(f"=== Daily update {yesterday} (UTC) ===")

    status = ingest_day_with_retry(yesterday)
    print(f"Pageviews: {status}")

    if status == "failed" and not has_day(yesterday):
        print("Yesterday not available from Wikimedia yet — skipping enrich/export.")
        print("The next scheduled run will retry (08:00, 14:00 and 20:00 UTC).")
        _set_output("ready", "false")
        sys.exit(0)

    n = enrich_daily()
    print(f"Wikidata: {n} articles updated")

    export_recent()
    print("JSON exported")
    _set_output("ready", "true")


if __name__ == "__main__":
    main()
