from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

from starnews.config import AvatarConfig, Settings


def _voice_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return slug[:60] or "voice"


def generate_voice(
    script: str,
    avatar: AvatarConfig,
    date_str: str,
    assets_dir: Path,
    settings: Settings,
) -> Path:
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set. Add it to ~/.starnews/.env")
    if not avatar.elevenlabs_voice_id:
        raise ValueError(
            f"ELEVENLABS_VOICE_{avatar.key.upper()} is not set for {avatar.display_name}."
        )

    assets_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%dT%H_%M_%S")
    filename = f"ElevenLabs_{timestamp}_{_voice_slug(avatar.elevenlabs_voice_name)}.mp3"
    output_path = assets_dir / filename

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{avatar.elevenlabs_voice_id}"
    payload = {
        "text": script,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {
            "stability": settings.elevenlabs_stability,
            "similarity_boost": settings.elevenlabs_similarity_boost,
            "style": settings.elevenlabs_style,
            "use_speaker_boost": settings.elevenlabs_use_speaker_boost,
        },
    }
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": settings.elevenlabs_api_key,
    }

    with httpx.Client(timeout=300) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        output_path.write_bytes(response.content)

    return output_path
