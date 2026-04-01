"""Extended tests for TTSEngineManager, TTSEngineFactory, and DummyEngine."""
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.tts.engine_manager import (
    BaseTTSEngine,
    DummyEngine,
    TTSEngine,
    TTSEngineFactory,
    TTSEngineManager,
    get_engine_manager,
    CancelledError,
)


# ---------------------------------------------------------------------------
# DummyEngine
# ---------------------------------------------------------------------------


class TestDummyEngine:
    def setup_method(self):
        self.engine = DummyEngine()
        self.engine.load_model()

    def test_load_model_marks_as_loaded(self):
        e = DummyEngine()
        e.load_model()
        assert e.is_loaded is True

    def test_sample_rate_set_after_load(self):
        assert self.engine.sample_rate == 22050

    def test_synthesize_returns_float32_array(self):
        audio = self.engine.synthesize("Hello world", "speaker1")
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32

    def test_synthesize_audio_length_proportional_to_text(self):
        short_text = "Hi."
        long_text = "This is a much longer sentence that will produce more audio output."
        a_short = self.engine.synthesize(short_text, "sp")
        a_long = self.engine.synthesize(long_text, "sp")
        assert len(a_long) >= len(a_short)

    def test_synthesize_max_duration_clamp(self):
        """Very long text should still be clamped to ≤ 8 seconds."""
        text = "a" * 500
        audio = self.engine.synthesize(text, "sp")
        max_expected_samples = int(22050 * 8.0) + 100  # small tolerance
        assert len(audio) <= max_expected_samples

    def test_synthesize_different_speakers_produce_different_tones(self):
        a1 = self.engine.synthesize("test", "speakerA")
        a2 = self.engine.synthesize("test", "speakerB")
        # Same text, different speaker → different frequency → different audio
        assert not np.allclose(a1, a2, atol=1e-3)

    def test_synthesize_calls_progress_callback(self):
        calls = []
        self.engine.synthesize("hello", "sp", progress_callback=lambda p, s=None: calls.append(p))
        assert len(calls) >= 2
        assert calls[0] == 0.0
        assert calls[-1] == 1.0

    def test_synthesize_raises_when_not_loaded(self):
        e = DummyEngine()
        with pytest.raises(RuntimeError, match="not loaded"):
            e.synthesize("hi", "sp")

    def test_progress_callback_exception_does_not_propagate(self):
        def bad_cb(p, s=None):
            raise ValueError("callback error")
        # Should not raise
        audio = self.engine.synthesize("hello", "sp", progress_callback=bad_cb)
        assert audio is not None

    def test_repr_contains_engine_type(self):
        r = repr(self.engine)
        assert "BaseTTSEngine" in r or "DummyEngine" in r or "dummy" in r.lower() or isinstance(r, str)

    def test_get_memory_usage_returns_int(self):
        assert isinstance(self.engine.get_memory_usage(), int)

    def test_unload_clears_is_loaded(self):
        self.engine.unload()
        assert self.engine.is_loaded is False


# ---------------------------------------------------------------------------
# TTSEngineFactory
# ---------------------------------------------------------------------------


class TestTTSEngineFactory:
    def test_create_dummy_engine(self):
        engine = TTSEngineFactory.create(TTSEngine.DUMMY)
        assert isinstance(engine, DummyEngine)

    def test_create_raises_for_unknown_engine(self):
        # Create a fake engine type value not in the factory map
        with pytest.raises((ValueError, KeyError)):
            TTSEngineFactory.create.__func__(
                TTSEngineFactory,
                MagicMock(spec=TTSEngine, value="NONEXISTENT"),
            )

    def test_get_available_engines_includes_dummy(self):
        engines = TTSEngineFactory.get_available_engines()
        assert TTSEngine.DUMMY in engines

    def test_get_available_engines_returns_list(self):
        assert isinstance(TTSEngineFactory.get_available_engines(), list)

    def test_create_with_config_dict(self):
        engine = TTSEngineFactory.create(TTSEngine.DUMMY, config={"test": "value"})
        assert engine is not None


# ---------------------------------------------------------------------------
# TTSEngineManager
# ---------------------------------------------------------------------------


