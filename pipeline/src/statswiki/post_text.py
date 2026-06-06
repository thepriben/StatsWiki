"""Shared text for daily and period top-N social posts."""

import calendar
import json
from datetime import date, timedelta
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


def short_day_label(day: date) -> str:
    return f"{day.strftime('%a')} {day.day} {MONTHS[day.month - 1][:3]}"


def week_range_label(start: date, end: date) -> str:
    if start.year == end.year:
        return f"{short_day_label(start)} – {short_day_label(end)} {end.year}"
    return f"{short_day_label(start)} {start.year} – {short_day_label(end)} {end.year}"


def load_lines(day: date) -> list[dict]:
    path = day_json(day)
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload.get("lines") or []


def day_url(day: date) -> str:
    return f"{SITE_URL}/{day.year}/{day.month:02d}/{day.day:02d}"


def _period_json_path(kind: str, key: str) -> Path | None:
    if kind == "week":
        return JSON_OUT / "week" / key[:4] / f"{key}.json"
    if kind == "month":
        year, month = key.split("-")
        return JSON_OUT / "month" / year / f"{month}.json"
    if kind == "year":
        return JSON_OUT / "year" / f"{key}.json"
    return None


def load_period_lines(kind: str, key: str) -> list[dict]:
    path = _period_json_path(kind, key)
    if not path or not path.exists():
        return []
    payload = json.loads(path.read_text())
    return payload.get("lines") or []


def period_url(kind: str, key: str) -> str:
    if kind == "week":
        end = date.fromisoformat(key)
        return f"{SITE_URL}/{end.year}/{end.month:02d}/{end.day:02d}"
    if kind == "month":
        year, month = key.split("-")
        return f"{SITE_URL}/{year}/{month}"
    if kind == "year":
        return f"{SITE_URL}/{key}"
    raise ValueError(f"Unknown period kind: {kind}")


def period_header(kind: str, key: str, n: int = 5) -> str:
    if kind == "week":
        end = date.fromisoformat(key)
        start = end - timedelta(days=6)
        return f"Top {n} English Wikipedia week ({week_range_label(start, end)}):"
    if kind == "month":
        year, month = key.split("-")
        return f"Top {n} English Wikipedia ({MONTHS[int(month) - 1]} {year}):"
    if kind == "year":
        return f"Top {n} English Wikipedia ({key}):"
    raise ValueError(f"Unknown period kind: {kind}")


def build_period_post(kind: str, key: str, lines: list[dict], n: int = 5, limit: int = 300) -> tuple[str, str]:
    """Return (body text, link URL). Body ends before the link line."""
    header = period_header(kind, key, n) + "\n"
    rows = []
    for line in lines[:n]:
        label = (line.get("label") or line["title"].replace("_", " "))[:40]
        rows.append(f"{line['rank']}. {label} — {compact_views(line['views'])}")
    link = period_url(kind, key)
    text = header + "\n".join(rows)
    if len(text) + len(link) + 1 > limit:
        text = header + "\n".join(rows[:3]) + "\n…"
    return text, link


def build_daily_post(day: date, lines: list[dict], n: int = 5, limit: int = 300) -> tuple[str, str]:
    """Return (body text, link URL). Body ends before the link line."""
    header = f"Top {n} English Wikipedia day ({day_label(day)}):\n"
    rows = []
    for line in lines[:n]:
        label = (line.get("label") or line["title"].replace("_", " "))[:40]
        rows.append(f"{line['rank']}. {label} — {compact_views(line['views'])}")
    link = day_url(day)
    text = header + "\n".join(rows)
    if len(text) + len(link) + 1 > limit:
        text = header + "\n".join(rows[:3]) + "\n…"
    return text, link


def period_keys(day: date) -> list[tuple[str, str]]:
    """Return (kind, log_key) pairs to post after `day` data is available."""
    out: list[tuple[str, str]] = []
    if day.weekday() == 6:
        out.append(("week", day.isoformat()))
    if (day + timedelta(days=1)).day == 1:
        out.append(("month", f"{day.year}-{day.month:02d}"))
    if day.month == 12 and day.day == calendar.monthrange(day.year, 12)[1]:
        out.append(("year", str(day.year)))
    return out
