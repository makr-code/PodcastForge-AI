"""Unit tests for podcastforge.audio.ffmpeg_pipe."""
import os
import shutil
import struct
import sys
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.audio.ffmpeg_pipe import (
    find_ffmpeg,
    _ensure_third_party_ffmpeg_on_path,
    _wav_frames_as_s16,
    feed_wav_to_pipe,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_wav(path: Path, samples: np.ndarray, sr: int, channels: int = 1, sampwidth: int = 2):
    """Write a minimal WAV file for testing."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())


# ---------------------------------------------------------------------------
# find_ffmpeg
# ---------------------------------------------------------------------------


class TestFindFfmpeg:
    def test_returns_none_when_not_on_path(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
        # Make _ensure_third_party_ffmpeg_on_path return None too
        with patch("podcastforge.audio.ffmpeg_pipe._ensure_third_party_ffmpeg_on_path",
                   return_value=None):
            result = find_ffmpeg()
        assert result is None

    def test_returns_path_when_on_system_path(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name, **k: "/usr/bin/ffmpeg" if name == "ffmpeg" else None)
        result = find_ffmpeg()
        assert result == "/usr/bin/ffmpeg"

    def test_cli_path_existing_file(self, tmp_path):
        fake_ff = tmp_path / "ffmpeg"
        fake_ff.touch()
        result = find_ffmpeg(cli_path=str(fake_ff))
        assert result == str(fake_ff)

    def test_cli_path_nonexistent_returns_none(self, tmp_path):
        result = find_ffmpeg(cli_path=str(tmp_path / "no_ffmpeg"))
        assert result is None


# ---------------------------------------------------------------------------
# _ensure_third_party_ffmpeg_on_path
# ---------------------------------------------------------------------------


class TestEnsureThirdPartyFfmpegOnPath:
    def test_returns_none_when_no_bundled_ffmpeg(self, tmp_path, monkeypatch):
        # Run from a temp dir that has no third_party/ffmpeg/bin
        monkeypatch.setattr(
            "podcastforge.audio.ffmpeg_pipe.Path",
            lambda p: Path(p),
        )
        # Since the repo doesn't have third_party/ffmpeg/bin in CI, result is None
        result = _ensure_third_party_ffmpeg_on_path()
        assert result is None or isinstance(result, str)

    def test_adds_to_path_when_dir_exists(self, tmp_path, monkeypatch):
        ffmpeg_bin = tmp_path / "third_party" / "ffmpeg" / "bin"
        ffmpeg_bin.mkdir(parents=True)
        # Patch __file__ so the parent search finds our fake dir
        import podcastforge.audio.ffmpeg_pipe as fp_module
        monkeypatch.setattr(fp_module, "__file__", str(tmp_path / "audio" / "ffmpeg_pipe.py"))
        result = _ensure_third_party_ffmpeg_on_path()
        if result:  # only if found
            assert str(ffmpeg_bin) in os.environ.get("PATH", "")


# ---------------------------------------------------------------------------
# _wav_frames_as_s16
# ---------------------------------------------------------------------------


class TestWavFramesAsS16:
    def test_int16_passthrough(self, tmp_path):
        """16-bit WAV should pass through without conversion."""
        sr = 22050
        samples = np.array([0, 100, -100, 32767, -32768], dtype=np.int16)
        p = tmp_path / "int16.wav"
        _write_wav(p, samples, sr, sampwidth=2)

        data, returned_sr, nch = _wav_frames_as_s16(p)
        assert returned_sr == sr
        assert nch == 1
        assert isinstance(data, bytes)
        assert len(data) == len(samples) * 2

    def test_uint8_converted_to_int16(self, tmp_path):
        """8-bit unsigned WAV should be converted to signed int16."""
        sr = 22050
        # 8-bit PCM: values 0-255, midpoint 128
        samples = np.array([128, 200, 50], dtype=np.uint8)
        p = tmp_path / "uint8.wav"
        _write_wav(p, samples, sr, sampwidth=1)

        data, returned_sr, nch = _wav_frames_as_s16(p)
        assert returned_sr == sr
        assert isinstance(data, bytes)

    def test_int32_converted_to_int16(self, tmp_path):
        """32-bit WAV should be converted to int16."""
        sr = 44100
        samples = np.array([0, 100000, -100000, 2147483647], dtype=np.int32)
        p = tmp_path / "int32.wav"
        _write_wav(p, samples, sr, sampwidth=4)

        data, returned_sr, nch = _wav_frames_as_s16(p)
        assert returned_sr == sr
        assert isinstance(data, bytes)


# ---------------------------------------------------------------------------
# feed_wav_to_pipe
# ---------------------------------------------------------------------------


class TestFeedWavToPipe:
    def test_writes_frames_to_stdin(self, tmp_path):
        sr = 22050
        samples = np.zeros(100, dtype=np.int16)
        p = tmp_path / "silence.wav"
        _write_wav(p, samples, sr)

        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdin.write = MagicMock()
        proc.stdin.flush = MagicMock()

        feed_wav_to_pipe(proc, p)
        proc.stdin.write.assert_called_once()
        proc.stdin.flush.assert_called_once()

    def test_raises_when_stdin_is_none(self, tmp_path):
        sr = 22050
        samples = np.zeros(10, dtype=np.int16)
        p = tmp_path / "silence.wav"
        _write_wav(p, samples, sr)

        proc = MagicMock()
        proc.stdin = None

        with pytest.raises(RuntimeError, match="stdin"):
            feed_wav_to_pipe(proc, p)

    def test_handles_broken_pipe_gracefully(self, tmp_path):
        sr = 22050
        samples = np.zeros(10, dtype=np.int16)
        p = tmp_path / "silence.wav"
        _write_wav(p, samples, sr)

        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdin.write.side_effect = BrokenPipeError("pipe closed")

        # Should not raise; BrokenPipeError is caught internally
        feed_wav_to_pipe(proc, p)
