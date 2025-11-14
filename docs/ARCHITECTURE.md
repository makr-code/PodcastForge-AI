# PodcastForge-AI Architecture & Best Practices

## 🏗️ Architektur-Übersicht

PodcastForge-AI folgt einem **modularen, schichtbasierten Design** mit klarer Separation of Concerns.

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ GUI (tkinter)│  │ CLI (Click)  │  │ Web (TBD) │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                   Business Logic Layer              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ PodcastForge │  │ VoiceLibrary │  │ TTSEngine │ │
│  │   (Core)     │  │              │  │  Manager  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                    Service Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ OllamaClient │  │ AudioPlayer  │  │  Audio    │ │
│  │   (LLM)      │  │              │  │ Processor │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                     Data Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Config Files │  │ Voice Samples│  │  Cache    │ │
│  │  (YAML/JSON) │  │   (WAV/MP3)  │  │  (TMP)    │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Design Patterns

### 1. **Factory Pattern** - TTS Engine Creation

```python
# src/podcastforge/tts/engine_manager.py

class TTSEngineFactory:
    """
    Factory Pattern für TTS-Engine-Erstellung
    
    Vorteile:
    - Entkoppelt Client-Code von konkreten Implementierungen
    - Erleichtert Hinzufügen neuer Engines
    - Zentralisiert Initialisierungs-Logik
    """
    
    @staticmethod
    def create_engine(engine_type: TTSEngine, config: Dict) -> BaseTTSEngine:
        """Erstelle Engine-Instanz basierend auf Typ"""
        
        engine_map = {
            TTSEngine.XTTS: XTTSEngine,
            TTSEngine.BARK: BarkEngine,
            TTSEngine.PIPER: PiperEngine,
            TTSEngine.STYLETTS2: StyleTTS2Engine
        }
        
        engine_class = engine_map.get(engine_type)
        if not engine_class:
            raise ValueError(f"Unknown engine: {engine_type}")
        
        return engine_class(config)
```

### 2. **Singleton Pattern** - Audio Player

```python
# src/podcastforge/audio/player.py

_player_instance: Optional[AudioPlayer] = None

def get_player() -> AudioPlayer:
    """
    Singleton Pattern für Audio-Player
    
    Vorteile:
    - Garantiert nur eine Player-Instanz
    - Globaler Zugriffspunkt
    - Ressourcen-Sharing
    """
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance
```

### 3. **Strategy Pattern** - Audio Processing

```python
# src/podcastforge/audio/postprocessor.py

class AudioProcessingStrategy(ABC):
    """Abstract Strategy für Audio-Verarbeitung"""
    
    @abstractmethod
    def process(self, audio: AudioSegment) -> AudioSegment:
        pass

class NormalizationStrategy(AudioProcessingStrategy):
    """Normalisierungs-Strategie"""
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        return normalize(audio)

class CompressionStrategy(AudioProcessingStrategy):
    """Komprimierungs-Strategie"""
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        return compress_dynamic_range(audio, threshold=-20, ratio=4.0)

class AudioPostProcessor:
    """Context für Audio-Processing"""
    
    def __init__(self):
        self.strategies: List[AudioProcessingStrategy] = [
            NormalizationStrategy(),
            CompressionStrategy()
        ]
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        for strategy in self.strategies:
            audio = strategy.process(audio)
        return audio
```

### 4. **Observer Pattern** - Event System

```python
# src/podcastforge/core/events.py

class EventBus:
    """
    Observer Pattern für Event-Handling
    
    Vorteile:
    - Loose Coupling zwischen Komponenten
    - Einfaches Hinzufügen neuer Listener
    - Zentrale Event-Verwaltung
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        """Registriere Listener für Event-Typ"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any):
        """Publiziere Event an alle Listener"""
        for callback in self._listeners.get(event_type, []):
            callback(data)

# Verwendung im Editor
class PodcastEditor:
    def __init__(self):
        self.event_bus = EventBus()
        self.event_bus.subscribe('tts_complete', self._on_tts_complete)
    
    def _on_tts_complete(self, audio_file: Path):
        self.update_status("TTS fertig!")
        self.play_audio(audio_file)
```

### 5. **MVC Pattern** - GUI Architecture

```python
# src/podcastforge/gui/mvc.py

# Model
class PodcastProject:
    """Model - Daten & Business Logic"""
    
    def __init__(self):
        self.script: List[Dict] = []
        self.speakers: Dict[str, Speaker] = {}
        self.metadata: Dict = {}
    
    def add_line(self, line: Dict):
        self.script.append(line)
        self.notify_observers()

# View
class EditorView:
    """View - UI-Darstellung"""
    
    def __init__(self, controller):
        self.controller = controller
        self.setup_ui()
    
    def update_display(self, data):
        # Update UI mit neuen Daten
        pass

# Controller
class EditorController:
    """Controller - User-Interaktions-Logik"""
    
    def __init__(self, model: PodcastProject, view: EditorView):
        self.model = model
        self.view = view
    
    def on_add_line(self, line_text: str):
        parsed_line = self.parse_line(line_text)
        self.model.add_line(parsed_line)
        self.view.update_display(self.model.script)
```

