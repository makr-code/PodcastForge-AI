# PodcastForge GUI Editor - Vollständige Anleitung

**Version:** 2.0  
**Stand:** 2025-11-17  
**Implementation:** 2,522 LOC (vollständig implementiert)

---

## 🎨 Features

### ✅ Implementierte Haupt-Features
- **Professioneller Text-Editor** mit Echtzeit-Syntax-Highlighting
- **Voice Library Integration** mit 40+ professionellen Stimmen
- **Drag & Drop Voice Assignment** - Stimmen per Drag & Drop zuweisen
- **Draft-System** - Entwürfe speichern, laden und verwalten
- **Sprecher-Management** mit visueller Verwaltung (Add/Edit/Remove)
- **Echtzeit-TTS-Vorschau** (F5/F6) für einzelne Zeilen oder komplette Skripte
- **Multi-Format-Support**: Structured Text, YAML, JSON
- **Audio-Player** mit Playback-Controls
- **Line Properties Panel** - Emotion, Pause, Speed pro Zeile
- **Context-Menüs** - Rechtsklick-Optionen für erweiterte Funktionen
- **Undo/Redo** - Vollständige Bearbeitungshistorie
- **Zeilennummerierung** - Automatisch aktualisiert
- **Cursor-Position-Tracking** - Zeile und Spalte in Statusbar
- **Project Info** - Live-Statistiken (Zeilen, Sprecher, geschätzte Dauer)
- **Theme-Support** - Anpassbares UI-Theme
- **Keyboard-Shortcuts** - Umfassende Tastenbedienung

### 🎯 Editor-Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Menü: Datei | Bearbeiten | TTS | Ansicht | Hilfe            │
├─────────────────────────────────────────────────────────────┤
│ Toolbar: [Neu] [Öffnen] [Speichern] | [Play] [Stop] [Export]│
├──────────┬──────────────────────────────┬───────────────────┤
│ Sprecher │    Skript-Editor             │ Eigenschaften     │
│          │                              │                   │
│ • Host   │ Host [excited]: Hallo!       │ Sprecher: [Host▼] │
│ • Gast   │ Gast [neutral]: Danke!       │ Emotion: [neutral]│
│          │                              │ Pause: [0.5s]     │
│ ──────── │ # Kommentar...               │ Speed: [1.0x]     │
│          │                              │                   │
│ Voices   │ Host [thoughtful]: Hmm...    │ [✓ Übernehmen]    │
│          │                              │                   │
│ 🔍 Filter│                              │ ─────────────────│
│ Lang: de │                              │ Audio-Vorschau    │
│ Stil: 🔽 │                              │ [▶] [⏸] 🔉─────   │
│          │                              │                   │
│ • Thorsten│                             │ [Wellenform]      │
│ • David A│                              │                   │
│ • Morgan │                              │ ℹ️ Info           │
│          │                              │ Zeilen: 12        │
│          │                              │ Sprecher: 2       │
│          │                              │ Dauer: ~3:45      │
└──────────┴──────────────────────────────┴───────────────────┘
│ Status: Bereit                           │ Zeile: 1, Sp: 0  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Verwendung

### Start
```bash
# Mit Python
python run_editor.py

# Oder via CLI
podcastforge edit
```

### Skript-Formate

#### 1. **Structured Format** (Einfach & Lesbar)
```
Host [excited]: Willkommen zu unserem Podcast! [0.8s]
Gast [neutral]: Vielen Dank für die Einladung! [0.5s]

Host [thoughtful]: Heute sprechen wir über KI... [0.6s]
Gast [enthusiastic]: Ein faszinierendes Thema! [0.4s]

# Kommentare beginnen mit #
```

**Format:**
```
SpreicherName [Emotion]: Text hier [Pause in Sekunden]
```

**Verfügbare Emotionen:**
- `neutral` - Standard
- `excited` - Begeistert
- `thoughtful` - Nachdenklich
- `serious` - Ernst
- `humorous` - Humorvoll
- `dramatic` - Dramatisch

#### 2. **YAML Format** (Strukturiert)
```yaml
title: Mein Podcast
style: interview
language: de

speakers:
  - name: Host
    voice: professional_male
    description: Moderator
  - name: Gast
    voice: professional_female
    description: Expertin

script:
  - speaker: Host
    text: Willkommen zu unserem Podcast!
    emotion: excited
    pause_after: 0.8
    speed: 1.0
    
  - speaker: Gast
    text: Vielen Dank für die Einladung!
    emotion: neutral
    pause_after: 0.5
```

