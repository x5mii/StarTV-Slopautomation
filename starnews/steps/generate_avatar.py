from __future__ import annotations

import time
from pathlib import Path

import httpx

from starnews.config import AvatarConfig, Settings


def _upload_audio(audio_path: Path, settings: Settings) -> str:
    url = "https://upload.heygen.com/v1/asset"
    headers = {
        "X-Api-Key": settings.heygen_api_key,
        "Content-Type": "audio/mpeg",
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(url, content=audio_path.read_bytes(), headers=headers)
        response.raise_for_status()
        data = response.json()
    asset_id = data.get("data", {}).get("id") or data.get("id")
    if not asset_id:
        raise ValueError(f"HeyGen upload did not return asset id: {data}")
    return asset_id


def _create_video_from_template(
    template_id: str,
    audio_asset_id: str,
    settings: Settings,
) -> str:
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": settings.heygen_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "caption": False,
        "dimension": {
            "width": settings.heygen_width,
            "height": settings.heygen_height,
        },
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": template_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "audio",
                    "audio_asset_id": audio_asset_id,
                },
            }
        ],
    }

    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            payload_template = {
                "caption": False,
                "title": "StarNews",
                "template_id": template_id,
                "variables": {
                    "audio": {"name": "audio", "type": "audio", "properties": {"asset_id": audio_asset_id}},
                },
            }
            response = client.post(url, json=payload_template, headers=headers)
        response.raise_for_status()
        data = response.json()
    video_id = data.get("data", {}).get("video_id") or data.get("video_id")
    if not video_id:
        raise ValueError(f"HeyGen generate did not return video_id: {data}")
    return video_id


def _poll_video(video_id: str, settings: Settings) -> str:
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {"X-Api-Key": settings.heygen_api_key}
    deadline = time.time() + settings.heygen_poll_timeout

    with httpx.Client(timeout=60) as client:
        while time.time() < deadline:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json().get("data", response.json())
            status = (data.get("status") or "").lower()
            if status == "completed":
                video_url = data.get("video_url")
                if not video_url:
                    raise ValueError(f"HeyGen completed without video_url: {data}")
                return video_url
            if status in {"failed", "error"}:
                raise ValueError(f"HeyGen video generation failed: {data}")
            time.sleep(settings.heygen_poll_interval)

    raise TimeoutError(f"HeyGen video {video_id} did not complete in time")


def _download_video(video_url: str, output_path: Path) -> Path:
    with httpx.Client(timeout=600, follow_redirects=True) as client:
        response = client.get(video_url)
        response.raise_for_status()
        output_path.write_bytes(response.content)
    return output_path


def generate_avatar_video(
    audio_path: Path,
    avatar: AvatarConfig,
    date_str: str,
    assets_dir: Path,
    settings: Settings,
    on_progress=None,
) -> Path:
    if not settings.heygen_api_key:
        raise ValueError("HEYGEN_API_KEY is not set. Add it to ~/.starnews/.env")
    if not avatar.heygen_template_id:
        raise ValueError(
            f"HeyGen template/avatar ID missing for {avatar.display_name}. "
            f"Set HEYGEN_TEMPLATE_{avatar.key.upper()} in ~/.starnews/.env"
        )

    assets_dir.mkdir(parents=True, exist_ok=True)
    output_path = assets_dir / f"{avatar.display_name}_{date_str}_1080p.mp4"

    if on_progress:
        on_progress("Uploading audio to HeyGen...")
    asset_id = _upload_audio(audio_path, settings)

    if on_progress:
        on_progress("Starting HeyGen video render...")
    video_id = _create_video_from_template(avatar.heygen_template_id, asset_id, settings)

    if on_progress:
        on_progress(f"Waiting for HeyGen (video_id={video_id})...")
    video_url = _poll_video(video_id, settings)

    if on_progress:
        on_progress("Downloading HeyGen video...")
    return _download_video(video_url, output_path)