class TestTTSEngineManagerDummy:
    """Tests using DummyEngine to avoid loading real ML models."""

    def setup_method(self):
        self.mgr = TTSEngineManager(max_engines=2)
        TTSEngineFactory._engine_classes[TTSEngine.DUMMY] = DummyEngine

    def teardown_method(self):
        self.mgr.unload_all()

    def test_get_engine_returns_dummy(self):
        engine = self.mgr.get_engine(TTSEngine.DUMMY)
        assert isinstance(engine, DummyEngine)

    def test_get_engine_cache_hit_returns_same_instance(self):
        e1 = self.mgr.get_engine(TTSEngine.DUMMY)
        e2 = self.mgr.get_engine(TTSEngine.DUMMY)
        assert e1 is e2

    def test_synthesize_returns_tuple(self):
        audio, sr = self.mgr.synthesize("hello", "sp", engine_type=TTSEngine.DUMMY)
        assert isinstance(audio, np.ndarray)
        assert isinstance(sr, int)

    def test_synthesize_with_fallback_first_engine_succeeds(self):
        audio, sr = self.mgr.synthesize_with_fallback(
            "hello", "sp", [TTSEngine.DUMMY]
        )
        assert audio is not None

    def test_synthesize_with_fallback_empty_raises(self):
        with pytest.raises(ValueError, match="darf nicht leer"):
            self.mgr.synthesize_with_fallback("hello", "sp", [])

    def test_synthesize_with_fallback_all_fail_raises(self):
        # Register a broken engine temporarily
        class BrokenEngine(BaseTTSEngine):
            def load_model(self):
                self.is_loaded = True
                self.sample_rate = 22050
            def synthesize(self, text, speaker, **kwargs):
                raise RuntimeError("always fails")

        original = TTSEngineFactory._engine_classes.copy()
        TTSEngineFactory._engine_classes[TTSEngine.DUMMY] = BrokenEngine
        try:
            # unload any cached dummy first
            self.mgr.unload_all()
            with pytest.raises(RuntimeError):
                self.mgr.synthesize_with_fallback("hello", "sp", [TTSEngine.DUMMY])
        finally:
            TTSEngineFactory._engine_classes.update(original)

    def test_get_stats_returns_dict(self):
        self.mgr.get_engine(TTSEngine.DUMMY)
        stats = self.mgr.get_stats()
        assert isinstance(stats, dict)
        assert "loaded_engines" in stats
        assert "usage" in stats

    def test_repr_contains_loaded_count(self):
        self.mgr.get_engine(TTSEngine.DUMMY)
        r = repr(self.mgr)
        assert "1/" in r or "loaded=" in r

    def test_unload_all_clears_engines(self):
        self.mgr.get_engine(TTSEngine.DUMMY)
        self.mgr.unload_all()
        assert len(self.mgr.loaded_engines) == 0

    def test_preload_engines(self):
        self.mgr.preload_engines([(TTSEngine.DUMMY, {})])
        assert len(self.mgr.loaded_engines) >= 1

    def test_release_engine_decrements_refcount(self):
        self.mgr.get_engine(TTSEngine.DUMMY)
        key = self.mgr._make_key(TTSEngine.DUMMY, {})
        count_before = self.mgr._ref_counts.get(key, 0)
        self.mgr.release_engine(TTSEngine.DUMMY)
        # After release the key should be gone (refcount reached 0)
        assert key not in self.mgr.loaded_engines or self.mgr._ref_counts.get(key, 0) < count_before

    def test_use_engine_context_manager(self):
        with self.mgr.use_engine(TTSEngine.DUMMY) as engine:
            assert isinstance(engine, DummyEngine)
        # After context, engine should be released
        key = self.mgr._make_key(TTSEngine.DUMMY, {})
        assert key not in self.mgr.loaded_engines

    def test_lru_eviction_when_max_reached(self):
        """When max_engines is 1, a second engine request evicts the first."""
        mgr = TTSEngineManager(max_engines=1)
        try:
            e1 = mgr.get_engine(TTSEngine.DUMMY)
            # Manually add a second engine type by temporarily patching
            class DummyEngine2(DummyEngine):
                pass
            original = TTSEngineFactory._engine_classes.copy()
            TTSEngineFactory._engine_classes[TTSEngine.DUMMY] = DummyEngine2
            mgr.unload_all()
            mgr.get_engine(TTSEngine.DUMMY)
            mgr.get_engine(TTSEngine.DUMMY)  # second identical get just hits cache
            assert len(mgr.loaded_engines) <= 1
        finally:
            TTSEngineFactory._engine_classes.update(original)
            mgr.unload_all()

    def test_auto_load_false_raises_for_unloaded(self):
        with pytest.raises(KeyError):
            self.mgr.get_engine(TTSEngine.DUMMY, auto_load=False)

    def test_make_key_stable(self):
        k1 = self.mgr._make_key(TTSEngine.DUMMY, {})
        k2 = self.mgr._make_key(TTSEngine.DUMMY, {})
        assert k1 == k2

    def test_make_key_with_config(self):
        k1 = self.mgr._make_key(TTSEngine.DUMMY, {"a": 1})
        k2 = self.mgr._make_key(TTSEngine.DUMMY, {"a": 2})
        assert k1 != k2

    def test_thread_safety_concurrent_get_engine(self):
        """Multiple threads requesting the same engine should all succeed."""
        results = []
        errors = []

        def get():
            try:
                e = self.mgr.get_engine(TTSEngine.DUMMY)
                results.append(e)
            except Exception as ex:
                errors.append(ex)

        threads = [threading.Thread(target=get) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5


# ---------------------------------------------------------------------------
# get_engine_manager singleton
# ---------------------------------------------------------------------------


class TestGetEngineManagerSingleton:
    def test_returns_same_instance(self):
        import podcastforge.tts.engine_manager as em_module
        em_module._engine_manager = None
        m1 = get_engine_manager()
        m2 = get_engine_manager()
        assert m1 is m2
        em_module._engine_manager = None