#### 3. **JSON Format** (Programmatisch)
```json
{
  "title": "Mein Podcast",
  "style": "interview",
  "language": "de",
  "speakers": [
    {
      "name": "Host",
      "voice": "professional_male",
      "description": "Moderator"
    }
  ],
  "script": [
    {
      "speaker": "Host",
      "text": "Willkommen!",
      "emotion": "excited",
      "pause_after": 0.8
    }
  ]
}
```

## 📋 Erweiterte Features

### Draft-System (Entwurfsverwaltung)
**NEU in v1.0** - Vollständig implementiert

Das Draft-System ermöglicht das Speichern und Verwalten mehrerer Entwürfe innerhalb eines Projekts:

**Features:**
- Entwürfe speichern und laden
- Mehrere Entwürfe pro Projekt
- Doppelklick zum Laden
- Entwürfe importieren/exportieren

**Verwendung:**
1. Schreibe Text im Editor
2. Klicke "Save Draft" im Draft-Panel
3. Entwurf erscheint in der Liste
4. Doppelklick auf Entwurf zum Laden

**Shortcuts:**
- `Ctrl+Shift+D` - Draft speichern
- Doppelklick auf Draft - Draft laden

### Drag & Drop Voice Assignment
**NEU in v1.0** - Vollständig implementiert

Weise Stimmen per Drag & Drop zu:

**Verwendung:**
1. Wähle Stimme in Voice Library (linkes Panel)
2. Klicke und halte die Maus
3. Ziehe auf Editor-Zeile
4. Loslassen = Stimme wird zugewiesen

**Visual Feedback:**
- Drag: Cursor ändert sich
- Drop-Zone: Zeile wird hervorgehoben
- Success: Bestätigung in Statusbar

### Context-Menüs (Rechtsklick)
**NEU in v1.0** - Vollständig implementiert

**Editor-Context-Menü:**
- Rechtsklick im Editor zeigt:
  - Zeile vorhören (F5)
  - Zeile bearbeiten
  - Zeile löschen
  - Sprecher zuweisen
  - Eigenschaften öffnen

**Voice Library Context-Menü:**
- Rechtsklick auf Stimme zeigt:
  - Als Sprecher verwenden
  - Vorschau abspielen
  - Details anzeigen

**Sprecher-Context-Menü:**
- Rechtsklick auf Sprecher zeigt:
  - Bearbeiten
  - Löschen
  - Alle Zeilen anzeigen

### Line Properties (Zeileneigenschaften)
**Vollständig implementiert**

Jede Zeile hat individuell einstellbare Eigenschaften:

**Eigenschaften:**
- **Sprecher:** Dropdown-Auswahl
- **Emotion:** neutral, excited, thoughtful, serious, humorous, dramatic
- **Pause:** 0.0s - 5.0s (Schieberegler)
- **Speed:** 0.5x - 2.0x (Geschwindigkeit)

**Presets:**
- "Normal" - Standard-Einstellungen
- "Excited" - Schnell, begeistert
- "Thoughtful" - Langsam, nachdenklich
- "Dramatic" - Mit Pausen, dramatisch

**Verwendung:**
1. Zeile im Editor markieren
2. Eigenschaften im rechten Panel anpassen
3. "✓ Übernehmen" klicken
4. Änderungen werden sofort gespeichert

### Zeilennummerierung & Navigation
**Vollständig implementiert**

- Automatische Zeilennummerierung (links vom Editor)
- Aktualisiert sich bei jeder Änderung
- Cursor-Position in Statusbar (Zeile:Spalte)
- Schnellnavigation: `Ctrl+G` → Zeile eingeben

### Project Info Widget
**Live-Statistiken**

Rechtes Panel zeigt:
- **Zeilen:** Anzahl Dialogzeilen
- **Sprecher:** Anzahl verwendeter Sprecher
- **Dauer:** Geschätzte Gesamtlänge

Aktualisiert sich automatisch bei Änderungen.

## 🖥️ Benutzeroberfläche im Detail

### 1. Neues Projekt erstellen
1. `Datei` → `Neu` (oder `Ctrl+N`)
2. Wähle Format (Structured/YAML/JSON)
3. Standard-Sprecher werden automatisch erstellt

### 2. Sprecher hinzufügen
1. Klicke `➕ Hinzufügen` im Sprecher-Panel
2. Gib Name und Beschreibung ein
3. Wähle Stimme:
   - **Aus Voice Library**: 40+ professionelle Stimmen
   - **Eigene Datei**: Lade .wav/.mp3
   - **Custom Voice**: Nutze Voice Cloning

