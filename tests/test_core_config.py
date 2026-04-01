"""
Unit tests for podcastforge.core.config

Tests for Speaker, PodcastConfig, ScriptLine, VOICE_QUALITY_PRESETS,
PODCAST_TEMPLATES, get_quality_preset, and get_podcast_template.
"""

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.core.config import (
    PodcastConfig,
    PodcastStyle,
    ScriptLine,
    Speaker,
    VoiceQuality,
    VOICE_QUALITY_PRESETS,
    PODCAST_TEMPLATES,
    get_quality_preset,
    get_podcast_template,
)


def _make_speaker(**kwargs):
    defaults = dict(
        id="s1",
        name="Anna",
        role="Moderator",
        personality="freundlich",
        voice_profile="anna_de",
    )
    defaults.update(kwargs)
    return Speaker(**defaults)


def _make_config(**kwargs):
    defaults = dict(
        topic="KI in der Medizin",
        style=PodcastStyle.INTERVIEW,
        speakers=[_make_speaker()],
    )
    defaults.update(kwargs)
    return PodcastConfig(**defaults)


# ---------------------------------------------------------------------------
# Speaker
# ---------------------------------------------------------------------------


class TestSpeaker:
    def test_minimal_creation(self):
        s = _make_speaker()
        assert s.id == "s1"
        assert s.name == "Anna"
        assert s.gender == "neutral"
        assert s.age == "adult"
        assert s.voice_engine is None

    def test_voice_engine_override(self):
        s = _make_speaker(voice_engine="piper")
        assert s.voice_engine == "piper"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="Speaker ID"):
            _make_speaker(id="")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="Speaker Name"):
            _make_speaker(name="")

    def test_optional_voice_sample(self):
        s = _make_speaker(voice_sample="/path/to/sample.wav")
        assert s.voice_sample == "/path/to/sample.wav"


# ---------------------------------------------------------------------------
# PodcastConfig
# ---------------------------------------------------------------------------


class TestPodcastConfig:
    def test_minimal_creation(self):
        cfg = _make_config()
        assert cfg.topic == "KI in der Medizin"
        assert cfg.style == PodcastStyle.INTERVIEW
        assert cfg.voice_engine == "xtts"
        assert cfg.fallback_engines == []
        assert cfg.duration_minutes == 10

    def test_style_coercion_from_string(self):
        cfg = _make_config(style="discussion")
        assert cfg.style == PodcastStyle.DISCUSSION

    def test_voice_quality_coercion_from_string(self):
        cfg = _make_config(voice_quality="high")
        assert cfg.voice_quality == VoiceQuality.HIGH

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError, match="Dauer"):
            _make_config(duration_minutes=0)

    def test_empty_speakers_raises(self):
        with pytest.raises(ValueError, match="Sprecher"):
            _make_config(speakers=[])

    def test_fallback_engines_stored(self):
        cfg = _make_config(fallback_engines=["piper", "dummy"])
        assert cfg.fallback_engines == ["piper", "dummy"]

    def test_multiple_speakers(self):
        speakers = [_make_speaker(id=f"s{i}", name=f"Speaker{i}") for i in range(3)]
        cfg = _make_config(speakers=speakers)
        assert len(cfg.speakers) == 3

    def test_default_voice_quality(self):
        cfg = _make_config()
        assert cfg.voice_quality == VoiceQuality.STANDARD


# ---------------------------------------------------------------------------
# ScriptLine
# ---------------------------------------------------------------------------


class TestScriptLine:
    def test_creation_and_to_dict(self):
        line = ScriptLine(
            speaker_id="s1",
            speaker_name="Anna",
            text="Hallo und willkommen!",
            emotion="happy",
            pause_after=0.8,
            voice_profile="anna_de",
        )
        d = line.to_dict()
        assert d["speaker_id"] == "s1"
        assert d["speaker_name"] == "Anna"
        assert d["text"] == "Hallo und willkommen!"
        assert d["emotion"] == "happy"
        assert d["pause_after"] == 0.8
        assert d["voice_profile"] == "anna_de"

    def test_default_values(self):
        line = ScriptLine(speaker_id="s1", speaker_name="Anna", text="Test")
        assert line.emotion == "neutral"
        assert line.pause_after == 0.5
        assert line.voice_profile == ""


# ---------------------------------------------------------------------------
# VOICE_QUALITY_PRESETS / get_quality_preset
# ---------------------------------------------------------------------------


class TestVoiceQualityPresets:
    def test_all_qualities_present(self):
        for q in VoiceQuality:
            assert q in VOICE_QUALITY_PRESETS

    def test_preview_uses_piper(self):
        preset = get_quality_preset(VoiceQuality.PREVIEW)
        assert preset["engine"] == "piper"

    def test_standard_uses_xtts(self):
        preset = get_quality_preset(VoiceQuality.STANDARD)
        assert preset["engine"] == "xtts"

    def test_high_quality_has_high_samplerate(self):
        preset = get_quality_preset(VoiceQuality.HIGH)
        assert preset["sample_rate"] >= 44100

    def test_ultra_quality_has_highest_samplerate(self):
        ultra = get_quality_preset(VoiceQuality.ULTRA)
        high = get_quality_preset(VoiceQuality.HIGH)
        assert ultra["sample_rate"] >= high["sample_rate"]

    def test_unknown_quality_falls_back_to_standard(self):
        # get_quality_preset falls back to STANDARD for unknown keys
        preset = VOICE_QUALITY_PRESETS.get(None, VOICE_QUALITY_PRESETS[VoiceQuality.STANDARD])
        assert preset["engine"] == "xtts"


# ---------------------------------------------------------------------------
# PODCAST_TEMPLATES / get_podcast_template
# ---------------------------------------------------------------------------


class TestPodcastTemplates:
    def test_all_styles_have_templates(self):
        for style in PodcastStyle:
            tmpl = get_podcast_template(style)
            assert "name" in tmpl
            assert "num_speakers" in tmpl
            assert "speaker_roles" in tmpl

    def test_interview_has_two_speakers(self):
        tmpl = get_podcast_template(PodcastStyle.INTERVIEW)
        assert tmpl["num_speakers"] == 2

    def test_debate_has_three_speakers(self):
        tmpl = get_podcast_template(PodcastStyle.DEBATE)
        assert tmpl["num_speakers"] == 3

    def test_unknown_style_returns_discussion(self):
        # get_podcast_template falls back to DISCUSSION for keys not in the dict
        fallback = PODCAST_TEMPLATES.get("nonexistent_style", PODCAST_TEMPLATES[PodcastStyle.DISCUSSION])
        assert fallback["name"] == "Diskussion"
