# StarTV-Slopautomation

Automation to make my daily work less of a pain. Will probably help future employees cursed with this position.

## StarNews Daily Pipeline

Local Mac automation for StarNews daily production: scrape a Gala.de article, generate the script with Gemini, the voice with ElevenLabs, and the moderator video with HeyGen (green background). Pictures and editing/export stay manual.

Output per day — nothing else:

```
/Users/samuel/Documents/StarTV/03.07/
  skript.docx
  assets/
    ElevenLabs_..._Philip_friendly_voice.mp3
    Tim_03.07_1080p.mp4
```

## Quick start

### 1. Install

```bash
cd ~/Projects/starnews-pipeline
python3 -m pip install -e .
```

### 2. API keys and IDs

Create `~/.starnews/.env` (never commit this file):

| Variable | Source |
|----------|--------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `ELEVENLABS_API_KEY` | ElevenLabs → Profile → API Key |
| `HEYGEN_API_KEY` | HeyGen → Settings → API |
| `ELEVENLABS_VOICE_TIM/LEON/CHRIS` | ElevenLabs voice IDs |
| `HEYGEN_AVATAR_TIM/LEON/CHRIS` | run `starnews heygen-avatars` |
| `HEYGEN_TEMPLATE_TIM/LEON/CHRIS` | optional — run `starnews heygen-templates` |

Voice mapping (automatic from rotation Tim → Leon → Chris):

| Avatar | ElevenLabs voice |
|--------|------------------|
| Tim | Philip, friendly voice |
| Leon | Odeon |
| Chris | Hans-Peter Lorenz – Modern News Voice |

Verify with:

```bash
starnews status
```

### 3. Green background

Two ways to get the homogeneous green background:

1. **Without template (default):** the video is rendered with your avatar look on a solid green background (`heygen.background_color` in `config.yaml`, default `#00B140`).
2. **With your HeyGen template:** open the template in HeyGen, mark its **audio element as a variable**, then set `HEYGEN_TEMPLATE_TIM/LEON/CHRIS`. Check which templates are usable with:

```bash
starnews heygen-templates
```

Templates without an audio variable cannot receive the ElevenLabs audio and are skipped automatically (with fallback to the green-background render).

## Daily usage

### One video

```bash
starnews run "https://www.gala.de/stars/..." --date 03.07
```

### Up to 7 in parallel (whole week)

```bash
starnews batch \
  -j 03.07 "https://www.gala.de/....html" \
  -j 04.07 "https://www.gala.de/....html" \
  -j 05.07 "https://www.gala.de/....html"
```

Each date gets the next avatar in rotation automatically (Tim, Leon, Chris, Tim, ...). Failed jobs can be retried individually:

```bash
starnews run "URL" --date 04.07 --resume
```

`--resume` reuses the already-generated script (and voice, if present) so you don't pay for Gemini/ElevenLabs again.

### Web UI (single runs)

```bash
starnews web
```

Open http://127.0.0.1:8765, paste URL + date, start.

## After the pipeline

Everything else is manual by design:

1. Find pictures yourself (Google)
2. Edit in Premiere, replace moderator with the HeyGen MP4
3. Export TV / YT / SM yourself
4. SwissTransfer to chef, then social media

## Troubleshooting

**`... is not set` errors** — check `~/.starnews/.env`; lines must not start with `#`. Run `starnews status`.

**Gemini quota (429)** — free tier limit; wait or switch `gemini.model` in `config.yaml`.

**HeyGen `Insufficient credit`** — top up API credits at app.heygen.com.

**HeyGen timeout while waiting** — the render may still finish; check app.heygen.com and download manually into the day's `assets/` folder, or re-run with `--resume`.

**Script/voice regenerated unexpectedly** — cached run data lives in `~/.starnews/runs/DD.MM.json`; `--resume` uses it.
