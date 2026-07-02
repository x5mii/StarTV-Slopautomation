from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class AvatarConfig:
    key: str
    display_name: str
    elevenlabs_voice_name: str
    elevenlabs_voice_id: str
    heygen_avatar_id: str
    heygen_template_id: str


@dataclass
class Settings:
    project_root: Path
    startv_root: Path
    avatars: dict[str, AvatarConfig]
    avatar_rotation: list[str]
    gemini_model: str
    gemini_prompt_file: Path
    elevenlabs_model_id: str
    elevenlabs_stability: float
    elevenlabs_similarity_boost: float
    elevenlabs_style: float
    elevenlabs_use_speaker_boost: bool
    heygen_poll_interval: int
    heygen_poll_timeout: int
    heygen_width: int
    heygen_height: int
    heygen_background_color: str
    gemini_api_key: str
    elevenlabs_api_key: str
    heygen_api_key: str
    state_file: Path
    web_host: str
    web_port: int
    raw: dict[str, Any] = field(default_factory=dict)


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def load_settings(config_path: Path | None = None) -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    config_path = config_path or project_root / "config.yaml"

    env_paths = [
        Path.home() / ".starnews" / ".env",
        project_root / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break

    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    avatars_cfg = raw.get("avatars", {})
    rotation = avatars_cfg.get("rotation", ["tim", "leon", "chris"])
    avatars: dict[str, AvatarConfig] = {}
    for key in rotation:
        entry = avatars_cfg.get(key, {})
        env_voice = os.getenv(f"ELEVENLABS_VOICE_{key.upper()}", "")
        env_avatar = os.getenv(f"HEYGEN_AVATAR_{key.upper()}", "")
        env_template = os.getenv(f"HEYGEN_TEMPLATE_{key.upper()}", "")
        avatars[key] = AvatarConfig(
            key=key,
            display_name=entry.get("display_name", key.title()),
            elevenlabs_voice_name=entry.get("elevenlabs_voice_name", ""),
            elevenlabs_voice_id=env_voice or entry.get("elevenlabs_voice_id", ""),
            heygen_avatar_id=env_avatar or entry.get("heygen_avatar_id", ""),
            heygen_template_id=env_template or entry.get("heygen_template_id", ""),
        )

    paths = raw.get("paths", {})
    gemini = raw.get("gemini", {})
    elevenlabs = raw.get("elevenlabs", {})
    heygen = raw.get("heygen", {})
    web = raw.get("web", {})
    dim = heygen.get("dimension", {})

    return Settings(
        project_root=project_root,
        startv_root=_expand(paths.get("startv_root", "~/Documents/StarTV")),
        avatars=avatars,
        avatar_rotation=rotation,
        gemini_model=gemini.get("model", "gemini-2.5-flash"),
        gemini_prompt_file=project_root / gemini.get("prompt_file", "prompts/gemini_script.txt"),
        elevenlabs_model_id=elevenlabs.get("model_id", "eleven_multilingual_v2"),
        elevenlabs_stability=float(elevenlabs.get("stability", 0.5)),
        elevenlabs_similarity_boost=float(elevenlabs.get("similarity_boost", 0.75)),
        elevenlabs_style=float(elevenlabs.get("style", 0.0)),
        elevenlabs_use_speaker_boost=bool(elevenlabs.get("use_speaker_boost", True)),
        heygen_poll_interval=int(heygen.get("poll_interval_seconds", 15)),
        heygen_poll_timeout=int(heygen.get("poll_timeout_seconds", 1800)),
        heygen_width=int(dim.get("width", 1920)),
        heygen_height=int(dim.get("height", 1080)),
        heygen_background_color=heygen.get("background_color", "#00B140"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", "").strip(),
        heygen_api_key=os.getenv("HEYGEN_API_KEY", "").strip(),
        state_file=_expand(raw.get("state_file", "~/.starnews/state.json")),
        web_host=web.get("host", "127.0.0.1"),
        web_port=int(web.get("port", 8765)),
        raw=raw,
    )