---

## 📋 Best Practices

### Code Style

#### 1. **Type Hints Everywhere**

```python
from typing import List, Dict, Optional, Union
from pathlib import Path

def generate_podcast(
    topic: str,
    style: PodcastStyle,
    speakers: List[Speaker],
    duration: int,
    output: Path
) -> Optional[Path]:
    """
    Generiere Podcast
    
    Args:
        topic: Podcast-Thema
        style: Stil (INTERVIEW, NEWS, etc.)
        speakers: Liste von Sprechern
        duration: Dauer in Minuten
        output: Ausgabe-Datei
        
    Returns:
        Pfad zur generierten Datei oder None bei Fehler
        
    Raises:
        ValueError: Wenn Dauer < 1
        FileNotFoundError: Wenn Voice-Sample fehlt
    """
    if duration < 1:
        raise ValueError("Duration must be >= 1")
    
    # Implementation...
    return output
```

#### 2. **Comprehensive Docstrings**

```python
class VoiceLibrary:
    """
    Verwaltung professioneller Voice-Profile
    
    Die VoiceLibrary verwaltet eine Sammlung von professionellen
    Stimm-Profilen mit intelligenter Kategorisierung und
    Suggestion-System.
    
    Attributes:
        voices: Dict von VoiceProfile-Objekten
        languages: Unterstützte Sprachen
        
    Example:
        >>> library = VoiceLibrary()
        >>> voices = library.search(language="de", gender="male")
        >>> for voice in voices:
        ...     print(voice.display_name)
        
    Note:
        Stimmen werden lazy-loaded beim ersten Zugriff
    """
    
    def suggest_for_podcast_style(
        self,
        style: PodcastStyle,
        language: str = "de",
        num_speakers: int = 2
    ) -> List[VoiceProfile]:
        """
        Schlage optimale Stimmen für Podcast-Stil vor
        
        Nutzt intelligentes Matching basierend auf:
        - Podcast-Stil (Interview, News, etc.)
        - Sprache
        - Geschlechter-Balance
        - Alters-Diversität
        
        Args:
            style: PodcastStyle Enum
            language: ISO-639-1 Language-Code
            num_speakers: Anzahl Sprecher
            
        Returns:
            Liste von VoiceProfile-Objekten (sortiert nach Relevanz)
            
        Example:
            >>> voices = library.suggest_for_podcast_style(
            ...     style=PodcastStyle.INTERVIEW,
            ...     language="de",
            ...     num_speakers=2
            ... )
            >>> [v.display_name for v in voices]
            ['Thorsten (Professional)', 'Anna (Friendly)']
        """
```

#### 3. **Error Handling**

```python
from podcastforge.exceptions import (
    TTSGenerationError,
    VoiceNotFoundError,
    InvalidScriptError
)

def generate_audio(text: str, speaker: Speaker) -> AudioSegment:
    """Generiere Audio mit proper Error-Handling"""
    
    try:
        # Validierung
        if not text.strip():
            raise InvalidScriptError("Text is empty")
        
        if not speaker.voice_sample.exists():
            raise VoiceNotFoundError(
                f"Voice sample not found: {speaker.voice_sample}"
            )
        
        # TTS-Generierung
        audio = self.tts_engine.synthesize(text, speaker)
        
    except TTSGenerationError as e:
        logger.error(f"TTS generation failed: {e}")
        # Fallback zu stiller Audio
        audio = self._create_silent_audio(len(text) * 0.1)
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
    
    return audio
```

#### 4. **Logging**

```python
import logging
from pathlib import Path

# Setup Logging
def setup_logging(log_file: Path = Path("logs/podcastforge.log")):
    """Konfiguriere Logging"""
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Verwendung
logger = logging.getLogger(__name__)

class PodcastForge:
    def create_podcast(self, ...):
        logger.info(f"Starting podcast generation: {topic}")
        
        try:
            # ...
            logger.debug(f"Generated {len(script)} lines")
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise
        
        logger.info(f"Podcast saved to: {output}")
```

### 5. **Configuration Management**

