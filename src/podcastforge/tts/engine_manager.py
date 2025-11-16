#!/usr/bin/env python3
"""
TTS Engine Manager
Modulares Multi-Engine TTS-System mit Factory Pattern und LRU-Caching
"""

import logging
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import threading
import contextlib
import hashlib

logger = logging.getLogger(__name__)


def _get_models_dir() -> Path:
    """Lokaler Models-Ordner (offline-first).

    Prüft die Umgebungsvariable `PF_MODELS_DIR`, ansonsten `./models` im Projektroot.
    Gibt ein Path-Objekt zurück (existiert möglicherweise noch nicht).
    """
    env = os.getenv("PF_MODELS_DIR")
    if env:
        return Path(env)
    # Default to repository-relative models folder
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "models"


class CancelledError(Exception):
    """Raised when a synth operation was cancelled cooperatively."""
    pass


class TTSEngine(Enum):
    """Unterstützte TTS-Engines"""

    XTTS = "xtts"  # Coqui XTTSv2 (Voice Cloning)
    BARK = "bark"  # Suno BARK (Natural + Emotions)
    VITS = "vits"  # VITS (Fast, Quality)
    PIPER = "piper"  # Piper (CPU, Fast)
    DUMMY = "dummy"  # Local dummy engine for testing (sine wave)
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

    # Context manager support to simplify safe load/unload usage
    def __enter__(self):
        if not self.is_loaded:
            try:
                self.load_model()
            except Exception:
                # propagate to caller
                raise
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.unload()
        except Exception:
            # Do not suppress original exceptions
            pass


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
            # Prefer local copy if present (offline-first)
            models_dir = _get_models_dir()
            local_model = models_dir / "tts_models_multilingual_multi-dataset_xtts_v2"
            if local_model.exists():
                logger.info(f"Found local XTTS model at {local_model}, loading offline")
                model_name = str(local_model)
            else:
                model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

            self.model = TTS(
                model_name=model_name,
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

        cancel_event = kwargs.get('cancel_event')
        progress_cb = kwargs.get('progress_callback')

        try:
            # cooperative cancel: check before starting
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("XTTS synthesis cancelled before start")

            # best-effort progress callback: started
            if progress_cb:
                try:
                    progress_cb(0.0, 'start')
                except Exception:
                    pass

            # Check if speaker is file path (voice cloning)
            speaker_path = Path(speaker)
            if speaker_path.exists():
                audio = self.model.tts(text=text, speaker_wav=str(speaker_path), language=language)
            else:
                # Use built-in speaker
                audio = self.model.tts(text=text, speaker=speaker, language=language)

            # cooperative cancel: check after generation
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("XTTS synthesis cancelled after generation")

            # best-effort progress callback: processing / done
            if progress_cb:
                try:
                    progress_cb(0.7, 'processing')
                except Exception:
                    pass
                try:
                    progress_cb(1.0, 'done')
                except Exception:
                    pass

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
            # If a local models directory exists, point HF cache-related envs
            # there so bark/huggingface loads models from disk (offline-first).
            models_dir = _get_models_dir()
            if models_dir.exists():
                logger.info(f"Using local models dir for Bark/HF cache: {models_dir}")
                os.environ.setdefault("HF_HOME", str(models_dir))
                os.environ.setdefault("TRANSFORMERS_CACHE", str(models_dir))
                os.environ.setdefault("TORCH_HOME", str(models_dir))

            # Attempt to preload models. Different bark versions accept
            # different `preload_models` signatures. We'll try the newer
            # signature first and fall back to the no-arg version. During
            # the load we temporarily allow the numpy scalar global for
            # torch.serialization and monkeypatch `torch.load` to pass
            # `weights_only=False` so legacy checkpoints can be restored.
            try:
                import numpy.core.multiarray as _multiarray
                _scalar = getattr(_multiarray, "scalar", None)
            except Exception:
                _scalar = None

            def _do_preload():
                orig_load = torch.load

                def _wrapped_load(f, *a, **k):
                    if "weights_only" not in k:
                        k["weights_only"] = False
                    return orig_load(f, *a, **k)

                try:
                    torch.load = _wrapped_load

                    ser = getattr(torch, "serialization", None)
                    if _scalar is not None and ser is not None and hasattr(ser, "safe_globals"):
                        with ser.safe_globals([_scalar]):
                            try:
                                preload_models(
                                    device=self.device,
                                    text_use_gpu=(self.device == "cuda"),
                                    coarse_use_gpu=(self.device == "cuda"),
                                    fine_use_gpu=(self.device == "cuda"),
                                )
                                return
                            except TypeError:
                                # fallback to no-arg
                                preload_models()
                                return

                    # If we reach here either scalar/ser not available or
                    # safe_globals not present — try with device args and
                    # fallback to no-arg, all while torch.load is patched.
                    try:
                        preload_models(
                            device=self.device,
                            text_use_gpu=(self.device == "cuda"),
                            coarse_use_gpu=(self.device == "cuda"),
                            fine_use_gpu=(self.device == "cuda"),
                        )
                    except TypeError:
                        preload_models()

                finally:
                    try:
                        torch.load = orig_load
                    except Exception:
                        pass

            _do_preload()

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

        cancel_event = kwargs.get('cancel_event')
        progress_cb = kwargs.get('progress_callback')

        try:
            # cooperative cancel before start
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("BARK synthesis cancelled before start")

            # best-effort progress callback: started
            if progress_cb:
                try:
                    progress_cb(0.0, 'start')
                except Exception:
                    pass

            audio = self.generate(
                text,
                history_prompt=speaker,
                text_temp=temperature,
                waveform_temp=kwargs.get("waveform_temp", 0.7),
                output_full=False,
            )

            # cooperative cancel after generation
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("BARK synthesis cancelled after generation")

            # best-effort progress callbacks
            if progress_cb:
                try:
                    progress_cb(0.9, 'processing')
                    progress_cb(1.0, 'done')
                except Exception:
                    pass

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

            # Check for local copy in models dir
            models_dir = _get_models_dir()
            local_candidate = models_dir / model_path
            if local_candidate.exists():
                logger.info(f"Found local Piper model candidate at {local_candidate}")
                # If the candidate is a directory, prefer a contained .onnx file or
                # the onnx.json manifest if present. This helps when assets are
                # downloaded into a subfolder (e.g. models/piper/<voice_key>/).
                if local_candidate.is_dir():
                    # search for .onnx first
                    onnx_files = list(local_candidate.glob('*.onnx'))
                    if onnx_files:
                        load_target = str(onnx_files[0])
                    else:
                        # fallback to onnx.json manifest inside the folder
                        json_files = list(local_candidate.glob('*.json'))
                        if json_files:
                            load_target = str(json_files[0])
                        else:
                            load_target = str(local_candidate)
                else:
                    load_target = str(local_candidate)
            else:
                logger.info(f"Loading Piper model: {model_path}")
                load_target = model_path

            self.model = PiperVoice.load(load_target)
            # If the loaded PiperVoice exposes a config with sample_rate,
            # prefer that so downstream WAV/ffmpeg uses the correct rate.
            try:
                self.sample_rate = int(getattr(self.model, 'config', {}).get('sample_rate', 22050))
            except Exception:
                # model.config may be an object, not a dict
                try:
                    self.sample_rate = int(getattr(self.model.config, 'sample_rate', 22050))
                except Exception:
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

        cancel_event = kwargs.get('cancel_event')
        progress_cb = kwargs.get('progress_callback')

        try:
            # cooperative cancel before start
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("Piper synthesis cancelled before start")

            # best-effort progress callback: started
            if progress_cb:
                try:
                    progress_cb(0.0, 'start')
                except Exception:
                    pass

            # Some Piper implementations expect the speaker id as a positional
            # argument rather than a keyword. Pass it positionally to be
            # compatible with multiple piper versions.
            # Be permissive: if `speaker` is a numeric string, convert to int;
            # otherwise pass the value through (some Piper versions accept
            # non-int speaker descriptors). Guard against generators/iterables.
            # Normalize speaker: protect against generators/iterables being
            # passed in (these can come from caller mistakes). If speaker is
            # an iterable but not a string/bytes, attempt to extract a single
            # representative value (first element). Fall back to 0 on error.
            try:
                if isinstance(speaker, (list, tuple)) and len(speaker) > 0:
                    speaker_val = speaker[0]
                elif not isinstance(speaker, (str, bytes)) and hasattr(speaker, '__iter__'):
                    try:
                        speaker_val = next(iter(speaker))
                    except Exception:
                        speaker_val = speaker
                else:
                    speaker_val = speaker

                if isinstance(speaker_val, (str, bytes)) and str(speaker_val).isdigit():
                    spk = int(speaker_val)
                else:
                    spk = speaker_val
            except Exception:
                spk = 0

            # Piper expects a SynthesisConfig (or similar) as second arg.
            # If caller provided an int/str speaker id, create a SynthesisConfig
            # with that speaker_id. If caller already passed a config-like
            # object (has attribute speaker_id), pass it through.
            try:
                from piper.config import SynthesisConfig
            except Exception:
                SynthesisConfig = None

            syn_cfg = None
            if hasattr(spk, 'speaker_id'):
                syn_cfg = spk
            else:
                # Try to build a SynthesisConfig when possible
                try:
                    if SynthesisConfig is not None:
                        if isinstance(spk, (int,)):
                            syn_cfg = SynthesisConfig(speaker_id=spk)
                        elif isinstance(spk, (str, bytes)) and str(spk).isdigit():
                            syn_cfg = SynthesisConfig(speaker_id=int(spk))
                        else:
                            syn_cfg = SynthesisConfig()
                    else:
                        syn_cfg = spk
                except Exception:
                    syn_cfg = spk

            audio = self.model.synthesize(text, syn_cfg)

            # cooperative cancel after generation
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                raise CancelledError("Piper synthesis cancelled after generation")

            # best-effort progress callbacks
            if progress_cb:
                try:
                    progress_cb(0.9, 'processing')
                    progress_cb(1.0, 'done')
                except Exception:
                    pass

            # Piper may return a generator/iterable, bytes, numpy array, or
            # a list of chunks. Materialize safely and handle common types.

            def _materialize_and_convert(a):
                """
                Normalize different Piper outputs into a single float32 numpy
                array in range [-1,1]. Supported forms:
                - Iterable of AudioChunk-like objects (has attribute
                  `audio_float_array`) -> concatenate their audio_float_array
                - Iterable of numpy arrays or lists of ints/float -> concat
                - bytes/bytearray representing int16 buffer -> convert
                - single numpy array -> convert
                """
                # bytes/bytearray -> int16 buffer
                if isinstance(a, (bytes, bytearray)):
                    arr = np.frombuffer(a, dtype=np.int16)
                    return arr.astype(np.float32) / 32768.0

                # numpy array -> cast
                if isinstance(a, np.ndarray):
                    # If float32 already in [-1,1], assume it's ready
                    if a.dtype == np.float32 or a.dtype == np.float64:
                        return a.astype(np.float32)
                    return a.astype(np.float32) / 32768.0

                # Try to iterate and collect items
                try:
                    seq = list(a)
                except Exception:
                    raise TypeError("Unable to materialize audio from Piper output")

                if not seq:
                    return np.zeros(0, dtype=np.float32)

                first = seq[0]

                # AudioChunk-like objects (present in piper implementation)
                if hasattr(first, 'audio_float_array'):
                    parts = []
                    for ch in seq:
                        try:
                            parts.append(np.asarray(getattr(ch, 'audio_float_array'), dtype=np.float32))
                        except Exception:
                            raise TypeError("AudioChunk elements lack audio_float_array or invalid format")
                    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)

                # If chunks are numpy arrays
                if isinstance(first, np.ndarray):
                    parts = [np.asarray(p, dtype=np.float32) for p in seq]
                    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)

                # If chunks are bytes (per-chunk), convert each
                if isinstance(first, (bytes, bytearray)):
                    parts = [np.frombuffer(p, dtype=np.int16) for p in seq]
                    arr = np.concatenate(parts) if parts else np.zeros(0, dtype=np.int16)
                    return arr.astype(np.float32) / 32768.0

                # Fallback: assume sequence of numeric samples
                try:
                    arr = np.asarray(seq, dtype=np.float32)
                    # If values look like int16 range, scale accordingly
                    if arr.dtype != np.float32:
                        arr = arr.astype(np.float32)
                    if arr.size and np.max(np.abs(arr)) > 1.1:
                        # Likely int16 range
                        arr = arr / 32768.0
                    return arr
                except Exception:
                    raise TypeError("Unable to convert Piper output to audio array")

            audio_float = _materialize_and_convert(audio)
            return audio_float

        except Exception as e:
            logger.exception("Piper synthesis failed")
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
        TTSEngine.DUMMY: None,  # will be filled later with DummyEngine
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
        # Reference counts for acquired engines (for deterministic release)
        self._ref_counts: Dict[str, int] = {}
        self.default_engine = TTSEngine.PIPER  # Schnell für Previews
        # Lock to protect cache operations and make manager thread-safe
        self._lock = threading.RLock()

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

        # First quick check under lock for cache hit
        with self._lock:
            if engine_key in self.loaded_engines:
                # Move to end (LRU)
                self.loaded_engines.move_to_end(engine_key)
                self.engine_usage[engine_key] = self.engine_usage.get(engine_key, 0) + 1
                self._ref_counts[engine_key] = self._ref_counts.get(engine_key, 0) + 1
                logger.debug(f"Engine cache hit: {engine_key}")
                return self.loaded_engines[engine_key]

            if not auto_load:
                raise KeyError(f"Engine not loaded: {engine_key}")

            # Evict LRU if needed (do under lock)
            if len(self.loaded_engines) >= self.max_engines:
                self._evict_lru()
        # Create and load engine outside lock (avoid blocking other threads)
        engine = TTSEngineFactory.create(engine_type, config)

        try:
            engine.load_model()
        except Exception as e:
            logger.error(f"Failed to load engine {engine_key}: {e}")

            # Fallback to Piper (CPU)
            if engine_type != TTSEngine.PIPER:
                logger.warning(f"Falling back to Piper (CPU)")
                return self.get_engine(TTSEngine.PIPER, config={})

            raise

        # Insert into cache under lock, but double-check in case another thread
        # loaded the same engine in the meantime
        with self._lock:
            if engine_key in self.loaded_engines:
                # Another thread already loaded it; discard our instance
                try:
                    engine.unload()
                except Exception:
                    pass
                self.loaded_engines.move_to_end(engine_key)
                self.engine_usage[engine_key] = self.engine_usage.get(engine_key, 0) + 1
                return self.loaded_engines[engine_key]

            self.loaded_engines[engine_key] = engine
            self.engine_usage[engine_key] = self.engine_usage.get(engine_key, 0) + 1
            self._ref_counts[engine_key] = self._ref_counts.get(engine_key, 0) + 1
            logger.info(
                f"Engine loaded: {engine_key} ({engine.get_memory_usage() / 1024**3:.2f} GB)"
            )
            return engine

    def _make_key(self, engine_type: TTSEngine, config: Dict) -> str:
        """Erstelle Cache-Key"""
        # Create a stable key from engine type and relevant config items.
        # We hash sorted config items to keep the key compact.
        if not config:
            return f"{engine_type.value}:default"

        try:
            items = tuple(sorted((k, str(v)) for k, v in config.items()))
            digest = hashlib.sha1(str(items).encode()).hexdigest()[:8]
            return f"{engine_type.value}:{digest}"
        except Exception:
            # Fallback
            return f"{engine_type.value}:default"

    def _evict_lru(self):
        """Entferne Least Recently Used Engine"""
        with self._lock:
            if not self.loaded_engines:
                return

            # Get LRU (first item in OrderedDict)
            lru_key, lru_engine = self.loaded_engines.popitem(last=False)

            logger.info(f"Evicting LRU engine: {lru_key}")
            try:
                lru_engine.unload()
            except Exception as e:
                logger.warning(f"Error while unloading engine {lru_key}: {e}")

            if lru_key in self.engine_usage:
                del self.engine_usage[lru_key]

    def release_engine(self, engine_type: TTSEngine, config: Optional[Dict] = None):
        """Release an acquired engine (decrement refcount and unload when zero)."""
        config = config or {}
        engine_key = self._make_key(engine_type, config)

        with self._lock:
            if engine_key not in self.loaded_engines:
                return

            # Decrement refcount
            self._ref_counts[engine_key] = self._ref_counts.get(engine_key, 1) - 1

            if self._ref_counts[engine_key] <= 0:
                # Fully release
                engine = self.loaded_engines.pop(engine_key)
                try:
                    engine.unload()
                except Exception as e:
                    logger.warning(f"Error while unloading engine {engine_key}: {e}")

                if engine_key in self.engine_usage:
                    del self.engine_usage[engine_key]

                if engine_key in self._ref_counts:
                    del self._ref_counts[engine_key]

    @contextlib.contextmanager
    def use_engine(self, engine_type: TTSEngine, config: Optional[Dict] = None, auto_load: bool = True):
        """Context manager to acquire and automatically release an engine.

        Usage:
            with manager.use_engine(TTSEngine.PIPER, config={"model": "..."}):
                # engine loaded and refcount increased
                ...
        """
        engine = self.get_engine(engine_type, config=config, auto_load=auto_load)
        try:
            yield engine
        finally:
            try:
                self.release_engine(engine_type, config)
            except Exception:
                pass

    def synthesize(
        self,
        text: str,
        speaker: str,
        engine_type: Optional[TTSEngine] = None,
        config: Optional[Dict] = None,
        progress_callback: Optional[callable] = None,
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

        # pass progress_callback into engine implementation if supported
        try:
            audio = engine.synthesize(text, speaker, progress_callback=progress_callback, **kwargs)
        except TypeError:
            # Engine doesn't accept progress_callback, call without
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

        with self._lock:
            for key, engine in list(self.loaded_engines.items()):
                try:
                    engine.unload()
                except Exception as e:
                    logger.warning(f"Error unloading engine {key}: {e}")

            self.loaded_engines.clear()
            self.engine_usage.clear()

        logger.info("All engines unloaded")

    def get_stats(self) -> Dict:
        """Hole Engine-Statistiken"""
        with self._lock:
            total_memory = sum(e.get_memory_usage() for e in self.loaded_engines.values()) / 1024 ** 3
            return {
                "loaded_engines": list(self.loaded_engines.keys()),
                "usage": self.engine_usage.copy(),
                "total_memory": total_memory,
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


# --- DummyEngine for offline testing -------------------------------------------------
class DummyEngine(BaseTTSEngine):
    """
    Very small deterministic dummy TTS engine used for offline testing.

    It generates a sine wave whose duration is derived from the text length so
    the rest of the pipeline (wav writing, ffmpeg encoding, JSONL events) can be
    exercised without real TTS models.
    """

    def load_model(self):
        # No heavy model to load; mark as loaded and leave default sample_rate
        logger.info("DummyEngine ready (no model load)")
        self.sample_rate = 22050
        self.is_loaded = True

    def synthesize(self, text: str, speaker: str, **kwargs) -> np.ndarray:
        import math

        if not self.is_loaded:
            raise RuntimeError("DummyEngine not loaded")

        cancel_event = kwargs.get('cancel_event')
        progress_cb = kwargs.get('progress_callback')

        try:
            if progress_cb:
                try:
                    progress_cb(0.0, 'start')
                except Exception:
                    pass

            # Simple duration heuristic: 0.05s per character, clamp 0.2..8.0s
            dur = max(0.2, min(8.0, 0.05 * len(text)))
            sr = int(self.sample_rate)
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)

            # Use a base frequency that varies by speaker hash so different
            # speakers produce different tones.
            h = int(hashlib.sha1(str(speaker).encode()).hexdigest(), 16)
            freq = 220 + (h % 220)

            wave = 0.25 * np.sin(2 * math.pi * freq * t)

            # simple amplitude envelope
            env = np.minimum(1.0, (t * 5.0)) * np.minimum(1.0, (dur - t) * 5.0)
            audio = (wave * env).astype(np.float32)

            if progress_cb:
                try:
                    progress_cb(0.6, 'processing')
                except Exception:
                    pass
                try:
                    progress_cb(1.0, 'done')
                except Exception:
                    pass

            return audio

        except Exception as e:
            logger.error(f"DummyEngine synthesis failed: {e}")
            raise


# Register DummyEngine into the factory mapping (monkey-patch the dict entry)
try:
    TTSEngineFactory._engine_classes[TTSEngine.DUMMY] = DummyEngine
except Exception:
    # If engine factory not yet defined or enum mutated unexpectedly,
    # ignore the registration failure — it's non-fatal for existing flows.
    pass

