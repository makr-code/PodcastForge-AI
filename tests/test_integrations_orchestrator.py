"""Unit tests for podcastforge.integrations.script_orchestrator — pure helper functions."""
import sys
import wave
import hashlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.integrations.script_orchestrator import (
    _cache_key,
    _write_wav,
    _write_stereo_wav,
    _concat_wavs,
)


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------


class TestCacheKey:
    def test_deterministic(self):
        k1 = _cache_key("hello", "speaker1", "PIPER")
        k2 = _cache_key("hello", "speaker1", "PIPER")
        assert k1 == k2

    def test_different_text_different_key(self):
        k1 = _cache_key("hello", "speaker1", "PIPER")
        k2 = _cache_key("world", "speaker1", "PIPER")
        assert k1 != k2

    def test_different_speaker_different_key(self):
        k1 = _cache_key("hello", "speaker1", "PIPER")
        k2 = _cache_key("hello", "speaker2", "PIPER")
        assert k1 != k2

    def test_different_engine_different_key(self):
        k1 = _cache_key("hello", "s1", "PIPER")
        k2 = _cache_key("hello", "s1", "BARK")
        assert k1 != k2

    def test_none_engine_works(self):
        k = _cache_key("text", "speaker", None)
        assert isinstance(k, str) and len(k) == 64  # sha256 hex

    def test_empty_strings(self):
        k = _cache_key("", "", "")
        assert isinstance(k, str)

    def test_returns_hex_string(self):
        k = _cache_key("test", "s", "e")
        int(k, 16)  # must be valid hex


# ---------------------------------------------------------------------------
# _write_wav
# ---------------------------------------------------------------------------


class TestWriteWav:
    def test_creates_valid_wav_file(self, tmp_path):
        p = tmp_path / "out.wav"
        audio = np.sin(np.linspace(0, 2 * np.pi, 22050)).astype(np.float32)
        _write_wav(p, audio, 22050)

        assert p.exists()
        with wave.open(str(p), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 22050

    def test_stereo_input_converted_to_mono(self, tmp_path):
        p = tmp_path / "stereo_in_mono_out.wav"
        audio = np.random.rand(1000, 2).astype(np.float32) * 2 - 1
        _write_wav(p, audio, 22050)

        with wave.open(str(p), "rb") as wf:
            assert wf.getnchannels() == 1

    def test_clipping_at_plus_minus_one(self, tmp_path):
        p = tmp_path / "clipped.wav"
        audio = np.array([2.0, -2.0, 0.5, -0.5], dtype=np.float32)
        _write_wav(p, audio, 22050)

        with wave.open(str(p), "rb") as wf:
            raw = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        assert raw[0] == 32767   # clipped to +1
        assert raw[1] == -32767  # clipped to -1

    def test_silent_audio(self, tmp_path):
        p = tmp_path / "silent.wav"
        audio = np.zeros(100, dtype=np.float32)
        _write_wav(p, audio, 16000)

        with wave.open(str(p), "rb") as wf:
            assert wf.getnframes() == 100


# ---------------------------------------------------------------------------
# _write_stereo_wav
# ---------------------------------------------------------------------------


class TestWriteStereoWav:
    def test_creates_stereo_wav(self, tmp_path):
        p = tmp_path / "stereo.wav"
        audio = np.random.rand(1000).astype(np.float32) * 2 - 1
        _write_stereo_wav(p, audio, 44100)

        with wave.open(str(p), "rb") as wf:
            assert wf.getnchannels() == 2
            assert wf.getframerate() == 44100

    def test_mono_input_duplicated_to_stereo(self, tmp_path):
        p = tmp_path / "mono_to_stereo.wav"
        audio = np.ones(100, dtype=np.float32) * 0.5
        _write_stereo_wav(p, audio, 22050)

        with wave.open(str(p), "rb") as wf:
            assert wf.getnchannels() == 2
            frames = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            # L and R channels should be equal
            L = frames[0::2]
            R = frames[1::2]
            np.testing.assert_array_equal(L, R)

    def test_already_stereo_input(self, tmp_path):
        p = tmp_path / "2ch.wav"
        audio = np.random.rand(500, 2).astype(np.float32) * 2 - 1
        _write_stereo_wav(p, audio, 22050)

        with wave.open(str(p), "rb") as wf:
            assert wf.getnchannels() == 2


# ---------------------------------------------------------------------------
# _concat_wavs
# ---------------------------------------------------------------------------


class TestConcatWavs:
    def _write_wav_file(self, path: Path, samples: np.ndarray, sr: int = 22050):
        """Helper to write a simple mono WAV."""
        int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(int16.tobytes())

    def test_empty_list_creates_empty_wav(self, tmp_path):
        out = tmp_path / "empty.wav"
        _concat_wavs(out, [])
        assert out.exists()
        with wave.open(str(out), "rb") as wf:
            assert wf.getnframes() == 0

    def test_single_file_concatenated(self, tmp_path):
        p = tmp_path / "a.wav"
        self._write_wav_file(p, np.ones(100) * 0.5)
        out = tmp_path / "concat.wav"
        _concat_wavs(out, [p])

        with wave.open(str(out), "rb") as wf:
            assert wf.getnframes() == 100

    def test_multiple_files_total_frames(self, tmp_path):
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        c = tmp_path / "c.wav"
        self._write_wav_file(a, np.ones(100) * 0.1)
        self._write_wav_file(b, np.ones(200) * 0.2)
        self._write_wav_file(c, np.ones(300) * 0.3)
        out = tmp_path / "abc.wav"
        _concat_wavs(out, [a, b, c])

        with wave.open(str(out), "rb") as wf:
            assert wf.getnframes() == 600

    def test_incompatible_params_falls_back_to_first(self, tmp_path):
        """When sample rates differ, output should still be written."""
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        self._write_wav_file(a, np.zeros(100), sr=22050)
        self._write_wav_file(b, np.zeros(100), sr=44100)  # different SR
        out = tmp_path / "mixed.wav"
        _concat_wavs(out, [a, b])
        # Output must exist (fallback copies first file)
        assert out.exists()
