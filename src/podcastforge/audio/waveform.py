#!/usr/bin/env python3
"""
Waveform Visualization Module
Erzeugt Wellenform-Visualisierungen für Audio-Dateien
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

try:
    from pydub import AudioSegment

    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class WaveformGenerator:
    """Generiert Wellenform-Visualisierungen"""

    def __init__(self, width: int = 800, height: int = 100):
        self.width = width
        self.height = height
        self.bg_color = (30, 30, 30)  # Dunkelgrau
        self.wave_color = (74, 144, 226)  # Blau
        self.center_line_color = (100, 100, 100)  # Grau

    def generate(self, audio_file: Path) -> Optional[Image.Image]:
        """
        Generiere Wellenform-Bild

        Args:
            audio_file: Pfad zur Audio-Datei

        Returns:
            PIL Image oder None bei Fehler
        """
        if not HAS_PYDUB:
            return self._generate_placeholder("Pydub nicht installiert")

        try:
            # Lade Audio
            audio = AudioSegment.from_file(audio_file)

            # Konvertiere zu Mono
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Extrahiere Samples
            samples = np.array(audio.get_array_of_samples())

            # Normalisiere
            if len(samples) > 0:
                samples = samples / np.max(np.abs(samples))

            # Erstelle Wellenform
            return self._draw_waveform(samples)

        except Exception as e:
            print(f"⚠️ Fehler bei Wellenform-Generierung: {e}")
            return self._generate_placeholder(f"Fehler: {e}")

    def _draw_waveform(self, samples: np.ndarray) -> Image.Image:
        """Zeichne Wellenform aus Samples"""
        # Erstelle Bild
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Mittellinie
        mid_y = self.height // 2
        draw.line([(0, mid_y), (self.width, mid_y)], fill=self.center_line_color)

        # Resample auf Bildbreite
        if len(samples) > self.width:
            step = len(samples) // self.width
            samples_resampled = samples[::step][: self.width]
        else:
            samples_resampled = samples

        # Zeichne Wellenform
        for i, sample in enumerate(samples_resampled):
            # Berechne y-Position
            y = int(mid_y - (sample * mid_y * 0.9))

            # Zeichne Linie von Mitte zu Sample
            draw.line([(i, mid_y), (i, y)], fill=self.wave_color, width=1)

        return img

    def _generate_placeholder(self, message: str = "Keine Vorschau") -> Image.Image:
        """Generiere Platzhalter-Bild"""
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Mittellinie
        mid_y = self.height // 2
        draw.line([(0, mid_y), (self.width, mid_y)], fill=self.center_line_color)

        # Text (falls PIL Font verfügbar)
        try:
            from PIL import ImageFont

            # Versuche Standard-Font
            text_width = len(message) * 6
            text_x = (self.width - text_width) // 2
            draw.text((text_x, mid_y - 10), message, fill=(150, 150, 150))
        except:
            # Ohne Text
            pass

        return img

    def generate_from_data(self, audio_data: np.ndarray, sample_rate: int = 22050) -> Image.Image:
        """
        Generiere Wellenform aus NumPy-Array

        Args:
            audio_data: Audio-Samples als NumPy-Array
            sample_rate: Sample-Rate

        Returns:
            PIL Image
        """
        # Normalisiere
        if len(audio_data) > 0 and np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        return self._draw_waveform(audio_data)


def generate_waveform_tkinter(
    audio_file: Path, width: int = 800, height: int = 100
) -> Optional[bytes]:
    """
    Generiere Wellenform als PNG-Bytes für tkinter PhotoImage

    Args:
        audio_file: Pfad zur Audio-Datei
        width: Breite in Pixeln
        height: Höhe in Pixeln

    Returns:
        PNG-Bytes oder None
    """
    try:
        from io import BytesIO

        generator = WaveformGenerator(width, height)
        img = generator.generate(audio_file)

        if img:
            # Konvertiere zu PNG-Bytes
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

    except Exception as e:
        print(f"⚠️ Fehler bei Wellenform-Generierung: {e}")

    return None