### 3. Skript schreiben
1. Schreibe im Editor (mit Auto-Completion)
2. Nutze Syntax-Highlighting zur Orientierung
3. Zeilen-Eigenschaften im rechten Panel anpassen

### 4. Vorschau & Verfeinerung
1. Markiere Zeile → `F5` für Vorschau
2. Höre Ergebnis im Audio-Player
3. Passe Emotion, Pause, Speed an
4. Klicke `✓ Übernehmen`

### 5. Export
1. `Datei` → `Exportieren` (oder `Ctrl+E`)
2. Wähle Format (MP3/WAV/OGG)
3. Warte auf Generierung
4. Fertig! 🎉

## ⌨️ Vollständige Tastatur-Shortcuts

### Datei-Operationen
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+N` | Neues Projekt | Erstellt leeres Projekt mit Template |
| `Ctrl+O` | Projekt öffnen | Öffnet Datei-Dialog |
| `Ctrl+S` | Speichern | Speichert aktuelles Projekt |
| `Ctrl+Shift+S` | Speichern als | Speichert unter neuem Namen |
| `Ctrl+E` | Export zu Audio | Startet Audio-Generierung |
| `Ctrl+Q` | Beenden | Schließt Editor (mit Bestätigung) |

### Editor-Befehle
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+Z` | Rückgängig | Undo letzte Änderung |
| `Ctrl+Y` | Wiederholen | Redo rückgängig gemachte Änderung |
| `Ctrl+Enter` | Neue Zeile einfügen | Fügt leere Zeile nach Cursor ein |
| `Ctrl+D` | Zeile löschen | Löscht aktuelle Zeile |
| `Ctrl+G` | Gehe zu Zeile | Öffnet Zeilen-Navigator |
| `Ctrl+F` | Suchen | Textsuche (falls implementiert) |
| `Ctrl+H` | Ersetzen | Suchen & Ersetzen (falls implementiert) |

### Sprecher-Verwaltung
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+Shift+A` | Sprecher hinzufügen | Öffnet Sprecher-Dialog |
| `Ctrl+Shift+E` | Sprecher bearbeiten | Bearbeitet ausgewählten Sprecher |
| `Ctrl+Shift+R` | Sprecher entfernen | Löscht Sprecher (mit Bestätigung) |

### TTS & Audio
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `F5` | Aktuelle Zeile vorhören | TTS-Preview für markierte Zeile |
| `F6` | Komplettes Skript vorhören | Preview aller Zeilen nacheinander |
| `F8` | Audio stoppen | Stoppt aktuellen Playback |
| `Space` | Play/Pause | Play/Pause bei Audio-Playback (wenn aktiv) |

### Draft-System
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+Shift+D` | Draft speichern | Speichert aktuellen Editor-Inhalt als Draft |
| Doppelklick | Draft laden | Lädt Draft in Editor |

### Ansicht
| Shortcut | Aktion | Beschreibung |
|----------|--------|--------------|
| `Ctrl+T` | Timeline toggle | Zeigt/verbirgt Timeline (falls verfügbar) |
| `Ctrl+L` | Voice Library toggle | Zeigt/verbirgt Voice Library Panel |
| `F11` | Vollbild | Vollbild-Modus toggle |

## 🎨 Voice Library

### Integrierte Stimmen

**Deutsch:**
- Thorsten (Professional Male)

**Englisch:**
- David Attenborough (Documentary, Elder)
- Morgan Freeman (Authoritative)
- Neil Gaiman (Storytelling)
- Rosamund Pike (Dramatic, Female)
- Scarlett Johansson (Professional, Female)
- Bob Ross (Calm, Relaxed)
- Ray Porter (Professional Narrator)
- ... und viele mehr!

### Voice verwenden
1. Öffne Voice Library Panel (links unten)
2. Filtere nach Sprache/Stil
3. Wähle Stimme
4. Klicke "Als Sprecher verwenden"
5. Stimme wird automatisch als Sprecher hinzugefügt

### Custom Voices
- Nutze eigene .wav/.mp3 Dateien
- Voice Cloning Feature (geplant)
- Voice Extraction aus Videos (geplant)

## 🎯 Best Practices

