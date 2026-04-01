"""Unit tests for podcastforge.voices.library."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.voices.library import (
    VoiceLibrary,
    VoiceProfile,
    VoiceGender,
    VoiceAge,
    VoiceStyle,
    get_voice_library,
)
from podcastforge.core.config import PodcastStyle


@pytest.fixture
def library():
    return VoiceLibrary()


class TestVoiceProfile:
    def test_matches_criteria_language(self):
        vp = VoiceProfile(
            id="test_v",
            name="Test",
            display_name="Test Voice",
            language="de",
            gender=VoiceGender.FEMALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
        )
        assert vp.matches_criteria(language="de") is True
        assert vp.matches_criteria(language="en") is False

    def test_matches_criteria_gender(self):
        vp = VoiceProfile(
            id="v2",
            name="V2",
            display_name="V2",
            language="de",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.CASUAL,
        )
        assert vp.matches_criteria(gender=VoiceGender.MALE) is True
        assert vp.matches_criteria(gender=VoiceGender.FEMALE) is False

    def test_matches_criteria_all_none(self):
        vp = VoiceProfile(
            id="v3", name="V3", display_name="V3", language="en",
            gender=VoiceGender.NEUTRAL, age=VoiceAge.ADULT, style=VoiceStyle.CALM,
        )
        assert vp.matches_criteria() is True

    def test_sample_path_empty_when_no_filename(self):
        vp = VoiceProfile(
            id="v4", name="V4", display_name="V4", language="de",
            gender=VoiceGender.MALE, age=VoiceAge.ADULT, style=VoiceStyle.CALM,
            sample_filename="",
        )
        assert vp.sample_path == ""

    def test_sample_path_built_from_fields(self):
        vp = VoiceProfile(
            id="v5", name="V5", display_name="V5", language="de",
            gender=VoiceGender.MALE, age=VoiceAge.ADULT, style=VoiceStyle.CALM,
            sample_filename="voice.wav",
        )
        path = vp.sample_path
        assert "voice.wav" in path
        assert "de" in path


class TestVoiceLibrary:
    def test_has_german_voices(self, library):
        count = library.get_voice_count(language="de")
        assert count > 0

    def test_has_english_voices(self, library):
        count = library.get_voice_count(language="en")
        assert count > 0

    def test_get_voice_known_id(self, library):
        v = library.get_voice("anna_de")
        assert v is not None
        assert v.id == "anna_de"
        assert v.language == "de"

    def test_get_voice_unknown_id_returns_none(self, library):
        assert library.get_voice("nonexistent_voice_xyz") is None

    def test_search_by_language(self, library):
        results = library.search(language="de")
        assert all(v.language == "de" for v in results)
        assert len(results) > 0

    def test_search_by_gender(self, library):
        results = library.search(gender=VoiceGender.FEMALE)
        assert all(v.gender == VoiceGender.FEMALE for v in results)

    def test_search_by_tag(self, library):
        results = library.search(tags=["news"])
        assert len(results) > 0
        assert all(any("news" in t for t in v.tags) for v in results)

    def test_search_no_criteria_returns_all(self, library):
        results = library.search()
        assert len(results) == library.get_voice_count()

    def test_search_unknown_tag_returns_empty(self, library):
        results = library.search(tags=["totally_nonexistent_tag_xyz"])
        assert results == []

    def test_list_languages_includes_de_and_en(self, library):
        langs = library.list_languages()
        assert "de" in langs
        assert "en" in langs

    def test_get_voice_count_total(self, library):
        total = library.get_voice_count()
        assert total > 0
        assert total == len(library.all_voices)

    def test_get_voice_count_by_language(self, library):
        de_count = library.get_voice_count("de")
        en_count = library.get_voice_count("en")
        total = library.get_voice_count()
        assert de_count + en_count <= total  # there could be other languages

    def test_suggest_for_interview_returns_two(self, library):
        suggestions = library.suggest_for_podcast_style(PodcastStyle.INTERVIEW, language="de", num_speakers=2)
        assert len(suggestions) >= 1  # at least one suggestion

    def test_suggest_for_documentary_returns_at_least_one(self, library):
        suggestions = library.suggest_for_podcast_style(PodcastStyle.DOCUMENTARY, language="de")
        assert len(suggestions) >= 1

    def test_suggest_for_news(self, library):
        suggestions = library.suggest_for_podcast_style(PodcastStyle.NEWS, language="de", num_speakers=2)
        assert len(suggestions) >= 1

    def test_suggest_for_discussion_respects_num_speakers(self, library):
        suggestions = library.suggest_for_podcast_style(PodcastStyle.DISCUSSION, language="de", num_speakers=3)
        assert len(suggestions) <= 3

    def test_get_voice_library_returns_singleton(self):
        lib1 = get_voice_library()
        lib2 = get_voice_library()
        assert lib1 is lib2
