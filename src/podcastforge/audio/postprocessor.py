"""
Audio-Nachbearbeitung und Optimierung
"""

import logging
import os
from pathlib import Path

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize
from rich.console import Console

from ..core.config import PodcastConfig

console = Console()
logger = logging.getLogger(__name__)


class AudioPostProcessor:
    """
    Audio-Nachbearbeitung für professionellen Sound
    """

    def process(self, input_path: str, output_path: str, config: PodcastConfig) -> str:
        """
        Bearbeitet Audio-Datei

        Args:
            input_path: Eingabe-Audio
            output_path: Ausgabe-Audio
            config: Konfiguration

        Returns:
            Pfad zur bearbeiteten Datei
        """
        console.print("[cyan]🎚️ Audio-Nachbearbeitung...[/cyan]")

        try:
            # Lade Audio
            audio = AudioSegment.from_file(input_path)

            # Normalisierung
            audio = normalize(audio)

            # Dynamik-Kompression
            audio = compress_dynamic_range(
                audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0
            )

            # Fade In/Out
            audio = audio.fade_in(2000).fade_out(3000)

            # Hintergrundmusik (optional)
            if config.background_music and os.path.exists(config.background_music):
                audio = self._add_background_music(audio, config.background_music)

            # Export
            output_format = config.output_format
            audio.export(
                output_path, format=output_format, bitrate=config.bitrate, parameters=["-q:a", "2"]
            )

            console.print(f"[green]✅ Audio bearbeitet: {output_path}[/green]")
            return output_path

        except Exception as e:
            logger.error(f"Audio-Nachbearbeitung fehlgeschlagen: {e}")
            # Fallback: Kopiere Original
            if input_path != output_path:
                import shutil

                shutil.copy(input_path, output_path)
            return output_path

    def _add_background_music(
        self, audio: AudioSegment, music_path: str, volume_reduction: int = 20
    ) -> AudioSegment:
        """Fügt Hintergrundmusik hinzu"""
        try:
            music = AudioSegment.from_file(music_path)

            # Musik leiser machen
            music = music - volume_reduction

            # Loop wenn zu kurz
            if len(music) < len(audio):
                loops = (len(audio) // len(music)) + 1
                music = music * loops

            # Auf Audio-Länge kürzen
            music = music[: len(audio)]

            # Fade für Musik
            music = music.fade_in(3000).fade_out(5000)

            # Overlay
            return audio.overlay(music)

        except Exception as e:
            logger.warning(f"Hintergrundmusik konnte nicht hinzugefügt werden: {e}")
            return audio
