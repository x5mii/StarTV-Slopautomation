from __future__ import annotations

import shutil
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
    assets_dir = day_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return day_dir


def copy_premiere_template(settings: Settings, date_str: str) -> Path:
    day_dir = prepare_day_folder(settings, date_str)
    target = day_dir / f"SN_{normalize_date(date_str)}.prproj"
    if not settings.premiere_template.exists():
        raise FileNotFoundError(f"Premiere template not found: {settings.premiere_template}")
    shutil.copy2(settings.premiere_template, target)
    return target


def print_checklist(day_dir: Path, avatar_name: str, video_path: Path | None) -> None:
    date_str = day_dir.name
    prproj = day_dir / f"SN_{date_str}.prproj"
    video_label = video_path.name if video_path else f"{avatar_name}_{date_str}_1080p.mp4"
    lines = [
        "",
        "=" * 60,
        "StarNews pipeline complete — next steps in Premiere:",
        "=" * 60,
        f"1. Open project: {prproj}",
        f"2. Replace moderator clip with: assets/{video_label}",
        "3. Swap article images (add Google images as needed)",
        "4. Trim sequence length to match audio",
        "5. Save project, then run premiere/starnews_export.jsx (File → Scripts)",
        "6. Exports (Adobe Media Encoder):",
        f"   - TV: SN_{date_str}_1   (sequence SN_Täglich, 720p 50fps)",
        f"   - SM: SN_{date_str}_SM  (sequence SN_Social)",
        f"   - YT: SN_{date_str}_YT  (StarNews YT.epr preset)",
        "7. Send exports to chef via SwissTransfer",
        "=" * 60,
        "",
    ]
    print("\n".join(lines))
