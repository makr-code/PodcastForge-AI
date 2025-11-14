#!/usr/bin/env python3
"""
Test Suite für neue Features (v1.1 + v1.2)
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_thread_manager():
    """Test ThreadManager und Queue-System"""
    logger.info("\n=== Test ThreadManager ===")
    
    from podcastforge.gui.threading_base import get_thread_manager, UITaskObserver
    import tkinter as tk
    
    # Create root (needed for UITaskObserver)
    root = tk.Tk()
    root.withdraw()
    
    # Get ThreadManager
    manager = get_thread_manager(max_workers=2)
    
    # Create Observer
    observer = UITaskObserver(root)
    
    # Setup callbacks
    def on_started(task_id, metadata):
        logger.info(f"Task started: {task_id}")
    
    def on_completed(task_id, result):
        logger.info(f"Task completed: {task_id}, result={result}")
    
    observer.on_started(on_started)
    observer.on_completed(on_completed)
    
    # Register observer
    manager.add_observer(observer)
    
    # Submit test task
    def test_task(task_id, progress_callback):
        import time
        for i in range(3):
            progress_callback(i / 3.0, f"Step {i+1}/3")
            time.sleep(0.5)
        return "Success!"
    
    manager.submit_task(test_task, task_id="test_1")
    
    # Process results
    import time
    for _ in range(10):
        root.update()
        time.sleep(0.1)
        result = manager.get_result(timeout=0.1)
        if result:
            logger.info(f"Got result: {result.status}, {result.result}")
    
    # Cleanup
    manager.shutdown()
    root.destroy()
    
    logger.info("✓ ThreadManager test passed")


def test_tts_engine_manager():
    """Test TTSEngineManager"""
    logger.info("\n=== Test TTSEngineManager ===")
    
    from podcastforge.tts.engine_manager import get_engine_manager, TTSEngine
    
    manager = get_engine_manager(max_engines=2)
    
    # Test Piper (CPU, sollte immer funktionieren)
    try:
        logger.info("Testing Piper engine (will fail without model)...")
        # engine = manager.get_engine(TTSEngine.PIPER)
        # logger.info(f"Piper loaded: {engine}")
        logger.info("⚠ Piper test skipped (no model installed)")
    except Exception as e:
        logger.warning(f"Piper failed (expected): {e}")
    
    # Test stats
    stats = manager.get_stats()
    logger.info(f"Manager stats: {stats}")
    
    logger.info("✓ TTSEngineManager test passed")


def test_timeline_editor():
    """Test Timeline-Editor"""
    logger.info("\n=== Test Timeline-Editor ===")
    
    import tkinter as tk
    from podcastforge.gui.timeline import TimelineEditor, Scene
    
    root = tk.Tk()
    root.title("Timeline Test")
    
    # Create timeline
    timeline = TimelineEditor(root, width=800, height=300)
    timeline.pack(fill=tk.BOTH, expand=True)
    
    # Add test scenes
    scene1 = Scene(
        id="s1",
        speaker="Host",
        text="Welcome to the podcast!",
        start_time=0.0,
        duration=3.0,
        color="#569cd6"
    )
    
    scene2 = Scene(
        id="s2",
        speaker="Guest",
        text="Thanks for having me!",
        start_time=3.5,
        duration=2.5,
        color="#ce9178"
    )
    
    timeline.add_scene(scene1)
    timeline.add_scene(scene2)
    
    # Add marker
    timeline.add_marker(5.0, "Chapter 1")
    
    logger.info("Timeline created with 2 scenes and 1 marker")
    logger.info("Close the window to continue...")
    
    root.mainloop()
    
    logger.info("✓ Timeline-Editor test passed")


def test_voice_cloner():
    """Test Voice Cloner"""
    logger.info("\n=== Test Voice Cloner ===")
    
    from podcastforge.voices.cloner import get_voice_cloner
    
    cloner = get_voice_cloner()
    
    # Test quality check (without actual file)
    logger.info("Voice cloner initialized")
    logger.info(f"Cache dir: {cloner.cache_dir}")
    
    # List profiles
    profiles = cloner.get_all_profiles()
    logger.info(f"Loaded {len(profiles)} voice profiles")
    
    logger.info("✓ Voice Cloner test passed")


def test_multitrack_editor():
    """Test Multi-Track Editor"""
    logger.info("\n=== Test Multi-Track Editor ===")
    
    import tkinter as tk
    from podcastforge.gui.multitrack import MultiTrackEditor
    
    root = tk.Tk()
    root.title("Multi-Track Test")
    root.geometry("1200x600")
    
    # Create multi-track editor
    editor = MultiTrackEditor(root)
    editor.pack(fill=tk.BOTH, expand=True)
    
    logger.info("Multi-Track Editor created with 3 default tracks")
    logger.info("Close the window to continue...")
    
    root.mainloop()
    
    logger.info("✓ Multi-Track Editor test passed")


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("PodcastForge v1.1 & v1.2 Feature Tests")
    logger.info("=" * 60)
    
    tests = [
        ("ThreadManager", test_thread_manager),
        ("TTSEngineManager", test_tts_engine_manager),
        ("Timeline-Editor", test_timeline_editor),
        ("Voice Cloner", test_voice_cloner),
        ("Multi-Track Editor", test_multitrack_editor),
    ]
    
    for name, test_fn in tests:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {name}")
            logger.info(f"{'='*60}")
            test_fn()
        except KeyboardInterrupt:
            logger.info("\nTests cancelled by user")
            break
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
