# 🎙️ PodcastForge AI

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Ollama](https://img.shields.io/badge/LLM-Ollama-orange)](https://ollama.ai)

**KI-gestützter Podcast-Generator mit Ollama LLMs und ebook2audiobook TTS**

Generiere professionelle Podcasts vollautomatisch: Von der Idee bis zur fertigen Audio-Datei - alles mit einem Befehl!

## ✨ Features

- 🤖 **KI-Drehbucherstellung** mit Ollama (Llama2, Mistral, etc.)
- 🎙️ **Natürliche Sprachsynthese** mit ebook2audiobook und XTTS
- 👥 **Multi-Speaker Support** - Verschiedene Stimmen für jeden Sprecher
- 🎨 **Verschiedene Podcast-Stile** - Interview, Diskussion, News, Comedy, etc.
- 🎚️ **Audio-Nachbearbeitung** - Normalisierung, Kompression, Hintergrundmusik
- 🐳 **Docker Support** - Einfaches Deployment
- 🌍 **Mehrsprachig** - Deutsch, Englisch und viele weitere Sprachen
- 🔒 **100% Lokal** - Keine Cloud-APIs, vollständige Privatsphäre

## 🚀 Schnellstart

### Installation

```bash
# Repository klonen
git clone https://github.com/makr-code/PodcastForge-AI.git
cd PodcastForge-AI

# Automatisches Setup
chmod +x setup.sh
./setup.sh

# Oder manuell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Ollama installieren
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
```

### Ersten Podcast generieren

```bash
# Einfaches Beispiel
podcastforge generate \
    --topic "Künstliche Intelligenz im Alltag" \
    --duration 10

# Mit erweiterten Optionen
podcastforge generate \
    --topic "Klimawandel und Nachhaltigkeit" \
    --style discussion \
    --duration 15 \
    --llm mistral \
    --language de \
    --output mein_podcast.mp3
```

### Mit Python

```python
from podcastforge import PodcastForge, PodcastStyle

# Initialisieren
forge = PodcastForge(llm_model="llama2", language="de")

# Podcast erstellen
podcast = forge.create_podcast(
    topic="Die Zukunft der Elektromobilität",
    style=PodcastStyle.INTERVIEW,
    duration=15,
    output="podcast.mp3"
)
```

## 📚 Podcast-Stile

- **Interview** - Fragen und Antworten zwischen Host und Gast
- **Discussion** - Lebhafte Diskussion mit mehreren Teilnehmern
- **Educational** - Lehrreicher Dialog mit Erklärungen
- **News** - Nachrichtenbeitrag mit Moderator und Experten
- **Narrative** - Erzählende Geschichte mit Dialogen
- **Comedy** - Humorvoller Dialog mit Witzen
- **Debate** - Strukturierte Debatte mit Pro/Contra

## 🎭 Custom Sprecher

```python
from podcastforge import Speaker

speakers = [
    Speaker(
        id="host",
        name="Max",
        role="Moderator",
        personality="freundlich, neugierig, professionell",
        voice_profile="de_male_1",
        gender="male"
    ),
    Speaker(
        id="expert",
        name="Dr. Anna Schmidt",
        role="Expertin",
        personality="kompetent, enthusiastisch",
        voice_profile="de_female_1",
        gender="female"
    )
]

forge.create_podcast(
    topic="Quantencomputer einfach erklärt",
    speakers=speakers,
    duration=20
)
```

## 🐳 Docker

```bash
# Mit Docker Compose
docker-compose up -d

# Podcast generieren
docker-compose exec podcastforge generate \
    --topic "Dein Thema" \
    --duration 10
```

## 🖥️ CLI Referenz

### Alle verfügbaren Befehle

```bash
# GUI Editor starten
podcastforge edit [datei]              # Neues Projekt oder vorhandene Datei öffnen

# Podcast generieren
podcastforge generate \
    --topic "Thema" \
    --style discussion \
    --duration 15 \
    --llm mistral \
    --language de \
    --output podcast.mp3

# Aus vorhandenem Skript generieren
podcastforge from-script script.json --output podcast.mp3

# Voice Library durchsuchen
podcastforge voices \
    --language de \
    --gender male \
    --style professional

# TTS-Test durchführen
podcastforge test

# Verfügbare Ollama Models anzeigen
podcastforge models
```

## 📖 Dokumentation

- [Setup & Installation](SETUP.md)
- [Editor Guide](docs/EDITOR_GUIDE.md)
- [Voice Integration](docs/VOICE_INTEGRATION.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Dokumentations-Index](docs/README.md)
- [Beispiele](examples/)
- [Copilot Introduction](./.github/indroduction)  
  (Kurzanleitung für automatisierte Assistenz; bitte bei automatischen Änderungen beachten)
- [Dokumentationspflicht / ToDo-Vorlage](docs/todo.md)

## 🛠️ Architektur

```
podcastforge/
├── core/              # Kern-Logik
│   ├── forge.py      # Hauptklasse
│   └── config.py     # Konfiguration
├── llm/              # LLM-Integration
│   └── ollama_client.py
├── tts/              # Text-to-Speech
│   └── ebook2audiobook_adapter.py
├── audio/            # Audio-Processing
│   └── postprocessor.py
└── cli.py            # Command Line Interface
```

## 🤝 Contributing

Beiträge sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
# Development Setup
make install-dev

# Tests
make test

# Code-Formatierung
make format

# Linting
make lint
```

## 📋 Roadmap

- [x] Ollama LLM Integration
- [x] Multi-Speaker Support
- [x] Docker Support
- [x] Voice Cloning mit eigenen Stimmen
- [x] Batch-Processing für Podcast-Serien (Script Orchestrator)
- [x] Timeline Editor
- [x] Multitrack Editor
- [x] 4 TTS Engines (XTTS, Bark, Piper, StyleTTS2)
- [ ] Web-Interface (Gradio/Streamlit)
- [ ] RSS-Feed Integration für News-Podcasts
- [ ] Real-time Streaming (FFmpeg Pipe teilweise implementiert)
- [ ] Cloud-Deployment (AWS/GCP)

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 🙏 Credits

- [DrewThomasson/ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) - TTS Backend
- [Ollama](https://ollama.ai) - Lokale LLMs
- [Coqui TTS](https://github.com/coqui-ai/TTS) - Voice Synthesis

## 📞 Support

- 🐛 [Issues](https://github.com/makr-code/PodcastForge-AI/issues)
- 💬 [Discussions](https://github.com/makr-code/PodcastForge-AI/discussions)

## ⭐ Star History

Wenn dir das Projekt gefällt, gib uns einen Stern! ⭐

---

Erstellt mit ❤️ von [makr-code](https://github.com/makr-code) | November 2025