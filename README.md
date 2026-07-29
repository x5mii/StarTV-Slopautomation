# StarTV-Slopautomation

Daily StarNews pipeline: Gala.de → Gemini script → ElevenLabs voice → HeyGen video (manual step).

**Repo:** [github.com/x5mii/StarTV-Slopautomation](https://github.com/x5mii/StarTV-Slopautomation)

> **Note:** Install instructions below are on the `cursor/starnews-daily-pipeline` branch. Merge to `main` or download the latest branch zip if GitHub `main` README looks outdated.

---

## For coworkers — install (Mac & Windows)

No Python, Git, or manual typing of API keys.

### What you need from your team lead

1. **`StarNews-macOS.zip`** or **`StarNews-Windows.zip`**
2. **`team-secrets.env`** — one file with all API keys (sent privately, e.g. WhatsApp/Drive)

### macOS

1. Unzip **`StarNews-macOS.zip`**
2. Double-click **`Start-StarNews.command`**
3. Browser opens → **Setup**:
   - **Load** `team-secrets.env` (or paste its content)
   - Enter your **StarTV folder**, e.g. `/Users/YourName/Documents/StarTV`
   - Click **Speichern & starten**
4. Paste a Gala.de URL → **Pipeline starten**

### Windows

1. Unzip **`StarNews-Windows.zip`**
2. Double-click **`Start-StarNews.bat`**
   - If Windows SmartScreen appears: **More info → Run anyway**
3. Browser opens → **Setup**:
   - **Load** `team-secrets.env` (or paste its content)
   - Enter your **StarTV folder**, e.g. `C:/Users/YourName/Documents/StarTV`
   - Use **forward slashes** in the path
   - Click **Speichern & starten**
4. Paste a Gala.de URL → **Pipeline starten**

Settings are saved locally in `config.local.yaml` next to the app — you only do this once.

---

## For team lead — build & share

Build on **macOS** for Mac coworkers, on **Windows** for Windows coworkers.

### 1. Prepare secrets (one-time)

```bash
cp team-secrets.env.example team-secrets.env
# Fill in real API keys in team-secrets.env
```

Send **`team-secrets.env`** privately to each coworker. Do **not** commit the filled file to GitHub (secret scanning blocks it).

Optional for builds with keys baked in:

```bash
cp starnews/team_defaults.example.yaml starnews/team_defaults.yaml
# Same keys as team-secrets.env — then coworkers only pick their folder
```

### 2. Build the app

**macOS:**

```bash
chmod +x scripts/build-release.sh scripts/Start-StarNews.command
./scripts/build-release.sh
```

**Windows (PowerShell):**

```powershell
.\scripts\build-release.ps1
```

Output:

| Platform | Folder | Zip |
|----------|--------|-----|
| macOS | `release/StarNews-macOS/` | `release/StarNews-macOS.zip` |
| Windows | `release/StarNews-Windows/` | `release/StarNews-Windows.zip` |

Share the **zip + team-secrets.env** with coworkers.

---

## Voice mapping

| Avatar | ElevenLabs voice | HeyGen draft |
|--------|------------------|--------------|
| Tim | Philip, friendly voice | Tim 02.07 |
| Leon | Odeon | Leo 30.06 |
| Chris | Hans-Peter Lorenz – Modern News Voice | Chris_01.07 |
| Annie | Emilia Roth | Annie_29.08 |

Rotation: **Tim → Leon → Chris → Annie → repeat**

---

## What it does

| Step | Tool | Automated? |
|------|------|------------|
| Scrape Gala.de | pipeline | yes |
| Script, title, caption, hashtags | Gemini | yes |
| Moderator voice | ElevenLabs | yes |
| Moderator video | HeyGen | manual (default) |

Pictures, Premiere, and exports stay manual.

**Output per day:**

```
StarTV/29.07/
  skript.docx
  assets/
    ElevenLabs_....mp3
    Tim_29.07_1080p.mp4    ← add after HeyGen
```

---

## Commands

| Command | Description |
|---------|-------------|
| `starnews web` | Browser UI (recommended) |
| `starnews setup` | CLI setup — import secrets + folder |
| `starnews import-secrets team-secrets.env --folder C:/Users/You/Documents/StarTV` | Import .env file |
| `starnews run URL --date DD.MM` | Run one article |
| `starnews batch -j DATE URL ...` | Up to 7 parallel |
| `starnews status` | Check config |

---

## Developer install (optional)

```bash
git clone https://github.com/x5mii/StarTV-Slopautomation.git
cd StarTV-Slopautomation
git checkout cursor/starnews-daily-pipeline   # latest install flow
python3 -m pip install -e .                   # Mac
# py -m pip install -e .                      # Windows

cp team-secrets.env.example team-secrets.env  # add keys
starnews import-secrets team-secrets.env --folder ~/Documents/StarTV
starnews web
```

Legacy: `~/.starnews/.env` still works and overrides team defaults.

---

## Daily workflow

1. **Run pipeline** — web UI or `starnews run "URL" --date 29.07`
2. **HeyGen (manual)** — upload MP3 from `assets/` into today's avatar draft → save MP4 as `{Avatar}_{date}_1080p.mp4`
3. **Premiere / export** — unchanged

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| README on GitHub looks old | Use branch `cursor/starnews-daily-pipeline` or merge it to `main` |
| Windows blocks `.bat` | More info → Run anyway |
| `Setup incomplete: secrets` | Load or paste `team-secrets.env` |
| Wrong output folder | Delete `config.local.yaml` and run setup again |
| `'starnews' is not recognized` | Use the zip build, or re-run `pip install -e .` |

---

## Project layout

```
StarTV-Slopautomation/
  config.yaml
  team-secrets.env.example    ← template for team lead
  starnews/team_defaults.example.yaml
  scripts/build-release.sh    ← Mac build
  scripts/build-release.ps1   ← Windows build
  scripts/Start-StarNews.command
  scripts/Start-StarNews.bat
```

Local (not in git): `team-secrets.env`, `config.local.yaml`, `starnews/team_defaults.yaml`
