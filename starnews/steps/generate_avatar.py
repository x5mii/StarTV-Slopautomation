from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx

from starnews.config import AvatarConfig, Settings


def _headers(settings: Settings, *, json: bool = False) -> dict[str, str]:
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


def _get_template_variables(template_id: str, settings: Settings) -> dict[str, Any] | None:
    url = f"https://api.heygen.com/v2/template/{template_id}"
    with httpx.Client(timeout=60) as client:
        response = client.get(url, headers=_headers(settings))
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        return None
    return (payload.get("data") or {}).get("variables") or {}


def _audio_variable_payload(variables: dict[str, Any], asset_id: str) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for name, spec in variables.items():
        if isinstance(spec, dict) and (spec.get("type") or "").lower() == "audio":
            mapped[name] = {
                "name": name,
                "type": "audio",
                "properties": {"asset_id": asset_id},
            }
    return mapped


def _create_from_template(
    template_id: str,
    audio_variables: dict[str, Any],
    settings: Settings,
) -> str:
    url = f"https://api.heygen.com/v2/template/{template_id}/generate"
    payload = {
        "title": "StarNews",
        "caption": False,
        "variables": audio_variables,
    }
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=_headers(settings, json=True))
        if response.status_code >= 400:
            raise ValueError(f"HeyGen template generate failed: {response.text}")
        data = response.json()
    if data.get("error"):
        raise ValueError(f"HeyGen template generate error: {data['error']}")
    video_id = (data.get("data") or {}).get("video_id")
    if not video_id:
        raise ValueError(f"HeyGen template generate returned no video_id: {data}")
    return video_id


def _create_v3_with_audio(
    avatar: AvatarConfig,
    asset_id: str,
    settings: Settings,
) -> str:
    look_id = avatar.heygen_avatar_id.strip()
    if not look_id:
        raise ValueError(
            f"HEYGEN_AVATAR_{avatar.key.upper()} is not set for {avatar.display_name}."
        )

    payload: dict[str, Any] = {
        "type": "avatar",
        "avatar_id": look_id,
        "audio_asset_id": asset_id,
        "title": "StarNews",
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "background": {
            "type": "color",
            "value": settings.heygen_background_color,
        },
    }
    if settings.heygen_fit:
        payload["fit"] = settings.heygen_fit

    url = "https://api.heygen.com/v3/videos"
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload, headers=_headers(settings, json=True))
        if response.status_code >= 400:
            raise ValueError(f"HeyGen v3 video create failed: {response.text}")
        data = response.json()
    if data.get("error"):
        raise ValueError(f"HeyGen v3 error: {data['error']}")
    video_id = (data.get("data") or {}).get("video_id")
    if not video_id:
        raise ValueError(f"HeyGen v3 returned no video_id: {data}")
    return video_id


def _create_v2_with_audio(
    avatar: AvatarConfig,
    asset_id: str,
    settings: Settings,
) -> str:
    look_id = avatar.heygen_avatar_id.strip()
    url = "https://api.heygen.com/v2/video/generate"
    background = {"type": "color", "value": settings.heygen_background_color}
    voice = {"type": "audio", "audio_asset_id": asset_id}
    characters = [
        {"type": "talking_photo", "talking_photo_id": look_id},
        {"type": "avatar", "avatar_id": look_id, "avatar_style": "normal"},
    ]
    last_error = ""
    with httpx.Client(timeout=120) as client:
        for character in characters:
            payload = {
                "caption": False,
                "dimension": {
                    "width": settings.heygen_width,
                    "height": settings.heygen_height,
                },
                "video_inputs": [
                    {
                        "character": character,
                        "voice": voice,
                        "background": background,
                    }
                ],
            }
            response = client.post(url, json=payload, headers=_headers(settings, json=True))
            if response.status_code < 400:
                data = response.json()
                if not data.get("error"):
                    video_id = (data.get("data") or {}).get("video_id")
                    if video_id:
                        return video_id
                last_error = str(data.get("error"))
            else:
                last_error = response.text
    raise ValueError(
        f"HeyGen v2 video generate failed for {avatar.display_name}: {last_error}"
    )


def _poll(video_id: str, settings: Settings) -> str:
    urls = [
        f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
        f"https://api.heygen.com/v3/videos/{video_id}",
    ]
    headers = {"X-Api-Key": settings.heygen_api_key}
    deadline = time.time() + settings.heygen_poll_timeout

    with httpx.Client(timeout=60) as client:
        while time.time() < deadline:
            for url in urls:
                try:
                    response = client.get(url, headers=headers)
                except httpx.HTTPError:
                    continue
                if response.status_code >= 400:
                    continue
                data = response.json().get("data") or response.json()
                status = (data.get("status") or "").lower()
                if status == "completed":
                    video_url = data.get("video_url") or data.get("download_url")
                    if video_url:
                        return video_url
                if status in {"failed", "error"}:
                    raise ValueError(f"HeyGen video generation failed: {data}")
            time.sleep(settings.heygen_poll_interval)

    raise TimeoutError(
        f"HeyGen video {video_id} did not complete within "
        f"{settings.heygen_poll_timeout // 60} minutes. "
        "Check https://app.heygen.com — if the video finished, download it manually."
    )


def _download(video_url: str, output_path: Path) -> Path:
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
) -> Path | None:
    if settings.heygen_mode == "manual":
        draft = avatar.heygen_draft_name.strip() or f"{avatar.display_name} draft"
        if on_progress:
            on_progress(
                f"HeyGen manual step: open draft \"{draft}\", upload {audio_path.name}, "
                f"save {avatar.display_name}_{date_str}_1080p.mp4 (see README)"
            )
        return None

    if not settings.heygen_api_key:
        raise ValueError("HEYGEN_API_KEY is not set. Add it to ~/.starnews/.env")

    assets_dir.mkdir(parents=True, exist_ok=True)
    output_path = assets_dir / f"{avatar.display_name}_{date_str}_1080p.mp4"

    if on_progress:
        on_progress("Uploading ElevenLabs audio to HeyGen...")
    asset_id = _upload_audio(audio_path, settings)

    template_id = avatar.heygen_template_id.strip()
    look_id = avatar.heygen_avatar_id.strip()
    video_id: str | None = None

    if template_id:
        variables = _get_template_variables(template_id, settings)
        if variables:
            audio_vars = _audio_variable_payload(variables, asset_id)
            if audio_vars:
                if on_progress:
                    on_progress("Rendering via HeyGen template (draft look + your audio)...")
                video_id = _create_from_template(template_id, audio_vars, settings)

    if video_id is None:
        if not look_id:
            raise ValueError(
                f"No HeyGen avatar look for {avatar.display_name}. "
                f"Set HEYGEN_AVATAR_{avatar.key.upper()} or use heygen.mode: manual in config.yaml."
            )
        if on_progress:
            on_progress(
                f"Rendering via HeyGen API (lip-sync to ElevenLabs, "
                f"{settings.heygen_background_color} background)..."
            )
        try:
            video_id = _create_v3_with_audio(avatar, asset_id, settings)
        except ValueError:
            if on_progress:
                on_progress("v3 failed — retrying via v2 studio API...")
            video_id = _create_v2_with_audio(avatar, asset_id, settings)

    if on_progress:
        on_progress(f"Waiting for HeyGen render (video_id={video_id})...")
    video_url = _poll(video_id, settings)

    if on_progress:
        on_progress("Downloading HeyGen video...")
    return _download(video_url, output_path)
