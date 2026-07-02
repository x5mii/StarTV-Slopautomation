from __future__ import annotations

from pathlib import Path

import click

from starnews.config import load_settings
from starnews.pipeline import run_batch, run_pipeline, save_run_manifest
from starnews.rotation import load_state, next_avatar


@click.group()
@click.version_option(package_name="starnews-pipeline")
def main() -> None:
    """StarNews daily production pipeline."""


@main.command()
@click.argument("url")
@click.option(
    "--date",
    required=True,
    help="Production date as DD.MM, e.g. 01.07",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Reuse cached script and ElevenLabs MP3 if already generated for this date.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def run(url: str, date: str, resume: bool, config_path: Path | None) -> None:
    """Run the pipeline for one Gala.de URL."""
    settings = load_settings(config_path)
    try:
        result = run_pipeline(url, date, settings=settings, resume=resume)
        save_run_manifest(result.day_dir, result)
        click.echo(f"\nDone. Output folder: {result.day_dir}")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@main.command()
@click.option(
    "--job",
    "-j",
    "jobs",
    type=(str, str),
    multiple=True,
    required=True,
    help="DATE URL pair, repeatable up to 7 times. Example: -j 03.07 https://...",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def batch(jobs: tuple[tuple[str, str], ...], config_path: Path | None) -> None:
    """Run up to 7 StarNews in parallel (one per date).

    Example for three days:

        starnews batch -j 03.07 URL1 -j 04.07 URL2 -j 05.07 URL3
    """
    if len(jobs) > 7:
        raise click.ClickException("Maximum 7 jobs per batch.")
    seen_dates = [date for date, _ in jobs]
    if len(seen_dates) != len(set(seen_dates)):
        raise click.ClickException("Each job needs a unique date.")

    settings = load_settings(config_path)
    click.echo(f"Starting {len(jobs)} pipeline run(s) in parallel...\n")
    results = run_batch(list(jobs), settings=settings)

    click.echo("\n" + "=" * 50)
    failures = 0
    for date, result, error in results:
        if result is not None:
            click.echo(f"  {date}: OK — {result.avatar_name} — {result.day_dir}")
            save_run_manifest(result.day_dir, result)
        else:
            failures += 1
            click.echo(f"  {date}: FAILED — {error}")
    click.echo("=" * 50)
    if failures:
        raise click.ClickException(
            f"{failures} job(s) failed. Retry them with: starnews run URL --date DD.MM --resume"
        )


@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def status(config_path: Path | None) -> None:
    """Show avatar rotation, paths, and API key status."""
    settings = load_settings(config_path)
    state = load_state(settings)
    next_key, next_av = next_avatar(settings)

    keys_ok = {
        "GEMINI_API_KEY": bool(settings.gemini_api_key),
        "ELEVENLABS_API_KEY": bool(settings.elevenlabs_api_key),
        "HEYGEN_API_KEY": bool(settings.heygen_api_key),
    }

    click.echo("StarNews pipeline status")
    click.echo("=" * 40)
    click.echo(f"StarTV root:       {settings.startv_root}")
    click.echo(f"State file:        {settings.state_file}")
    click.echo(f"Last avatar:       {state.get('last_avatar') or '(none)'}")
    click.echo(f"Next avatar:       {next_av.display_name} ({next_key})")
    click.echo(f"Next ElevenLabs:   {next_av.elevenlabs_voice_name}")
    click.echo(f"HeyGen mode:       {settings.heygen_mode}")
    click.echo("")
    click.echo("API keys:")
    for name, ok in keys_ok.items():
        click.echo(f"  {name}: {'set' if ok else 'MISSING'}")
    click.echo("")
    click.echo("Avatar setup:")
    for key in settings.avatar_rotation:
        av = settings.avatars[key]
        el_ok = "set" if av.elevenlabs_voice_id else "MISSING"
        avatar_ok = "set" if av.heygen_avatar_id else "(manual mode ok)"
        draft = av.heygen_draft_name or "(set heygen_draft_name in config.yaml)"
        click.echo(
            f"  {av.display_name}: elevenlabs={el_ok}, heygen_draft={draft}"
        )
        if settings.heygen_mode == "auto":
            click.echo(f"    avatar_look={avatar_ok}")


@main.command("heygen-templates")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def heygen_templates(config_path: Path | None) -> None:
    """List HeyGen templates and whether the API can inject a new script."""
    import httpx

    settings = load_settings(config_path)
    if not settings.heygen_api_key:
        raise click.ClickException("HEYGEN_API_KEY is not set in ~/.starnews/.env")

    configured = {
        av.heygen_template_id: av.display_name
        for av in settings.avatars.values()
        if av.heygen_template_id
    }

    headers = {"X-Api-Key": settings.heygen_api_key}
    with httpx.Client(timeout=60) as client:
        response = client.get("https://api.heygen.com/v2/templates", headers=headers)
        response.raise_for_status()
        templates = response.json().get("data", {}).get("templates", [])

        click.echo("HeyGen templates ([USABLE] = has an audio placeholder for ElevenLabs MP3):\n")
        for t in templates[:30]:
            detail = client.get(
                f"https://api.heygen.com/v2/template/{t['template_id']}",
                headers=headers,
            )
            variables = {}
            if detail.status_code == 200:
                variables = (detail.json().get("data") or {}).get("variables") or {}
            has_audio = any(
                isinstance(v, dict) and (v.get("type") or "").lower() == "audio"
                for v in variables.values()
            )
            marker = "USABLE " if has_audio else "no-audio"
            suffix = ""
            if t["template_id"] in configured:
                suffix = f"  ← {configured[t['template_id']]} (configured)"
            click.echo(f"  [{marker}] {t['template_id']}  —  {t.get('name')}{suffix}")

    click.echo(
        "\nFor heygen.mode: auto — [USABLE] templates keep draft look with your ElevenLabs audio."
        "\nManual mode (default) skips the API; upload the MP3 in your HeyGen draft instead."
    )


def _parse_heygen_voices_payload(data: object) -> list[dict]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        voices = data.get("voices")
        if isinstance(voices, list):
            return voices
    return []


def _fetch_heygen_voices(
    client: httpx.Client,
    headers: dict[str, str],
    params: dict[str, str | int],
) -> list[dict]:
    voices: list[dict] = []
    token: str | None = None
    while True:
        query = dict(params)
        if token:
            query["token"] = token
        response = client.get(
            "https://api.heygen.com/v3/voices",
            headers=headers,
            params=query,
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data")
        voices.extend(_parse_heygen_voices_payload(data))
        if isinstance(data, dict) and data.get("has_more") and data.get("next_token"):
            token = data["next_token"]
            continue
        break
    return voices


def _voice_id(voice: dict) -> str:
    return str(voice.get("voice_id") or voice.get("id") or "")


@main.command("heygen-voices")
@click.option(
    "--language",
    default="German",
    show_default=True,
    help="Filter voices by language (e.g. German, English).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def heygen_voices(language: str, config_path: Path | None) -> None:
    """List HeyGen voices (optional — only if you want to override the default look voice)."""
    import httpx

    settings = load_settings(config_path)
    if not settings.heygen_api_key:
        raise click.ClickException("HEYGEN_API_KEY is not set in ~/.starnews/.env")

    headers = {"X-Api-Key": settings.heygen_api_key}
    params: dict[str, str | int] = {"language": language, "limit": 100}
    with httpx.Client(timeout=60) as client:
        voices = _fetch_heygen_voices(client, headers, params)

    click.echo(f"HeyGen voices ({language}) — copy voice_id into ~/.starnews/.env:\n")
    for avatar_key in settings.avatar_rotation:
        av = settings.avatars[avatar_key]
        env_name = f"HEYGEN_VOICE_{avatar_key.upper()}"
        click.echo(f"## {av.display_name} ({env_name})")
        name_hint = av.display_name.lower()
        if avatar_key == "leon":
            matches = [
                v
                for v in voices
                if name_hint in (v.get("name") or "").lower()
                or "leo" in (v.get("name") or "").lower()
                or "odeon" in (v.get("name") or "").lower()
            ]
        elif avatar_key == "tim":
            matches = [
                v
                for v in voices
                if "philip" in (v.get("name") or "").lower()
                or name_hint in (v.get("name") or "").lower()
            ]
        else:
            matches = [
                v
                for v in voices
                if "hans" in (v.get("name") or "").lower()
                or "lorenz" in (v.get("name") or "").lower()
                or name_hint in (v.get("name") or "").lower()
            ]
        if not matches:
            click.echo("  (no name match — pick from full list below)\n")
            continue
        for voice in matches[:5]:
            click.echo(
                f"  {_voice_id(voice)}  —  {voice.get('name')}  ({voice.get('gender')})"
            )
        click.echo("")

    click.echo(f"All {language} voices:")
    for voice in voices:
        click.echo(
            f"  {_voice_id(voice)}  —  {voice.get('name')}  ({voice.get('gender')})"
        )
    click.echo(
        f"\nOptional override only — leave HEYGEN_VOICE_* unset to use each avatar look's voice."
        "\nSet HEYGEN_VOICE_TIM/LEON/CHRIS only if the default sound is wrong."
    )


@main.command("heygen-avatars")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def heygen_avatars(config_path: Path | None) -> None:
    """List HeyGen avatar look IDs for HEYGEN_AVATAR_* env vars."""
    import httpx

    settings = load_settings(config_path)
    if not settings.heygen_api_key:
        raise click.ClickException("HEYGEN_API_KEY is not set in ~/.starnews/.env")

    with httpx.Client(timeout=120) as client:
        response = client.get(
            "https://api.heygen.com/v3/avatars/looks",
            headers={"X-Api-Key": settings.heygen_api_key},
        )
        response.raise_for_status()
        looks = response.json().get("data", [])

    click.echo("HeyGen avatar looks (copy id into ~/.starnews/.env as HEYGEN_AVATAR_*):\n")
    for avatar_key in settings.avatar_rotation:
        av = settings.avatars[avatar_key]
        env_name = f"HEYGEN_AVATAR_{avatar_key.upper()}"
        click.echo(f"## {av.display_name} ({env_name})")
        matches = [
            look
            for look in looks
            if av.display_name.lower() in (look.get("name") or "").lower()
            or avatar_key in (look.get("name") or "").lower()
            or (avatar_key == "leon" and "leo" in (look.get("name") or "").lower())
        ]
        if not matches:
            click.echo("  (no name match — check full list below or HeyGen dashboard)\n")
            continue
        for look in matches[:5]:
            click.echo(
                f"  {look['id']}  —  {look.get('name')}  ({look.get('avatar_type')})"
            )
        click.echo("")

    click.echo("All avatar looks in your account:")
    for look in looks:
        click.echo(
            f"  {look['id']}  —  {look.get('name')}  ({look.get('avatar_type')})"
        )


@main.command()
@click.option(
    "--host",
    default=None,
    help="Bind host (default from config.yaml)",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Bind port (default from config.yaml)",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def web(host: str | None, port: int | None, config_path: Path | None) -> None:
    """Start the local web UI on localhost:8765."""
    from starnews.web.app import create_app

    settings = load_settings(config_path)
    app = create_app(settings)
    bind_host = host or settings.web_host
    bind_port = port or settings.web_port
    click.echo(f"StarNews web UI: http://{bind_host}:{bind_port}")
    app.run(host=bind_host, port=bind_port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