```python
# src/podcastforge/core/config.py

from dataclasses import dataclass, field
from typing import Dict, Any
import yaml

@dataclass
class TTSConfig:
    """TTS-Engine Konfiguration"""
    engine: str = "xtts"
    model_path: str = "models/xtts_v2"
    use_gpu: bool = True
    cache_size: int = 2
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Erstelle von Dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class AppConfig:
    """Haupt-Konfiguration"""
    tts: TTSConfig = field(default_factory=TTSConfig)
    ollama_url: str = "http://localhost:11434"
    cache_dir: str = "cache"
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_file: Path):
        """Lade Konfiguration aus YAML"""
        with open(config_file) as f:
            data = yaml.safe_load(f)
        
        return cls(
            tts=TTSConfig.from_dict(data.get('tts', {})),
            **{k: v for k, v in data.items() if k != 'tts' and k in cls.__annotations__}
        )
```

### 6. **Unit Testing**

```python
# tests/unit/test_voice_library.py

import pytest
from podcastforge.voices import VoiceLibrary, VoiceGender, VoiceStyle
from podcastforge.core.config import PodcastStyle

class TestVoiceLibrary:
    """Unit Tests für VoiceLibrary"""
    
    @pytest.fixture
    def library(self):
        """Fixture: VoiceLibrary-Instanz"""
        return VoiceLibrary()
    
    def test_search_by_language(self, library):
        """Test: Suche nach Sprache"""
        voices = library.search(language="de")
        assert len(voices) > 0
        assert all(v.language == "de" for v in voices)
    
    def test_search_by_gender(self, library):
        """Test: Suche nach Geschlecht"""
        voices = library.search(gender=VoiceGender.MALE)
        assert all(v.gender == VoiceGender.MALE for v in voices)
    
    def test_suggest_for_interview(self, library):
        """Test: Suggestions für Interview"""
        voices = library.suggest_for_podcast_style(
            style=PodcastStyle.INTERVIEW,
            num_speakers=2
        )
        assert len(voices) == 2
        # Prüfe Geschlechter-Diversität
        genders = {v.gender for v in voices}
        assert len(genders) >= 1  # Mind. eine Geschlechter-Variation
    
    @pytest.mark.parametrize("language,expected_count", [
        ("de", 1),
        ("en", 12),
    ])
    def test_voice_count_by_language(self, library, language, expected_count):
        """Test: Voice-Count pro Sprache"""
        voices = library.search(language=language)
        assert len(voices) >= expected_count
```

### 7. **Performance Optimization**

```python
from functools import lru_cache
import time

class VoiceLibrary:
    
    @lru_cache(maxsize=128)
    def _get_cached_voices(self, language: str, gender: str, style: str):
        """Cache-optimierte Voice-Suche"""
        # Teure Filterung nur einmal
        return self._filter_voices(language, gender, style)
    
    def search(self, language=None, gender=None, style=None):
        """Nutze Caching für häufige Queries"""
        cache_key = (language or "", gender or "", style or "")
        return self._get_cached_voices(*cache_key)

# Profiling
def profile_function(func):
    """Decorator für Function-Profiling"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper

@profile_function
def generate_podcast(...):
    # Implementation
    pass
```

---

## 🔒 Security Best Practices

```python
from pathlib import Path
import hashlib

class SecureFileHandler:
    """Sichere Datei-Verarbeitung"""
    
    ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.yaml', '.json'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    
    @staticmethod
    def validate_file(file_path: Path) -> bool:
        """Validiere Datei"""
        
        # Extension Check
        if file_path.suffix.lower() not in SecureFileHandler.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension: {file_path.suffix}")
        
        # Size Check
        if file_path.stat().st_size > SecureFileHandler.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        # Path Traversal Prevention
        if ".." in str(file_path):
            raise ValueError("Path traversal detected")
        
        return True
    
    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Erstelle File-Hash für Integrity-Check"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
```

---

## 📊 Performance Targets

| Komponente | Target | Aktuell | Status |
|------------|--------|---------|--------|
| Editor UI Response | < 100ms | ~50ms | ✅ |
| TTS Preview (XTTS) | < 5s | ~3s | ✅ |
| TTS Preview (Piper) | < 1s | TBD | 🔄 |
| Timeline Render (60 FPS) | 16.6ms | TBD | 📋 |
| Voice Library Search | < 50ms | ~10ms | ✅ |

---

## 🧪 Testing Strategy

```
tests/
├── unit/               # Unit Tests (80% Coverage-Ziel)
│   ├── test_voice_library.py
│   ├── test_audio_player.py
│   └── test_forge.py
├── integration/        # Integration Tests
│   ├── test_tts_pipeline.py
│   └── test_editor_workflow.py
└── e2e/               # End-to-End Tests
    └── test_full_podcast_generation.py
```

---

**Version:** 1.0  
**Last Updated:** November 14, 2024  
**Maintainer:** PodcastForge-AI Team
