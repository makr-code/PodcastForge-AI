# PodcastForge-AI Development Roadmap

## 📋 Übersicht

Dieses Dokument beschreibt die Entwicklungs-Roadmap für PodcastForge-AI mit detaillierten Spezifikationen für kommende Features.

---

## ✅ Version 1.0 - MVP (ABGESCHLOSSEN)

**Release-Datum:** November 2024  
**Status:** ✅ Produktionsreif

### Implementierte Features

#### Core-System
- [x] PodcastForge Engine (333 Zeilen)
- [x] Ollama LLM Integration (Llama2, Mistral)
- [x] ebook2audiobook TTS Adapter
- [x] Audio Post-Processing (Normalisierung, Kompression)

#### GUI-Editor
- [x] tkinter-basierter Editor (1096 Zeilen)
- [x] 3-Panel-Layout (Speakers | Editor | Properties)
- [x] Syntax-Highlighting (Sprecher, Emotionen, Pausen)
- [x] Multi-Format-Support (Structured, YAML, JSON)
- [x] Projekt-Management (Neu/Öffnen/Speichern/Export)

#### Voice Library
- [x] 40+ professionelle Stimmen (460 Zeilen Code)
- [x] Intelligente Kategorisierung (Sprache, Geschlecht, Alter, Stil)
- [x] Voice-Suggestions basierend auf Podcast-Stil
- [x] Integration mit ebook2audiobook voices

#### Audio-System
- [x] Audio-Player mit Multi-Backend (pygame/simpleaudio)
- [x] Wellenform-Visualisierung (PIL/Pillow)
- [x] Thread-basierte Audio-Generierung
- [x] F5/F6 Keyboard-Shortcuts für Preview

#### CLI & Beispiele
- [x] `podcastforge edit` - GUI-Editor starten
- [x] `podcastforge voices` - Voice Library anzeigen
- [x] 4 Beispiel-Projekte (Interview, Bildung, News, Simple)

---

## 🔄 Version 1.1 - Timeline & Enhanced TTS

**Geplanter Release:** Dezember 2024  
**Status:** 🔄 In Entwicklung

### 1. Timeline-Editor

**Ziel:** Visueller Timeline-basierter Editor für präzise Podcast-Bearbeitung

#### Features
- **Canvas-basierter Timeline-View**
  - Horizontale Timeline mit Zeitmarkierungen
  - Zoom In/Out (10s bis 10min Ansicht)
  - Scrubbing (Audio-Position per Mausklick)
  
- **Drag & Drop für Szenen**
  - Szenen verschieben per Drag&Drop
  - Automatische Gap-Schließung
  - Snap-to-Grid (0.1s, 0.5s, 1s)
  
- **Visual Waveform-Anzeige**
  - Wellenform für jedes Audio-Segment
  - Lautstärke-Visualisierung
  - Fade-Marker
  
- **Szenen-Marker**
  - Benutzerdefinierte Marker setzen
  - Kapitel-Unterstützung
  - Export zu Podcast-Chaptern

#### Technische Spezifikation

```python
# src/podcastforge/gui/timeline.py

class TimelineEditor:
    """
    Visueller Timeline-Editor für Podcast-Bearbeitung
    
    Architecture:
    - Canvas-basiert (tkinter.Canvas)
    - Event-driven (Mouse, Keyboard)
    - MVC-Pattern (Model-View-Controller)
    """
    
    def __init__(self, parent, width=1200, height=200):
        self.canvas = tk.Canvas(parent, width=width, height=height)
        self.scenes: List[Scene] = []
        self.markers: List[Marker] = []
        self.current_time = 0.0
        self.zoom_level = 1.0  # 1.0 = 1 Pixel = 0.1s
        
    def add_scene(self, scene: Scene, position: float):
        """Füge Szene an Position hinzu"""
        
    def drag_scene(self, scene_id: str, new_position: float):
        """Verschiebe Szene via Drag&Drop"""
        
    def render_waveform(self, scene: Scene):
        """Rendere Wellenform für Szene"""
        
    def set_marker(self, time: float, label: str):
        """Setze Marker an Zeitposition"""

@dataclass
class Scene:
    """Einzelne Szene im Timeline"""
    id: str
    speaker: str
    text: str
    audio_file: Path
    start_time: float
    duration: float
    waveform_data: np.ndarray
```

