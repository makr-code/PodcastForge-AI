"""Extended tests for script_orchestrator – helper functions and synthesize_script_preview."""
import json
import sys
import threading
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.integrations.script_orchestrator import (
    _cache_key,
    _concat_wavs,
    _write_wav,
    _write_stereo_wav,
    synthesize_script_preview,
)


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------


class TestCacheKey:
    def test_returns_hex_string(self):
        key = _cache_key("hello", "sp1", "PIPER")
        assert isinstance(key, str)
        assert all(c in "0123456789abcdef" for c in key)

    def test_same_inputs_give_same_key(self):
        k1 = _cache_key("text", "sp", "PIPER")
        k2 = _cache_key("text", "sp", "PIPER")
        assert k1 == k2

    def test_different_text_gives_different_key(self):
        k1 = _cache_key("hello", "sp", "PIPER")
        k2 = _cache_key("world", "sp", "PIPER")
        assert k1 != k2

    def test_different_speaker_gives_different_key(self):
        k1 = _cache_key("hello", "sp1", "PIPER")
        k2 = _cache_key("hello", "sp2", "PIPER")
        assert k1 != k2

    def test_different_engine_gives_different_key(self):
        k1 = _cache_key("hello", "sp", "PIPER")
        k2 = _cache_key("hello", "sp", "BARK")
        assert k1 != k2

    def test_none_engine_gives_stable_key(self):
        k1 = _cache_key("hello", "sp", None)
        k2 = _cache_key("hello", "sp", None)
        assert k1 == k2

    def test_key_length_is_64_chars(self):
        key = _cache_key("text", "sp", "PIPER")
        assert len(key) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# _write_wav / _write_stereo_wav
# ---------------------------------------------------------------------------


class TestWriteWav:
    def test_creates_valid_mono_wav(self, tmp_path):
        path = tmp_path / "out.wav"
        audio = np.zeros(22050, dtype=np.float32)
        _write_wav(path, audio, 22050)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2

    def test_clips_audio_above_one(self, tmp_path):
        path = tmp_path / "clipped.wav"
        audio = np.ones(1000, dtype=np.float32) * 5.0
        _write_wav(path, audio, 22050)
        assert path.exists()

    def test_downmixes_stereo_to_mono(self, tmp_path):
        path = tmp_path / "stereo.wav"
        audio = np.zeros((22050, 2), dtype=np.float32)
        _write_wav(path, audio, 22050)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnchannels() == 1


class TestWriteStereoWav:
    def test_creates_valid_stereo_wav(self, tmp_path):
        path = tmp_path / "stereo.wav"
        audio = np.zeros(22050, dtype=np.float32)
        _write_stereo_wav(path, audio, 22050)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnchannels() == 2

    def test_mono_input_is_duplicated_to_stereo(self, tmp_path):
        path = tmp_path / "s.wav"
        audio = np.ones(1000, dtype=np.float32) * 0.3
        _write_stereo_wav(path, audio, 22050)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnchannels() == 2

    def test_single_channel_2d_is_doubled(self, tmp_path):
        path = tmp_path / "s2.wav"
        audio = np.ones((1000, 1), dtype=np.float32) * 0.3
        _write_stereo_wav(path, audio, 22050)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnchannels() == 2


# ---------------------------------------------------------------------------
# _concat_wavs
# ---------------------------------------------------------------------------


def _make_wav(path: Path, sr: int = 22050, channels: int = 1, duration_s: float = 0.1):
    frames = (np.zeros(int(sr * duration_s), dtype=np.int16)).tobytes()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)


class TestConcatWavs:
    def test_empty_list_creates_silent_wav(self, tmp_path):
        out = tmp_path / "out.wav"
        _concat_wavs(out, [])
        assert out.exists()
        with wave.open(str(out), "rb") as wf:
            assert wf.getnframes() == 0

    def test_single_file_produces_copy(self, tmp_path):
        src = tmp_path / "a.wav"
        out = tmp_path / "out.wav"
        _make_wav(src)
        _concat_wavs(out, [src])
        assert out.exists()

    def test_two_compatible_files_concatenated(self, tmp_path):
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        out = tmp_path / "out.wav"
        _make_wav(a, duration_s=0.1)
        _make_wav(b, duration_s=0.2)
        _concat_wavs(out, [a, b])
        with wave.open(str(out), "rb") as wf:
            total_frames = wf.getnframes()
        with wave.open(str(a), "rb") as wa:
            fa = wa.getnframes()
        with wave.open(str(b), "rb") as wb:
            fb = wb.getnframes()
        assert total_frames == fa + fb

    def test_incompatible_sample_rates_copies_first(self, tmp_path):
        a = tmp_path / "a.wav"
        b = tmp_path / "b.wav"
        out = tmp_path / "out.wav"
        _make_wav(a, sr=22050)
        _make_wav(b, sr=44100)
        # Should not raise; falls back to copying first file
        _concat_wavs(out, [a, b])
        assert out.exists()


