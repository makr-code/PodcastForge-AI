# PodcastForge-AI CLI Referenz

**Version:** 1.0  
**Stand:** 2025-11-17

---

## Übersicht

PodcastForge-AI bietet eine umfassende Command-Line-Interface (CLI) für die Podcast-Generierung und -Verwaltung.

---

## Installation & Setup

```bash
# Installation
pip install -e .

# Version prüfen
podcastforge --version
```

---

## Befehle

### 1. `edit` - GUI Editor starten

Öffnet den grafischen Editor für Podcast-Skripte.

**Syntax:**
```bash
podcastforge edit [DATEI]
```

**Argumente:**
- `DATEI` (optional): Pfad zu einer vorhandenen Projektdatei (.yaml, .json)

**Beispiele:**
```bash
# Neues Projekt
podcastforge edit

# Vorhandenes Projekt öffnen
podcastforge edit mein_podcast.yaml
podcastforge edit projekt/script.json
```

**Features:**
- 3-Panel-Layout (Sprecher | Editor | Properties)
- Syntax-Highlighting
- Drag & Drop für Voice-Zuweisung
- Echtzeit-Preview (F5/F6)
- Multi-Format-Support

---

### 2. `generate` - Podcast generieren

Generiert einen kompletten Podcast von Thema bis Audio-Datei.

**Syntax:**
```bash
podcastforge generate [OPTIONEN]
```

**Optionen:**
- `-t, --topic TEXT` (erforderlich): Podcast-Thema
- `--style TEXT`: Podcast-Stil (interview, discussion, educational, news, narrative, comedy, debate)
- `-d, --duration INTEGER`: Dauer in Minuten (Standard: 10)
- `-l, --language TEXT`: Sprache (de, en, etc., Standard: de)
- `--llm TEXT`: Ollama LLM Modell (Standard: llama2)
- `-o, --output TEXT`: Ausgabedatei (Standard: podcast.mp3)
- `--music TEXT`: Pfad zu Hintergrundmusik (optional)

**Beispiele:**

```bash
# Einfaches Beispiel
podcastforge generate --topic "Künstliche Intelligenz im Alltag" --duration 10

# Mit allen Optionen
podcastforge generate \
    --topic "Klimawandel und Nachhaltigkeit" \
    --style discussion \
    --duration 15 \
    --llm mistral \
    --language de \
    --output mein_podcast.mp3 \
    --music background.mp3

# Interview-Stil
podcastforge generate \
    --topic "Die Zukunft der Elektromobilität" \
    --style interview \
    --duration 20

# Englischer Podcast
podcastforge generate \
    --topic "The Future of AI" \
    --language en \
    --llm llama2 \
    --duration 15
```

**Verfügbare Stile:**
- `interview` - Fragen und Antworten zwischen Host und Gast
- `discussion` - Lebhafte Diskussion mit mehreren Teilnehmern
- `educational` - Lehrreicher Dialog mit Erklärungen
- `news` - Nachrichtenbeitrag mit Moderator und Experten
- `narrative` - Erzählende Geschichte mit Dialogen
- `comedy` - Humorvoller Dialog mit Witzen
- `debate` - Strukturierte Debatte mit Pro/Contra

---

### 3. `from-script` - Aus Skript generieren

Generiert Audio aus einem vorhandenen Podcast-Skript.

**Syntax:**
```bash
podcastforge from-script SCRIPT_PATH [OPTIONEN]
```

**Argumente:**
- `SCRIPT_PATH` (erforderlich): Pfad zur Skript-Datei (.json, .yaml)

**Optionen:**
- `-o, --output TEXT`: Ausgabedatei (Standard: podcast.mp3)

**Beispiele:**

```bash
# Aus JSON-Skript
podcastforge from-script mein_script.json

# Mit custom Output
podcastforge from-script script.yaml --output episode_01.mp3

# Aus Beispiel-Skript
podcastforge from-script examples/sample_script.json --output test.mp3
```

**Skript-Format (JSON):**
```json
{
  "title": "Episode Titel",
  "speakers": [
    {
      "id": "host",
      "name": "Max",
      "voice_profile": "de_male_1"
    }
  ],
  "lines": [
    {
      "speaker_id": "host",
      "text": "Willkommen zum Podcast!",
      "emotion": "happy",
      "pause_after": 1.0
    }
  ]
}
```

---

### 4. `voices` - Voice Library durchsuchen

Zeigt verfügbare Stimmen aus der Voice Library an.

**Syntax:**
```bash
podcastforge voices [OPTIONEN]
```

**Optionen:**
- `-l, --language TEXT`: Filter nach Sprache (de, en, es, fr, etc.)
- `--gender TEXT`: Filter nach Geschlecht (male, female, neutral)
- `-s, --style TEXT`: Filter nach Stil (professional, friendly, documentary, etc.)