### Natürliche Dialoge
```
# ❌ Schlecht
Host: Hallo
Gast: Hallo

# ✅ Besser
Host [excited]: Hallo und herzlich willkommen! [0.8s]
Gast [friendly]: Hallo! Schön, hier zu sein. [0.6s]

Host [thoughtful]: Heute sprechen wir über... [0.5s]
```

### Pausen richtig setzen
- **0.3-0.5s**: Normale Satzpausen
- **0.6-0.8s**: Nach Fragen
- **0.8-1.2s**: Themenwechsel
- **1.5-2.0s**: Szenenwechsel

### Emotionen variieren
```
Host [excited]: Unglaublich! [0.4s]
Host [thoughtful]: Aber wie funktioniert das genau? [0.7s]
Gast [serious]: Das ist kompliziert... [0.6s]
Gast [enthusiastic]: Aber ich erkläre es gerne! [0.5s]
```

### Sprecher-Vielfalt
- Nutze unterschiedliche Stimmen (Geschlecht, Alter, Stil)
- Achte auf passende Charakterisierung
- Teste Stimmen in Vorschau

## 🔧 Technische Details & Architektur

### Editor-Architektur (2,522 LOC)

```python
PodcastEditor (Hauptklasse)
├── __init__() - Initialisierung
├── setup_theme() - UI-Theme konfigurieren
├── setup_menu() - Menüleiste erstellen
├── setup_toolbar() - Toolbar mit Buttons
├── setup_main_layout() - 3-Panel-Layout (PanedWindow)
│
├── Left Panel (Sprecher & Voices)
│   ├── setup_left_panel()
│   ├── Speakers Listbox (Verwaltung)
│   │   ├── add_speaker() - Sprecher hinzufügen
│   │   ├── edit_speaker() - Sprecher bearbeiten
│   │   ├── remove_speaker() - Sprecher löschen
│   │   └── update_speakers_list() - Liste aktualisieren
│   └── Voice Library Listbox
│       ├── update_voice_list() - Filter anwenden
│       ├── use_voice_as_speaker() - Stimme als Sprecher
│       ├── show_voice_library() - Details anzeigen
│       ├── _voice_drag_start() - Drag & Drop Start
│       ├── _voice_drag_motion() - Drag Bewegung
│       ├── _voice_drop_on_editor() - Drop auf Editor
│       └── _on_voice_right_click() - Context-Menü
│
├── Center Panel (Editor)
│   ├── setup_center_panel()
│   ├── Draft Pane (oben)
│   │   ├── setup_draft_pane()
│   │   ├── _save_draft() - Draft speichern
│   │   ├── _import_draft() - Draft importieren
│   │   └── _on_draft_double_click() - Draft laden
│   ├── Line Numbers (Canvas, links)
│   │   └── update_line_numbers() - Nummerierung
│   ├── Script Editor (Text Widget)
│   │   ├── setup_syntax_tags() - Syntax-Highlighting
│   │   ├── apply_syntax_highlighting() - Echtzeit-Highlighting
│   │   ├── insert_line() - Zeile einfügen
│   │   ├── delete_line() - Zeile löschen
│   │   ├── undo() - Rückgängig
│   │   ├── redo() - Wiederholen
│   │   ├── _get_current_line_text() - Aktuelle Zeile
│   │   └── _parse_line() - Zeile parsen
│   └── Block View Toggle
│       └── _toggle_block_view() - Ansicht wechseln
│
├── Right Panel (Properties & Info)
│   ├── setup_right_panel()
│   ├── Line Properties
│   │   ├── Sprecher Dropdown
│   │   ├── Emotion Dropdown
│   │   ├── Pause Slider (0-5s)
│   │   ├── Speed Slider (0.5x-2.0x)
│   │   ├── Preset Dropdown
│   │   ├── _apply_preset() - Preset anwenden
│   │   └── _on_slider_change() - Slider-Update
│   └── Project Info
│       └── update_info() - Statistiken aktualisieren
│
├── Status Bar (unten)
│   ├── setup_status_bar()
│   └── update_cursor_position() - Cursor-Position
│
├── Project Management
│   ├── new_project() - Neues Projekt
│   ├── open_project() - Projekt öffnen
│   ├── save_project() - Projekt speichern
│   ├── save_project_as() - Speichern als
│   ├── _save_to_file() - Datei schreiben
│   ├── load_project_data() - Daten laden
│   └── get_template() - Template-Text
│
├── TTS & Preview
│   ├── preview_line() - Zeile vorhören (F5)
│   ├── _on_preview_selected_voice() - Voice-Preview
│   └── _generate_preview() - Audio generieren
│
└── Keyboard Shortcuts
    └── setup_shortcuts() - Alle Shortcuts binden
```

