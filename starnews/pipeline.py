from __future__ import annotations

import json
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from starnews.config import Settings, load_settings
from starnews.rotation import mark_avatar_used, next_avatar
from starnews.steps.generate_avatar import generate_avatar_video
from starnews.steps.generate_script import (
    ScriptPackage,
    generate_script,
    write_script_docx,
)
from starnews.steps.generate_voice import generate_voice
from starnews.steps.prepare_folder import normalize_date, prepare_day_folder
from starnews.steps.scrape_gala import scrape_gala

ProgressCallback = Callable[[str], None]


@dataclass
class PipelineResult:
    date: str
    day_dir: Path
    avatar_key: str
    avatar_name: str
    voice_name: str
    article_url: str
    script_title: str
    audio_path: Path | None = None
    video_path: Path | None = None
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("day_dir", "audio_path", "video_path"):
            value = data.get(key)
            if value is not None:
                data[key] = str(value)
        return data


@dataclass
class PipelineRunState:
    status: str = "idle"
    message: str = ""
    error: str | None = None
    result: dict | None = None
    log: list[str] = field(default_factory=list)


_run_state = PipelineRunState()


def get_run_state() -> PipelineRunState:
    return _run_state


def _reset_run_state() -> None:
    global _run_state
    _run_state = PipelineRunState()


def _log(msg: str, on_progress: ProgressCallback | None) -> None:
    _run_state.message = msg
    _run_state.log.append(msg)
    if on_progress:
        on_progress(msg)
    else:
        print(msg)


def _runs_dir(settings: Settings) -> Path:
    runs = settings.state_file.parent / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    return runs


