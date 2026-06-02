from datetime import date, timedelta

from statswiki.export import export_recent
from statswiki.fetch import ingest_day
from statswiki.wikidata import enrich_daily


def main():
    yesterday = date.today() - timedelta(days=1)
    print(f"=== Daily update {yesterday} ===")

    if ingest_day(yesterday):
        print("Pageviews ingested")
    else:
        print("Pageviews already present")

    n = enrich_daily()
    print(f"Wikidata: {n} articles updated")

    export_recent()
    print("JSON exported")


if __name__ == "__main__":
    main()
