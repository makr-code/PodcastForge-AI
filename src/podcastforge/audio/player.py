#!/usr/bin/env python3
"""
Audio Player Module
Einfacher Audio-Player für TTS-Vorschau im Editor
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

# Try different audio backends
AUDIO_BACKEND = None

try:
    import pygame

    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO_BACKEND = "pygame"
except ImportError:
    try:
        import simpleaudio as sa

        AUDIO_BACKEND = "simpleaudio"
    except ImportError:
        try:
            from pydub import AudioSegment
            from pydub.playback import play

            AUDIO_BACKEND = "pydub"
        except ImportError:
            AUDIO_BACKEND = None


class AudioPlayer:
    """Einfacher Audio-Player mit verschiedenen Backends"""

    def __init__(self):
        self.backend = AUDIO_BACKEND
        self.current_playback = None
        self.is_playing = False
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        if self.backend is None:
            print("⚠️ Kein Audio-Backend verfügbar. Installiere pygame oder simpleaudio:")
            print("  pip install pygame")
            print("  oder: pip install simpleaudio")

    def play(self, audio_file: Path, on_complete: Optional[Callable] = None):
        """
        Spiele Audio-Datei ab

        Args:
            audio_file: Pfad zur Audio-Datei
            on_complete: Callback wenn Wiedergabe beendet
        """
        if self.backend is None:
            print(f"⚠️ Kann {audio_file} nicht abspielen - kein Audio-Backend")
            return

        # Stoppe aktuelle Wiedergabe
        self.stop()

        # Starte neue Wiedergabe in Thread
        self.stop_event.clear()
        self.playback_thread = threading.Thread(
            target=self._playback_worker, args=(audio_file, on_complete), daemon=True
        )
        self.playback_thread.start()

    def _playback_worker(self, audio_file: Path, on_complete: Optional[Callable]):
        """Worker-Thread für Audio-Wiedergabe"""
        try:
            self.is_playing = True

            if self.backend == "pygame":
                self._play_pygame(audio_file)
            elif self.backend == "simpleaudio":
                self._play_simpleaudio(audio_file)
            elif self.backend == "pydub":
                self._play_pydub(audio_file)

            self.is_playing = False

            if on_complete and not self.stop_event.is_set():
                on_complete()

        except Exception as e:
            print(f"❌ Fehler bei Audio-Wiedergabe: {e}")
            self.is_playing = False

    def _play_pygame(self, audio_file: Path):
        """Wiedergabe mit pygame"""
        import pygame

        pygame.mixer.music.load(str(audio_file))
        pygame.mixer.music.play()

        # Warte bis Wiedergabe beendet
        while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
            time.sleep(0.1)

        pygame.mixer.music.stop()

    def _play_simpleaudio(self, audio_file: Path):
        """Wiedergabe mit simpleaudio"""
        import simpleaudio as sa
        from pydub import AudioSegment

        # Lade Audio
        audio = AudioSegment.from_file(audio_file)

        # Konvertiere zu raw audio
        playback_obj = sa.play_buffer(
            audio.raw_data,
            num_channels=audio.channels,
            bytes_per_sample=audio.sample_width,
            sample_rate=audio.frame_rate,
        )

        self.current_playback = playback_obj

        # Warte bis Wiedergabe beendet
        while playback_obj.is_playing() and not self.stop_event.is_set():
            time.sleep(0.1)

        if self.stop_event.is_set():
            playback_obj.stop()

    def _play_pydub(self, audio_file: Path):
        """Wiedergabe mit pydub"""
        from pydub import AudioSegment
        from pydub.playback import play

        audio = AudioSegment.from_file(audio_file)
        play(audio)

    def stop(self):
        """Stoppe Wiedergabe"""
        self.stop_event.set()

        if self.backend == "pygame":
            import pygame

            pygame.mixer.music.stop()
        elif self.backend == "simpleaudio" and self.current_playback:
            self.current_playback.stop()

        # Warte auf Thread
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

        self.is_playing = False

    def pause(self):
        """Pausiere Wiedergabe (nur pygame)"""
        if self.backend == "pygame":
            import pygame

            pygame.mixer.music.pause()

    def resume(self):
        """Setze Wiedergabe fort (nur pygame)"""
        if self.backend == "pygame":
            import pygame

            pygame.mixer.music.unpause()

    def set_volume(self, volume: float):
        """
        Setze Lautstärke

        Args:
            volume: Lautstärke 0.0 - 1.0
        """
        if self.backend == "pygame":
            import pygame

            pygame.mixer.music.set_volume(volume)

    def get_backend(self) -> Optional[str]:
        """Gibt aktuelles Backend zurück"""
        return self.backend


# Singleton-Instanz
_player_instance: Optional[AudioPlayer] = None


def get_player() -> AudioPlayer:
    """Gibt Singleton AudioPlayer zurück"""
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance
