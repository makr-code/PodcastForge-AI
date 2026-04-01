"""Extended tests for podcastforge.tts.ebook2audiobook_adapter – resolve/script helpers."""
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, List

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.tts.ebook2audiobook_adapter import Ebook2AudiobookAdapter
from podcastforge.core.config import PodcastConfig, PodcastStyle, Speaker
from podcastforge.tts.engine_manager import TTSEngine


def _make_adapter():
    with patch.object(Ebook2AudiobookAdapter, "_verify_installation"):
        return Ebook2AudiobookAdapter("/tmp/fake_ebook2audiobook")


def _make_speaker(sid="s1", name="Anna", engine=None):
    return Speaker(
        id=sid,
        name=name,
        role="Host",
        personality="pro",
        voice_profile=f"{sid}_voice",
        voice_engine=engine,
    )


def _make_config(speakers=None, voice_engine=None, fallback_engines=None):
    return PodcastConfig(
        topic="Test",
        style=PodcastStyle.INTERVIEW,
        speakers=speakers or [_make_speaker()],
        voice_engine=voice_engine,
        fallback_engines=fallback_engines or [],
    )


# ---------------------------------------------------------------------------
# _script_to_text
# ---------------------------------------------------------------------------


class TestScriptToText:
    def setup_method(self):
        self.adapter = _make_adapter()

    def test_formats_speaker_and_text(self):
        script = [{"speaker_name": "Anna", "text": "Hello!", "emotion": "neutral"}]
        result = self.adapter._script_to_text(script)
        assert "Anna: Hello!" in result

    def test_emotion_prefix_added_when_not_neutral(self):
        script = [{"speaker_name": "Bob", "text": "Wow!", "emotion": "excited"}]
        result = self.adapter._script_to_text(script)
        assert "[excited]" in result
        assert "Bob: Wow!" in result

    def test_neutral_emotion_has_no_prefix(self):
        script = [{"speaker_name": "Clara", "text": "Hello.", "emotion": "neutral"}]
        result = self.adapter._script_to_text(script)
        assert "[neutral]" not in result

    def test_multiple_entries_joined_by_double_newline(self):
        script = [
            {"speaker_name": "A", "text": "Line 1", "emotion": "neutral"},
            {"speaker_name": "B", "text": "Line 2", "emotion": "neutral"},
        ]
        result = self.adapter._script_to_text(script)
        assert "\n\n" in result

    def test_falls_back_to_speaker_id_when_no_name(self):
        script = [{"speaker_id": "s99", "text": "Hello", "emotion": "neutral"}]
        result = self.adapter._script_to_text(script)
        assert "s99:" in result

    def test_uses_unknown_when_no_id_or_name(self):
        script = [{"text": "Mystery text", "emotion": "neutral"}]
        result = self.adapter._script_to_text(script)
        assert "Unknown:" in result

    def test_empty_script_returns_empty_string(self):
        result = self.adapter._script_to_text([])
        assert result == ""


# ---------------------------------------------------------------------------
# _resolve_engine_chain
# ---------------------------------------------------------------------------


class TestResolveEngineChain:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.mock_manager = MagicMock()
        self.mock_manager.default_engine = TTSEngine.PIPER

    def test_speaker_engine_is_highest_priority(self):
        speaker = _make_speaker(sid="s1", engine=TTSEngine.BARK.value)
        config = _make_config(
            speakers=[speaker],
            voice_engine=TTSEngine.PIPER.value,
        )
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        assert chain[0] == TTSEngine.BARK

    def test_global_engine_second_priority(self):
        speaker = _make_speaker(sid="s1", engine=None)
        config = _make_config(
            speakers=[speaker],
            voice_engine=TTSEngine.XTTS.value,
        )
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        assert TTSEngine.XTTS in chain

    def test_fallback_engines_appended(self):
        speaker = _make_speaker(sid="s1", engine=None)
        config = _make_config(
            speakers=[speaker],
            voice_engine=None,
            fallback_engines=[TTSEngine.BARK.value, TTSEngine.PIPER.value],
        )
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        assert TTSEngine.BARK in chain
        assert TTSEngine.PIPER in chain

    def test_unknown_engine_name_is_skipped(self):
        speaker = _make_speaker(sid="s1", engine="DOES_NOT_EXIST")
        config = _make_config(speakers=[speaker])
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        # Unknown engine skipped → chain falls back to manager.default_engine
        assert chain == [TTSEngine.PIPER]

    def test_no_engines_configured_uses_default(self):
        speaker = _make_speaker(sid="s1", engine=None)
        config = _make_config(speakers=[speaker], voice_engine=None, fallback_engines=[])
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        assert chain == [TTSEngine.PIPER]  # default_engine

    def test_no_duplicate_engines_in_chain(self):
        # global engine same as fallback
        speaker = _make_speaker(sid="s1", engine=TTSEngine.PIPER.value)
        config = _make_config(
            speakers=[speaker],
            voice_engine=TTSEngine.PIPER.value,
            fallback_engines=[TTSEngine.PIPER.value],
        )
        entry = {"speaker_id": "s1"}
        chain = self.adapter._resolve_engine_chain(entry, config, {"s1": speaker}, self.mock_manager)
        assert chain.count(TTSEngine.PIPER) == 1

    def test_speaker_not_in_map_skips_speaker_engine(self):
        config = _make_config(voice_engine=TTSEngine.BARK.value)
        entry = {"speaker_id": "nonexistent"}
        chain = self.adapter._resolve_engine_chain(entry, config, {}, self.mock_manager)
        assert TTSEngine.BARK in chain


# ---------------------------------------------------------------------------
# generate_audio – error path (all engines fail → RuntimeError)
# ---------------------------------------------------------------------------


class TestGenerateAudioErrors:
    def test_raises_when_tts_fails_and_ebook2audiobook_unavailable(self, tmp_path):
        adapter = _make_adapter()
        script = [
            {"speaker_id": "s1", "speaker_name": "Anna", "text": "Hello", "emotion": "neutral",
             "voice_profile": "anna_de", "pause_after": 0.0}
        ]
        config = _make_config()

        with patch("podcastforge.tts.ebook2audiobook_adapter.get_engine_manager") as mock_mgr:
            mock_mgr.return_value.synthesize_with_fallback.side_effect = RuntimeError("engine fail")
            mock_mgr.return_value.default_engine = TTSEngine.PIPER
            with pytest.raises(Exception):
                adapter.generate_audio(script, str(tmp_path / "out.wav"), config)