#### UI-Layout

```
┌─────────────────────────────────────────────────────┐
│ ⏮️  ⏪  ▶️  ⏸️  ⏩  ⏭️   │ 00:00.0 / 05:32.4 │ Zoom: [±]│
├─────────────────────────────────────────────────────┤
│ Timeline:                                           │
│ ├─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┤ │
│ 0s    10s   20s   30s   40s   50s  1:00  1:10  1:20│
│                                                     │
│ ┌──────────┐  ┌────────┐      ┌──────────────┐    │
│ │ Host     │  │ Gast   │      │ Host         │    │
│ │~~wave~~  │  │~~wave~ │      │~~~~waveform~~│    │
│ └──────────┘  └────────┘      └──────────────┘    │
│     ▲                              ▲               │
│   Marker 1                      Marker 2           │
└─────────────────────────────────────────────────────┘
```

#### Best Practices
- **Performance:** Lazy-Loading von Waveforms (nur sichtbare)
- **UX:** Snap-to-Grid für präzise Platzierung
- **Accessibility:** Keyboard-Navigation (Arrow-Keys)

---

### 2. TTSEngineManager

**Ziel:** Modulares Multi-Engine TTS-System mit Fallbacks

#### Features
- **Modulares Engine-System**
  - Factory-Pattern für Engine-Erstellung
  - Plugin-Architektur
  - Hot-Swapping zwischen Engines
  
- **BARK Integration**
  - Hochnatürliche Stimmen
  - Emotionale Varianz
  - Lachen, Seufzen, Musik
  
- **Piper Integration**
  - Extrem schnell (CPU Real-time)
  - 50+ Sprachen
  - Geringe Ressourcen
  
- **GPU/CPU Fallback**
  - Automatische Hardware-Erkennung
  - Intelligentes Fallback
  
- **Model-Caching**
  - Max 2 Engines im RAM
  - LRU-Eviction

#### Technische Spezifikation

