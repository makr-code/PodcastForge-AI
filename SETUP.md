# 🚀 PodcastForge-AI Setup Guide

Vollständige Installationsanleitung für PodcastForge-AI.

## Inhaltsverzeichnis

- [Systemanforderungen](#systemanforderungen)
- [Installation](#installation)
- [Ollama Setup](#ollama-setup)
- [Test](#test)
- [Verwendung](#verwendung)
- [Troubleshooting](#troubleshooting)

## Systemanforderungen

### Minimal

- **OS**: Linux, macOS, Windows (WSL2)
- **Python**: 3.8 oder höher
- **RAM**: 8 GB (16 GB empfohlen für große LLMs)
- **Disk**: 10 GB freier Speicher
- **FFmpeg**: Für Audio-Processing

### Empfohlen

- **RAM**: 16+ GB
- **GPU**: CUDA-fähige GPU (optional, für schnellere TTS)
- **CPU**: Multi-Core für Parallelverarbeitung

## Installation

### 1. Automatische Installation (empfohlen)

```bash
# Repository klonen
git clone https://github.com/makr-code/PodcastForge-AI.git
cd PodcastForge-AI

# Automatisches Setup ausführen
chmod +x setup.sh
./setup.sh
```

Das Setup-Script installiert automatisch:
- Python Virtual Environment
- Alle Python-Dependencies
- Ollama (optional)
- LLM-Models (optional)

### 2. Manuelle Installation

#### Schritt 1: Python Environment

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate  # Linux/macOS
# oder
venv\Scripts\activate  # Windows
```

#### Schritt 2: Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Installiere Requirements
pip install -r requirements.txt

# Installiere PodcastForge
pip install -e .
```

#### Schritt 3: FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download von [ffmpeg.org](https://ffmpeg.org/download.html)
- Zu PATH hinzufügen

## Ollama Setup

### Installation

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
- Download von [ollama.ai](https://ollama.ai/download)

### Ollama starten

```bash
ollama serve
```

Läuft im Hintergrund auf `http://localhost:11434`

### LLM Models herunterladen

```bash
# Llama2 (Empfohlen für Deutsch)
ollama pull llama2

# Alternative: Mistral (schneller)
ollama pull mistral

# Alternative: Neural-Chat
ollama pull neural-chat

# Für bessere Qualität: Llama2 70B (benötigt viel RAM)
ollama pull llama2:70b
```

**Model-Größen:**
- `llama2` (~4 GB)
- `mistral` (~4 GB)
- `llama2:70b` (~40 GB)

### Verfügbare Models anzeigen

```bash
ollama list
# oder
podcastforge models
```

## Test

### Installation testen

```bash
# PodcastForge Test-Suite
podcastforge test
```

Prüft:
- ✓ Python-Pakete
- ✓ Ollama-Verbindung
- ✓ FFmpeg
- ✓ Verfügbare Models

### Demo-Podcast generieren

```bash
# Aktiviere Virtual Environment
source venv/bin/activate

# Stelle sicher, dass Ollama läuft
ollama serve &

# Führe Demo aus
python examples/demo.py

# Oder mit Make
make demo
```

## Verwendung

### CLI

```bash
# Einfacher Podcast
podcastforge generate \
    --topic "Künstliche Intelligenz" \
    --duration 10

# Mit allen Optionen
podcastforge generate \
    --topic "Klimawandel" \
    --style discussion \
    --duration 15 \
    --llm mistral \
    --language de \
    --output mein_podcast.mp3
```

### Python API

```python
from podcastforge import PodcastForge, PodcastStyle

# Initialisieren
forge = PodcastForge(
    llm_model="llama2",
    language="de"
)

# Podcast erstellen
podcast = forge.create_podcast(
    topic="Die Zukunft der Mobilität",
    style=PodcastStyle.INTERVIEW,
    duration=15,
    output="podcast.mp3"
)

print(f"Podcast erstellt: {podcast}")
```

## Docker Setup

### Mit Docker Compose

```bash
# Container starten
docker-compose up -d

# Warten bis Ollama bereit ist
docker-compose logs -f ollama

# Model herunterladen
docker-compose exec ollama ollama pull llama2

# Podcast generieren
docker-compose run podcastforge generate \
    --topic "Dein Thema" \
    --duration 10
```

### Nur Docker

```bash
# Image bauen
docker build -t podcastforge-ai .

# Container starten
docker run -it podcastforge-ai --help
```

## Troubleshooting

### Problem: "Ollama nicht erreichbar"

**Lösung:**
```bash
# Prüfe ob Ollama läuft
curl http://localhost:11434/api/tags

# Starte Ollama
ollama serve

# In neuem Terminal
ollama pull llama2
```

### Problem: "FFmpeg nicht gefunden"

**Lösung:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Test
ffmpeg -version
```

### Problem: "Model nicht gefunden"

**Lösung:**
```bash
# Verfügbare Models anzeigen
ollama list

# Model herunterladen
ollama pull llama2

# Prüfen
podcastforge models
```

### Problem: "Audio-Generierung schlägt fehl"

**Lösung:**
```bash
# Prüfe TTS-Dependencies
pip install TTS pydub

# Prüfe FFmpeg
which ffmpeg

# Teste mit kleinerem Beispiel
podcastforge generate --topic "Test" --duration 2
```

### Problem: "Out of Memory"

**Lösungen:**
1. Verwende kleineres LLM-Model:
   ```bash
   podcastforge generate --llm mistral --topic "Test"
   ```

2. Reduziere Podcast-Dauer:
   ```bash
   podcastforge generate --topic "Test" --duration 5
   ```

3. Schließe andere Anwendungen

### Problem: "Slow Generation"

**Lösungen:**
1. GPU-Support aktivieren (wenn verfügbar)
2. Kleineres Model verwenden: `mistral` statt `llama2:70b`
3. Kürzere Podcasts generieren

## Erweiterte Konfiguration

### Environment Variables

Erstelle `.env` Datei:

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434

# Default Settings
DEFAULT_LLM_MODEL=llama2
DEFAULT_LANGUAGE=de
DEFAULT_DURATION=10

# TTS
TTS_ENGINE=xtts
AUDIO_BITRATE=192k
```

### Custom Voice Samples

```bash
# Eigene Stimmen-Samples verwenden
mkdir -p voices
# Lege .wav Dateien in voices/ ab (10-30 Sekunden)

# Verwende in Python:
from podcastforge import Speaker

speaker = Speaker(
    id="custom",
    name="Meine Stimme",
    role="Sprecher",
    personality="freundlich",
    voice_profile="custom",
    voice_sample="voices/meine_stimme.wav"
)
```

## Updates

### Code aktualisieren

```bash
cd PodcastForge-AI
git pull origin main
pip install -r requirements.txt
pip install -e .
```

### Models aktualisieren

```bash
# Aktualisiere Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Aktualisiere Models
ollama pull llama2
```

## Deinstallation

```bash
# Virtual Environment löschen
rm -rf venv

# Ollama deinstallieren (optional)
# Linux:
sudo rm -rf /usr/local/bin/ollama /usr/share/ollama

# macOS:
brew uninstall ollama
```

## Support

- 📖 [Dokumentation](docs/)
- 🐛 [Issues](https://github.com/makr-code/PodcastForge-AI/issues)
- 💬 [Discussions](https://github.com/makr-code/PodcastForge-AI/discussions)

---

**Viel Erfolg mit PodcastForge-AI! 🎙️**
