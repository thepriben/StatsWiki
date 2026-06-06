"""Export compact QID catalog for Wikirace autocomplete."""

import json
from pathlib import Path

from statswiki.config import ROOT

Q_DIR = ROOT / "web" / "public" / "data" / "q"
OUT = ROOT / "web" / "public" / "wikirace" / "catalog.json"


def export_wikirace_catalog() -> int:
    items = []
    for path in sorted(Q_DIR.glob("Q*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        qid = data.get("qid")
        label = data.get("label")
        if qid and label and str(qid).startswith("Q"):
            items.append({
                "qid": qid,
                "label": label,
                "article": data.get("title", ""),
            })

    items.sort(key=lambda x: x["label"].lower())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"count": len(items), "items": items}, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    )
    return len(items)


def main() -> None:
    n = export_wikirace_catalog()
    print(f"Wikirace catalog: {n} items → {OUT}")


if __name__ == "__main__":
    main()
