from __future__ import annotations

import os
import sys
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
    heygen_draft_name: str


@dataclass
class Settings:
    project_root: Path
    app_dir: Path
    config_local_path: Path | None
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
    heygen_mode: str
    heygen_poll_interval: int
    heygen_poll_timeout: int
    heygen_width: int
    heygen_height: int
    heygen_background_color: str
    heygen_fit: str
    gemini_api_key: str
    elevenlabs_api_key: str
    heygen_api_key: str
    state_file: Path
    web_host: str
    web_port: int
    raw: dict[str, Any] = field(default_factory=dict)


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[1]


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def config_local_candidates() -> list[Path]:
    return [
        app_dir() / "config.local.yaml",
        Path.home() / ".starnews" / "config.local.yaml",
    ]


def find_config_local() -> Path | None:
    for path in config_local_candidates():
        if path.exists():
            return path
    return None


def default_config_local_path() -> Path:
    return app_dir() / "config.local.yaml"


def resolve_config_path(config_path: Path | None = None) -> Path:
    if config_path:
        return config_path
    for candidate in (app_dir() / "config.yaml", resource_dir() / "config.yaml"):
        if candidate.exists():
            return candidate
    return resource_dir() / "config.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def _load_env_files() -> None:
    for env_path in (
        app_dir() / ".env",
        Path.home() / ".starnews" / ".env",
        resource_dir() / ".env",
    ):
        if env_path.exists():
            load_dotenv(env_path)
            return


def _pick_str(*values: object) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _team_defaults_path() -> Path:
    bundled = resource_dir() / "starnews" / "team_defaults.yaml"
    if bundled.exists():
        return bundled
    return Path(__file__).resolve().parent / "team_defaults.yaml"


def _load_team_defaults() -> dict[str, Any]:
    return _load_yaml(_team_defaults_path())


def has_required_secrets(settings: Settings) -> bool:
    if not settings.gemini_api_key or not settings.elevenlabs_api_key:
        return False
    for key in settings.avatar_rotation:
        if not settings.avatars[key].elevenlabs_voice_id:
            return False
    return True


def missing_setup_fields(settings: Settings) -> list[str]:
    missing: list[str] = []
    if not has_required_secrets(settings):
        missing.append("secrets")
    if settings.config_local_path:
        local_raw = _load_yaml(settings.config_local_path)
        if not _pick_str(local_raw.get("paths", {}).get("startv_root")):
            missing.append("startv_root")
    else:
        missing.append("startv_root")
    return missing


def is_setup_complete(settings: Settings) -> bool:
    return not missing_setup_fields(settings)


