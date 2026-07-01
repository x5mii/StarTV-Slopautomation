from __future__ import annotations

import threading
import traceback

from flask import Flask, jsonify, render_template, request

from starnews.config import Settings
from starnews.pipeline import get_run_state, run_pipeline_tracked, save_run_manifest
from starnews.rotation import load_state, next_avatar


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["STARNNEWS_SETTINGS"] = settings
    _lock = threading.Lock()
    _running = {"active": False}

    @app.get("/")
    def index():
        state = load_state(settings)
        _, next_av = next_avatar(settings)
        return render_template(
            "index.html",
            last_avatar=state.get("last_avatar"),
            next_avatar=next_av.display_name,
            next_voice=next_av.elevenlabs_voice_name,
            startv_root=str(settings.startv_root),
        )

    @app.post("/api/run")
    def api_run():
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
                result = run_pipeline_tracked(url, date, settings=settings)
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
        state = load_state(settings)
        next_key, next_av = next_avatar(settings)
        return jsonify(
            {
                "last_avatar": state.get("last_avatar"),
                "next_avatar": next_av.display_name,
                "next_avatar_key": next_key,
                "next_voice": next_av.elevenlabs_voice_name,
                "startv_root": str(settings.startv_root),
                "keys": {
                    "gemini": bool(settings.gemini_api_key),
                    "elevenlabs": bool(settings.elevenlabs_api_key),
                    "heygen": bool(settings.heygen_api_key),
                },
            }
        )

    return app
