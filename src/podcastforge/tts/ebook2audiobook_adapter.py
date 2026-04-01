"""
Adapter für ebook2audiobook Integration
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import scipy.io.wavfile as wavfile
from rich.console import Console

from ..core.config import PodcastConfig, Speaker
from .engine_manager import TTSEngine, get_engine_manager

console = Console()
logger = logging.getLogger(__name__)

# Maximaler Wert für 16-Bit vorzeichenbehaftete Integer (für WAV-Export)
_INT16_MAX = 32767


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
            speaker = entry.get("speaker_name") or entry.get("speaker_id") or "Unknown"
            text = entry.get("text", "")
            emotion = entry.get("emotion", "neutral")

            # Format: Speaker: Text
            line = f"{speaker}: {text}"

            if emotion != "neutral":
                line = f"[{emotion}] {line}"

            lines.append(line)

        return "\n\n".join(lines)

    def _resolve_engine_chain(
        self,
        entry: Dict,
        config: PodcastConfig,
        speaker_map: Dict,
        engine_manager,
    ) -> List[TTSEngine]:
        """Bestimmt die Engine-Fallback-Kette für einen Script-Eintrag.

        Priorität: Speaker.voice_engine > PodcastConfig.voice_engine > fallback_engines.
        Unbekannte Engine-Namen werden übersprungen. Falls die Kette leer bleibt,
        wird die Standard-Engine des Managers verwendet.
        """
        chain: List[str] = []

        # 1. Individuelle Engine des Sprechers (höchste Priorität)
        speaker_id = entry.get("speaker_id", "")
        speaker = speaker_map.get(speaker_id)
        if speaker and speaker.voice_engine:
            chain.append(speaker.voice_engine)

        # 2. Globale Engine aus der Podcast-Konfiguration
        if config.voice_engine and config.voice_engine not in chain:
            chain.append(config.voice_engine)

        # 3. Konfigurierte Fallback-Engines
        for fb in (config.fallback_engines or []):
            if fb not in chain:
                chain.append(fb)

        # Unbekannte Engine-Namen überspringen
        result: List[TTSEngine] = []
        for name in chain:
            try:
                result.append(TTSEngine(name))
            except ValueError:
                logger.warning(f"Unbekannte TTS-Engine '{name}' wird übersprungen.")

        # Letzter Ausweg: Standard-Engine des Managers
        if not result:
            result.append(engine_manager.default_engine)

        return result

    def _generate_with_tts(
        self, script: List[Dict], output_path: str, config: PodcastConfig
    ) -> str:
        """
        Fallback: Direkte TTS-Generierung ohne ebook2audiobook.

        Nutzt pro Sprecher die individuell konfigurierte Engine (``Speaker.voice_engine``),
        ansonsten die globale Engine (``PodcastConfig.voice_engine``), und im Fehlerfall
        die in ``PodcastConfig.fallback_engines`` definierten Alternativen.
        """
        try:
            from pydub import AudioSegment

            console.print("[cyan]🎙️ Verwende direkte TTS-Generierung...[/cyan]")

            engine_manager = get_engine_manager()

            # Sprecher-Lookup für schnellen Zugriff: speaker_id -> Speaker
            speaker_map: Dict[str, Speaker] = {s.id: s for s in (config.speakers or [])}

            # Alle Segmente generieren
            segments = []
            for i, entry in enumerate(script):
                fd, temp_segment = tempfile.mkstemp(suffix=".wav")
                os.close(fd)

                engine_chain = self._resolve_engine_chain(entry, config, speaker_map, engine_manager)
                logger.debug(
                    f"Segment {i} ({entry.get('speaker_id', '?')}): "
                    f"Engine-Kette = {[e.value for e in engine_chain]}"
                )

                audio, sample_rate = engine_manager.synthesize_with_fallback(
                    text=entry["text"],
                    speaker=entry.get("voice_profile", entry.get("speaker_id", "")),
                    engines=engine_chain,
                )

                # Audio als WAV schreiben
                audio_int16 = (np.clip(audio, -1.0, 1.0) * _INT16_MAX).astype(np.int16)
                wavfile.write(temp_segment, sample_rate, audio_int16)

                segment = AudioSegment.from_wav(temp_segment)
                pause = AudioSegment.silent(duration=int(entry.get("pause_after", 0.5) * 1000))
                segments.append(segment + pause)
                os.remove(temp_segment)

            # Kombiniere alle Segmente
            final_audio = sum(segments)

            # Exportiere
            final_audio.export(output_path, format="wav", parameters=["-ar", str(config.sample_rate)])

            console.print("[green]✅ Audio mit direkter TTS generiert[/green]")
            return output_path

        except Exception as e:
            logger.error(f"Direkte TTS fehlgeschlagen: {e}")
            raise RuntimeError("Audio-Generierung fehlgeschlagen")
