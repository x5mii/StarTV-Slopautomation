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
from starnews.steps.generate_script import ScriptPackage, generate_script, write_script_outputs
from starnews.steps.generate_voice import generate_voice
from starnews.steps.prepare_folder import (
    copy_premiere_template,
    normalize_date,
    prepare_day_folder,
    print_checklist,
)
from starnews.steps.scrape_gala import (
    download_images,
    save_article_text,
    scrape_gala,
)

ProgressCallback = Callable[[str], None]


@dataclass
class PipelineResult:
    date: str
    day_dir: Path
    avatar_key: str
    avatar_name: str
    voice_name: str
    article_url: str
    article_title: str
    script_title: str
    audio_path: Path | None = None
    video_path: Path | None = None
    prproj_path: Path | None = None
    image_count: int = 0
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("day_dir", "audio_path", "video_path", "prproj_path"):
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


def _load_script_package(day_dir: Path) -> tuple[ScriptPackage, str]:
    from starnews.steps.generate_script import ScriptPackage
    import json

    meta_path = day_dir / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return (
            ScriptPackage(
                title=meta["title"],
                caption=meta["caption"],
                hashtags=meta["hashtags"],
                script=meta["script"],
            ),
            meta.get("title", ""),
        )
    existing_script = day_dir / "skript.docx"
    script = existing_script.read_text(encoding="utf-8")
    return ScriptPackage(title="", caption="", hashtags="", script=script), ""


def run_pipeline(
    url: str,
    date_str: str,
    *,
    settings: Settings | None = None,
    on_progress: ProgressCallback | None = None,
    resume: bool = False,
    skip_images: bool = False,
) -> PipelineResult:
    settings = settings or load_settings()
    date_str = normalize_date(date_str)
    day_dir = prepare_day_folder(settings, date_str)
    assets_dir = day_dir / "assets"

    existing_audio = sorted(assets_dir.glob("ElevenLabs*.mp3")) if assets_dir.exists() else []
    existing_script = day_dir / "skript.docx"
    resume_script = resume and existing_script.exists()
    resume_audio = resume and bool(existing_audio)

    if resume_script:
        script_pkg, article_title = _load_script_package(day_dir)
        article_url = url
        image_count = len(
            [
                p
                for p in assets_dir.glob("*")
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".avif"}
            ]
        )
        if resume_audio:
            _log("Resume mode: reusing existing script and voice audio", on_progress)
            audio_path = existing_audio[-1]
        else:
            _log("Resume mode: reusing script, generating voice", on_progress)
    else:
        _log(f"Scraping Gala.de article: {url}", on_progress)
        article = scrape_gala(url)
        save_article_text(article, assets_dir)
        if skip_images:
            _log("Skipping automatic image download (add pictures manually in Premiere)", on_progress)
            images = []
        else:
            images = download_images(article.image_urls, assets_dir)
            _log(f"Saved article text and {len(images)} image(s) to {assets_dir}", on_progress)

        _log("Generating script with Gemini...", on_progress)
        script_pkg = generate_script(article.text, settings)
        write_script_outputs(script_pkg, day_dir)
        _log(f"Script ready: {script_pkg.title}", on_progress)
        article_url = url
        article_title = article.title
        image_count = len(images)
        resume_audio = False

    avatar_key, avatar = next_avatar(settings)
    _log(
        f"Avatar: {avatar.display_name} (voice: {avatar.elevenlabs_voice_name})",
        on_progress,
    )

    if not resume_audio:
        _log("Generating voice with ElevenLabs...", on_progress)
        audio_path = generate_voice(
            script_pkg.script, avatar, date_str, assets_dir, settings
        )
        _log(f"Voice saved: {audio_path.name}", on_progress)

    _log("Generating avatar video with HeyGen (may take 10–20 min)...", on_progress)
    video_path = generate_avatar_video(
        audio_path,
        avatar,
        date_str,
        assets_dir,
        settings,
        on_progress=lambda msg: _log(msg, on_progress),
    )
    mark_avatar_used(settings, avatar_key)
    _log(f"HeyGen video saved: {video_path.name}", on_progress)

    _log("Copying Premiere template...", on_progress)
    prproj_path = copy_premiere_template(settings, date_str)
    _log(f"Premiere project: {prproj_path.name}", on_progress)

    result = PipelineResult(
        date=date_str,
        day_dir=day_dir,
        avatar_key=avatar_key,
        avatar_name=avatar.display_name,
        voice_name=avatar.elevenlabs_voice_name,
        article_url=article_url,
        article_title=article_title,
        script_title=script_pkg.title,
        audio_path=audio_path,
        video_path=video_path,
        prproj_path=prproj_path,
        image_count=image_count,
    )

    print_checklist(day_dir, avatar.display_name, video_path)
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
    manifest_path = day_dir / "pipeline.json"
    manifest_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path
