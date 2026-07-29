# StarNews Pipeline

StarNews automatisiert: Gala.de → Skript → ElevenLabs Stimme → HeyGen (manuell).

**GitHub:** https://github.com/x5mii/StarTV-Slopautomation

---

# Installieren & starten (für alle im Team)

Du brauchst **einmalig**: Python + Git (Links unten).  
Danach: **einen Befehl kopieren → Terminal einfügen → Enter**.

---

## Windows

### Einmal installieren

1. **`Windows-Taste`** drücken, **`powershell`** tippen, **Enter**
2. **Alles** markieren, kopieren, ins schwarze Fenster **rechtsklicken** (einfügen), **Enter**:

```powershell
git clone -b cursor/starnews-daily-pipeline https://github.com/x5mii/StarTV-Slopautomation.git $HOME\StarTV-Slopautomation; cd $HOME\StarTV-Slopautomation; py -m pip install -e .; py -m starnews web
```

> Geht `py` nicht? Ersetze **beide** `py` durch `python` und nochmal Enter.

3. **Browser** öffnet sich automatisch
4. **Einmal einrichten** (nur beim ersten Mal):
   - Datei **`team-secrets.env`** vom Team-Lead laden **oder** Inhalt einfügen  
     *(bekommst du per WhatsApp/Drive — nicht selbst tippen)*
   - **StarTV Ordner** eintragen, z.B. `C:/Users/DeinName/Documents/StarTV`
   - **Speichern & starten** klicken

### Jeden Tag starten

1. **`Windows-Taste`** → **`powershell`** → **Enter**
2. Kopieren, einfügen, **Enter**:

```powershell
cd $HOME\StarTV-Slopautomation; py -m starnews web
```

3. Gala-URL einfügen → Datum → **Pipeline starten**

---

## Mac

### Einmal installieren

1. **`Spotlight`** (`Cmd + Leertaste`) → **`Terminal`** → **Enter**
2. **Alles** kopieren, einfügen, **Enter**:

```bash
git clone -b cursor/starnews-daily-pipeline https://github.com/x5mii/StarTV-Slopautomation.git ~/StarTV-Slopautomation && cd ~/StarTV-Slopautomation && python3 -m pip install -e . && python3 -m starnews web
```

3. **Browser** öffnet sich
4. **Einmal einrichten** (nur beim ersten Mal):
   - **`team-secrets.env`** laden oder einfügen (vom Team-Lead)
   - **StarTV Ordner**, z.B. `/Users/DeinName/Documents/StarTV`
   - **Speichern & starten**

### Jeden Tag starten

1. **Terminal** öffnen
2. Kopieren, einfügen, **Enter**:

```bash
cd ~/StarTV-Slopautomation && python3 -m starnews web
```

---

## Was du vom Team-Lead brauchst

| Was | Wofür |
|-----|--------|
| **`team-secrets.env`** | API-Keys — **einmal** in der Einrichtung laden (nicht abtippen!) |

---

## Einmalig: Python & Git installieren

Nur nötig, wenn der Befehl oben mit „nicht gefunden“ / „not recognized“ abbricht.

| Programm | Windows | Mac |
|----------|---------|-----|
| **Python** | [python.org/downloads](https://www.python.org/downloads/) — Haken: **Add to PATH** | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | [git-scm.com/download/win](https://git-scm.com/download/win) | Terminal: `xcode-select --install` |

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
4. Video speichern als `{Avatar}_DD.MM_1080p.mp4` im gleichen `assets/` Ordner

---

## Probleme?

| Fehler | Lösung |
|--------|--------|
| `'git' is not recognized` | Git installieren (Tabelle oben) |
| `'py' / 'python3' is not recognized` | Python installieren, Terminal neu öffnen |
| `'starnews' is not recognized` | Ignorieren — immer `py -m starnews web` (Windows) bzw. `python3 -m starnews web` (Mac) nutzen |
| Setup: secrets fehlen | `team-secrets.env` laden oder einfügen |
| Falscher Ordner | `config.local.yaml` im App-Ordner löschen, neu starten |

---

## Für Team-Lead (optional)

**Zip-App ohne Terminal** (Windows-Build auf Windows-PC, Mac-Build auf Mac):

```bash
./scripts/build-release.sh      # Mac → release/StarNews-macOS.zip
.\scripts\build-release.ps1     # Windows → release/StarNews-Windows.zip
```

**Secrets-Datei erstellen:** `cp team-secrets.env.example team-secrets.env` → Keys eintragen → privat verschicken.

**Alle Befehle:**

| Befehl (Windows) | Befehl (Mac) | Beschreibung |
|------------------|--------------|--------------|
| `py -m starnews web` | `python3 -m starnews web` | Browser-Oberfläche |
| `py -m starnews run "URL" --date 29.07` | `python3 -m starnews run "URL" --date 29.07` | Ein Artikel |
| `py -m starnews status` | `python3 -m starnews status` | Einstellungen prüfen |
