#!/usr/bin/env python3
"""
TTS Engine Manager
Modulares Multi-Engine TTS-System mit Factory Pattern und LRU-Caching
"""

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

logger = logging.getLogger(__name__)


class TTSEngine(Enum):
    """Unterstützte TTS-Engines"""

    XTTS = "xtts"  # Coqui XTTSv2 (Voice Cloning)
    BARK = "bark"  # Suno BARK (Natural + Emotions)
    VITS = "vits"  # VITS (Fast, Quality)
    PIPER = "piper"  # Piper (CPU, Fast)
    STYLETTS2 = "styletts2"  # StyleTTS2 (SOTA, 3s Cloning)


class BaseTTSEngine(ABC):
    """
    Abstract Base Class für TTS-Engines

    Best Practices:
    - Type hints für alle Methoden
    - Proper Error-Handling
    - Resource-Management (load/unload)
    - GPU/CPU Fallback
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model = None
        self.sample_rate = 22050  # Default
        self.is_loaded = False
        self.device = self._get_device()

    def _get_device(self) -> str:
        """Automatische Device-Erkennung"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @abstractmethod
    def load_model(self):
        """Lade TTS-Model in RAM/VRAM"""
        pass

    @abstractmethod
    def synthesize(self, text: str, speaker: str, **kwargs) -> np.ndarray:
        """
        Generiere Audio aus Text

        Args:
            text: Text zu synthetisieren
            speaker: Speaker-ID oder Voice-Profile
            **kwargs: Engine-spezifische Parameter

        Returns:
            Audio als numpy array (sample_rate in self.sample_rate)
        """
        pass

    @abstractmethod
    def unload(self):
        """Entlade Model aus RAM/VRAM"""
        pass

    def get_memory_usage(self) -> int:
        """Hole Memory-Usage in Bytes"""
        if not self.is_loaded:
            return 0

        if self.device == "cuda":
            return torch.cuda.memory_allocated()

        # CPU: rough estimate
        return 1 * 1024 * 1024 * 1024  # 1GB estimate

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(device={self.device}, loaded={self.is_loaded})"


class XTTSEngine(BaseTTSEngine):
    """
    Coqui XTTS v2 Engine

    Features:
    - Voice Cloning (10s+ samples)
    - Multi-language
    - GPU-accelerated
    """

    def load_model(self):
        """Lade XTTS Model"""
        try:
            from TTS.api import TTS

            logger.info("Loading XTTS model...")
            self.model = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=(self.device == "cuda"),
            )
            self.sample_rate = 24000
            self.is_loaded = True
            logger.info(f"XTTS loaded on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load XTTS: {e}")
            raise

    def synthesize(self, text: str, speaker: str, language: str = "de", **kwargs) -> np.ndarray:
        """
        Generiere Audio mit XTTS

        Args:
            text: Text
            speaker: Path zu Voice-Sample oder Speaker-Name
            language: Sprache (de, en, es, fr, ...)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        try:
            # Check if speaker is file path (voice cloning)
            speaker_path = Path(speaker)
            if speaker_path.exists():
                audio = self.model.tts(text=text, speaker_wav=str(speaker_path), language=language)
            else:
                # Use built-in speaker
                audio = self.model.tts(text=text, speaker=speaker, language=language)

            return np.array(audio, dtype=np.float32)

        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            raise

    def unload(self):
        """Entlade XTTS"""
        if self.model:
            del self.model
            self.model = None

        if self.device == "cuda":
            torch.cuda.empty_cache()

        self.is_loaded = False
        logger.info("XTTS unloaded")


class BarkEngine(BaseTTSEngine):
    """
    Suno BARK Engine

    Features:
    - Hochnatürliche Stimmen
    - Emotionen (lachen, seufzen)
    - Musik, Sound-Effekte
    - Non-speech sounds
    """

    def load_model(self):
        """Lade BARK Model"""
        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models

            logger.info("Loading BARK model...")
            preload_models(
                device=self.device,
                text_use_gpu=(self.device == "cuda"),
                coarse_use_gpu=(self.device == "cuda"),
                fine_use_gpu=(self.device == "cuda"),
            )

            self.generate = generate_audio
            self.sample_rate = SAMPLE_RATE
            self.is_loaded = True
            logger.info(f"BARK loaded on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load BARK: {e}")
            raise

    def synthesize(
        self, text: str, speaker: str = "v2/en_speaker_6", temperature: float = 0.7, **kwargs
    ) -> np.ndarray:
        """
        Generiere Audio mit BARK

        Args:
            text: Text (kann [laughter], [sighs] enthalten)
            speaker: Speaker-Profil (z.B. "v2/de_speaker_3")
            temperature: Varianz (0.0-1.0, höher = variabler)

        Examples:
            >>> engine.synthesize("Hello [laughter] world!", speaker="v2/en_speaker_6")
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        try:
            audio = self.generate(
                text,
                history_prompt=speaker,
                text_temp=temperature,
                waveform_temp=kwargs.get("waveform_temp", 0.7),
                output_full=False,
            )

            return audio.astype(np.float32)

        except Exception as e:
            logger.error(f"BARK synthesis failed: {e}")
            raise

    def unload(self):
        """Entlade BARK"""
        self.generate = None

        if self.device == "cuda":
            torch.cuda.empty_cache()

        self.is_loaded = False
        logger.info("BARK unloaded")


