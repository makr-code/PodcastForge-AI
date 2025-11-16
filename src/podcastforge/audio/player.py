#!/usr/bin/env python3
"""
Audio Player Module
Einfacher Audio-Player für TTS-Vorschau im Editor
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional
import queue

# Try different audio backends
BACKEND_NAME = None
_HAS_PYGAME = False
try:
    import pygame

    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    BACKEND_NAME = "pygame"
    _HAS_PYGAME = True
except Exception:
    try:
        import simpleaudio as sa

        BACKEND_NAME = "simpleaudio"
    except Exception:
        try:
            from pydub import AudioSegment
            from pydub.playback import play

            BACKEND_NAME = "pydub"
        except Exception:
            BACKEND_NAME = None


class AudioPlayer:
    """Audio player with optional queue and best-effort crossfade for pygame.

    The player exposes `enqueue(path, crossfade_sec)` so the UI can build a
    near-realtime playlist. Crossfade is best-effort and only supported for the
    `pygame` backend (uses fadeout/fade_ms). Other backends fall back to sequential play.
    """

    def __init__(self):
        self.backend = BACKEND_NAME
        self.current_playback = None
        self.is_playing = False
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Queue for near-realtime playlist
        self._queue: "queue.Queue[Path]" = queue.Queue()
        self._queue_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self._queue_thread.start()

        # crossfade seconds to use when enqueueing (can be overridden per enqueue)
        self.crossfade_default = 0.5

        if self.backend is None:
            print("⚠️ Kein Audio-Backend verfügbar. Installiere pygame oder simpleaudio:")
            print("  pip install pygame")
            print("  oder: pip install simpleaudio")

    # ========== Public API ==========
    def play(self, audio_file: Path, on_complete: Optional[Callable] = None):
        """Play immediately (stop any current playback)."""
        self.stop()
        self.stop_event.clear()
        self.playback_thread = threading.Thread(
            target=self._playback_worker, args=(audio_file, on_complete, None), daemon=True
        )
        self.playback_thread.start()

    def enqueue(self, audio_file: Path, crossfade_sec: Optional[float] = None):
        """Add a file to the playback queue."""
        self._queue.put((audio_file, float(crossfade_sec) if crossfade_sec is not None else self.crossfade_default))

    def stop(self):
        """Stop playback and clear current play state."""
        self.stop_event.set()
        # stop backend-specific playback
        if self.backend == "pygame" and _HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        # no reliable stop for other backends beyond signaling

        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

        self.is_playing = False

    def pause(self):
        if self.backend == "pygame" and _HAS_PYGAME:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def resume(self):
        if self.backend == "pygame" and _HAS_PYGAME:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    def set_volume(self, volume: float):
        if self.backend == "pygame" and _HAS_PYGAME:
            try:
                pygame.mixer.music.set_volume(volume)
            except Exception:
                pass

    def get_backend(self) -> Optional[str]:
        return self.backend

    # ========== Internal playback ==========
    def _queue_worker(self):
        while True:
            try:
                item = self._queue.get()
                if item is None:
                    break
                audio_file, crossfade = item
                # If something is currently playing and backend supports fade, do crossfade
                if self.is_playing and self.backend == "pygame" and _HAS_PYGAME and crossfade and crossfade > 0:
                    try:
                        fade_ms = int(crossfade * 1000)
                        # fade out current track
                        pygame.mixer.music.fadeout(fade_ms)
                        # start next with fade-in
                        pygame.mixer.music.load(str(audio_file))
                        pygame.mixer.music.play(fade_ms=fade_ms)
                        # wait until done
                        self.is_playing = True
                        while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                            time.sleep(0.1)
                        pygame.mixer.music.stop()
                        self.is_playing = False
                    except Exception:
                        # fallback to immediate play
                        self.play(audio_file)
                else:
                    # sequential play
                    self.play(audio_file)

            except Exception:
                time.sleep(0.1)

    def _playback_worker(self, audio_file: Path, on_complete: Optional[Callable], _unused):
        try:
            self.is_playing = True
            if self.backend == "pygame" and _HAS_PYGAME:
                try:
                    pygame.mixer.music.load(str(audio_file))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                        time.sleep(0.1)
                    pygame.mixer.music.stop()
                except Exception as e:
                    print(f"Playback error (pygame): {e}")
            elif self.backend == "simpleaudio":
                try:
                    import simpleaudio as sa
                    from pydub import AudioSegment

                    audio = AudioSegment.from_file(audio_file)
                    playback_obj = sa.play_buffer(
                        audio.raw_data,
                        num_channels=audio.channels,
                        bytes_per_sample=audio.sample_width,
                        sample_rate=audio.frame_rate,
                    )
                    while playback_obj.is_playing() and not self.stop_event.is_set():
                        time.sleep(0.1)
                    if self.stop_event.is_set():
                        playback_obj.stop()
                except Exception as e:
                    print(f"Playback error (simpleaudio): {e}")
            elif self.backend == "pydub":
                try:
                    from pydub import AudioSegment
                    from pydub.playback import play

                    audio = AudioSegment.from_file(audio_file)
                    play(audio)
                except Exception as e:
                    print(f"Playback error (pydub): {e}")
            else:
                print(f"No audio backend to play {audio_file}")

            self.is_playing = False
            if on_complete and not self.stop_event.is_set():
                try:
                    on_complete()
                except Exception:
                    pass

        except Exception as e:
            print(f"❌ Fehler bei Audio-Wiedergabe: {e}")
            self.is_playing = False


# Singleton-Instanz
_player_instance: Optional[AudioPlayer] = None


def get_player() -> AudioPlayer:
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance
