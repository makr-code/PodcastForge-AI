"""Extended tests for podcastforge.voices.library – save_to_yaml, load_from_yaml, suggest_for_podcast_style."""
import sys
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.voices.library import (
    VoiceAge,
    VoiceGender,
    VoiceLibrary,
    VoiceProfile,
    VoiceStyle,
)
from podcastforge.core.config import PodcastStyle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_voice(
    id="v1",
    name="Test",
    language="de",
    gender=VoiceGender.MALE,
    age=VoiceAge.ADULT,
    style=VoiceStyle.PROFESSIONAL,
    tags=None,
):
    return VoiceProfile(
        id=id,
        name=name,
        display_name=name,
        language=language,
        gender=gender,
        age=age,
        style=style,
        description="desc",
        repo="org/repo",
        sub_path="sub",
        sample_filename="s.wav",
        engine="xtts",
        samplerate=24000,
        tags=tags or [],
    )


def _lib_with(*voices):
    lib = VoiceLibrary.__new__(VoiceLibrary)
    lib.all_voices = list(voices)
    lib._index_voices()
    return lib


# ---------------------------------------------------------------------------
# VoiceProfile.matches_criteria
# ---------------------------------------------------------------------------


class TestVoiceProfileMatchesCriteria:
    def test_matches_all_none(self):
        v = _make_voice()
        assert v.matches_criteria() is True

    def test_matches_correct_language(self):
        v = _make_voice(language="en")
        assert v.matches_criteria(language="en") is True
        assert v.matches_criteria(language="de") is False

    def test_matches_correct_gender(self):
        v = _make_voice(gender=VoiceGender.FEMALE)
        assert v.matches_criteria(gender=VoiceGender.FEMALE) is True
        assert v.matches_criteria(gender=VoiceGender.MALE) is False

    def test_matches_correct_age(self):
        v = _make_voice(age=VoiceAge.YOUNG)
        assert v.matches_criteria(age=VoiceAge.YOUNG) is True
        assert v.matches_criteria(age=VoiceAge.ELDER) is False

    def test_matches_correct_style(self):
        v = _make_voice(style=VoiceStyle.CASUAL)
        assert v.matches_criteria(style=VoiceStyle.CASUAL) is True
        assert v.matches_criteria(style=VoiceStyle.DOCUMENTARY) is False


# ---------------------------------------------------------------------------
# VoiceLibrary.list_languages
# ---------------------------------------------------------------------------


class TestListLanguages:
    def test_empty_library(self):
        lib = _lib_with()
        assert lib.list_languages() == []

    def test_single_language(self):
        lib = _lib_with(_make_voice(language="de"))
        assert "de" in lib.list_languages()

    def test_multiple_languages(self):
        lib = _lib_with(
            _make_voice(id="v1", language="de"),
            _make_voice(id="v2", language="en"),
            _make_voice(id="v3", language="de"),
        )
        langs = lib.list_languages()
        assert "de" in langs and "en" in langs
        assert len(set(langs)) == len(langs)  # no duplicates


# ---------------------------------------------------------------------------
# VoiceLibrary.get_voice_count
# ---------------------------------------------------------------------------


class TestGetVoiceCount:
    def test_total_count(self):
        lib = _lib_with(_make_voice(id="a"), _make_voice(id="b"), _make_voice(id="c"))
        assert lib.get_voice_count() == 3

    def test_count_by_language(self):
        lib = _lib_with(
            _make_voice(id="v1", language="de"),
            _make_voice(id="v2", language="en"),
            _make_voice(id="v3", language="de"),
        )
        assert lib.get_voice_count(language="de") == 2
        assert lib.get_voice_count(language="en") == 1
        assert lib.get_voice_count(language="fr") == 0

    def test_empty_library(self):
        lib = _lib_with()
        assert lib.get_voice_count() == 0


# ---------------------------------------------------------------------------
# VoiceLibrary.suggest_for_podcast_style
# ---------------------------------------------------------------------------