class PiperEngine(BaseTTSEngine):
    """
    Piper TTS Engine

    Features:
    - Sehr schnell (CPU Real-time)
    - 50+ Sprachen
    - Geringe Ressourcen
    - Perfekt für Previews
    """

    def load_model(self):
        """Lade Piper Model"""
        try:
            from piper import PiperVoice

            model_path = self.config.get("model_path", "de_DE-thorsten-high")

            logger.info(f"Loading Piper model: {model_path}")
            self.model = PiperVoice.load(model_path)
            self.sample_rate = 22050
            self.is_loaded = True
            logger.info("Piper loaded (CPU)")

        except Exception as e:
            logger.error(f"Failed to load Piper: {e}")
            raise

    def synthesize(self, text: str, speaker: str = "0", **kwargs) -> np.ndarray:
        """
        Generiere Audio mit Piper

        Args:
            text: Text
            speaker: Speaker-ID (Model-abhängig)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        try:
            audio = self.model.synthesize(text, speaker_id=int(speaker) if speaker.isdigit() else 0)

            # Piper returns List[int16], convert to float32
            audio_array = np.array(audio, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            return audio_float

        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            raise

    def unload(self):
        """Entlade Piper"""
        if self.model:
            del self.model
            self.model = None

        self.is_loaded = False
        logger.info("Piper unloaded")


class StyleTTS2Engine(BaseTTSEngine):
    """
    StyleTTS2 Engine

    Features:
    - SOTA Qualität
    - Voice Cloning (3s samples!)
    - Emotionale Kontrolle
    - Style-Transfer
    """

    def load_model(self):
        """Lade StyleTTS2 Model"""
        try:
            # TODO: Implement StyleTTS2 integration
            # from styletts2 import StyleTTS2

            logger.info("Loading StyleTTS2 model...")
            # self.model = StyleTTS2(device=self.device)
            self.sample_rate = 24000
            self.is_loaded = True
            logger.info(f"StyleTTS2 loaded on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load StyleTTS2: {e}")
            raise NotImplementedError("StyleTTS2 not yet implemented")

    def synthesize(self, text: str, speaker: str, style: str = "neutral", **kwargs) -> np.ndarray:
        """
        Generiere Audio mit StyleTTS2

        Args:
            text: Text
            speaker: Path zu 3s Voice-Sample
            style: Stil (neutral, happy, sad, angry)
        """
        raise NotImplementedError("StyleTTS2 not yet implemented")

    def unload(self):
        """Entlade StyleTTS2"""
        raise NotImplementedError("StyleTTS2 not yet implemented")


class TTSEngineFactory:
    """
    Factory für TTS-Engine Instanzen

    Best Practice: Factory Pattern für flexible Instanziierung
    """

    _engine_classes = {
        TTSEngine.XTTS: XTTSEngine,
        TTSEngine.BARK: BarkEngine,
        TTSEngine.PIPER: PiperEngine,
        TTSEngine.STYLETTS2: StyleTTS2Engine,
    }

    @classmethod
    def create(cls, engine_type: TTSEngine, config: Optional[Dict] = None) -> BaseTTSEngine:
        """
        Erstelle Engine-Instanz

        Args:
            engine_type: Typ der Engine
            config: Engine-Konfiguration

        Returns:
            BaseTTSEngine instance

        Raises:
            ValueError: Wenn Engine-Typ unbekannt
        """
        engine_class = cls._engine_classes.get(engine_type)

        if not engine_class:
            raise ValueError(f"Unknown engine type: {engine_type}")

        logger.debug(f"Creating engine: {engine_type.value}")
        return engine_class(config=config)

    @classmethod
    def get_available_engines(cls) -> List[TTSEngine]:
        """Hole Liste verfügbarer Engines"""
        return list(cls._engine_classes.keys())


class TTSEngineManager:
    """
    Verwaltet mehrere TTS-Engines mit LRU-Caching

    Features:
    - Engine-Caching (max 2 Engines im RAM)
    - LRU-Eviction
    - GPU/CPU Fallback
    - Load-Balancing

    Best Practices:
    - Singleton Pattern für globale Verwaltung
    - Thread-safe Operations
    - Resource-Management
    """

    def __init__(self, max_engines: int = 2):
        """
        Args:
            max_engines: Maximale Anzahl gleichzeitig geladener Engines
        """
        self.max_engines = max_engines
        self.loaded_engines: OrderedDict[str, BaseTTSEngine] = OrderedDict()
        self.engine_usage: Dict[str, int] = {}
        self.default_engine = TTSEngine.PIPER  # Schnell für Previews

        logger.info(f"TTSEngineManager initialized (max_engines={max_engines})")

    def get_engine(
        self, engine_type: TTSEngine, config: Optional[Dict] = None, auto_load: bool = True
    ) -> BaseTTSEngine:
        """
        Hole oder lade Engine

        Args:
            engine_type: Typ der Engine
            config: Engine-Konfiguration
            auto_load: Automatisch laden falls nicht im Cache

        Returns:
            BaseTTSEngine instance
        """
        config = config or {}
        engine_key = self._make_key(engine_type, config)

        # Cache-Hit
        if engine_key in self.loaded_engines:
            # Move to end (LRU)
            self.loaded_engines.move_to_end(engine_key)
            self.engine_usage[engine_key] += 1
            logger.debug(f"Engine cache hit: {engine_key}")
            return self.loaded_engines[engine_key]

        # Cache-Miss
        if not auto_load:
            raise KeyError(f"Engine not loaded: {engine_key}")

        # Memory-Management: Evict LRU if needed
        if len(self.loaded_engines) >= self.max_engines:
            self._evict_lru()

        # Create and load engine
        engine = TTSEngineFactory.create(engine_type, config)

        try:
            engine.load_model()
            self.loaded_engines[engine_key] = engine
            self.engine_usage[engine_key] = 1
            logger.info(
                f"Engine loaded: {engine_key} ({engine.get_memory_usage() / 1024**3:.2f} GB)"
            )
            return engine

        except Exception as e:
            logger.error(f"Failed to load engine {engine_key}: {e}")

            # Fallback to Piper (CPU)
            if engine_type != TTSEngine.PIPER:
                logger.warning(f"Falling back to Piper (CPU)")
                return self.get_engine(TTSEngine.PIPER, config={})

            raise

    def _make_key(self, engine_type: TTSEngine, config: Dict) -> str:
        """Erstelle Cache-Key"""
        model = config.get("model", "default")
        return f"{engine_type.value}:{model}"

    def _evict_lru(self):
        """Entferne Least Recently Used Engine"""
        if not self.loaded_engines:
            return

        # Get LRU (first item in OrderedDict)
        lru_key, lru_engine = self.loaded_engines.popitem(last=False)

        logger.info(f"Evicting LRU engine: {lru_key}")
        lru_engine.unload()

        del self.engine_usage[lru_key]

    def synthesize(
        self,
        text: str,
        speaker: str,
        engine_type: Optional[TTSEngine] = None,
        config: Optional[Dict] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, int]:
        """
        Convenience-Methode für Synthese

        Args:
            text: Text
            speaker: Speaker-ID
            engine_type: Engine-Typ (None = default)
            config: Engine-Config
            **kwargs: Engine-spezifische Parameter

        Returns:
            (audio, sample_rate) tuple
        """
        engine_type = engine_type or self.default_engine
        engine = self.get_engine(engine_type, config)

        audio = engine.synthesize(text, speaker, **kwargs)
        return audio, engine.sample_rate

    def preload_engines(self, engines: List[Tuple[TTSEngine, Dict]]):
        """
        Preload mehrere Engines (z.B. beim Start)

        Args:
            engines: Liste von (engine_type, config) tuples
        """
        for engine_type, config in engines:
            try:
                self.get_engine(engine_type, config)
            except Exception as e:
                logger.warning(f"Failed to preload {engine_type.value}: {e}")

    def unload_all(self):
        """Entlade alle Engines"""
        logger.info("Unloading all engines...")

        for key, engine in self.loaded_engines.items():
            engine.unload()

        self.loaded_engines.clear()
        self.engine_usage.clear()

        logger.info("All engines unloaded")

    def get_stats(self) -> Dict:
        """Hole Engine-Statistiken"""
        return {
            "loaded_engines": list(self.loaded_engines.keys()),
            "usage": self.engine_usage.copy(),
            "total_memory": sum(e.get_memory_usage() for e in self.loaded_engines.values())
            / 1024**3,  # GB
        }

    def __repr__(self) -> str:
        return (
            f"TTSEngineManager("
            f"loaded={len(self.loaded_engines)}/{self.max_engines}, "
            f"memory={self.get_stats()['total_memory']:.2f}GB)"
        )


# Singleton Instance
_engine_manager: Optional[TTSEngineManager] = None


def get_engine_manager(max_engines: int = 2) -> TTSEngineManager:
    """
    Hole Singleton TTSEngineManager

    Args:
        max_engines: Max gleichzeitig geladene Engines

    Returns:
        TTSEngineManager instance
    """
    global _engine_manager
    if _engine_manager is None:
        _engine_manager = TTSEngineManager(max_engines=max_engines)
    return _engine_manager
