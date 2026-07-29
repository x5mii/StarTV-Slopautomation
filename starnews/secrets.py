from __future__ import annotations

from pathlib import Path
from typing import Any

AVATAR_KEYS = ("tim", "leon", "chris", "annie")


def parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def parse_env_file(path: Path) -> dict[str, str]:
    return parse_env_text(path.read_text(encoding="utf-8"))


def env_to_config_local(
    env: dict[str, str],
    startv_root: str = "",
) -> dict[str, Any]:
    data: dict[str, Any] = {}

    if startv_root.strip():
        data["paths"] = {"startv_root": startv_root.strip()}

    api_keys: dict[str, str] = {}
    if env.get("GEMINI_API_KEY"):
        api_keys["gemini"] = env["GEMINI_API_KEY"]
    if env.get("ELEVENLABS_API_KEY"):
        api_keys["elevenlabs"] = env["ELEVENLABS_API_KEY"]
    if env.get("HEYGEN_API_KEY"):
        api_keys["heygen"] = env["HEYGEN_API_KEY"]
    if api_keys:
        data["api_keys"] = api_keys

    voices: dict[str, str] = {}
    avatars: dict[str, str] = {}
    templates: dict[str, str] = {}
    for key in AVATAR_KEYS:
        voice_key = f"ELEVENLABS_VOICE_{key.upper()}"
        avatar_key = f"HEYGEN_AVATAR_{key.upper()}"
        template_key = f"HEYGEN_TEMPLATE_{key.upper()}"
        if env.get(voice_key):
            voices[key] = env[voice_key]
        if env.get(avatar_key):
            avatars[key] = env[avatar_key]
        if env.get(template_key):
            templates[key] = env[template_key]

    if voices:
        data["elevenlabs_voices"] = voices
    if avatars:
        data["heygen_avatars"] = avatars
    if templates:
        data["heygen_templates"] = templates

    return data


def merge_config_dict(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for section, values in updates.items():
        if isinstance(values, dict) and isinstance(merged.get(section), dict):
            section_merged = dict(merged[section])
            section_merged.update(values)
            merged[section] = section_merged
        else:
            merged[section] = values
    return merged


def validate_config_local(data: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    api = data.get("api_keys", {})
    if not str(api.get("gemini", "")).strip():
        missing.append("GEMINI_API_KEY")
    if not str(api.get("elevenlabs", "")).strip():
        missing.append("ELEVENLABS_API_KEY")

    voices = data.get("elevenlabs_voices", {})
    for key in AVATAR_KEYS:
        if not str(voices.get(key, "")).strip():
            missing.append(f"ELEVENLABS_VOICE_{key.upper()}")

    if not str(data.get("paths", {}).get("startv_root", "")).strip():
        missing.append("startv_root")

    return missing