### Threading-Modell

**TTS-Preview läuft asynchron:**
```python
def preview_line(self):
    # UI bleibt responsiv während TTS
    threading.Thread(target=self._generate_preview, daemon=True).start()
```

**Vorteile:**
- Editor bleibt während TTS bedienbar
- Kein Freeze der UI
- Gleichzeitige TTS-Generierung möglich

### Datenformat

**Interne Projekt-Struktur:**
```python
{
    "title": str,
    "style": str,
    "language": str,
    "speakers": [
        {
            "name": str,
            "voice_profile": str,
            "description": str,
            "gender": str,
            "age": str
        }
    ],
    "script": [
        {
            "speaker": str,
            "text": str,
            "emotion": str,
            "pause_after": float,
            "speed": float
        }
    ],
    "drafts": [
        {
            "name": str,
            "content": str,
            "timestamp": str
        }
    ]
}
```

### Performance-Optimierung

**Syntax-Highlighting:**
- Lazy evaluation (nur sichtbarer Bereich)
- Debouncing (verzögerte Aktualisierung)
- Tag-Wiederverwendung

**Voice Library:**
- LRU-Cache für Voice-Metadaten
- Lazy-Loading von Audio-Samples
- Filter-Indizierung

**TTS-Preview:**
- Audio-Caching (keine Neu-Generierung für identischen Text)
- Abbruch laufender Previews bei Neustart

### Abhängigkeiten

```python
# Core
tkinter          # GUI Framework (Standard-Library)
threading        # Async TTS Operations

# Data Handling
pyyaml           # YAML Support
json (builtin)   # JSON Support
pathlib          # File Path handling

# Audio (Optional)
pygame           # Audio Playback Backend
simpleaudio      # Alternative Audio Backend

# TTS Integration
# Verwendet TTSEngineManager aus podcastforge.tts
```

### Memory Usage

| Komponente | Speicher | Notizen |
|------------|----------|---------|
| GUI (tkinter) | ~30-50 MB | Basis-UI |
| Voice Library Metadata | ~5-10 MB | 40+ Stimmen |
| Editor Buffer | ~1-5 MB | Text-Content |
| Audio Cache | ~50-200 MB | TTS-Previews |
| **Gesamt** | ~100-300 MB | Ohne TTS-Models |

**TTS-Models (separate):**
- XTTS: ~2 GB
- Bark: ~10 GB
- Piper: ~10-50 MB
- StyleTTS2: ~2 GB

## 🐛 Ausführliches Troubleshooting

### Problem: Editor startet nicht

**Symptom:** Fenster öffnet sich nicht oder stürzt sofort ab

**Lösungen:**

1. **Python-Version prüfen:**
```bash
python --version  # Sollte 3.8+ sein
python3 --version
```

2. **tkinter installieren:**
```bash
# Linux (Ubuntu/Debian)
sudo apt-get install python3-tk

# Linux (Fedora)
sudo dnf install python3-tkinter

# macOS (mit Homebrew)
brew install python-tk

# Windows
# tkinter ist normalerweise in Python enthalten
# Falls nicht: Python neu installieren mit "tcl/tk and IDLE" Option
```

3. **Abhängigkeiten prüfen:**
```bash
pip install -r requirements.txt
pip list | grep -E "(tk|yaml|pygame)"
```

4. **Display-Variable (Linux/macOS):**
```bash
echo $DISPLAY  # Sollte z.B. ":0" sein
export DISPLAY=:0  # Falls leer
```

### Problem: TTS-Vorschau funktioniert nicht

**Symptom:** F5/F6 führt zu Fehler oder keine Audio-Ausgabe

**Lösungen:**

1. **Ollama-Server prüfen:**
```bash
ollama list  # Zeigt verfügbare Models
ollama serve  # Startet Server (falls nicht läuft)

# Test
curl http://localhost:11434/api/tags
```

2. **TTS-Engine testen:**
```bash
podcastforge test  # TTS-Test-Befehl
```

3. **Logs prüfen:**
```bash
# Logs anzeigen
cat logs/podcastforge.log | tail -50

# Echtzeit-Monitoring
tail -f logs/podcastforge.log
```

4. **Audio-Backend prüfen:**
```bash
# pygame testen
python -c "import pygame; pygame.mixer.init(); print('OK')"

# simpleaudio testen
python -c "import simpleaudio; print('OK')"
```

