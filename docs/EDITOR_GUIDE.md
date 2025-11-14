# PodcastForge GUI Editor

## 🎨 Features

### ✅ Haupt-Features
- **Professioneller Text-Editor** mit Syntax-Highlighting
- **Voice Library Integration** mit 40+ professionellen Stimmen
- **Sprecher-Management** mit visueller Verwaltung
- **Echtzeit-TTS-Vorschau** für einzelne Zeilen oder komplette Skripte
- **Multi-Format-Support**: Structured Text, YAML, JSON
- **Audio-Player** mit Wellenform-Visualisierung
- **Timeline-Editor** für Podcast-Segmente (geplant)

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

## 📋 Workflow

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

## ⌨️ Tastatur-Shortcuts

### Datei
- `Ctrl+N` - Neues Projekt
- `Ctrl+O` - Projekt öffnen
- `Ctrl+S` - Speichern
- `Ctrl+Shift+S` - Speichern als
- `Ctrl+E` - Export zu Audio
- `Ctrl+Q` - Beenden

### Bearbeiten
- `Ctrl+Z` - Rückgängig
- `Ctrl+Y` - Wiederholen
- `Ctrl+Enter` - Neue Zeile einfügen
- `Ctrl+D` - Zeile löschen
- `Ctrl+Shift+S` - Sprecher hinzufügen

### TTS
- `F5` - Aktuelle Zeile vorhören
- `F6` - Komplettes Skript vorhören

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

## 🔧 Technische Details

### Architektur
```python
PodcastEditor
├── GUI (tkinter)
│   ├── MenuBar
│   ├── Toolbar
│   ├── LeftPanel (Speakers, Voices)
│   ├── CenterPanel (Script Editor)
│   ├── RightPanel (Properties, Audio)
│   └── StatusBar
│
├── Voice Library Integration
├── TTS Preview System
├── Project Management
└── Export System
```

### Abhängigkeiten
```python
tkinter          # GUI Framework
pyyaml           # YAML Support
json (builtin)   # JSON Support
threading        # Async TTS
pathlib          # File handling
```

### Performance
- **Editor**: Sofortige Reaktion
- **Syntax-Highlighting**: Real-time
- **TTS-Vorschau**: 2-5 Sekunden pro Zeile
- **Export**: ~1-2 Minuten pro Podcast-Minute

## 🐛 Troubleshooting

### Editor startet nicht
```bash
# Prüfe Python-Version
python --version  # Sollte 3.8+

# Installiere tkinter (falls fehlt)
sudo apt-get install python3-tk  # Linux
brew install python-tk           # macOS
```

### TTS-Vorschau funktioniert nicht
1. Prüfe Ollama-Server: `ollama list`
2. Prüfe TTS-Engine: `podcastforge test`
3. Überprüfe Log: `logs/podcastforge.log`

### Audio-Export schlägt fehl
1. Prüfe Festplattenspeicher
2. Überprüfe Schreibrechte
3. Teste mit kürzerem Skript

## 🚀 Feature Roadmap

### ✅ v1.0 - MVP (FERTIG)
- [x] Professioneller GUI-Editor (tkinter)
- [x] Voice Library (40+ Stimmen)
- [x] Multi-Format Support (Structured/YAML/JSON)
- [x] Audio-Preview mit Playback
- [x] Wellenform-Visualisierung
- [x] Projekt-Management
- [x] CLI-Integration
- [x] Beispiel-Projekte

### 🔄 v1.1 - Timeline & Enhanced TTS (In Entwicklung)
- [ ] **Timeline-Editor**
  - Canvas-basierter Timeline-View
  - Drag&Drop für Szenen
  - Visual Waveform-Anzeige
  - Szenen-Marker & Zeitstempel
  - Multi-Track-Ansicht
- [ ] **TTSEngineManager**
  - Modulares Engine-System
  - BARK Integration (natürlichere Stimmen)
  - Piper Integration (schnelle CPU-Alternative)
  - GPU/CPU Fallback
  - Model-Caching
- [ ] **Batch-Export**
  - Mehrere Projekte gleichzeitig
  - Export-Profile
- [ ] **Auto-Save**
  - Automatische Sicherung
  - Wiederherstellung nach Crash

### 🎯 v1.2 - Voice Cloning & Professional Audio
- [ ] **Voice Cloning mit StyleTTS2**
  - 3-Sekunden Voice-Cloning
  - Custom Voice Upload
  - Voice-Profil-Management
- [ ] **Voice Extraction**
  - Aus Videos/Podcasts extrahieren
  - Demucs Vocal-Separation
  - Voice Activity Detection
- [ ] **Multi-Track Audio-Editor**
  - Parallel-Spuren für Musik/SFX
  - Visual Mixing
  - Fade In/Out Editor
- [ ] **Sound-Effekte & Musik**
  - Integrierte SFX-Library
  - Hintergrundmusik-Support
  - Volume-Automation
- [ ] **Templates Library**
  - Vordefinierte Podcast-Vorlagen
  - Custom Templates speichern
  - Template-Marketplace

### 🌐 v2.0 - Web & Collaboration
- [ ] **Web-basierte Version (Gradio)**
  - Browser-basierter Editor
  - Keine lokale Installation nötig
  - Cloud-TTS-Generation
- [ ] **Kollaborative Bearbeitung**
  - Real-time Co-Editing
  - Kommentar-System
  - Version-History
- [ ] **KI-Skript-Assistent**
  - Auto-Vervollständigung
  - Stil-Vorschläge
  - Dialog-Optimierung
  - Emotion-Empfehlungen
- [ ] **Cloud-Voice-Library**
  - 1000+ professionelle Stimmen
  - Community-Voices
  - Voice-Sharing
  - Pay-per-Use Modell

### 🔮 v3.0 - Advanced Features
- [ ] Echtzeit-TTS-Streaming
- [ ] Multi-Language Auto-Translation
- [ ] AI Voice Director (automatische Emotion)
- [ ] Podcast-Analytics
- [ ] RSS-Feed Generator
- [ ] Direct Publishing (Spotify, Apple Podcasts)

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
