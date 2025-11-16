#!/usr/bin/env python3
"""
Unit tests for TTSEngineManager using mock engines.
"""
import threading
from pathlib import Path
import time

# Ensure src is importable (tests already do this elsewhere)
import sys
from pathlib import Path as P
sys.path.insert(0, str(P(__file__).parent.parent / "src"))

from podcastforge.tts.engine_manager import (
    TTSEngineManager,
    TTSEngineFactory,
    BaseTTSEngine,
    TTSEngine,
    get_engine_manager,
)


class MockEngine(BaseTTSEngine):
    """Simple mock engine that simulates load/unload and memory usage."""

    load_count = 0
    unload_count = 0

    def load_model(self):
        MockEngine.load_count += 1
        self.model = object()
        self.is_loaded = True
        self.sample_rate = 22050

    def synthesize(self, text: str, speaker: str, **kwargs):
        if not self.is_loaded:
            raise RuntimeError("not loaded")
        return b"audio-bytes"

    def unload(self):
        MockEngine.unload_count += 1
        self.model = None
        self.is_loaded = False

    def get_memory_usage(self) -> int:
        return 10 * 1024 * 1024  # 10MB


def test_engine_manager_basic_eviction_and_fallback():
    mgr = TTSEngineManager(max_engines=1)

    # Patch factory to use MockEngine for a custom pseudo-type
    original_map = TTSEngineFactory._engine_classes.copy()
    try:
        TTSEngineFactory._engine_classes[TTSEngine.PIPER] = MockEngine
        TTSEngineFactory._engine_classes[TTSEngine.BARK] = MockEngine

        # Load Piper
        e1 = mgr.get_engine(TTSEngine.PIPER, config={})
        assert e1.is_loaded

        # Load Bark -> should evict Piper because max_engines=1
        e2 = mgr.get_engine(TTSEngine.BARK, config={})
        assert e2.is_loaded

        stats = mgr.get_stats()
        assert len(stats["loaded_engines"]) == 1

        # Ensure unload was called at least once (eviction)
        assert MockEngine.unload_count >= 1

    finally:
        TTSEngineFactory._engine_classes = original_map
        mgr.unload_all()


def test_engine_manager_concurrent_load_same_key():
    mgr = TTSEngineManager(max_engines=2)

    original_map = TTSEngineFactory._engine_classes.copy()
    try:
        TTSEngineFactory._engine_classes[TTSEngine.PIPER] = MockEngine

        results = []

        def worker():
            e = mgr.get_engine(TTSEngine.PIPER, config={})
            results.append(id(e))

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should have same engine id (cached instance)
        assert len(set(results)) == 1

    finally:
        TTSEngineFactory._engine_classes = original_map
        mgr.unload_all()


def test_use_engine_context_and_refcount_release():
    mgr = TTSEngineManager(max_engines=2)

    original_map = TTSEngineFactory._engine_classes.copy()
    try:
        TTSEngineFactory._engine_classes[TTSEngine.PIPER] = MockEngine

        key = "piper:default"

        # Acquire engine twice using nested contexts
        with mgr.use_engine(TTSEngine.PIPER, config={}):
            # inside first context the engine must be loaded
            stats = mgr.get_stats()
            assert key in stats["loaded_engines"]

            with mgr.use_engine(TTSEngine.PIPER, config={}):
                # still loaded and refcount should prevent unload
                stats2 = mgr.get_stats()
                assert key in stats2["loaded_engines"]

        # After exiting both contexts, engine should be unloaded
        stats_final = mgr.get_stats()
        assert key not in stats_final["loaded_engines"]
        assert MockEngine.unload_count >= 1

    finally:
        TTSEngineFactory._engine_classes = original_map
        mgr.unload_all()