5. **VRAM/RAM prüfen:**
```bash
# GPU-Speicher (NVIDIA)
nvidia-smi

# RAM-Verfügbarkeit
free -h  # Linux
top  # macOS
```

### Problem: Drag & Drop funktioniert nicht

**Symptom:** Voice lässt sich nicht auf Editor ziehen

**Lösungen:**

1. **Klick-Timing:**
   - Stimme anklicken und **kurz warten** (0.5s)
   - Dann ziehen (nicht sofort)

2. **Drop-Zone:**
   - Auf Textzeile droppen (nicht auf Rand)
   - Zeile sollte sich beim Hover hervorheben

3. **Alternative Methode:**
   - Stimme auswählen → "Als Sprecher verwenden" Button
   - Oder Rechtsklick → "Als Sprecher verwenden"

### Problem: Syntax-Highlighting fehlt

**Symptom:** Text ist schwarz/weiß, keine Farben

**Lösungen:**

1. **Syntax manuell aktualisieren:**
   - `Ansicht` → `Syntax aktualisieren`
   - Oder: Text ändern (triggert Update)

2. **Format prüfen:**
```
# Korrekt:
Host [excited]: Hallo! [0.8s]

# Falsch (keine Highlighting):
Host excited Hallo 0.8s
```

3. **Theme prüfen:**
   - Helles vs. Dunkles Theme
   - `Ansicht` → `Theme wechseln`

### Problem: Audio-Export schlägt fehl

**Symptom:** Export startet nicht oder bricht ab

**Lösungen:**

1. **Speicherplatz prüfen:**
```bash
df -h  # Linux/macOS
# Mindestens 1 GB frei für Audio-Export
```

2. **Schreibrechte prüfen:**
```bash
ls -la out/  # Prüfe Ordner-Permissions
chmod 755 out/  # Falls nötig
```

3. **Kürzeres Testskript:**
   - Teste mit nur 2-3 Zeilen
   - Erhöhe schrittweise

4. **Engine wechseln:**
   - Piper statt XTTS (schneller, weniger RAM)
   - `Settings` → `TTS Engine` → `Piper`

5. **Logs prüfen:**
```bash
tail -f logs/podcastforge.log
# Achte auf "ERROR" oder "Exception"
```

### Problem: Sprecher können nicht hinzugefügt werden

**Symptom:** "Sprecher hinzufügen" Dialog öffnet nicht

**Lösungen:**

1. **Dialog-Blocker:**
   - Schließe andere Dialoge
   - Fenster in Vordergrund bringen

2. **Keyboard-Shortcut:**
   - `Ctrl+Shift+A` statt Button

3. **Manuell in Datei:**
```yaml
speakers:
  - name: NeuerSprecher
    voice_profile: "de_male_1"
    description: "Beschreibung"
```

### Problem: Projekt lädt nicht

**Symptom:** Öffnen schlägt fehl mit Fehler

**Lösungen:**

1. **Datei-Format prüfen:**
```bash
file projekt.yaml  # Sollte "ASCII text" oder "UTF-8" sein
```

2. **YAML-Syntax validieren:**
```bash
yamllint projekt.yaml  # Installiere yamllint falls nötig
```

3. **Backup verwenden:**
```bash
# Editor erstellt automatisch Backups
ls -la *.yaml.backup
cp projekt.yaml.backup projekt.yaml
```

4. **Neu anlegen:**
   - Neues Projekt erstellen
   - Inhalt manuell kopieren

### Problem: Hoher CPU/RAM-Verbrauch

**Symptom:** System wird langsam, Editor ruckelt

**Lösungen:**

1. **TTS-Cache leeren:**
```bash
rm -rf cache/tts/*
```

2. **Engine-Limit reduzieren:**
```python
# In Settings oder Code
max_engines = 1  # Statt 2 oder mehr
```

3. **Piper verwenden:**
   - CPU-optimiert, weniger RAM
   - `Settings` → `Engine` → `Piper`

4. **Großes Skript aufteilen:**
   - Mehrere kleinere Dateien
   - Kapitel-weise bearbeiten

5. **Prozess beenden/neu starten:**
```bash
killall python  # Vorsicht: beendet alle Python-Prozesse
# Oder: Über Task Manager/Activity Monitor
```

### Problem: Voice Library lädt nicht

**Symptom:** Voice-Liste bleibt leer

**Lösungen:**

