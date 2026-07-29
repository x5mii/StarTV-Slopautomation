from __future__ import annotations

import threading
import traceback

from flask import Flask, jsonify, redirect, render_template, request, url_for

from starnews.config import (
    Settings,
    default_config_local_path,
    is_setup_complete,
    load_settings,
    save_folder_setup,
)
from starnews.pipeline import get_run_state, run_pipeline_tracked, save_run_manifest
from starnews.rotation import load_state, next_avatar


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["STARNNEWS_SETTINGS"] = settings
    _lock = threading.Lock()
    _running = {"active": False}

    def current_settings() -> Settings:
        return app.config["STARNNEWS_SETTINGS"]

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
            avatars=settings_ref.avatar_rotation,
            avatar_info={key: settings_ref.avatars[key] for key in settings_ref.avatar_rotation},
            config_local=str(default_config_local_path()),
        )

    @app.post("/api/setup")
    def setup_save():
        payload = request.get_json(silent=True) or {}
        startv_root = (payload.get("startv_root") or "").strip()

        if not startv_root:
            return jsonify({"error": "Output folder is required."}), 400

        target = save_folder_setup(startv_root)
        app.config["STARNNEWS_SETTINGS"] = load_settings()
        return jsonify({"ok": True, "path": str(target)})

    @app.get("/")
    def index():
        settings_ref = current_settings()
        state = load_state(settings_ref)
        _, next_av = next_avatar(settings_ref)
        return render_template(
            "index.html",
            last_avatar=state.get("last_avatar"),
            next_avatar=next_av.display_name,
            next_voice=next_av.elevenlabs_voice_name,
            startv_root=str(settings_ref.startv_root),
        )

    @app.post("/api/run")
    def api_run():
        settings_ref = current_settings()
        payload = request.get_json(silent=True) or {}
        url = (payload.get("url") or request.form.get("url") or "").strip()
        date = (payload.get("date") or request.form.get("date") or "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400
        if not date:
            return jsonify({"error": "Date is required (DD.MM)"}), 400

        with _lock:
            if _running["active"]:
                return jsonify({"error": "A pipeline run is already in progress"}), 409
            _running["active"] = True

        def worker():
            try:
                result = run_pipeline_tracked(url, date, settings=settings_ref)
                save_run_manifest(result.day_dir, result)
            except Exception:
                run_state = get_run_state()
                if not run_state.error:
                    run_state.error = traceback.format_exc()
            finally:
                with _lock:
                    _running["active"] = False

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return jsonify({"status": "started"})

    @app.get("/api/progress")
    def api_progress():
        run_state = get_run_state()
        return jsonify(
            {
                "status": run_state.status,
                "message": run_state.message,
                "error": run_state.error,
                "result": run_state.result,
                "log": run_state.log[-80:],
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
                "keys": {
                    "gemini": bool(settings_ref.gemini_api_key),
                    "elevenlabs": bool(settings_ref.elevenlabs_api_key),
                    "heygen": bool(settings_ref.heygen_api_key),
                },
            }
        )

    return app