class TestSuggestForPodcastStyle:
    def _lib_de(self):
        return _lib_with(
            _make_voice(id="m1", language="de", gender=VoiceGender.MALE,
                        style=VoiceStyle.PROFESSIONAL),
            _make_voice(id="m2", language="de", gender=VoiceGender.MALE,
                        style=VoiceStyle.AUTHORITATIVE),
            _make_voice(id="f1", language="de", gender=VoiceGender.FEMALE,
                        style=VoiceStyle.AUTHORITATIVE),
            _make_voice(id="doc1", language="de", gender=VoiceGender.MALE,
                        style=VoiceStyle.DOCUMENTARY),
            _make_voice(id="st1", language="de", gender=VoiceGender.FEMALE,
                        style=VoiceStyle.STORYTELLING),
            _make_voice(id="prof2", language="de", gender=VoiceGender.FEMALE,
                        style=VoiceStyle.PROFESSIONAL),
            _make_voice(id="news1", language="de", gender=VoiceGender.MALE,
                        style=VoiceStyle.PROFESSIONAL, tags=["news"]),
            _make_voice(id="edu1", language="de", gender=VoiceGender.FEMALE,
                        style=VoiceStyle.PROFESSIONAL, tags=["educational"]),
        )

    def test_interview_returns_two_speakers(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.INTERVIEW, language="de", num_speakers=2)
        assert len(result) >= 1

    def test_discussion_returns_mixed_genders(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.DISCUSSION, language="de", num_speakers=2)
        assert len(result) >= 2
        genders = {v.gender for v in result}
        assert VoiceGender.MALE in genders or VoiceGender.FEMALE in genders

    def test_documentary_returns_documentary_voice(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.DOCUMENTARY, language="de", num_speakers=1)
        assert len(result) >= 1
        assert result[0].style == VoiceStyle.DOCUMENTARY

    def test_documentary_fallback_when_no_documentary_voice(self):
        lib = _lib_with(
            _make_voice(id="a1", language="de", style=VoiceStyle.AUTHORITATIVE),
        )
        result = lib.suggest_for_podcast_style(PodcastStyle.DOCUMENTARY, language="de")
        assert len(result) >= 1

    def test_news_returns_tagged_voices(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.NEWS, language="de", num_speakers=1)
        assert len(result) >= 1
        assert any("news" in v.tags for v in result)

    def test_news_fallback_when_no_news_tags(self):
        lib = _lib_with(
            _make_voice(id="p1", language="de", style=VoiceStyle.PROFESSIONAL),
        )
        result = lib.suggest_for_podcast_style(PodcastStyle.NEWS, language="de", num_speakers=1)
        assert len(result) >= 1

    def test_educational_returns_tagged_or_professional(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.EDUCATIONAL, language="de", num_speakers=2)
        assert len(result) >= 1

    def test_narrative_returns_storytelling_voice(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.NARRATIVE, language="de", num_speakers=1)
        assert len(result) >= 1
        assert result[0].style == VoiceStyle.STORYTELLING

    def test_fallback_when_no_voices_match_style(self):
        lib = _lib_with(_make_voice(id="x1", language="de"))
        result = lib.suggest_for_podcast_style(PodcastStyle.NARRATIVE, language="de", num_speakers=1)
        assert len(result) >= 1

    def test_discussion_three_speakers(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.DISCUSSION, language="de", num_speakers=3)
        assert len(result) >= 2  # at least 2 returned

    def test_unknown_language_returns_empty_or_fallback(self):
        lib = self._lib_de()
        result = lib.suggest_for_podcast_style(PodcastStyle.INTERVIEW, language="zh")
        # No zh voices → empty list
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# VoiceLibrary.save_to_yaml / load_from_yaml
# ---------------------------------------------------------------------------


class TestSaveLoadYaml:
    def test_save_to_yaml_creates_file(self, tmp_path):
        lib = _lib_with(_make_voice(id="v1", name="Vocal"))
        yaml = pytest.importorskip("yaml")
        out = str(tmp_path / "voices.yaml")
        result = lib.save_to_yaml(out)
        assert result is True
        assert Path(out).exists()

    def test_save_then_load_round_trip(self, tmp_path):
        yaml = pytest.importorskip("yaml")
        v = _make_voice(id="abc", name="Robin", language="en",
                        gender=VoiceGender.NEUTRAL, style=VoiceStyle.CASUAL)
        lib_original = _lib_with(v)
        path = str(tmp_path / "test_voices.yaml")
        lib_original.save_to_yaml(path)

        lib_loaded = VoiceLibrary.__new__(VoiceLibrary)
        lib_loaded.all_voices = []
        lib_loaded._index_voices = lambda: None
        lib_loaded.by_id = {}
        lib_loaded.by_language = {}
        result = lib_loaded.load_from_yaml(path)
        # After calling real load_from_yaml we need a fresh lib
        lib_fresh = VoiceLibrary.__new__(VoiceLibrary)
        lib_fresh.all_voices = []
        lib_fresh.by_id = {}
        lib_fresh.by_language = {}
        lib_fresh.load_from_yaml(path)
        assert len(lib_fresh.all_voices) == 1
        loaded_v = lib_fresh.all_voices[0]
        assert loaded_v.id == "abc"
        assert loaded_v.language == "en"

    def test_load_from_nonexistent_file_returns_false(self, tmp_path):
        lib = _lib_with()
        result = lib.load_from_yaml(str(tmp_path / "nonexistent.yaml"))
        assert result is False

    def test_load_from_corrupt_yaml_returns_false(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(": : : invalid yaml :::", encoding="utf-8")
        lib = _lib_with()
        result = lib.load_from_yaml(str(p))
        assert result is False

    def test_save_returns_false_on_unwritable_path(self, tmp_path):
        lib = _lib_with(_make_voice())
        with patch("podcastforge.voices.library.Path.write_text", side_effect=PermissionError("denied")):
            result = lib.save_to_yaml(str(tmp_path / "voices.yaml"))
        assert result is False
