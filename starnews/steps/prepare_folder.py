from __future__ import annotations

from pathlib import Path

from starnews.config import Settings


def normalize_date(date_str: str) -> str:
    cleaned = date_str.strip()
    if len(cleaned.split(".")) != 2:
        raise ValueError("Date must be DD.MM, e.g. 01.07")
    day, month = cleaned.split(".")
    if len(day) != 2 or len(month) != 2:
        raise ValueError("Date must be DD.MM with leading zeros, e.g. 01.07")
    return cleaned


def day_directory(settings: Settings, date_str: str) -> Path:
    return settings.startv_root / normalize_date(date_str)


def prepare_day_folder(settings: Settings, date_str: str) -> Path:
    day_dir = day_directory(settings, date_str)
    (day_dir / "assets").mkdir(parents=True, exist_ok=True)
    return day_dir
