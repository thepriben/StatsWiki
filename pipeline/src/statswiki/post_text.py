"""Shared text for daily top-N social posts."""

import json
from datetime import date
from pathlib import Path

from statswiki.config import JSON_OUT, MONTHS, SITE_URL, TOP_N


def compact_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:,}"


def day_json(day: date) -> Path:
    return JSON_OUT / "day" / f"{day.year}" / f"{day.month:02d}" / f"{day.day:02d}.json"


def day_label(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1][:3]} {day.year}"


def load_lines(day: date) -> list[dict]:
    path = day_json(day)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload.get("lines") or []


def day_url(day: date) -> str:
    return f"{SITE_URL}/{day.year}/{day.month:02d}/{day.day:02d}"


def build_daily_post(day: date, lines: list[dict], n: int = 5, limit: int = 300) -> tuple[str, str]:
    """Return (body text, link URL). Body ends before the link line."""
    header = f"Top {n} English Wikipedia ({day_label(day)}):\n"
    rows = []
    for line in lines[:n]:
        label = (line.get("label") or line["title"].replace("_", " "))[:40]
        rows.append(f"{line['rank']}. {label} — {compact_views(line['views'])}")
    link = day_url(day)
    text = header + "\n".join(rows)
    if len(text) + len(link) + 1 > limit:
        text = header + "\n".join(rows[:3]) + "\n…"
    return text, link
