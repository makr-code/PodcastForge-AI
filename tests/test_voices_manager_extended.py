"""Extended tests for podcastforge.voices.manager – preview_voice and speaker_from_voice."""
import os
import wave
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.voices.manager import preview_voice, speaker_from_voice


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_voice_stub(voice_id="v1"):
    class V:
        id = voice_id
        name = "Test Voice"
        display_name = "Test Voice (Display)"
        repo = "org/repo"
        sub_path = "sub"
        sample_filename = "sample.wav"
        description = "A test voice"
        gender = type("G", (), {"value": "female"})()
        age = type("A", (), {"value": "adult"})()

    return V()


def _make_lib(voice=None):
    """Return a minimal voice library stub."""
    v = voice

    class Lib:
        def get_voice(self, vid):
            return v

    return Lib()


def _make_engine(sr=22050, raise_first=False):
    class Eng:
        _calls = 0

        def synthesize(self, text, voice_id):
            Eng._calls += 1
            if raise_first and Eng._calls == 1:
                raise RuntimeError("first call fails")
            return np.zeros(sr, dtype=np.float32), sr

    Eng._calls = 0
    return Eng()


# ---------------------------------------------------------------------------
# preview_voice – happy path
# ---------------------------------------------------------------------------


class TestPreviewVoiceHappy:
    def test_returns_path_string(self, monkeypatch):
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: _make_engine())
        monkeypatch.setattr("podcastforge.voices.manager.get_player",
                            lambda: type("P", (), {"play": lambda self, p: None})())
        result = preview_voice("v1", play=False)
        assert isinstance(result, str)

    def test_output_file_is_valid_wav(self, monkeypatch, tmp_path):
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: _make_engine())
        monkeypatch.setattr("podcastforge.voices.manager.get_player",
                            lambda: type("P", (), {"play": lambda self, p: None})())
        result = preview_voice("v1", play=False)
        assert result is not None
        with wave.open(result, "rb") as wf:
            assert wf.getsampwidth() == 2
            assert wf.getnchannels() == 1

    def test_play_true_calls_player(self, monkeypatch):
        played = []
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: _make_engine())

        class Player:
            def play(self, path):
                played.append(str(path))

        monkeypatch.setattr("podcastforge.voices.manager.get_player", lambda: Player())
        result = preview_voice("v1", play=True)
        assert result is not None
        assert len(played) == 1

    def test_stereo_audio_is_downmixed_to_mono(self, monkeypatch):
        """Engine returning stereo audio should still produce mono WAV."""
        sr = 22050

        class StereoEngine:
            def synthesize(self, text, voice_id):
                return np.zeros((sr, 2), dtype=np.float32), sr

        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: StereoEngine())
        monkeypatch.setattr("podcastforge.voices.manager.get_player",
                            lambda: type("P", (), {"play": lambda self, p: None})())
        result = preview_voice("v1", play=False)
        assert result is not None
        with wave.open(result, "rb") as wf:
            assert wf.getnchannels() == 1

    def test_player_error_does_not_propagate(self, monkeypatch):
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: _make_engine())

        class BadPlayer:
            def play(self, path):
                raise OSError("audio device unavailable")

        monkeypatch.setattr("podcastforge.voices.manager.get_player", lambda: BadPlayer())
        result = preview_voice("v1", play=True)
        assert result is not None  # should still return a path

    def test_engine_fallback_on_first_call_failure(self, monkeypatch):
        """First synthesize call fails → fallback synthesize by name is tried."""
        sr = 22050
        call_count = {"n": 0}

        class FallbackEngine:
            def synthesize(self, text, voice_id):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    raise RuntimeError("primary fails")
                return np.zeros(sr, dtype=np.float32), sr

        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: FallbackEngine())
        monkeypatch.setattr("podcastforge.voices.manager.get_player",
                            lambda: type("P", (), {"play": lambda self, p: None})())
        result = preview_voice("v1", play=False)
        assert result is not None
        assert call_count["n"] == 2  # tried twice


# ---------------------------------------------------------------------------
# preview_voice – error / edge cases
# ---------------------------------------------------------------------------


class TestPreviewVoiceErrors:
    def test_returns_none_for_unknown_voice_id(self, monkeypatch):
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(None))
        result = preview_voice("nonexistent", play=False)
        assert result is None

    def test_returns_none_when_all_synth_calls_fail(self, monkeypatch):
        class BrokenEngine:
            def synthesize(self, text, voice_id):
                raise RuntimeError("always fails")

        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(_make_voice_stub()))
        monkeypatch.setattr("podcastforge.voices.manager.get_engine_manager",
                            lambda: BrokenEngine())
        monkeypatch.setattr("podcastforge.voices.manager.get_player",
                            lambda: type("P", (), {"play": lambda self, p: None})())
        result = preview_voice("v1", play=False)
        assert result is None


# ---------------------------------------------------------------------------
# speaker_from_voice
# ---------------------------------------------------------------------------


class TestSpeakerFromVoice:
    def test_returns_speaker_with_correct_fields(self, monkeypatch):
        v = _make_voice_stub("anna")
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(v))
        sp = speaker_from_voice("anna")
        assert sp.id == "anna"
        assert sp.voice_profile == "anna"
        assert sp.gender == "female"
        assert sp.age == "adult"
        assert sp.name == "Test Voice (Display)"

    def test_custom_speaker_name_overrides_display_name(self, monkeypatch):
        v = _make_voice_stub("anna")
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(v))
        sp = speaker_from_voice("anna", speaker_name="Custom Anna")
        assert sp.name == "Custom Anna"

    def test_raises_for_unknown_voice_id(self, monkeypatch):
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(None))
        with pytest.raises(ValueError, match="Voice not found"):
            speaker_from_voice("nonexistent")

    def test_voice_sample_path_constructed(self, monkeypatch):
        v = _make_voice_stub("bob")
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(v))
        sp = speaker_from_voice("bob")
        assert "org/repo" in sp.voice_sample
        assert "sample.wav" in sp.voice_sample

    def test_role_is_guest(self, monkeypatch):
        v = _make_voice_stub("x")
        monkeypatch.setattr("podcastforge.voices.manager.get_voice_library",
                            lambda: _make_lib(v))
        sp = speaker_from_voice("x")
        assert sp.role == "guest"
