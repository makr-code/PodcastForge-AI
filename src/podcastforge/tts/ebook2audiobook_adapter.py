"""
Adapter für ebook2audiobook Integration
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from rich.console import Console

from ..core.config import PodcastConfig

console = Console()
logger = logging.getLogger(__name__)


class Ebook2AudiobookAdapter:
    """
    Adapter für ebook2audiobook TTS-Engine
    """

    def __init__(self, ebook2audiobook_path: str = "./ebook2audiobook"):
        self.e2a_path = Path(ebook2audiobook_path)
        self._verify_installation()

    def _verify_installation(self):
        """Überprüft ebook2audiobook Installation"""
        if not self.e2a_path.exists():
            console.print("[yellow]📦 ebook2audiobook nicht gefunden[/yellow]")
            console.print("[yellow]Klone Repository...[/yellow]")

            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/DrewThomasson/ebook2audiobook.git",
                        str(self.e2a_path),
                    ],
                    check=True,
                    capture_output=True,
                )

                console.print("[green]✅ ebook2audiobook geklont[/green]")

            except subprocess.CalledProcessError as e:
                logger.error(f"Fehler beim Klonen: {e}")
                console.print("[red]❌ Konnte ebook2audiobook nicht klonen[/red]")
                console.print("[yellow]Bitte manuell klonen:[/yellow]")
                console.print(
                    f"[yellow]git clone https://github.com/DrewThomasson/ebook2audiobook.git {self.e2a_path}[/yellow]"
                )

    def generate_audio(self, script: List[Dict], output_path: str, config: PodcastConfig) -> str:
        """
        Generiert Audio mit ebook2audiobook

        Args:
            script: Drehbuch als Liste von Dialogen
            output_path: Ausgabepfad
            config: Podcast-Konfiguration

        Returns:
            Pfad zur generierten Audio-Datei
        """
        console.print("[cyan]🎙️ Generiere Audio mit TTS...[/cyan]")

        # Konvertiere Script zu Text-Format
        ebook_content = self._script_to_text(script)

        # Temporäre Input-Datei
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(ebook_content)
            tmp_path = tmp.name

        try:
            # Fallback: Verwende TTS direkt wenn ebook2audiobook nicht verfügbar
            if not (self.e2a_path / "ebook2audiobook.py").exists():
                console.print(
                    "[yellow]⚠️ ebook2audiobook nicht gefunden, verwende TTS direkt[/yellow]"
                )
                return self._generate_with_tts(script, output_path, config)

            # ebook2audiobook Befehl
            cmd = [
                "python3",
                str(self.e2a_path / "ebook2audiobook.py"),
                "--input",
                tmp_path,
                "--output",
                output_path,
                "--language",
                config.language,
            ]

            # TTS-Engine auswählen
            if config.voice_engine:
                cmd.extend(["--tts", config.voice_engine])

            # Ausführen
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                logger.error(f"ebook2audiobook Fehler: {result.stderr}")
                # Fallback zu direkter TTS
                return self._generate_with_tts(script, output_path, config)

            console.print("[green]✅ Audio generiert[/green]")
            return output_path

        except Exception as e:
            logger.error(f"Fehler bei Audio-Generierung: {e}")
            # Fallback zu direkter TTS
            return self._generate_with_tts(script, output_path, config)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _script_to_text(self, script: List[Dict]) -> str:
        """Konvertiert Script zu Text-Format"""
        lines = []

        for entry in script:
            speaker = entry["speaker_name"]
            text = entry["text"]
            emotion = entry.get("emotion", "neutral")

            # Format: Speaker: Text
            line = f"{speaker}: {text}"

            if emotion != "neutral":
                line = f"[{emotion}] {line}"

            lines.append(line)

        return "\n\n".join(lines)

    def _generate_with_tts(
        self, script: List[Dict], output_path: str, config: PodcastConfig
    ) -> str:
        """
        Fallback: Direkte TTS-Generierung ohne ebook2audiobook
        """
        try:
            from pydub import AudioSegment
            from TTS.api import TTS

            console.print("[cyan]🎙️ Verwende direkte TTS-Generierung...[/cyan]")

            # TTS initialisieren
            tts = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC")

            # Alle Segmente generieren
            segments = []
            for i, entry in enumerate(script):
                # Temporäre Datei für Segment
                temp_segment = f"/tmp/segment_{i}.wav"

                # Generiere Audio
                tts.tts_to_file(text=entry["text"], file_path=temp_segment)

                # Lade Segment
                segment = AudioSegment.from_wav(temp_segment)

                # Füge Pause hinzu
                pause = AudioSegment.silent(duration=int(entry.get("pause_after", 0.5) * 1000))

                segments.append(segment + pause)
                os.remove(temp_segment)

            # Kombiniere alle Segmente
            final_audio = sum(segments)

            # Exportiere
            final_audio.export(output_path, format="wav", parameters=["-ar", "22050"])

            console.print("[green]✅ Audio mit direkter TTS generiert[/green]")
            return output_path

        except Exception as e:
            logger.error(f"Direkte TTS fehlgeschlagen: {e}")
            raise RuntimeError("Audio-Generierung fehlgeschlagen")
