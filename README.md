# StarTV-Slopautomation

Automation to make my daily work less of a pain. Will probably help future employees cursed with this position.

## StarNews Daily Pipeline

Local Mac automation for StarNews daily production: scrape a Gala.de article, generate script and metadata with Gemini, voice with ElevenLabs, avatar video with HeyGen, and prepare your dated StarTV folder with a copied Premiere project.

## Quick start

### 1. Install

```bash
cd ~/Projects/starnews-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. API keys

Create `~/.starnews/.env` (never commit this file):

```bash
mkdir -p ~/.starnews
cp .env.example ~/.starnews/.env
```

Fill in:

| Variable | Source |
|----------|--------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `ELEVENLABS_API_KEY` | [ElevenLabs](https://elevenlabs.io/) → Profile → API Key |
| `HEYGEN_API_KEY` | [HeyGen](https://app.heygen.com/) → Settings → API |

Optional per-avatar overrides (recommended — copy voice/template IDs from your dashboards):

```env
ELEVENLABS_VOICE_TIM=...
ELEVENLABS_VOICE_LEON=...
ELEVENLABS_VOICE_CHRIS=...
HEYGEN_TEMPLATE_TIM=...
HEYGEN_TEMPLATE_LEON=...
HEYGEN_TEMPLATE_CHRIS=...
```

Voice mapping (automatic from rotation):

| Avatar | ElevenLabs voice |
|--------|------------------|
| Tim | Philip, friendly voice |
| Leon | Odeon |
| Chris | Hans-Peter Lorenz – Modern News Voice |

Avatar rotation state is stored in `~/.starnews/state.json` (Tim → Leon → Chris → Tim).

### 3. Verify setup

```bash
starnews status
```

All API keys and avatar voice/template IDs should show as `set`.

## Daily workflow

### Option A — CLI (recommended)

```bash
starnews run "https://www.gala.de/stars/..." --date 01.07
```

The pipeline:

1. Scrapes the article and downloads candidate images to `assets/`
2. Generates `skript.docx`, `metadata.json`, `metadata.txt` via Gemini
3. Picks the next avatar (Tim/Leon/Chris) and matching ElevenLabs voice
4. Renders voice MP3 and HeyGen 1080p avatar video (10–20 min wait)
5. Copies `Vorlage_Neu Sämi_3.prproj` → `SN_01.07.prproj`
6. Prints a Premiere checklist

Output folder:

```
/Users/samuel/Documents/StarTV/01.07/
  assets/
    article.txt
    ElevenLabs_....mp3
    Tim_01.07_1080p.mp4
    [article images]
  skript.docx
  metadata.json
  metadata.txt
  pipeline.json
  SN_01.07.prproj
```

### Option B — Web UI

```bash
starnews web
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765), paste the Gala.de URL and date, click **Pipeline starten**. Progress updates every few seconds.

### Manual steps in Premiere

1. Open `SN_DD.MM.prproj` from the dated folder
2. Replace the moderator clip with the HeyGen MP4 in `assets/`
3. Swap/add images (Google Images for quality picks)
4. Trim sequence length to match audio
5. Save the project
6. Run **File → Scripts → `starnews_export.jsx`** (from `premiere/` in this repo)

The ExtendScript queues three exports in Adobe Media Encoder:

| Output | Source | Filename |
|--------|--------|----------|
| TV | Sequence `SN_Täglich` (720p, 50fps) | `SN_DD.MM_1.mp4` |
| Social | Sequence `SN_Social` | `SN_DD.MM_SM.mp4` |
| YouTube | Sequence `SN_Täglich` + `StarNews YT.epr` preset | `SN_DD.MM_YT.mp4` |

7. Start exports in Media Encoder
8. Send files to chef via SwissTransfer

## Configuration

Edit `config.yaml` in the project root for paths, sequence names, Gemini model, and ElevenLabs/HeyGen defaults. Environment variables in `~/.starnews/.env` override voice and HeyGen template IDs.

Key paths (defaults):

- StarTV root: `/Users/samuel/Documents/StarTV`
- Premiere template: `Vorlage_Neu Sämi_3.prproj`
- YT preset: `~/Documents/Adobe/Adobe Media Encoder/26.0/Presets/StarNews YT.epr`

## Troubleshooting

### `GEMINI_API_KEY is not set`

Create `~/.starnews/.env` with your keys. Run `starnews status` to confirm.

### `Could not extract enough article text`

Gala.de may have changed layout. Try a different article URL or check the page loads in a browser. Raw HTML is still attempted via trafilatura.

### ElevenLabs / HeyGen voice or template missing

Set `ELEVENLABS_VOICE_TIM` (etc.) and `HEYGEN_TEMPLATE_TIM` (etc.) in `~/.starnews/.env`. Voice IDs are in the ElevenLabs voice library; HeyGen IDs are avatar or template IDs from your HeyGen dashboard.

### HeyGen timeout

Default wait is 30 minutes (`heygen.poll_timeout_seconds` in `config.yaml`). Re-run after checking the HeyGen dashboard if a video completed but the download failed.

### Premiere script cannot find sequences

Open the template project and confirm sequence names are exactly `SN_Täglich` and `SN_Social`. Update `config.yaml` → `premiere` if your names differ.

### YT export fails

Confirm the preset exists at the path in `config.yaml` and matches your Media Encoder version (26.0). Update `YT_PRESET` in `premiere/starnews_export.jsx` if needed.

### Web UI shows "already in progress"

Only one pipeline run at a time. Wait for completion or restart `starnews web`.

## Project layout

```
starnews-pipeline/
  config.yaml
  prompts/gemini_script.txt
  premiere/starnews_export.jsx
  starnews/
    cli.py              # run, web, status
    pipeline.py         # orchestration
    config.py
    rotation.py
    steps/              # scrape, gemini, elevenlabs, heygen, folder prep
    web/                # Flask UI
```

## License

Internal StarNews production tool — not for public distribution.
