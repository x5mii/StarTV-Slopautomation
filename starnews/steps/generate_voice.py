from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

from starnews.config import AvatarConfig, Settings


def _voice_slug(name: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", name.strip())
    return slug.strip("_")[:60] or "voice"


def generate_voice(
    script_text: str,
    avatar: AvatarConfig,
    date_str: str,
    assets_dir: Path,
    settings: Settings,
) -> Path:
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set. Add it to ~/.starnews/.env")
    if not avatar.elevenlabs_voice_id:
        raise ValueError(
            f"ElevenLabs voice ID missing for {avatar.display_name}. "
            f"Set ELEVENLABS_VOICE_{avatar.key.upper()} in ~/.starnews/.env"
        )

    assets_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H_%M_%S")
    filename = f"ElevenLabs_{timestamp}_{_voice_slug(avatar.elevenlabs_voice_name)}.mp3"
    output_path = assets_dir / filename

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{avatar.elevenlabs_voice_id}"
    payload = {
        "text": script_text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {
            "stability": settings.elevenlabs_stability,
            "similarity_boost": settings.elevenlabs_similarity_boost,
            "style": settings.elevenlabs_style,
            "use_speaker_boost": settings.elevenlabs_use_speaker_boost,
        },
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    with httpx.Client(timeout=300) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        output_path.write_bytes(response.content)

    return output_path
