from __future__ import annotations

import threading
import traceback

from flask import Flask, jsonify, redirect, render_template, request, url_for

from starnews.config import (
    Settings,
    default_config_local_path,
    has_required_secrets,
    is_setup_complete,
    load_settings,
    missing_setup_fields,
    save_setup_config,
)
from starnews.pipeline import (
    get_run_state,
    run_batch_tracked,
    run_pipeline_tracked,
    save_run_manifest,
)
from starnews.rotation import load_state, next_avatar
from starnews.secrets import env_to_config_local, parse_env_text
from starnews.steps.prepare_folder import normalize_date


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["STARNNEWS_SETTINGS"] = settings
    _lock = threading.Lock()
    _running = {"active": False}

    def current_settings() -> Settings:
        return app.config["STARNNEWS_SETTINGS"]

    def avatar_options(settings_ref: Settings) -> list[dict]:
        return [
            {
                "key": key,
                "name": settings_ref.avatars[key].display_name,
                "voice": settings_ref.avatars[key].elevenlabs_voice_name,
            }
            for key in settings_ref.avatar_rotation
        ]

    @app.before_request
    def require_setup():
        if request.endpoint in {"setup_page", "setup_save", "static"}:
            return None
        if not is_setup_complete(current_settings()):
            return redirect(url_for("setup_page"))
        return None

    @app.get("/setup")
    def setup_page():
        settings_ref = current_settings()
        return render_template(
            "setup.html",
            startv_root=str(settings_ref.startv_root),
            config_local=str(default_config_local_path()),
            secrets_ready=has_required_secrets(settings_ref),
        )

    @app.post("/api/setup")
    def setup_save():
        startv_root = ""
        env_text = ""

        if request.content_type and "multipart/form-data" in request.content_type:
            startv_root = (request.form.get("startv_root") or "").strip()
            env_text = (request.form.get("env_text") or "").strip()
            upload = request.files.get("env_file")
            if upload and upload.filename:
                env_text = upload.read().decode("utf-8", errors="replace")
        else:
            payload = request.get_json(silent=True) or {}
            startv_root = (payload.get("startv_root") or "").strip()
            env_text = (payload.get("env_text") or "").strip()

        if not startv_root:
            return jsonify({"error": "StarTV output folder is required."}), 400

        settings_ref = current_settings()
        if not env_text.strip() and not has_required_secrets(settings_ref):
            return jsonify(
                {
                    "error": (
                        "Import team-secrets.env (file or paste). "
                        "Ask your team lead for this file."
                    )
                }
            ), 400

        updates: dict = {"paths": {"startv_root": startv_root}}
        if env_text.strip():
            env_vars = parse_env_text(env_text)
            updates = env_to_config_local(env_vars, startv_root=startv_root)

        save_setup_config(updates)
        app.config["STARNNEWS_SETTINGS"] = load_settings()
        refreshed = current_settings()

        if not is_setup_complete(refreshed):
            missing = missing_setup_fields(refreshed)
            labels = ", ".join(missing)
            return jsonify({"error": f"Setup incomplete: {labels}"}), 400

        return jsonify({"ok": True, "path": str(default_config_local_path())})

    @app.get("/")
    def index():
        settings_ref = current_settings()
        state = load_state(settings_ref)
        next_key, next_av = next_avatar(settings_ref)
        return render_template(
            "index.html",
            last_avatar=state.get("last_avatar"),
            next_avatar=next_av.display_name,
            next_avatar_key=next_key,
            next_voice=next_av.elevenlabs_voice_name,
            startv_root=str(settings_ref.startv_root),
            avatars=avatar_options(settings_ref),
        )

    def _parse_jobs(payload: dict) -> tuple[list[dict] | None, str | None]:
        settings_ref = current_settings()
        jobs_raw = payload.get("jobs")
        if not jobs_raw:
            url = (payload.get("url") or "").strip()
            date = (payload.get("date") or "").strip()
            avatar_key = (payload.get("avatar") or payload.get("avatar_key") or "").strip()
            if url or date:
                jobs_raw = [{"url": url, "date": date, "avatar": avatar_key}]

        if not isinstance(jobs_raw, list) or not jobs_raw:
            return None, "At least one job is required"

        if len(jobs_raw) > 7:
            return None, "Maximum 7 jobs at once"

        jobs: list[dict] = []
        dates: list[str] = []
        for i, raw in enumerate(jobs_raw, start=1):
            if not isinstance(raw, dict):
                return None, f"Job {i}: invalid payload"
            url = str(raw.get("url") or "").strip()
            date = str(raw.get("date") or "").strip()
            avatar_key = str(
                raw.get("avatar") or raw.get("avatar_key") or ""
            ).strip().lower()
            if not url:
                return None, f"Job {i}: URL is required"
            if not date:
                return None, f"Job {i}: Date is required (DD.MM)"
            try:
                date = normalize_date(date)
            except Exception:
                return None, f"Job {i}: Date must be DD.MM"
            if not avatar_key:
                return None, f"Job {i}: Avatar is required"
            if avatar_key not in settings_ref.avatars:
                return None, f"Job {i}: Unknown avatar '{avatar_key}'"
            if date in dates:
                return None, f"Job {i}: Duplicate date {date}"
            dates.append(date)
            jobs.append({"url": url, "date": date, "avatar_key": avatar_key})
        return jobs, None

    @app.post("/api/run")
    def api_run():
        settings_ref = current_settings()
        payload = request.get_json(silent=True) or {}
        jobs, error = _parse_jobs(payload)
        if error or jobs is None:
            return jsonify({"error": error or "Invalid jobs"}), 400

        with _lock:
            if _running["active"]:
                return jsonify({"error": "A pipeline run is already in progress"}), 409
            _running["active"] = True

        def worker():
            try:
                if len(jobs) == 1:
                    job = jobs[0]
                    result = run_pipeline_tracked(
                        job["url"],
                        job["date"],
                        settings=settings_ref,
                        avatar_key=job["avatar_key"],
                    )
                    save_run_manifest(result.day_dir, result)
                else:
                    run_batch_tracked(jobs, settings=settings_ref)
            except Exception:
                run_state = get_run_state()
                if not run_state.error:
                    run_state.error = traceback.format_exc()
            finally:
                with _lock:
                    _running["active"] = False

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return jsonify({"status": "started", "jobs": len(jobs)})

    @app.get("/api/progress")
    def api_progress():
        run_state = get_run_state()
        return jsonify(
            {
                "status": run_state.status,
                "message": run_state.message,
                "error": run_state.error,
                "result": run_state.result,
                "results": run_state.results,
                "jobs": run_state.jobs,
                "log": run_state.log[-120:],
                "running": _running["active"],
            }
        )

    @app.get("/api/status")
    def api_status():
        settings_ref = current_settings()
        state = load_state(settings_ref)
        next_key, next_av = next_avatar(settings_ref)
        return jsonify(
            {
                "last_avatar": state.get("last_avatar"),
                "next_avatar": next_av.display_name,
                "next_avatar_key": next_key,
                "next_voice": next_av.elevenlabs_voice_name,
                "heygen_mode": settings_ref.heygen_mode,
                "startv_root": str(settings_ref.startv_root),
                "avatars": avatar_options(settings_ref),
                "keys": {
                    "gemini": bool(settings_ref.gemini_api_key),
                    "elevenlabs": bool(settings_ref.elevenlabs_api_key),
                    "heygen": bool(settings_ref.heygen_api_key),
                },
            }
        )

    return app
