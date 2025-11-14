#!/bin/bash

#================================================
# PodcastForge AI - Automatisiertes Setup Script
# Author: makr-code
# Date: 2025-11-14
#================================================

set -e

echo "🚀 PodcastForge AI Setup"
echo "========================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funktion für Erfolgs-Meldungen
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Funktion für Warn-Meldungen
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Funktion für Fehler-Meldungen
error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Python-Version prüfen
echo "1. Python-Version prüfen..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    success "Python $PYTHON_VERSION gefunden"
else
    error "Python 3.8+ erforderlich, gefunden: $PYTHON_VERSION"
    exit 1
fi

# 2. Virtual Environment erstellen
echo ""
echo "2. Virtual Environment erstellen..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual Environment erstellt"
else
    warning "Virtual Environment existiert bereits"
fi

# 3. Virtual Environment aktivieren
echo ""
echo "3. Aktiviere Virtual Environment..."
source venv/bin/activate
success "Virtual Environment aktiviert"

# 4. Dependencies installieren
echo ""
echo "4. Installiere Python-Dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
success "Dependencies installiert"

# 5. Ollama prüfen/installieren
echo ""
echo "5. Ollama prüfen..."
if command -v ollama &> /dev/null; then
    success "Ollama ist installiert"
    
    # Prüfe ob Ollama läuft
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        success "Ollama läuft"
    else
        warning "Ollama ist installiert aber läuft nicht"
        echo "  Starte mit: ollama serve"
    fi
else
    warning "Ollama nicht gefunden"
    echo ""
    read -p "Möchtest du Ollama jetzt installieren? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
        success "Ollama installiert"
    fi
fi

# 6. LLM Model herunterladen
echo ""
echo "6. LLM Model prüfen..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if echo "$MODELS" | grep -q "llama2"; then
        success "llama2 Model vorhanden"
    else
        warning "llama2 Model nicht gefunden"
        echo ""
        read -p "Möchtest du llama2 jetzt herunterladen? (~4GB) (j/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            ollama pull llama2
            success "llama2 heruntergeladen"
        fi
    fi
else
    warning "Ollama läuft nicht - kann Models nicht prüfen"
fi

# 7. FFmpeg prüfen
echo ""
echo "7. FFmpeg prüfen..."
if command -v ffmpeg &> /dev/null; then
    success "FFmpeg ist installiert"
else
    warning "FFmpeg nicht gefunden (für Audio-Processing benötigt)"
    echo "  Installiere mit: apt-get install ffmpeg"
fi

# 8. ebook2audiobook klonen (optional)
echo ""
echo "8. ebook2audiobook prüfen..."
if [ -d "ebook2audiobook" ]; then
    success "ebook2audiobook vorhanden"
else
    warning "ebook2audiobook nicht gefunden"
    read -p "Möchtest du ebook2audiobook klonen? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        git clone https://github.com/DrewThomasson/ebook2audiobook.git
        success "ebook2audiobook geklont"
    fi
fi

# 9. Ausgabe-Verzeichnisse erstellen
echo ""
echo "9. Erstelle Ausgabe-Verzeichnisse..."
mkdir -p output podcasts logs cache
success "Verzeichnisse erstellt"

# 10. Test durchführen
echo ""
echo "10. Installation testen..."
if podcastforge test > /dev/null 2>&1; then
    success "PodcastForge erfolgreich installiert"
else
    warning "Test fehlgeschlagen - prüfe Konfiguration"
fi

# Abschluss
echo ""
echo "================================================"
echo -e "${GREEN}✨ Setup abgeschlossen!${NC}"
echo "================================================"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Aktiviere Virtual Environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Starte Ollama (falls nicht läuft):"
echo "   ollama serve"
echo ""
echo "3. Teste Installation:"
echo "   podcastforge test"
echo ""
echo "4. Erstelle ersten Podcast:"
echo "   podcastforge generate --topic \"Dein Thema\" --duration 5"
echo ""
echo "Oder führe Demo aus:"
echo "   make demo"
echo ""
echo "Dokumentation: docs/README.md"
echo ""
