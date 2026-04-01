"""Tests for podcastforge.voices.cloner – ClonedVoiceProfile and VoiceCloner helpers."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.voices.cloner import (
    ClonedVoiceProfile,
    VoiceCloner,
    VoiceQuality,
)


# ---------------------------------------------------------------------------
# ClonedVoiceProfile
# ---------------------------------------------------------------------------


class TestClonedVoiceProfileToDict:
    def _profile(self, **kwargs):
        defaults = dict(
            id="v1",
            name="TestVoice",
            sample_file=Path("/tmp/sample.wav"),
            quality=VoiceQuality.GOOD,
            sample_duration=7.5,
            sample_rate=24000,
        )
        defaults.update(kwargs)
        return ClonedVoiceProfile(**defaults)

    def test_to_dict_contains_required_keys(self):
        d = self._profile().to_dict()
        for k in ("id", "name", "sample_file", "quality", "sample_duration", "sample_rate"):
            assert k in d

    def test_to_dict_quality_is_string(self):
        d = self._profile(quality=VoiceQuality.EXCELLENT).to_dict()
        assert d["quality"] == "excellent"

    def test_to_dict_sample_file_is_string(self):
        d = self._profile().to_dict()
        assert isinstance(d["sample_file"], str)

    def test_from_dict_round_trip(self):
        p = self._profile()
        d = p.to_dict()
        restored = ClonedVoiceProfile.from_dict(d)
        assert restored.id == p.id
        assert restored.name == p.name
        assert restored.quality == p.quality
        assert restored.sample_duration == p.sample_duration

    def test_from_dict_defaults_for_missing_keys(self):
        data = {"id": "x", "name": "X", "sample_file": "/tmp/x.wav", "quality": "good"}
        p = ClonedVoiceProfile.from_dict(data)
        assert p.sample_duration == 0.0
        assert p.sample_rate == 24000
        assert p.metadata == {}

    def test_all_quality_values_serializable(self):
        for q in VoiceQuality:
            p = self._profile(quality=q)
            d = p.to_dict()
            restored = ClonedVoiceProfile.from_dict(d)
            assert restored.quality == q


# ---------------------------------------------------------------------------
# VoiceCloner – __init__ / profile management
# ---------------------------------------------------------------------------


class TestVoiceClonerInit:
    def test_creates_cache_dir(self, tmp_path):
        cache = tmp_path / "voice_clones"
        assert not cache.exists()
        cloner = VoiceCloner(cache_dir=cache)
        assert cache.exists()

    def test_starts_with_empty_profiles_when_no_file(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        assert cloner.get_all_profiles() == []

    def test_load_profiles_from_json(self, tmp_path):
        cache = tmp_path / "vc"
        cache.mkdir()
        profile_data = {
            "profiles": [
                {
                    "id": "p1", "name": "Anna", "sample_file": "/tmp/anna.wav",
                    "quality": "good", "sample_duration": 6.0, "sample_rate": 24000,
                    "metadata": {},
                }
            ]
        }
        (cache / "profiles.json").write_text(json.dumps(profile_data))
        cloner = VoiceCloner(cache_dir=cache)
        assert len(cloner.get_all_profiles()) == 1
        assert cloner.profiles["p1"].name == "Anna"

    def test_load_profiles_ignores_corrupt_json(self, tmp_path):
        cache = tmp_path / "vc"
        cache.mkdir()
        (cache / "profiles.json").write_text("{BROKEN JSON}")
        # Should not raise
        cloner = VoiceCloner(cache_dir=cache)
        assert cloner.get_all_profiles() == []


class TestVoiceClonerSaveDelete:
    def test_save_and_reload_profiles(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        p = ClonedVoiceProfile(
            id="p1", name="Bob", sample_file=Path("/tmp/bob.wav"),
            quality=VoiceQuality.GOOD, sample_duration=8.0, sample_rate=24000,
        )
        cloner.profiles["p1"] = p
        cloner._save_profiles()

        cloner2 = VoiceCloner(cache_dir=tmp_path / "vc")
        assert "p1" in cloner2.profiles
        assert cloner2.profiles["p1"].name == "Bob"

    def test_delete_profile_removes_it(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        p = ClonedVoiceProfile(
            id="p2", name="Clara", sample_file=Path("/tmp/c.wav"),
            quality=VoiceQuality.ACCEPTABLE,
        )
        cloner.profiles["p2"] = p
        cloner.delete_profile("p2")
        assert "p2" not in cloner.profiles

    def test_delete_nonexistent_profile_is_noop(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        cloner.delete_profile("does_not_exist")  # Should not raise

    def test_get_all_profiles_returns_list(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        result = cloner.get_all_profiles()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# VoiceCloner.check_audio_quality
# ---------------------------------------------------------------------------


class TestCheckAudioQuality:
    def test_poor_quality_for_very_short_audio(self, tmp_path):
        """Mock pydub to return a 1-second AudioSegment (< 3s MIN)."""
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 1000  # 1 second in ms
        with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
            quality = cloner.check_audio_quality(Path("/tmp/short.wav"))
        assert quality == VoiceQuality.POOR

    def test_acceptable_quality_for_4s_audio(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 4000  # 4 seconds
        with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
            quality = cloner.check_audio_quality(Path("/tmp/4s.wav"))
        assert quality == VoiceQuality.ACCEPTABLE

    def test_good_quality_for_7s_audio(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 7000  # 7 seconds
        with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
            quality = cloner.check_audio_quality(Path("/tmp/7s.wav"))
        assert quality == VoiceQuality.GOOD

    def test_excellent_quality_for_12s_audio(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 12000  # 12 seconds
        with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
            quality = cloner.check_audio_quality(Path("/tmp/12s.wav"))
        assert quality == VoiceQuality.EXCELLENT

    def test_returns_poor_when_pydub_raises(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        with patch("pydub.AudioSegment.from_file",
                   side_effect=Exception("file not found")):
            quality = cloner.check_audio_quality(Path("/tmp/missing.wav"))
        assert quality == VoiceQuality.POOR


# ---------------------------------------------------------------------------
# VoiceCloner.synthesize_with_cloned_voice – KeyError on missing voice
# ---------------------------------------------------------------------------


class TestSynthesizeWithClonedVoice:
    def test_raises_key_error_for_unknown_voice(self, tmp_path):
        cloner = VoiceCloner(cache_dir=tmp_path / "vc")
        with pytest.raises(KeyError, match="Voice not found"):
            cloner.synthesize_with_cloned_voice("text", "nonexistent_id")
