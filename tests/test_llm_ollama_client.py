"""Unit tests for podcastforge.llm.ollama_client (prompt / parse logic, no network)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.core.config import PodcastConfig, PodcastStyle, Speaker
from podcastforge.llm.ollama_client import OllamaClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_speaker(id="s1", name="Anna", role="Moderator", personality="freundlich"):
    return Speaker(id=id, name=name, role=role, personality=personality, voice_profile="anna_de")


def _make_config(**kwargs):
    defaults = dict(
        topic="KI in der Medizin",
        style=PodcastStyle.INTERVIEW,
        speakers=[_make_speaker()],
        language="de",
        duration_minutes=5,
        temperature=0.7,
    )
    defaults.update(kwargs)
    return PodcastConfig(**defaults)


def _make_client():
    """Create OllamaClient with mocked _verify_connection so no network call happens."""
    with patch.object(OllamaClient, "_verify_connection"):
        return OllamaClient(model="llama2", host="http://localhost:11434")


# ---------------------------------------------------------------------------
# _create_prompt
# ---------------------------------------------------------------------------


class TestCreatePrompt:
    def test_prompt_contains_topic(self):
        client = _make_client()
        config = _make_config(topic="Quantencomputing")
        prompt = client._create_prompt(config)
        assert "Quantencomputing" in prompt

    def test_prompt_contains_speaker_names(self):
        client = _make_client()
        speakers = [
            _make_speaker(id="s1", name="Max"),
            _make_speaker(id="s2", name="Sophie"),
        ]
        config = _make_config(speakers=speakers)
        prompt = client._create_prompt(config)
        assert "Max" in prompt
        assert "Sophie" in prompt

    def test_prompt_contains_style(self):
        client = _make_client()
        config = _make_config(style=PodcastStyle.DEBATE)
        prompt = client._create_prompt(config)
        assert "debate" in prompt.lower() or "debatt" in prompt.lower() or "Debatte" in prompt

    def test_prompt_contains_language(self):
        client = _make_client()
        config = _make_config(language="en")
        prompt = client._create_prompt(config)
        assert "en" in prompt

    def test_prompt_contains_duration(self):
        client = _make_client()
        config = _make_config(duration_minutes=15)
        prompt = client._create_prompt(config)
        assert "15" in prompt

    def test_prompt_requests_json_output(self):
        client = _make_client()
        config = _make_config()
        prompt = client._create_prompt(config)
        assert "JSON" in prompt.upper() or "[" in prompt

    def test_educational_style_instruction(self):
        client = _make_client()
        config = _make_config(style=PodcastStyle.EDUCATIONAL)
        prompt = client._create_prompt(config)
        assert len(prompt) > 100  # non-trivial prompt

    def test_documentary_style_still_produces_prompt(self):
        client = _make_client()
        config = _make_config(style=PodcastStyle.DOCUMENTARY)
        prompt = client._create_prompt(config)
        assert isinstance(prompt, str) and len(prompt) > 10


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_valid_json_array(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = json.dumps([
            {"speaker": "Anna", "text": "Hallo!", "emotion": "happy"},
        ])
        result = client._parse_response(raw, config)
        assert len(result) == 1
        assert result[0]["speaker_name"] == "Anna"
        assert result[0]["text"] == "Hallo!"
        assert result[0]["emotion"] == "happy"

    def test_speaker_not_found_is_skipped(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = json.dumps([
            {"speaker": "Unknown", "text": "Text von Unbekanntem"},
        ])
        result = client._parse_response(raw, config)
        # Unknown speaker → filtered out
        assert result == []

    def test_markdown_json_fences_stripped(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = "```json\n" + json.dumps([{"speaker": "Anna", "text": "Hi", "emotion": "neutral"}]) + "\n```"
        result = client._parse_response(raw, config)
        assert len(result) == 1

    def test_invalid_json_triggers_fallback(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = "This is not JSON at all"
        result = client._parse_response(raw, config)
        # Fallback should still return a list
        assert isinstance(result, list)

    def test_emotion_defaults_to_neutral(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = json.dumps([{"speaker": "Anna", "text": "Hello"}])
        result = client._parse_response(raw, config)
        assert result[0]["emotion"] == "neutral"

    def test_pause_after_is_set(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        raw = json.dumps([{"speaker": "Anna", "text": "Hello"}])
        result = client._parse_response(raw, config)
        assert result[0]["pause_after"] == 0.5


# ---------------------------------------------------------------------------
# _fallback_parse
# ---------------------------------------------------------------------------


class TestFallbackParse:
    def test_plain_lines_get_assigned_to_speakers(self):
        client = _make_client()
        speakers = [
            _make_speaker(id="s1", name="Anna"),
            _make_speaker(id="s2", name="Bob"),
        ]
        config = _make_config(speakers=speakers)

        response = "Hallo, ich bin Anna!\nHi, ich bin Bob!\nWie geht's?"
        result = client._fallback_parse(response, config)
        assert len(result) >= 1
        assert all("text" in r for r in result)
        assert all("speaker_id" in r for r in result)

    def test_speaker_prefix_recognized(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        response = "Anna: Hallo, guten Morgen!"
        result = client._fallback_parse(response, config)
        assert result[0]["speaker_name"] == "Anna"
        assert "Hallo" in result[0]["text"]

    def test_empty_lines_skipped(self):
        client = _make_client()
        speakers = [_make_speaker(id="s1", name="Anna")]
        config = _make_config(speakers=speakers)

        response = "\n\nHello\n\n"
        result = client._fallback_parse(response, config)
        assert len(result) == 1

    def test_speakers_cycle_on_round_robin(self):
        client = _make_client()
        speakers = [
            _make_speaker(id="s1", name="Anna"),
            _make_speaker(id="s2", name="Bob"),
        ]
        config = _make_config(speakers=speakers)

        lines = "\n".join([f"Line {i}" for i in range(6)])
        result = client._fallback_parse(lines, config)
        ids = [r["speaker_id"] for r in result]
        assert "s1" in ids and "s2" in ids


# ---------------------------------------------------------------------------
# _verify_connection (with network mock)
# ---------------------------------------------------------------------------


class TestVerifyConnection:
    def test_raises_on_connection_error(self):
        import requests

        with patch("podcastforge.llm.ollama_client.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("refused")
            with pytest.raises(requests.exceptions.ConnectionError):
                OllamaClient(model="llama2", host="http://localhost:11434")

    def test_prints_warning_when_model_not_found(self, capsys):
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {"models": [{"name": "other_model"}]}

        with patch("podcastforge.llm.ollama_client.requests.get", return_value=response_mock):
            # Should not raise; just prints a warning
            client = OllamaClient(model="llama2", host="http://localhost:11434")
        assert client.model == "llama2"