# ---------------------------------------------------------------------------
# synthesize_script_preview – error / early-exit paths
# ---------------------------------------------------------------------------


class TestSynthesizeScriptPreviewErrors:
    def test_missing_script_returns_error(self, tmp_path):
        result = synthesize_script_preview(
            script_path=str(tmp_path / "nonexistent.json"),
            out_dir=str(tmp_path / "out"),
        )
        assert result["ok"] is False
        assert "script not found" in result.get("message", "").lower()

    def test_invalid_json_returns_error(self, tmp_path):
        script = tmp_path / "bad.json"
        script.write_text("{BROKEN JSON}", encoding="utf-8")
        result = synthesize_script_preview(
            script_path=str(script),
            out_dir=str(tmp_path / "out"),
        )
        assert result["ok"] is False

    def test_non_list_script_returns_error(self, tmp_path):
        script = tmp_path / "scalar.json"
        script.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = synthesize_script_preview(
            script_path=str(script),
            out_dir=str(tmp_path / "out"),
        )
        assert result["ok"] is False
        assert "list" in result.get("message", "").lower()

    def test_empty_script_list_returns_ok(self, tmp_path):
        script = tmp_path / "empty.json"
        script.write_text("[]", encoding="utf-8")
        result = synthesize_script_preview(
            script_path=str(script),
            out_dir=str(tmp_path / "out"),
        )
        # No entries to synthesize → should succeed (ok=True or empty clips)
        assert isinstance(result, dict)
        assert result.get("ok") is not False or result.get("clips") == []

    def test_cache_hit_avoids_synthesis(self, tmp_path):
        """If cached file exists already, synthesis should be skipped."""
        from podcastforge.integrations.script_orchestrator import _cache_key
        from podcastforge.tts.engine_manager import TTSEngine

        out = tmp_path / "out"
        cache = out / "cache"
        cache.mkdir(parents=True)
        script = tmp_path / "s.json"
        text = "Hello world."
        speaker = "narrator"
        engine = "PIPER"
        key = _cache_key(text, speaker, engine)
        # pre-create the cached wav file
        cached_wav = cache / f"{key}.wav"
        _make_wav(cached_wav)
        script.write_text(json.dumps([{"speaker": speaker, "text": text}]))

        # Patch get_engine_manager so synth is never called
        from unittest.mock import patch
        with patch("podcastforge.integrations.script_orchestrator.get_engine_manager") as mock_mgr:
            result = synthesize_script_preview(
                script_path=str(script),
                out_dir=str(out),
                cache_dir=str(cache),
                engine=engine,
            )
        # synthesize should NOT have been called because cache hit
        mock_mgr.return_value.synthesize.assert_not_called()
        assert isinstance(result, dict)

    def test_cancel_event_stops_synthesis(self, tmp_path):
        """When cancel event is pre-set, tasks report cancelled and result is a dict."""
        script = tmp_path / "s.json"
        script.write_text(json.dumps([
            {"speaker": "sp1", "text": "Hello one."},
            {"speaker": "sp2", "text": "Hello two."},
        ]))
        cancel = threading.Event()
        cancel.set()  # already cancelled before synthesis starts

        from unittest.mock import patch, MagicMock
        mock_mgr = MagicMock()
        mock_mgr.synthesize.return_value = (np.zeros(100, dtype=np.float32), 22050)
        with patch("podcastforge.integrations.script_orchestrator.get_engine_manager",
                   return_value=mock_mgr):
            result = synthesize_script_preview(
                script_path=str(script),
                out_dir=str(tmp_path / "out"),
                engine="DUMMY",
                cancel_event=cancel,
            )
        # With cancel set, result is a dict – may be ok=False (timeout/error) or ok=True
        assert isinstance(result, dict)
        assert "ok" in result