**Beispiele:**

```bash
# Alle Stimmen anzeigen
podcastforge voices

# Deutsche Stimmen
podcastforge voices --language de

# Männliche Stimmen
podcastforge voices --gender male

# Professionelle deutsche Stimmen
podcastforge voices --language de --style professional

# Weibliche englische Stimmen
podcastforge voices --language en --gender female

# Kombinierte Filter
podcastforge voices --language de --gender male --style friendly
```

**Output-Format:**
```
Voice Library
─────────────────────────────────────────────
ID: de_male_professional_1
Name: Thorsten
Language: de
Gender: male
Style: professional
Age: adult
Description: Professional German voice
─────────────────────────────────────────────
```

---

### 5. `test` - TTS-Test durchführen

Testet die TTS-Engine mit einem einfachen Text.

**Syntax:**
```bash
podcastforge test
```

**Beispiele:**

```bash
# TTS-Test ausführen
podcastforge test
```

**Was wird getestet:**
- TTS-Engine-Verfügbarkeit
- Audio-Generierung
- Ausgabe-Datei wird erstellt
- Grundlegende Funktionalität

---

### 6. `models` - Verfügbare Ollama Models anzeigen

Zeigt alle verfügbaren Ollama LLM-Models an.

**Syntax:**
```bash
podcastforge models
```

**Beispiele:**

```bash
# Models auflisten
podcastforge models
```

**Output:**
```
Available Ollama Models:
  - llama2 (7B)
  - mistral (7B)
  - neural-chat (7B)
  - codellama (7B)
```

---

## Häufige Workflows

### Workflow 1: Schneller Podcast

```bash
# 1. Podcast direkt generieren
podcastforge generate \
    --topic "Machine Learning Grundlagen" \
    --duration 10

# Fertig! podcast.mp3 wurde erstellt
```

### Workflow 2: Mit Editor

```bash
# 1. Editor öffnen
podcastforge edit

# 2. Skript im Editor erstellen und speichern als script.yaml

# 3. Audio generieren
podcastforge from-script script.yaml --output episode.mp3
```

### Workflow 3: Voice Library erkunden

```bash
# 1. Verfügbare Stimmen ansehen
podcastforge voices --language de

# 2. Stimme testen
podcastforge test

# 3. Mit gewählter Stimme Podcast generieren
podcastforge generate --topic "Test" --duration 5
```

---

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `OLLAMA_HOST` | Ollama Server URL | `http://localhost:11434` |
| `PODCASTFORGE_CACHE` | Cache-Verzeichnis | `./cache` |
| `PODCASTFORGE_OUTPUT` | Output-Verzeichnis | `./out` |

**Beispiel:**
```bash
export OLLAMA_HOST="http://192.168.1.100:11434"
podcastforge generate --topic "Test"
```

---

## Tipps & Tricks

### Performance

```bash
# Kürzere Podcasts für Tests
podcastforge generate --topic "Test" --duration 1

# Schnelleres LLM-Modell verwenden
podcastforge generate --topic "Test" --llm mistral
```

### Batch-Processing

```bash
# Mehrere Podcasts nacheinander
for topic in "AI" "ML" "DL"; do
    podcastforge generate --topic "$topic" --output "${topic}.mp3"
done
```

### Debugging

```bash
# Mit verbose Logging
podcastforge --verbose generate --topic "Test"

# TTS-Test vor Produktion
podcastforge test
```

---

## Troubleshooting

### Problem: "Ollama not found"

**Lösung:**
```bash
# Ollama installieren
curl -fsSL https://ollama.ai/install.sh | sh

# Model herunterladen
ollama pull llama2

# Status prüfen
ollama list
```

### Problem: "TTS Engine not available"

**Lösung:**
```bash
# Abhängigkeiten installieren
pip install -r requirements-tts.txt

# Test durchführen
podcastforge test
```

### Problem: "Voice not found"

**Lösung:**
```bash
# Verfügbare Stimmen prüfen
podcastforge voices

# Voice Library aktualisieren
pip install -e . --upgrade
```

---

## Exit Codes

| Code | Bedeutung |
|------|-----------|
| 0 | Erfolg |
| 1 | Allgemeiner Fehler |
| 2 | Ungültige Argumente |
| 3 | Ollama nicht erreichbar |
| 4 | TTS-Fehler |

---

## Weitere Ressourcen

- **Editor Guide:** [docs/EDITOR_GUIDE.md](EDITOR_GUIDE.md)
- **Voice Integration:** [docs/VOICE_INTEGRATION.md](VOICE_INTEGRATION.md)
- **Beispiele:** [examples/](../examples/)
- **API Dokumentation:** [docs/README.md](README.md)

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
