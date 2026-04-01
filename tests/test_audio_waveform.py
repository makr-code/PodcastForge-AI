"""Unit tests for podcastforge.audio.waveform."""
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.audio.waveform import WaveformGenerator, generate_waveform_tkinter


class TestWaveformGeneratorPlaceholder:
    def test_returns_pil_image(self):
        gen = WaveformGenerator(width=200, height=50)
        img = gen._generate_placeholder("Test")
        assert img is not None
        assert img.size == (200, 50)

    def test_default_size(self):
        gen = WaveformGenerator()
        img = gen._generate_placeholder()
        assert img.size == (800, 100)

    def test_image_mode_rgb(self):
        gen = WaveformGenerator(width=100, height=40)
        img = gen._generate_placeholder("hello")
        assert img.mode == "RGB"

    def test_custom_message_does_not_crash(self):
        gen = WaveformGenerator()
        img = gen._generate_placeholder("Fehler: Datei nicht gefunden")
        assert img is not None


class TestWaveformGeneratorDrawWaveform:
    def _make_gen(self, w=200, h=60):
        return WaveformGenerator(width=w, height=h)

    def test_output_size_matches(self):
        gen = self._make_gen()
        samples = np.sin(np.linspace(0, 2 * np.pi, 500)).astype(np.float32)
        img = gen._draw_waveform(samples)
        assert img.size == (200, 60)

    def test_empty_samples(self):
        gen = self._make_gen()
        img = gen._draw_waveform(np.array([], dtype=np.float32))
        assert img is not None

    def test_single_sample(self):
        gen = self._make_gen()
        img = gen._draw_waveform(np.array([0.5], dtype=np.float32))
        assert img is not None

    def test_samples_larger_than_width_downsampled(self):
        gen = self._make_gen(w=50)
        samples = np.random.rand(10000).astype(np.float32) * 2 - 1
        img = gen._draw_waveform(samples)
        assert img.size == (50, 60)

    def test_returns_rgb_image(self):
        gen = self._make_gen()
        img = gen._draw_waveform(np.zeros(100, dtype=np.float32))
        assert img.mode == "RGB"


class TestWaveformGeneratorFromData:
    def test_normalized_audio(self):
        gen = WaveformGenerator(width=100, height=40)
        data = np.sin(np.linspace(0, 4 * np.pi, 220)).astype(np.float32)
        img = gen.generate_from_data(data, sample_rate=22050)
        assert img.size == (100, 40)

    def test_silent_audio(self):
        gen = WaveformGenerator(width=80, height=30)
        data = np.zeros(1000, dtype=np.float32)
        img = gen.generate_from_data(data)
        assert img is not None

    def test_empty_array(self):
        gen = WaveformGenerator()
        img = gen.generate_from_data(np.array([]))
        assert img is not None

    def test_clips_non_normalized_input(self):
        gen = WaveformGenerator(width=50, height=30)
        # values outside [-1, 1] should be normalized before drawing
        data = np.array([10.0, -10.0, 5.0], dtype=np.float32)
        img = gen.generate_from_data(data)
        assert img is not None


class TestWaveformGeneratorGenerate:
    def test_returns_placeholder_without_pydub(self, monkeypatch):
        import podcastforge.audio.waveform as wm
        monkeypatch.setattr(wm, "HAS_PYDUB", False)
        gen = WaveformGenerator()
        img = gen.generate(Path("nonexistent.wav"))
        assert img is not None  # returns placeholder

    def test_returns_placeholder_on_file_not_found(self, monkeypatch):
        import podcastforge.audio.waveform as wm
        monkeypatch.setattr(wm, "HAS_PYDUB", True)
        # AudioSegment.from_file raises
        with patch("podcastforge.audio.waveform.AudioSegment") as mock_as:
            mock_as.from_file.side_effect = FileNotFoundError("not found")
            gen = WaveformGenerator()
            img = gen.generate(Path("nonexistent.wav"))
        assert img is not None


class TestGenerateWaveformTkinter:
    def test_returns_bytes(self):
        gen = WaveformGenerator(width=50, height=20)
        # patch WaveformGenerator.generate to return a known image
        with patch("podcastforge.audio.waveform.WaveformGenerator") as mock_cls:
            from PIL import Image
            fake_img = Image.new("RGB", (50, 20), (0, 0, 0))
            mock_instance = MagicMock()
            mock_instance.generate.return_value = fake_img
            mock_cls.return_value = mock_instance

            result = generate_waveform_tkinter(Path("fake.wav"), width=50, height=20)
        assert result is not None
        assert isinstance(result, bytes)
        # PNG magic bytes
        assert result[:4] == b"\x89PNG"

    def test_returns_none_on_error(self):
        with patch("podcastforge.audio.waveform.WaveformGenerator") as mock_cls:
            mock_cls.side_effect = RuntimeError("crash")
            result = generate_waveform_tkinter(Path("fake.wav"))
        assert result is None
