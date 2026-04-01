"""Extended tests for OllamaClient._create_prompt and _fallback_parse."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.llm.ollama_client import OllamaClient
from podcastforge.core.config import PodcastConfig, PodcastStyle, Speaker


def _make_speaker(sid="s1", name="Alice", role="Host", personality="professional"):
    return Speaker(id=sid, name=name, role=role, personality=personality,
                   voice_profile=f"{sid}_voice")


def _make_config(
    topic="AI in Healthcare",
    style=PodcastStyle.INTERVIEW,
    speakers=None,
    duration_minutes=10,
    language="de",
):
    return PodcastConfig(
        topic=topic,
        style=style,
        speakers=speakers or [_make_speaker("h1", "Host"), _make_speaker("g1", "Guest")],
        duration_minutes=duration_minutes,
        language=language,
    )


def _make_client(model="llama2"):
    """Create client with mocked _verify_connection."""
    with patch.object(OllamaClient, "_verify_connection"):
        return OllamaClient(model=model)


# ---------------------------------------------------------------------------
# _create_prompt
# ---------------------------------------------------------------------------


class TestCreatePrompt:
    def setup_method(self):
        self.client = _make_client()

    def test_prompt_contains_topic(self):
        config = _make_config(topic="Quantum Computing")
        prompt = self.client._create_prompt(config)
        assert "Quantum Computing" in prompt

    def test_prompt_contains_speaker_names(self):
        config = _make_config(speakers=[_make_speaker("h", "Moderator"), _make_speaker("g", "Prof. Schmidt")])
        prompt = self.client._create_prompt(config)
        assert "Moderator" in prompt
        assert "Prof. Schmidt" in prompt

    def test_prompt_contains_duration(self):
        config = _make_config(duration_minutes=15)
        prompt = self.client._create_prompt(config)
        assert "15" in prompt

    def test_prompt_contains_language(self):
        config = _make_config(language="en")
        prompt = self.client._create_prompt(config)
        assert "en" in prompt

    def test_prompt_contains_style_instruction(self):
        config = _make_config(style=PodcastStyle.INTERVIEW)
        prompt = self.client._create_prompt(config)
        assert "Interview" in prompt or "interview" in prompt.lower() or "Fragen" in prompt

    def test_prompt_requests_json_array(self):
        config = _make_config()
        prompt = self.client._create_prompt(config)
        assert "JSON" in prompt or "json" in prompt.lower() or "[" in prompt

    def test_all_podcast_styles_generate_prompt(self):
        for style in PodcastStyle:
            config = _make_config(style=style)
            prompt = self.client._create_prompt(config)
            assert isinstance(prompt, str)
            assert len(prompt) > 50

    def test_prompt_includes_word_count_estimate(self):
        config = _make_config(duration_minutes=5)
        prompt = self.client._create_prompt(config)
        # 5 * 150 = 750 words
        assert "750" in prompt

    def test_discussion_style_has_specific_instruction(self):
        config = _make_config(style=PodcastStyle.DISCUSSION)
        prompt = self.client._create_prompt(config)
        assert "Diskussion" in prompt or "discussion" in prompt.lower() or "Meinungen" in prompt

    def test_news_style_has_specific_instruction(self):
        config = _make_config(style=PodcastStyle.NEWS)
        prompt = self.client._create_prompt(config)
        assert "Nachrichten" in prompt or "news" in prompt.lower() or "Moderator" in prompt


# ---------------------------------------------------------------------------
# _fallback_parse
# ---------------------------------------------------------------------------


class TestFallbackParse:
    def setup_method(self):
        self.client = _make_client()

    def _config(self, speakers=None):
        return _make_config(speakers=speakers)

    def test_parses_plain_text_lines(self):
        response = "Hello from speaker A.\nHello from speaker B."
        config = self._config()
        result = self.client._fallback_parse(response, config)
        assert len(result) == 2
        assert all("text" in e for e in result)

    def test_strips_speaker_prefix(self):
        """Lines starting with 'SpeakerName:' should strip the prefix."""
        sp = [_make_speaker("h", "Host"), _make_speaker("g", "Guest")]
        config = self._config(speakers=sp)
        response = "Host: Good morning everyone!\nGuest: Thanks for having me."
        result = self.client._fallback_parse(response, config)
        assert "Host:" not in result[0]["text"]
        assert "Guest:" not in result[1]["text"]
        assert result[0]["speaker_name"] == "Host"
        assert result[1]["speaker_name"] == "Guest"

    def test_assigns_speakers_round_robin(self):
        sp = [_make_speaker("h", "Host"), _make_speaker("g", "Guest")]
        config = self._config(speakers=sp)
        response = "Line 1\nLine 2\nLine 3\nLine 4"
        result = self.client._fallback_parse(response, config)
        assert result[0]["speaker_name"] == "Host"
        assert result[1]["speaker_name"] == "Guest"
        assert result[2]["speaker_name"] == "Host"
        assert result[3]["speaker_name"] == "Guest"

    def test_skips_empty_lines(self):
        config = self._config()
        response = "Line one.\n\n\nLine two."
        result = self.client._fallback_parse(response, config)
        assert len(result) == 2

    def test_all_entries_have_required_keys(self):
        config = self._config()
        response = "Hello.\nWorld."
        result = self.client._fallback_parse(response, config)
        for entry in result:
            for k in ("speaker_id", "speaker_name", "text", "emotion", "voice_profile", "pause_after"):
                assert k in entry

    def test_emotion_defaults_to_neutral(self):
        config = self._config()
        result = self.client._fallback_parse("Hello world.", config)
        assert result[0]["emotion"] == "neutral"

    def test_pause_after_is_numeric(self):
        config = self._config()
        result = self.client._fallback_parse("Hello.", config)
        assert isinstance(result[0]["pause_after"], (int, float))


# ---------------------------------------------------------------------------
# _parse_response – JSON code-fence stripping
# ---------------------------------------------------------------------------


class TestParseResponse:
    def setup_method(self):
        self.client = _make_client()

    def test_parses_clean_json_array(self):
        sp = [_make_speaker("h", "Host")]
        config = _make_config(speakers=sp)
        json_str = '[{"speaker": "Host", "text": "Hello.", "emotion": "neutral"}]'
        result = self.client._parse_response(json_str, config)
        assert len(result) == 1
        assert result[0]["text"] == "Hello."

    def test_strips_code_fence(self):
        sp = [_make_speaker("h", "Host")]
        config = _make_config(speakers=sp)
        response = '```json\n[{"speaker": "Host", "text": "Hi.", "emotion": "happy"}]\n```'
        result = self.client._parse_response(response, config)
        assert len(result) == 1
        assert result[0]["emotion"] == "happy"

    def test_unknown_speaker_is_skipped(self):
        sp = [_make_speaker("h", "Host")]
        config = _make_config(speakers=sp)
        json_str = '[{"speaker": "Unknown Person", "text": "Who am I?", "emotion": "neutral"}]'
        result = self.client._parse_response(json_str, config)
        assert len(result) == 0

    def test_invalid_json_falls_back(self):
        config = _make_config()
        result = self.client._parse_response("this is not json at all\nAnother line", config)
        # fallback parse should return a list (possibly non-empty)
        assert isinstance(result, list)

    def test_voice_profile_populated_from_speaker(self):
        sp = [_make_speaker("h1", "Host")]
        config = _make_config(speakers=sp)
        json_str = '[{"speaker": "Host", "text": "Hello.", "emotion": "neutral"}]'
        result = self.client._parse_response(json_str, config)
        assert result[0]["voice_profile"] == "h1_voice"
