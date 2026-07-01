from __future__ import annotations

import json
from pathlib import Path

from starnews.config import Settings


def load_state(settings: Settings) -> dict:
    path = settings.state_file
    if not path.exists():
        return {"last_avatar": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_avatar": None}


def save_state(settings: Settings, state: dict) -> None:
    path = settings.state_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_avatar(settings: Settings) -> tuple[str, object]:
    state = load_state(settings)
    rotation = settings.avatar_rotation
    last = state.get("last_avatar")
    if last in rotation:
        idx = rotation.index(last)
        key = rotation[(idx + 1) % len(rotation)]
    else:
        key = rotation[0]
    avatar = settings.avatars[key]
    return key, avatar


def mark_avatar_used(settings: Settings, avatar_key: str) -> None:
    state = load_state(settings)
    state["last_avatar"] = avatar_key
    save_state(settings, state)
