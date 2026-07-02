# StarTV-Slopautomation

Automation for daily StarNews production on Mac.

## What it does

| Step | Tool | Automated? |
|------|------|------------|
| Scrape Gala.de article | pipeline | yes |
| Script, title, caption, hashtags | Gemini | yes |
| Moderator voice (Philip / Odeon / Hans-Peter) | ElevenLabs | yes |
| Moderator video (draft look + lip-sync) | HeyGen | **manual** (default) or optional API |

Pictures, Premiere editing, and exports stay manual.

## Output folder

After `starnews run`, you get:

```
/Users/samuel/Documents/StarTV/03.07/
  skript.docx
  assets/
    ElevenLabs_2026_07_02T..._Philip_friendly_voice.mp3
    Tim_03.07_1080p.mp4          ← you add this after HeyGen
```

## Setup

### 1. Install

```bash
cd ~/Projects/starnews-pipeline
python3 -m pip install -e .
```

### 2. API keys

Create `~/.starnews/.env` (never commit):

```env
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...

ELEVENLABS_VOICE_TIM=m0jFDzIcZy0rC88oAehX      # Philip, friendly voice
ELEVENLABS_VOICE_LEON=XJ6WvkWn5AiImouUWf8S      # Odeon
ELEVENLABS_VOICE_CHRIS=MLFHn2hZ3zKifXrugl26    # Hans-Peter Lorenz

# Only needed for heygen.mode: auto (not recommended):
# HEYGEN_API_KEY=...
# HEYGEN_AVATAR_TIM=...
# HEYGEN_AVATAR_LEON=...
# HEYGEN_AVATAR_CHRIS=...
```

Check:

```bash
starnews status
```

### 3. HeyGen mode

In `config.yaml`:

```yaml
heygen:
  mode: manual   # recommended
```

**Manual (default)** — pipeline stops after ElevenLabs. You finish the video in HeyGen (correct draft look + voice).

**Auto** — pipeline calls HeyGen API with your MP3. Often wrong outfit/framing; use only if you accept that trade-off.

## Daily workflow

### Run the pipeline

```bash
starnews run "https://www.gala.de/stars/....html" --date 03.07
```

Avatar rotation is automatic: Tim → Leon → Chris → repeat.

```bash
starnews run "URL" --date 03.07 --resume    # reuse script + MP3
starnews batch -j 03.07 URL1 -j 04.07 URL2   # up to 7 parallel
starnews web                                 # http://127.0.0.1:8765
```

### Finish in HeyGen (manual mode)

The pipeline prints which avatar and MP3 to use. Steps:

1. Open [app.heygen.com](https://app.heygen.com)
2. Open **your draft** for today's avatar:

   | Avatar | Draft name (in `config.yaml`) |
   |--------|-------------------------------|
   | Tim | Tim 02.07 |
   | Leon | Leo 30.06 |
   | Chris | Chris_01.07 |

3. In the **Script** panel, choose **Upload Audio** (not typed script)
4. Select the ElevenLabs MP3 from that day's `assets/` folder
5. Click **Generate** / **Submit**
6. Download the MP4 and save as `{Avatar}_{date}_1080p.mp4` in the same `assets/` folder  
   Example: `Tim_03.07_1080p.mp4`

This matches your old workflow: draft look, ElevenLabs voice, green background.

### After that (manual)

1. Find pictures (Google)
2. Edit in Premiere — replace moderator clip with the HeyGen MP4
3. Export TV / YT / SM
4. SwissTransfer + social posts

## Troubleshooting

**`ELEVENLABS_VOICE_* is not set`** — uncomment lines in `~/.starnews/.env`, run `starnews status`.

**Gemini parse error** — re-run the same command; the pipeline retries with stricter formatting. Use `--resume` after a successful script to avoid paying twice.

**Gemini 429** — wait or set `gemini.model: gemini-2.5-flash` in `config.yaml`.

**HeyGen auto mode looks wrong** — set `heygen.mode: manual` and use the steps above.

**Helper commands**

```bash
starnews status
starnews heygen-avatars    # look IDs for auto mode
starnews heygen-templates  # templates with audio placeholders for auto mode
starnews heygen-voices     # optional voice override list
```