def save_setup_config(data: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_config_local_path()
    existing = _load_yaml(target) if target.exists() else {}
    from starnews.secrets import merge_config_dict

    merged = merge_config_dict(existing, data)
    return save_config_local(merged, target)


def save_folder_setup(startv_root: str, path: Path | None = None) -> Path:
    return save_setup_config({"paths": {"startv_root": startv_root.strip()}}, path)


def save_config_local(data: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_config_local_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)
    return target


def load_settings(config_path: Path | None = None) -> Settings:
    root = resource_dir()
    install_dir = app_dir()
    config_path = resolve_config_path(config_path)
    local_path = find_config_local()
    local_raw = _load_yaml(local_path) if local_path else {}
    team_raw = _load_team_defaults()

    _load_env_files()

    with open(config_path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    local_paths = local_raw.get("paths", {})
    local_api = local_raw.get("api_keys", {})
    local_voices = local_raw.get("elevenlabs_voices", {})
    local_avatars = local_raw.get("heygen_avatars", {})
    local_templates = local_raw.get("heygen_templates", {})
    team_api = team_raw.get("api_keys", {})
    team_voices = team_raw.get("elevenlabs_voices", {})
    team_avatars = team_raw.get("heygen_avatars", {})
    team_templates = team_raw.get("heygen_templates", {})

    avatars_cfg = raw.get("avatars", {})
    rotation = avatars_cfg.get("rotation", ["tim", "leon", "chris", "annie"])
    avatars: dict[str, AvatarConfig] = {}
    for key in rotation:
        entry = avatars_cfg.get(key, {})
        env_el_voice = os.getenv(f"ELEVENLABS_VOICE_{key.upper()}", "")
        env_avatar = os.getenv(f"HEYGEN_AVATAR_{key.upper()}", "")
        env_template = os.getenv(f"HEYGEN_TEMPLATE_{key.upper()}", "")
        avatars[key] = AvatarConfig(
            key=key,
            display_name=entry.get("display_name", key.title()),
            elevenlabs_voice_name=entry.get("elevenlabs_voice_name", ""),
            elevenlabs_voice_id=_pick_str(
                local_voices.get(key),
                env_el_voice,
                team_voices.get(key),
                entry.get("elevenlabs_voice_id"),
            ),
            heygen_avatar_id=_pick_str(
                local_avatars.get(key),
                env_avatar,
                team_avatars.get(key),
                entry.get("heygen_avatar_id"),
            ),
            heygen_template_id=_pick_str(
                local_templates.get(key),
                env_template,
                team_templates.get(key),
                entry.get("heygen_template_id"),
            ),
            heygen_draft_name=entry.get("heygen_draft_name", ""),
        )

    paths = raw.get("paths", {})
    gemini = raw.get("gemini", {})
    elevenlabs = raw.get("elevenlabs", {})
    heygen = raw.get("heygen", {})
    web = raw.get("web", {})
    dim = heygen.get("dimension", {})
    prompt_rel = gemini.get("prompt_file", "prompts/gemini_script.txt")

    return Settings(
        project_root=root,
        app_dir=install_dir,
        config_local_path=local_path,
        startv_root=_expand(
            _pick_str(local_paths.get("startv_root"), paths.get("startv_root"), "~/Documents/StarTV")
        ),
        avatars=avatars,
        avatar_rotation=rotation,
        gemini_model=gemini.get("model", "gemini-2.5-flash"),
        gemini_prompt_file=root / prompt_rel,
        elevenlabs_model_id=elevenlabs.get("model_id", "eleven_multilingual_v2"),
        elevenlabs_stability=float(elevenlabs.get("stability", 0.5)),
        elevenlabs_similarity_boost=float(elevenlabs.get("similarity_boost", 0.75)),
        elevenlabs_style=float(elevenlabs.get("style", 0.0)),
        elevenlabs_use_speaker_boost=bool(elevenlabs.get("use_speaker_boost", True)),
        heygen_mode=str(heygen.get("mode", "manual")).lower(),
        heygen_poll_interval=int(heygen.get("poll_interval_seconds", 15)),
        heygen_poll_timeout=int(heygen.get("poll_timeout_seconds", 1800)),
        heygen_width=int(dim.get("width", 1920)),
        heygen_height=int(dim.get("height", 1080)),
        heygen_background_color=heygen.get("background_color", "#00B140"),
        heygen_fit=str(heygen.get("fit", "cover")),
        gemini_api_key=_pick_str(
            local_api.get("gemini"),
            os.getenv("GEMINI_API_KEY"),
            team_api.get("gemini"),
        ),
        elevenlabs_api_key=_pick_str(
            local_api.get("elevenlabs"),
            os.getenv("ELEVENLABS_API_KEY"),
            team_api.get("elevenlabs"),
        ),
        heygen_api_key=_pick_str(
            local_api.get("heygen"),
            os.getenv("HEYGEN_API_KEY"),
            team_api.get("heygen"),
        ),
        state_file=_expand(raw.get("state_file", "~/.starnews/state.json")),
        web_host=web.get("host", "127.0.0.1"),
        web_port=int(web.get("port", 8765)),
        raw=raw,
    )