1. **Voice Library neu laden:**
   - `Ansicht` → `Voice Library aktualisieren`
   - Oder Editor neu starten

2. **Metadaten prüfen:**
```bash
ls -la voices/  # Prüfe Voice-Dateien
```

3. **Filter zurücksetzen:**
   - Alle Filter auf "Alle" setzen
   - Language: Alle
   - Gender: Alle
   - Style: Alle

### Problem: Cursor-Position falsch

**Symptom:** Cursor springt, Position stimmt nicht

**Lösungen:**

1. **Zeilennummern aktualisieren:**
   - Text ändern (triggert Update)
   - Oder: `Ansicht` → `Aktualisieren`

2. **Text neu formatieren:**
   - `Ctrl+A` (alles markieren)
   - Ausschneiden + Einfügen

3. **Editor neu starten**

## 🚀 Feature-Status & Roadmap

### ✅ v1.0 - MVP (VOLLSTÄNDIG IMPLEMENTIERT)

**Editor-Core (2,522 LOC):**
- [x] Professioneller GUI-Editor (tkinter)
- [x] 3-Panel-Layout (Sprecher | Editor | Properties)
- [x] Syntax-Highlighting (Echtzeit, farbcodiert)
- [x] Zeilennummerierung (automatisch)
- [x] Cursor-Position-Tracking
- [x] Undo/Redo-System

**Sprecher-Management:**
- [x] Sprecher hinzufügen/bearbeiten/löschen
- [x] Sprecher-Liste mit Visualisierung
- [x] Context-Menü für Sprecher
- [x] Voice-Profile-Integration

**Voice Library:**
- [x] 40+ professionelle Stimmen
- [x] Filter (Sprache, Geschlecht, Stil)
- [x] Voice-Preview
- [x] Drag & Drop Voice-Assignment
- [x] "Als Sprecher verwenden" Feature
- [x] Context-Menü für Voices

**Draft-System:**
- [x] Drafts speichern und laden
- [x] Mehrere Drafts pro Projekt
- [x] Draft-Liste mit Doppelklick-Laden
- [x] Draft-Import/Export

**Line Properties:**
- [x] Sprecher-Auswahl pro Zeile
- [x] Emotion-Dropdown (6 Optionen)
- [x] Pause-Slider (0-5s)
- [x] Speed-Slider (0.5x-2.0x)
- [x] Presets (Normal, Excited, Thoughtful, Dramatic)

**Project Management:**
- [x] Neues Projekt mit Template
- [x] Projekt öffnen (YAML/JSON)
- [x] Projekt speichern
- [x] Speichern als
- [x] Auto-Format-Erkennung

**TTS & Audio:**
- [x] Audio-Preview mit Playback
- [x] F5: Zeile vorhören
- [x] F6: Komplettes Skript vorhören
- [x] Threading (non-blocking UI)
- [x] Audio-Caching

**UI/UX:**
- [x] Theme-Support
- [x] Context-Menüs (Rechtsklick)
- [x] Keyboard-Shortcuts (20+)
- [x] Status-Bar mit Live-Info
- [x] Project-Info-Widget
- [x] Toolbar mit Icon-Buttons

**Formate:**
- [x] Structured Text Format
- [x] YAML Support
- [x] JSON Support
- [x] Multi-Format-Import/Export

### ✅ Vollständig Implementiert (aber in anderen Modulen)

**Timeline-Editor** (631 LOC - `gui/timeline.py`):
- [x] Canvas-basierter Timeline-View
- [x] Drag & Drop für Szenen
- [x] Visual Waveform-Anzeige
- [x] Szenen-Marker & Zeitstempel
- [x] Zoom In/Out
- [x] Snap-to-Grid
- [x] Playback-Controls

**Multitrack-Editor** (560 LOC - `gui/multitrack.py`):
- [x] Multi-Track-Audio-Bearbeitung
- [x] Track-Management
- [x] Visual Display
- [x] Mixing-Funktionen

**TTS Engine Manager** (1088 LOC - `tts/engine_manager.py`):
- [x] 4 TTS Engines (XTTS, Bark, Piper, StyleTTS2)
- [x] Factory Pattern
- [x] Resource Management
- [x] LRU-Caching
- [x] GPU/CPU Fallback

**Voice Cloning** (467 LOC - `voices/cloner.py`):
- [x] VoiceCloner-Klasse
- [x] Voice-Extraction-Engine
- [x] Quality-Assessment
- [x] Profile-Management

### 🔄 v1.1 - Geplante Verbesserungen

