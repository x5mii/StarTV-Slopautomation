from __future__ import annotations

from pathlib import Path

import click

from starnews.config import load_settings
from starnews.pipeline import get_run_state, run_pipeline, run_pipeline_tracked, save_run_manifest
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
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Optional path to config.yaml",
)
def run(url: str, date: str, config_path: Path | None) -> None:
    """Run the full pipeline for a Gala.de URL."""
    settings = load_settings(config_path)
    try:
        result = run_pipeline(url, date, settings=settings)
        save_run_manifest(result.day_dir, result)
        click.echo(f"\nDone. Output folder: {result.day_dir}")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


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
    click.echo(f"Premiere template: {settings.premiere_template}")
    click.echo(f"YT export preset:  {settings.export_preset_yt}")
    click.echo(f"State file:        {settings.state_file}")
    click.echo(f"Last avatar:       {state.get('last_avatar') or '(none)'}")
    click.echo(f"Next avatar:       {next_av.display_name} ({next_key})")
    click.echo(f"Next voice:        {next_av.elevenlabs_voice_name}")
    click.echo("")
    click.echo("API keys:")
    for name, ok in keys_ok.items():
        click.echo(f"  {name}: {'set' if ok else 'MISSING'}")
    click.echo("")
    click.echo("Avatar voice/template IDs:")
    for key in settings.avatar_rotation:
        av = settings.avatars[key]
        voice_ok = "set" if av.elevenlabs_voice_id else "MISSING"
        template_ok = "set" if av.heygen_template_id else "MISSING"
        click.echo(
            f"  {av.display_name}: voice={voice_ok}, heygen={template_ok}"
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
