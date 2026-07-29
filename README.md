# StarNews Pipeline

StarNews automatisiert: Gala.de → Skript → ElevenLabs Stimme → HeyGen (manuell).

**GitHub:** https://github.com/x5mii/StarTV-Slopautomation

---

# Windows — so geht’s

## 1. Einmal installieren

1. **Windows-Taste** → `powershell` tippen → **Enter**
2. Diesen Text **komplett** kopieren und einfügen (Rechtsklick), dann **Enter**:

```powershell
git clone -b cursor/starnews-daily-pipeline https://github.com/x5mii/StarTV-Slopautomation.git $HOME\StarTV-Slopautomation; cd $HOME\StarTV-Slopautomation; py -m pip install -e .
```

> Wenn `py` nicht geht: `python` statt `py` schreiben.

3. Warte bis `Successfully installed` erscheint.  
   Eine gelbe Meldung `not on PATH` ist **egal** — einfach ignorieren.

## 2. Jeden Tag starten (ohne Tippen)

1. Öffne den Ordner: `C:\Users\DEINNAME\StarTV-Slopautomation`
2. **Doppelklick** auf **`Start.bat`**
3. Browser öffnet sich → fertig

### Oder in PowerShell (wenn du lieber tippst)

**WICHTIG:** Schreibe **genau** das hier — **nicht** nur `starnews`:

```powershell
cd $HOME\StarTV-Slopautomation; py -m starnews web
```

Falsch ❌ `starnews web`  
Richtig ✅ `py -m starnews web`

## 3. Erste Einrichtung (nur 1×)

Im Browser:

1. **`team-secrets.env`** vom Team-Lead laden
2. StarTV-Ordner eintragen, z.B. `C:/Users/DeinName/Documents/StarTV`
3. **Speichern & starten**

---

# Mac — so geht’s

## 1. Einmal installieren

Terminal öffnen, dann:

```bash
git clone -b cursor/starnews-daily-pipeline https://github.com/x5mii/StarTV-Slopautomation.git ~/StarTV-Slopautomation && cd ~/StarTV-Slopautomation && python3 -m pip install -e .
```

## 2. Jeden Tag starten

```bash
cd ~/StarTV-Slopautomation && python3 -m starnews web
```

Oder Doppelklick auf **`Start.command`** im Ordner `StarTV-Slopautomation`.

---

## Was du vom Team-Lead brauchst

| Was | Wofür |
|-----|--------|
| **`team-secrets.env`** | Einmal in der Browser-Einrichtung laden |

---

## Python & Git (nur wenn der Install-Befehl scheitert)

| Programm | Windows | Mac |
|----------|---------|-----|
| **Python** | [python.org/downloads](https://www.python.org/downloads/) — Haken: **Add to PATH** | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | [git-scm.com/download/win](https://git-scm.com/download/win) | `xcode-select --install` |

---

## Stimmen & Avatare

| Avatar | ElevenLabs Stimme | HeyGen Draft |
|--------|-------------------|--------------|
| Tim | Philip, friendly voice | Tim 02.07 |
| Leon | Odeon | Leo 30.06 |
| Chris | Hans-Peter Lorenz | Chris_01.07 |
| Annie | Emilia Roth | Annie_29.08 |

Rotation: Tim → Leon → Chris → Annie → …

---

## Nach dem Pipeline-Lauf (HeyGen)

1. [app.heygen.com](https://app.heygen.com) öffnen
2. Draft für heutigen Avatar öffnen
3. **Upload Audio** → MP3 aus `StarTV/DD.MM/assets/`
4. Speichern als `{Avatar}_DD.MM_1080p.mp4` in `assets/`

---

## Probleme?

| Fehler | Lösung |
|--------|--------|
| `starnews is not recognized` | **Nicht** `starnews` tippen. Nutze `Start.bat` **oder** `py -m starnews web` |
| `Scripts which is not on PATH` | Ignorieren |
| `py` / `python` nicht gefunden | Python installieren, PowerShell **schließen und neu öffnen** |
| `git` nicht gefunden | Git installieren |
| Secrets fehlen | `team-secrets.env` laden |

---

## Team-Lead

```bash
./scripts/build-release.sh      # Mac-Zip
.\scripts\build-release.ps1     # Windows-Zip
```

Secrets: `team-secrets.env.example` → `team-secrets.env` → privat verschicken.