def _cache_script(settings: Settings, date_str: str, package: ScriptPackage) -> None:
    path = _runs_dir(settings) / f"{date_str}.json"
    path.write_text(
        json.dumps(
            {
                "title": package.title,
                "caption": package.caption,
                "hashtags": package.hashtags,
                "script": package.script,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _load_cached_script(settings: Settings, date_str: str) -> ScriptPackage | None:
    path = _runs_dir(settings) / f"{date_str}.json"
    if not path.exists():
        return None
    meta = json.loads(path.read_text(encoding="utf-8"))
    return ScriptPackage(
        title=meta["title"],
        caption=meta["caption"],
        hashtags=meta["hashtags"],
        script=meta["script"],
    )


def run_pipeline(
    url: str,
    date_str: str,
    *,
    settings: Settings | None = None,
    on_progress: ProgressCallback | None = None,
    resume: bool = False,
    avatar_key: str | None = None,
) -> PipelineResult:
    settings = settings or load_settings()
    date_str = normalize_date(date_str)
    day_dir = prepare_day_folder(settings, date_str)
    assets_dir = day_dir / "assets"

    script_pkg = _load_cached_script(settings, date_str) if resume else None
    if script_pkg is not None:
        _log("Resume mode: reusing existing script", on_progress)
        write_script_docx(script_pkg, day_dir)
    else:
        _log(f"Scraping Gala.de article: {url}", on_progress)
        article = scrape_gala(url)

        _log("Generating script with Gemini...", on_progress)
        script_pkg = generate_script(article.text, settings)
        write_script_docx(script_pkg, day_dir)
        _cache_script(settings, date_str, script_pkg)
        _log(f"Script ready: {script_pkg.title}", on_progress)

    if avatar_key is not None:
        avatar = settings.avatars[avatar_key]
        rotation_managed = False
    else:
        avatar_key, avatar = next_avatar(settings)
        rotation_managed = True
    _log(
        f"Avatar: {avatar.display_name} (ElevenLabs: {avatar.elevenlabs_voice_name})",
        on_progress,
    )

    existing_audio = sorted(assets_dir.glob("ElevenLabs*.mp3"))
    if resume and existing_audio:
        audio_path = existing_audio[-1]
        _log(f"Reusing voice audio: {audio_path.name}", on_progress)
    else:
        _log("Generating voice with ElevenLabs...", on_progress)
        audio_path = generate_voice(
            script_pkg.script, avatar, date_str, assets_dir, settings
        )
        _log(f"Voice saved: {audio_path.name}", on_progress)

    if settings.heygen_mode == "manual":
        _log("HeyGen: manual mode — skipping API render", on_progress)
    else:
        _log("Generating avatar video with HeyGen (may take 10–20 min)...", on_progress)

    video_path = generate_avatar_video(
        audio_path,
        avatar,
        date_str,
        assets_dir,
        settings,
        on_progress=lambda msg: _log(msg, on_progress),
    )

    if video_path is not None:
        _log(f"HeyGen video saved: {video_path.name}", on_progress)
    else:
        draft = avatar.heygen_draft_name.strip() or f"{avatar.display_name} draft"
        _log(
            f"HeyGen manual: open \"{draft}\", upload {audio_path.name}, "
            f"save {avatar.display_name}_{date_str}_1080p.mp4 → assets/ (README)",
            on_progress,
        )

    if rotation_managed:
        mark_avatar_used(settings, avatar_key)

    result = PipelineResult(
        date=date_str,
        day_dir=day_dir,
        avatar_key=avatar_key,
        avatar_name=avatar.display_name,
        voice_name=avatar.elevenlabs_voice_name,
        article_url=url,
        script_title=script_pkg.title,
        audio_path=audio_path,
        video_path=video_path,
    )

    suffix = (
        "skript.docx + ElevenLabs MP3 (HeyGen step: see README)"
        if video_path is None
        else "skript.docx + assets/"
    )
    _log(f"Done: {day_dir} ({suffix})", on_progress)
    return result


def run_pipeline_tracked(
    url: str,
    date_str: str,
    *,
    settings: Settings | None = None,
) -> PipelineResult:
    _reset_run_state()
    _run_state.status = "running"
    try:
        result = run_pipeline(url, date_str, settings=settings, on_progress=_log)
        _run_state.status = "completed"
        _run_state.result = result.to_dict()
        return result
    except Exception as exc:
        _run_state.status = "failed"
        _run_state.error = str(exc)
        _run_state.log.append(traceback.format_exc())
        raise


def save_run_manifest(day_dir: Path, result: PipelineResult) -> Path:
    """Persist the run manifest in the state dir (keeps the date folder clean)."""
    settings = load_settings()
    manifest_path = _runs_dir(settings) / f"{result.date}_manifest.json"
    manifest_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def run_batch(
    jobs: list[tuple[str, str]],
    *,
    settings: Settings | None = None,
    max_workers: int = 7,
) -> list[tuple[str, PipelineResult | None, str | None]]:
    """Run several (date, url) jobs in parallel with pre-assigned avatar rotation.

    Returns a list of (date, result_or_None, error_or_None).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from starnews.rotation import load_state, save_state

    settings = settings or load_settings()
    jobs = [(normalize_date(date), url) for date, url in jobs]

    rotation = settings.avatar_rotation
    state = load_state(settings)
    last = state.get("last_avatar")
    start_idx = (rotation.index(last) + 1) % len(rotation) if last in rotation else 0
    assignments = {
        date: rotation[(start_idx + i) % len(rotation)]
        for i, (date, _) in enumerate(jobs)
    }
    state["last_avatar"] = rotation[(start_idx + len(jobs) - 1) % len(rotation)]
    save_state(settings, state)

    results: list[tuple[str, PipelineResult | None, str | None]] = []

    def worker(date: str, url: str) -> tuple[str, PipelineResult | None, str | None]:
        prefix = f"[{date}]"
        try:
            result = run_pipeline(
                url,
                date,
                settings=settings,
                on_progress=lambda msg: print(f"{prefix} {msg}"),
                avatar_key=assignments[date],
            )
            return date, result, None
        except Exception as exc:
            print(f"{prefix} FAILED: {exc}")
            return date, None, str(exc)

    with ThreadPoolExecutor(max_workers=min(max_workers, len(jobs))) as pool:
        futures = [pool.submit(worker, date, url) for date, url in jobs]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item[0])
    return results
