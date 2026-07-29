# StarTV-Slopautomation

Daily StarNews pipeline: Gala.de article → Gemini script → ElevenLabs voice → HeyGen video (manual step).

**Repo:** [github.com/x5mii/StarTV-Slopautomation](https://github.com/x5mii/StarTV-Slopautomation)

Works on **macOS** and **Windows** (Python 3.10+).

---

## Easy install (for teammates — no `.env` file)

**You do not need to edit a `.env` file.** Use one of these:

### Option A — Zip folder (easiest, no Python for friends)

1. **You** build once on your Mac or PC:
   ```bash
   # macOS
   ./scripts/build-release.sh
   # Windows (PowerShell)
   .\scripts\build-release.ps1
   ```
2. Copy `config.local.example.yaml` → `config.local.yaml` in the `release/StarNews-*` folder and paste your **team API keys + voice IDs** (same ElevenLabs account for everyone).
3. Zip the folder and send it privately (WhatsApp, Drive, etc.) — **not** via public GitHub.
4. **Friend** unzips and double-clicks:
   - Mac: `Start-StarNews.command`
   - Windows: `Start-StarNews.bat`
5. Browser opens. If setup is missing, they only enter their **output folder** (or you pre-fill it). Then: paste Gala URL → start.

### Option B — One setup file instead of `.env`

```bash
cp config.local.example.yaml config.local.yaml
# edit config.local.yaml (keys + voices in one place)
starnews web
```

Or run the guided wizard:

```bash
starnews setup
starnews web
```

The web UI also shows a **setup page** on first launch if keys are missing.

| Old way | New way |
|---------|---------|
| `~/.starnews/.env` | `config.local.yaml` next to the app (or `~/.starnews/config.local.yaml`) |
| Manual nano/notepad | `starnews setup` or browser form |
| `pip install` + terminal | Zip + double-click launcher |

`.env` still works if you already use it — `config.local.yaml` takes priority.

---

## What it does

| Step | Tool | Automated? |
|------|------|------------|
| Scrape Gala.de article | pipeline | yes |
| Script, title, caption, hashtags | Gemini | yes |
| Moderator voice | ElevenLabs | yes |
| Moderator video (draft look) | HeyGen | manual (default) |

Pictures, Premiere editing, and exports stay manual.

**Avatar rotation:** Tim → Leon → Chris → Annie → repeat.

---

## Requirements

- **Python 3.10 or newer** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- API keys: [Google Gemini](https://aistudio.google.com/apikey), [ElevenLabs](https://elevenlabs.io/), optionally [HeyGen](https://app.heygen.com/)
- Paid API credits on Gemini / ElevenLabs (and HeyGen if using auto mode)

---

## Installation

### macOS

```bash
# 1. Clone
git clone https://github.com/x5mii/StarTV-Slopautomation.git
cd StarTV-Slopautomation

# 2. Install (creates the `starnews` command)
python3 -m pip install -e .

# 3. Config folder + API keys
mkdir -p ~/.starnews
nano ~/.starnews/.env
```

Edit `config.yaml` — set your output folder, e.g.:

```yaml
paths:
  startv_root: /Users/YOURNAME/Documents/StarTV
```

### Windows

Open **PowerShell** or **Command Prompt**:

```powershell
# 1. Clone
git clone https://github.com/x5mii/StarTV-Slopautomation.git
cd StarTV-Slopautomation

# 2. Install (use py if python is not on PATH)
py -m pip install -e .

# 3. Config folder + API keys
mkdir $env:USERPROFILE\.starnews
notepad $env:USERPROFILE\.starnews\.env
```

Edit `config.yaml` — set your output folder, e.g.:

```yaml
paths:
  startv_root: C:/Users/YOURNAME/Documents/StarTV
```

Use forward slashes in YAML paths on Windows (`C:/Users/...`).

### Verify install

```bash
starnews --version
starnews status
```

---

## API keys

**Recommended:** `config.local.yaml` (see `config.local.example.yaml`) — one file, no `.env` syntax.

**Legacy:** `~/.starnews/.env` still supported.

Create a file:

| Method | Path |
|--------|------|
| **Easy (recommended)** | `config.local.yaml` next to the app |
| macOS / Linux legacy | `~/.starnews/.env` |
| Windows legacy | `%USERPROFILE%\.starnews\.env` |

**config.local.yaml** example (fill in your own keys — **never commit this file**):

```yaml
paths:
  startv_root: /Users/YOURNAME/Documents/StarTV

api_keys:
  gemini: your_gemini_key
  elevenlabs: your_elevenlabs_key

elevenlabs_voices:
  tim: your_tim_voice_id
  leon: your_leon_voice_id
  chris: your_chris_voice_id
  annie: your_annie_voice_id
```

**Legacy `.env`** example:

```env
GEMINI_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# One voice ID per avatar (from ElevenLabs → Voices)
ELEVENLABS_VOICE_TIM=your_tim_voice_id
ELEVENLABS_VOICE_LEON=your_leon_voice_id
ELEVENLABS_VOICE_CHRIS=your_chris_voice_id
ELEVENLABS_VOICE_ANNIE=your_annie_voice_id

# Optional — only for heygen.mode: auto in config.yaml
# HEYGEN_API_KEY=...
# HEYGEN_AVATAR_TIM=...
```

Copy avatar names, draft names, and voice labels from `config.yaml` in the repo and adjust for your team.

---

## Configuration (`config.yaml`)

After cloning, edit in the repo folder:

- **`paths.startv_root`** — where daily folders are created (`DD.MM/skript.docx`, `assets/`)
- **`avatars`** — display names, ElevenLabs voice labels, HeyGen draft names
- **`heygen.mode`** — `manual` (recommended) or `auto`

```yaml
heygen:
  mode: manual
```

**Manual** — pipeline saves script + MP3; you upload audio in HeyGen.  
**Auto** — pipeline calls HeyGen API (often wrong framing; not recommended).

---

## Output folder

After a run:

```
StarTV/03.07/
  skript.docx
  assets/
    ElevenLabs_...mp3
    Tim_03.07_1080p.mp4    ← you add this after HeyGen
```

---

## Command reference

All commands support `--config PATH` to use a custom `config.yaml`.

### `starnews setup`

First-time wizard — saves `config.local.yaml` (no `.env` needed).

```bash
starnews setup
```

### `starnews run`

Run the pipeline for one article.

```bash
starnews run "https://www.gala.de/stars/....html" --date 03.07
starnews run "URL" --date 03.07 --resume
```

| Option | Description |
|--------|-------------|
| `URL` | Gala.de article URL (required) |
| `--date DD.MM` | Production date, e.g. `03.07` (required) |
| `--resume` | Reuse cached script and MP3 from a previous run for this date |
| `--config PATH` | Custom config file |

### `starnews batch`

Run up to **7** jobs in parallel (one date each).

```bash
starnews batch \
  -j 03.07 "https://www.gala.de/....html" \
  -j 04.07 "https://www.gala.de/....html"
```

| Option | Description |
|--------|-------------|
| `-j DATE URL` | Repeatable date + URL pair (max 7, unique dates) |
| `--config PATH` | Custom config file |

### `starnews status`

Show API keys, next avatar in rotation, and configured IDs.

```bash
starnews status
```

### `starnews web`

Local web UI to paste URL + date and run the pipeline.

```bash
starnews web
starnews web --port 9000
```

Open http://127.0.0.1:8765 (default port from `config.yaml`).

### `starnews heygen-avatars`

List HeyGen avatar look IDs (for `heygen.mode: auto`).

```bash
starnews heygen-avatars
```

### `starnews heygen-templates`

List templates and whether they accept audio from the API (`[USABLE]`).

```bash
starnews heygen-templates
```

### `starnews heygen-voices`

List HeyGen voices (optional override; not needed for manual mode).

```bash
starnews heygen-voices
starnews heygen-voices --language German
```

### `starnews --version`

```bash
starnews --version
```

---

## Daily workflow

### 1. Run pipeline

```bash
starnews run "https://www.gala.de/stars/....html" --date 29.07
```

### 2. Finish in HeyGen (manual mode)

1. Open [app.heygen.com](https://app.heygen.com)
2. Open today's avatar draft (names in `config.yaml`)
3. **Script** panel → **Upload Audio** → pick the MP3 from `assets/`
4. Generate → save as `{Avatar}_{date}_1080p.mp4` in `assets/`

### 3. Edit & export (manual)

Premiere, pictures, TV/YT/SM exports — unchanged.

---

## Standalone app for teammates (advanced)

There is **no pre-built installer on GitHub** (API keys must stay private). **You** build a folder and zip it for your team:

```bash
# macOS
./scripts/build-release.sh
# Windows
.\scripts\build-release.ps1
```

Output: `release/StarNews-macOS/` or `release/StarNews-Windows/` containing:

- `starnews` / `starnews.exe`
- `config.yaml`
- `Start-StarNews.command` / `Start-StarNews.bat`

Before zipping, add **`config.local.yaml`** with team keys (copy from `config.local.example.yaml`). Friends only change `startv_root` if needed.

Manual PyInstaller (if you prefer):

```bash
pip install pyinstaller
cd StarTV-Slopautomation

# macOS / Linux — add-data uses :
pyinstaller --onefile -n starnews \
  --add-data "config.yaml:." \
  --add-data "prompts:prompts" \
  --add-data "starnews/web/templates:starnews/web/templates" \
  starnews/__main__.py

# Windows — add-data uses ;
pyinstaller --onefile -n starnews ^
  --add-data "config.yaml;." ^
  --add-data "prompts;prompts" ^
  --add-data "starnews/web/templates;starnews/web/templates" ^
  starnews/__main__.py
```

The exe lands in `dist/starnews` (or `dist/starnews.exe`). You still need:

- `config.yaml` beside the binary (or run from the repo folder)
- `%USERPROFILE%\.starnews\.env` (Windows) or `~/.starnews/.env` (Mac)

If imports fail at runtime, use `pip install -e .` instead — that is the supported method.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `'starnews' is not recognized` | Re-run `pip install -e .`; on Windows try `py -m starnews status` |
| `ELEVENLABS_VOICE_* is not set` | Add IDs to `.env`, run `starnews status` |
| `GEMINI_API_KEY is not set` | Add key to `.env` |
| Gemini parse error | Re-run; use `--resume` after script succeeded |
| Gemini 429 | Wait or set `gemini.model: gemini-2.5-flash` in `config.yaml` |
| Wrong HeyGen look (auto mode) | Set `heygen.mode: manual` |

---

## Project layout

```
StarTV-Slopautomation/
  config.yaml          ← paths, avatars, HeyGen mode
  prompts/             ← Gemini prompt template
  starnews/            ← Python package
  pyproject.toml       ← install metadata
```

User data (not in repo):

```
~/.starnews/.env       ← API keys
~/.starnews/state.json ← avatar rotation
~/.starnews/runs/      ← cached scripts for --resume
```