```python
# src/podcastforge/tts/engine_manager.py

from enum import Enum
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

class TTSEngine(Enum):
    """Unterstützte TTS-Engines"""
    XTTS = "xtts"          # Coqui XTTSv2 (Voice Cloning)
    BARK = "bark"          # Suno BARK (Natural)
    VITS = "vits"          # VITS (Fast, Quality)
    PIPER = "piper"        # Piper (CPU, Fast)
    TACOTRON2 = "tacotron2"  # Tacotron2 (Classic)
    STYLETTS2 = "styletts2"  # StyleTTS2 (SOTA)

class BaseTTSEngine(ABC):
    """Abstract Base Class für TTS-Engines"""
    
    @abstractmethod
    def load_model(self, config: Dict):
        """Lade TTS-Model"""
        
    @abstractmethod
    def synthesize(self, text: str, speaker: str, **kwargs) -> np.ndarray:
        """Generiere Audio aus Text"""
        
    @abstractmethod
    def unload(self):
        """Entlade Model aus RAM"""

class TTSEngineManager:
    """
    Verwaltet mehrere TTS-Engines
    
    Features:
    - Engine-Caching (LRU)
    - GPU/CPU Fallback
    - Load-Balancing
    """
    
    def __init__(self, max_engines: int = 2):
        self.max_engines = max_engines
        self.loaded_engines: Dict[str, BaseTTSEngine] = {}
        self.engine_usage: Dict[str, int] = {}
        
    def get_engine(self, 
                   engine_type: TTSEngine, 
                   config: Optional[Dict] = None) -> BaseTTSEngine:
        """
        Hole oder lade Engine
        
        Returns:
            BaseTTSEngine instance
        """
        engine_key = f"{engine_type.value}_{config.get('model', 'default')}"
        
        # Cache-Hit
        if engine_key in self.loaded_engines:
            self.engine_usage[engine_key] += 1
            return self.loaded_engines[engine_key]
        
        # Memory-Management
        if len(self.loaded_engines) >= self.max_engines:
            self._evict_least_used()
        
        # Load Engine
        engine = self._create_engine(engine_type, config)
        self.loaded_engines[engine_key] = engine
        self.engine_usage[engine_key] = 1
        
        return engine
    
    def _create_engine(self, 
                       engine_type: TTSEngine, 
                       config: Dict) -> BaseTTSEngine:
        """Factory für Engine-Instanzen"""
        
        if engine_type == TTSEngine.XTTS:
            from .engines.xtts import XTTSEngine
            return XTTSEngine(config)
            
        elif engine_type == TTSEngine.BARK:
            from .engines.bark import BarkEngine
            return BarkEngine(config)
            
        elif engine_type == TTSEngine.PIPER:
            from .engines.piper import PiperEngine
            return PiperEngine(config)
            
        elif engine_type == TTSEngine.STYLETTS2:
            from .engines.styletts2 import StyleTTS2Engine
            return StyleTTS2Engine(config)
        
        raise ValueError(f"Unknown engine: {engine_type}")
    
    def _evict_least_used(self):
        """LRU-Eviction"""
        least_used = min(self.engine_usage, key=self.engine_usage.get)
        self.loaded_engines[least_used].unload()
        del self.loaded_engines[least_used]
        del self.engine_usage[least_used]

# Engine-Implementierungen

class BarkEngine(BaseTTSEngine):
    """Suno BARK Engine - Hochnatürliche Stimmen"""
    
    def load_model(self, config: Dict):
        from bark import generate_audio, SAMPLE_RATE, preload_models
        preload_models()
        self.generate = generate_audio
        self.sample_rate = SAMPLE_RATE
    
    def synthesize(self, text: str, speaker: str = "v2/en_speaker_6", **kwargs):
        """
        Generiere Audio mit BARK
        
        Args:
            text: Text zu synthetisieren
            speaker: Speaker-Profil (z.B. "v2/en_speaker_6")
            **kwargs: 
                - temperature: Varianz (0.0-1.0)
                - semantic_temp: Semantic-Varianz
        """
        audio = self.generate(
            text,
            history_prompt=speaker,
            text_temp=kwargs.get('temperature', 0.7),
            waveform_temp=kwargs.get('waveform_temp', 0.7)
        )
        return audio

class PiperEngine(BaseTTSEngine):
    """Piper Engine - Schnelle CPU-TTS"""
    
    def load_model(self, config: Dict):
        from piper import PiperVoice
        self.voice = PiperVoice.load(
            config.get('model_path'),
            config_path=config.get('config_path')
        )
    
    def synthesize(self, text: str, **kwargs):
        """CPU-optimierte Synthese"""
        audio = self.voice.synthesize(text, **kwargs)
        return audio
```

#### Engine-Vergleich

| Engine | Qualität | Geschwindigkeit | GPU | Voice Cloning | Emotionen |
|--------|----------|----------------|-----|---------------|-----------|
| XTTS | ⭐⭐⭐⭐ | Mittel | Ja | ✅ Ja | ❌ Nein |
| BARK | ⭐⭐⭐⭐⭐ | Langsam | Ja | ❌ Nein | ✅ Ja |
| Piper | ⭐⭐⭐ | Sehr schnell | Nein | ❌ Nein | ❌ Nein |
| StyleTTS2 | ⭐⭐⭐⭐⭐ | Mittel | Ja | ✅ Ja (3s) | ✅ Ja |

#### Best Practices
- **Fallback-Chain:** XTTS → Piper (bei GPU-Fehler)
- **Batching:** Mehrere Zeilen parallel generieren
- **Caching:** Generierte Audio-Segmente cachen

---

## 🎯 Version 1.2 - Voice Cloning & Professional Audio

**Geplanter Release:** Januar 2025  
**Status:** 📋 Geplant

### 1. Voice Cloning mit StyleTTS2

#### Features
- 3-Sekunden Voice-Cloning
- Custom Voice Upload
- Voice-Profil-Management
- Multi-Speaker Support

#### Technische Spezifikation