**Editor-Erweiterungen:**
- [ ] Auto-Save mit konfigurierbarem Intervall
- [ ] Wiederherstellung nach Crash
- [ ] Multi-Tab-Unterstützung (mehrere Projekte gleichzeitig)
- [ ] Find & Replace (Ctrl+F, Ctrl+H)
- [ ] Spell-Checker (Rechtschreibprüfung)
- [ ] Auto-Completion für Sprecher/Emotionen

**Export-Optionen:**
- [ ] Batch-Export (mehrere Projekte)
- [ ] Export-Profile (verschiedene Qualitätsstufen)
- [ ] Kapitel-Marker für MP3/M4A
- [ ] ID3-Tags automatisch setzen

**UI/UX-Verbesserungen:**
- [ ] Dark Mode / Light Mode Toggle
- [ ] Anpassbare Font-Größe
- [ ] Minimap (Code-Overview)
- [ ] Split-View (zwei Editoren nebeneinander)

### 🎯 v1.2 - Professional Audio Features

**Audio-Processing:**
- [ ] Integrierter Audio-Editor
- [ ] Fade-Editor (visuell)
- [ ] Noise-Reduction
- [ ] Loudness-Normalization (-16 LUFS)

**Sound-Effekte:**
- [ ] SFX-Library-Integration
- [ ] Hintergrundmusik-Verwaltung
- [ ] Volume-Automation per Zeile
- [ ] Crossfade-Editor

**Templates:**
- [ ] Template-Library
- [ ] Custom Templates speichern
- [ ] Template-Marketplace (Community)

### 🌐 v2.0 - Web & Collaboration

**Web-Version:**
- [ ] Browser-basierter Editor (Gradio/Streamlit)
- [ ] Keine lokale Installation nötig
- [ ] Cloud-TTS-Generation
- [ ] Mobile-Responsive

**Collaboration:**
- [ ] Real-time Co-Editing
- [ ] Kommentar-System
- [ ] Version-History
- [ ] Team-Workspaces

**KI-Assistenz:**
- [ ] Auto-Vervollständigung (KI-gestützt)
- [ ] Stil-Vorschläge
- [ ] Dialog-Optimierung
- [ ] Emotion-Empfehlungen

### 🔮 v3.0 - Advanced & Enterprise

- [ ] Echtzeit-TTS-Streaming
- [ ] Multi-Language Auto-Translation
- [ ] AI Voice Director
- [ ] Podcast-Analytics
- [ ] RSS-Feed Generator
- [ ] Direct Publishing (Spotify, Apple)
- [ ] Enterprise-Features (Teams, SSO, etc.)

## 📚 Beispiele

### Interview-Podcast
```
Host [excited]: Willkommen zu "Tech Talk"! [0.8s]
Host [professional]: Heute zu Gast: Dr. Anna Müller. [0.6s]
Gast [friendly]: Hallo! Danke für die Einladung. [0.5s]

Host [curious]: Sie forschen zu Quantencomputing? [0.7s]
Gast [enthusiastic]: Ja, ein faszinierendes Feld! [0.5s]
Gast [thoughtful]: Es geht um die fundamentalen... [0.6s]
```

### Bildungs-Podcast
```
Lehrer [professional]: Willkommen zu "Physik einfach erklärt". [0.8s]
Lehrer [thoughtful]: Heute: Warum ist der Himmel blau? [0.7s]

Schüler [curious]: Wegen den Wolken? [0.4s]
Lehrer [encouraging]: Gute Überlegung, aber... [0.6s]
Lehrer [explanatory]: Es hat mit Lichtstreuung zu tun. [0.8s]
```

### Nachrichten-Podcast
```
Sprecher1 [serious]: Die Nachrichten vom 14. November. [1.0s]
Sprecher1 [neutral]: Politik: Neue Klimavereinbarung... [0.7s]

Sprecher2 [professional]: Wirtschaft: Börsen steigen... [0.7s]
Sprecher1 [neutral]: Und nun zum Wetter. [0.5s]
```

## 💡 Tipps & Tricks

1. **Nutze Templates**: Speichere häufig verwendete Skript-Strukturen
2. **Voice-Shortcuts**: Erstelle Favoriten-Voices
3. **Batch-Vorschau**: Höre mehrere Zeilen auf einmal
4. **Export-Profile**: Speichere Audio-Einstellungen
5. **Keyboard-First**: Lerne Shortcuts für schnelleres Arbeiten

---

**Happy Podcasting! 🎙️**
