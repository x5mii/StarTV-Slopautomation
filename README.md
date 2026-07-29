# StarTV-Slopautomation

Daily StarNews pipeline: Gala.de article → Gemini script → ElevenLabs voice → HeyGen video (manual step).

**Repo:** [github.com/x5mii/StarTV-Slopautomation](https://github.com/x5mii/StarTV-Slopautomation)

Works on **macOS** and **Windows** (Python 3.10+).

---

## Install for coworkers (recommended)

API keys and voice IDs are **built into the app**. Each person only picks their **output folder** once on first launch.

### macOS

1. Download **`StarNews-macOS.zip`** from your team lead (or build it: `./scripts/build-release.sh`).
2. Unzip the folder.
3. Double-click **`Start-StarNews.command`**.
4. Browser opens → enter your StarTV folder, e.g. `/Users/YourName/Documents/StarTV`.
5. Paste a Gala.de URL, pick the date, click **Pipeline starten**.

### Windows

1. Download **`StarNews-Windows.zip`** from your team lead (or build it: `.\scripts\build-release.ps1`).
2. Unzip the folder.
3. Double-click **`Start-StarNews.bat`**.
4. Browser opens → enter your StarTV folder, e.g. `C:/Users/YourName/Documents/StarTV`.
5. Paste a Gala.de URL, pick the date, click **Pipeline starten**.

No Python, Git, or `.env` file needed.

---

## Build the zip (team lead)

From the repo on **macOS** (builds the Mac app) or **Windows** (builds the Windows app):

```bash
# macOS
chmod +x scripts/build-release.sh scripts/Start-StarNews.command
./scripts/build-release.sh

# Windows (PowerShell)
.\scripts\build-release.ps1
```

Output: `release/StarNews-macOS/` or `release/StarNews-Windows/` — zip that folder and share it.

---

## Voice mapping

| Avatar | ElevenLabs voice | HeyGen draft (`config.yaml`) |
|--------|------------------|------------------------------|
| Tim | Philip, friendly voice | Tim 02.07 |
| Leon | Odeon | Leo 30.06 |
| Chris | Hans-Peter Lorenz – Modern News Voice | Chris_01.07 |
| Annie | Emilia Roth | Annie_29.08 |

Rotation: Tim → Leon → Chris → Annie → repeat.

---

## Developer install (optional)

If you work on the code itself:

## What it does

| Step | Tool | Automated? |
|------|------|------------|
| Scrape Gala.de article | pipeline | yes |
| Script, title, caption, hashtags | Gemini | yes |
| Moderator voice | ElevenLabs | yes |
| Moderator video (draft look) | HeyGen | manual (default) |

Pictures, Premiere editing, and exports stay manual.

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

**Coworkers:** keys are in `starnews/team_defaults.yaml` (built into the app). Nothing to configure.

**Per user:** only `config.local.yaml` with the output folder (created automatically on first launch).

**Legacy dev option:** `~/.starnews/.env` still works and overrides team defaults.

**config.local.yaml** (auto-created — only the folder matters):

```yaml
paths:
  startv_root: /Users/YOURNAME/Documents/StarTV
```

**Legacy `.env`** (developers only):

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

Choose the StarTV output folder (API keys are built in).

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

## Standalone app bundle

Build on the target OS, then zip `release/StarNews-*` for coworkers:

```bash
./scripts/build-release.sh      # macOS
.\scripts\build-release.ps1     # Windows
```

Contains `starnews`, `Start-StarNews` launcher, and built-in team keys. Coworkers only set their output folder on first run.

Manual PyInstaller:

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
