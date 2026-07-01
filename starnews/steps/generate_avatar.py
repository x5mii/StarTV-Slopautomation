from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx

from starnews.config import AvatarConfig, Settings


def _heygen_headers(settings: Settings, *, json: bool = False) -> dict[str, str]:
    headers = {"X-Api-Key": settings.heygen_api_key, "Accept": "application/json"}
    if json:
        headers["Content-Type"] = "application/json"
    return headers


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


def _get_template_schema(template_id: str, settings: Settings) -> dict[str, Any] | None:
    url = f"https://api.heygen.com/v2/template/{template_id}"
    with httpx.Client(timeout=60) as client:
        response = client.get(url, headers=_heygen_headers(settings))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        return None
    return payload.get("data", {})


def _audio_variables(variables: dict[str, Any], asset_id: str) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for name, spec in variables.items():
        if not isinstance(spec, dict):
            continue
        if (spec.get("type") or "").lower() != "audio":
            continue
        mapped[name] = {
            "name": name,
            "type": "audio",
            "properties": {"asset_id": asset_id},
        }
    return mapped


def _create_video_from_template(
    template_id: str,
    audio_asset_id: str,
    settings: Settings,
    template_schema: dict[str, Any],
) -> str:
    url = f"https://api.heygen.com/v2/template/{template_id}/generate"
    payload: dict[str, Any] = {
        "title": "StarNews",
        "caption": False,
        "dimension": {
            "width": settings.heygen_width,
            "height": settings.heygen_height,
        },
        "variables": _audio_variables(template_schema.get("variables") or {}, audio_asset_id),
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=_heygen_headers(settings, json=True))
        if response.status_code >= 400:
            raise ValueError(
                "HeyGen template generate failed. "
                f"Template {template_id} may not expose an audio variable. "
                f"Details: {response.text}"
            )
        data = response.json()
    if data.get("error"):
        raise ValueError(f"HeyGen template generate error: {data['error']}")
    video_id = data.get("data", {}).get("video_id") or data.get("video_id")
    if not video_id:
        raise ValueError(f"HeyGen generate did not return video_id: {data}")
    return video_id


def _create_video_v3(avatar: AvatarConfig, audio_asset_id: str, settings: Settings) -> str:
    """Create avatar video with custom audio via HeyGen v3 API (avatar look IDs)."""
    look_id = avatar.heygen_avatar_id.strip()
    url = "https://api.heygen.com/v3/videos"
    payload = {
        "type": "avatar",
        "avatar_id": look_id,
        "audio_asset_id": audio_asset_id,
        "title": "StarNews",
        "resolution": "1080p",
        "aspect_ratio": "16:9",
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=_heygen_headers(settings, json=True))
        if response.status_code >= 400:
            raise ValueError(
                "HeyGen v3 video create failed. "
                f"Check HEYGEN_AVATAR_{avatar.key.upper()} in ~/.starnews/.env — "
                "it must be an avatar look ID from `starnews heygen-avatars`, "
                "not a template ID. "
                f"Details: {response.text}"
            )
        data = response.json()
    if data.get("error"):
        raise ValueError(f"HeyGen v3 error: {data['error']}")
    video_id = data.get("data", {}).get("video_id") or data.get("video_id")
    if not video_id:
        raise ValueError(f"HeyGen v3 did not return video_id: {data}")
    return video_id


def _poll_video_v3(video_id: str, settings: Settings) -> str:
    url = f"https://api.heygen.com/v3/videos/{video_id}"
    headers = {"X-Api-Key": settings.heygen_api_key}
    deadline = time.time() + settings.heygen_poll_timeout

    with httpx.Client(timeout=60) as client:
        while time.time() < deadline:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json().get("data", response.json())
            status = (data.get("status") or "").lower()
            if status == "completed":
                video_url = data.get("video_url") or data.get("download_url")
                if not video_url:
                    raise ValueError(f"HeyGen completed without video_url: {data}")
                return video_url
            if status in {"failed", "error"}:
                raise ValueError(f"HeyGen video generation failed: {data}")
            time.sleep(settings.heygen_poll_interval)

    raise TimeoutError(f"HeyGen video {video_id} did not complete in time")


def _poll_video_v2(video_id: str, settings: Settings) -> str:
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

    assets_dir.mkdir(parents=True, exist_ok=True)
    output_path = assets_dir / f"{avatar.display_name}_{date_str}_1080p.mp4"

    if on_progress:
        on_progress("Uploading audio to HeyGen...")
    asset_id = _upload_audio(audio_path, settings)

    if on_progress:
        on_progress("Starting HeyGen video render...")

    use_v3 = bool(avatar.heygen_avatar_id.strip())
    use_template = bool(avatar.heygen_template_id.strip())

    if use_v3:
        if on_progress:
            on_progress(f"Using avatar look {avatar.heygen_avatar_id[:8]}... (v3 API)")
        video_id = _create_video_v3(avatar, asset_id, settings)
        poll = _poll_video_v3
    elif use_template:
        template_id = avatar.heygen_template_id.strip()
        template_schema = _get_template_schema(template_id, settings)
        if template_schema is None:
            raise ValueError(
                f"HeyGen template {template_id} not found. "
                f"Set HEYGEN_AVATAR_{avatar.key.upper()} with a look ID from `starnews heygen-avatars`."
            )
        audio_vars = _audio_variables(template_schema.get("variables") or {}, asset_id)
        if not audio_vars:
            raise ValueError(
                f"HeyGen template {template_id} has no audio placeholder. "
                f"Set HEYGEN_AVATAR_{avatar.key.upper()} instead — run `starnews heygen-avatars` "
                "to find your Tim/Leon/Chris look IDs."
            )
        video_id = _create_video_from_template(template_id, asset_id, settings, template_schema)
        poll = _poll_video_v2
    else:
        raise ValueError(
            f"HeyGen IDs missing for {avatar.display_name}. "
            f"Set HEYGEN_AVATAR_{avatar.key.upper()} in ~/.starnews/.env "
            "(run `starnews heygen-avatars` to list look IDs)."
        )

    if on_progress:
        on_progress(f"Waiting for HeyGen (video_id={video_id})...")
    video_url = poll(video_id, settings)

    if on_progress:
        on_progress("Downloading HeyGen video...")
    return _download_video(video_url, output_path)