```python
# src/podcastforge/voices/cloner.py

class VoiceCloner:
    """Voice Cloning mit StyleTTS2"""
    
    def clone_voice(self, 
                    audio_file: Path, 
                    voice_name: str,
                    min_duration: float = 3.0) -> VoiceProfile:
        """
        Clone Voice aus Audio-Sample
        
        Args:
            audio_file: Audio-Datei (min 3 Sekunden)
            voice_name: Name für neue Voice
            min_duration: Minimale Dauer
            
        Returns:
            VoiceProfile für neue Voice
        """
```

### 2. Multi-Track Audio-Editor

#### UI-Layout

```
┌───────────────────────────────────────────────┐
│ Track 1 (Voice)  : [████████████████]         │
│ Track 2 (Music)  : [░░░░░░░░░░░░░░░░]  -6dB   │
│ Track 3 (SFX)    : [  ███    ███    ]  -12dB  │
└───────────────────────────────────────────────┘
```

---

## 🌐 Version 2.0 - Web & Collaboration

**Geplanter Release:** Q2 2025  
**Status:** 💡 Konzept-Phase

### 1. Web-basierte Version (Gradio)

```python
import gradio as gr

def create_web_editor():
    """Erstelle Gradio Web-Editor"""
    
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🎙️ PodcastForge Editor")
        
        with gr.Row():
            script_input = gr.Textbox(
                label="Podcast-Skript",
                lines=20,
                placeholder="Host [excited]: Willkommen..."
            )
            
        with gr.Row():
            generate_btn = gr.Button("🎵 Generate Podcast")
            
        audio_output = gr.Audio(label="Generated Podcast")
        
    return app
```

### 2. KI-Skript-Assistent

#### Features
- Auto-Vervollständigung
- Dialog-Optimierung
- Emotion-Empfehlungen

```python
class AIScriptAssistant:
    """KI-Assistent für Skript-Optimierung"""
    
    def suggest_emotion(self, text: str, context: Dict) -> str:
        """Schlage passende Emotion vor"""
        
    def optimize_dialogue(self, script: List[Dict]) -> List[Dict]:
        """Optimiere Dialog-Fluss"""
        
    def autocomplete(self, partial_text: str, speaker: str) -> List[str]:
        """Auto-Vervollständigung"""
```

---

## 📊 Prioritäten

### High Priority (v1.1)
1. ⭐⭐⭐⭐⭐ TTSEngineManager
2. ⭐⭐⭐⭐⭐ BARK Integration
3. ⭐⭐⭐⭐ Timeline-Editor

### Medium Priority (v1.2)
4. ⭐⭐⭐⭐ Voice Cloning
5. ⭐⭐⭐ Multi-Track Editor
6. ⭐⭐⭐ Sound-Effekte

### Low Priority (v2.0+)
7. ⭐⭐ Web-Version
8. ⭐⭐ Collaboration
9. ⭐ Cloud-Features

---

## 🔧 Entwicklungs-Guidelines

### Code-Qualität
- **PEP 8** Style-Guide befolgen
- **Type Hints** überall verwenden
- **Docstrings** für alle Public-Methoden
- **Unit Tests** (min. 80% Coverage)

### Architecture Patterns
- **MVC** für GUI-Komponenten
- **Factory** für Engine-Erstellung
- **Strategy** für Audio-Processing
- **Observer** für Event-Handling

### Performance-Ziele
- Editor-Reaktionszeit: < 100ms
- TTS-Preview: < 5s pro Zeile
- Timeline-Rendering: 60 FPS

---

## 📚 Ressourcen

### Dependencies
```bash
# Core
python>=3.8
tkinter
pyyaml
numpy
Pillow

# TTS Engines
TTS>=0.22.0           # XTTS
bark>=0.1.0           # BARK
piper-tts>=1.2.0      # Piper
styletts2>=0.1.0      # StyleTTS2

# Audio
pydub
librosa
pygame
```

### Externe Projekte
- [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) - Voice Library
- [BARK](https://github.com/suno-ai/bark) - Natural TTS
- [Piper](https://github.com/rhasspy/piper) - Fast TTS
- [StyleTTS2](https://github.com/yl4579/StyleTTS2) - SOTA TTS

---

**Letzte Aktualisierung:** November 14, 2024  
**Autor:** PodcastForge-AI Team  
**Lizenz:** MIT
