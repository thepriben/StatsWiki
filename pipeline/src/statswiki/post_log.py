"""Track published social posts (daily, week, month, year)."""

import json
from pathlib import Path


def load_log(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    if "last" in data and "daily" not in data:
        data["daily"] = data["last"]
    return data


def already_posted(path: Path, kind: str, key: str) -> bool:
    return load_log(path).get(kind) == key


def mark_posted(path: Path, kind: str, key: str) -> None:
    data = load_log(path)
    data[kind] = key
    if kind == "daily":
        data["last"] = key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
