"""Unit tests for podcastforge.tts.ebook2audiobook_adapter."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import scipy.io.wavfile as wavfile

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.tts.ebook2audiobook_adapter import Ebook2AudiobookAdapter
from podcastforge.core.config import PodcastConfig, PodcastStyle, Speaker


def _make_speaker(id="s1", name="Anna", voice_engine=None):
    return Speaker(
        id=id, name=name, role="Moderator",
        personality="freundlich", voice_profile=f"{name.lower()}_de",
        voice_engine=voice_engine,
    )


def _make_config(**kwargs):
    defaults = dict(
        topic="KI", style=PodcastStyle.INTERVIEW,
        speakers=[_make_speaker()], voice_engine="dummy",
    )
    defaults.update(kwargs)
    return PodcastConfig(**defaults)


def _make_adapter(path="./nonexistent_path"):
    """Create adapter without triggering git clone."""
    with patch("podcastforge.tts.ebook2audiobook_adapter.subprocess.run"):
        return Ebook2AudiobookAdapter(ebook2audiobook_path=path)


def _make_segment_mock():
    """Build a MagicMock that behaves like a pydub AudioSegment."""
    seg = MagicMock()
    seg.__len__ = MagicMock(return_value=100)
    seg.__add__ = MagicMock(return_value=seg)
    seg.__radd__ = MagicMock(return_value=seg)
    seg.export = MagicMock()
    return seg


# ---------------------------------------------------------------------------
# _script_to_text
# ---------------------------------------------------------------------------


class TestScriptToText:
    def test_basic_format(self):
        adapter = _make_adapter()
        script = [{"speaker_name": "Anna", "text": "Hallo!", "emotion": "neutral"}]
        result = adapter._script_to_text(script)
        assert "Anna: Hallo!" in result

    def test_emotion_prefix(self):
        adapter = _make_adapter()
        script = [{"speaker_name": "Bob", "text": "Wow!", "emotion": "excited"}]
        result = adapter._script_to_text(script)
        assert "[excited]" in result

    def test_neutral_emotion_no_prefix(self):
        adapter = _make_adapter()
        script = [{"speaker_name": "Bob", "text": "Hello"}]
        result = adapter._script_to_text(script)
        assert "[neutral]" not in result

    def test_missing_speaker_name_falls_back_to_speaker_id(self):
        adapter = _make_adapter()
        script = [{"speaker_id": "s1", "text": "No name here"}]
        result = adapter._script_to_text(script)
        assert "s1:" in result

    def test_missing_all_speaker_info_uses_unknown(self):
        adapter = _make_adapter()
        script = [{"text": "No speaker at all"}]
        result = adapter._script_to_text(script)
        assert "Unknown:" in result

    def test_multiple_entries_separated_by_blank_lines(self):
        adapter = _make_adapter()
        script = [
            {"speaker_name": "A", "text": "First"},
            {"speaker_name": "B", "text": "Second"},
        ]
        result = adapter._script_to_text(script)
        assert "\n\n" in result

    def test_empty_script_returns_empty_string(self):
        adapter = _make_adapter()
        assert adapter._script_to_text([]) == ""


# ---------------------------------------------------------------------------
# _generate_with_tts — engine chain resolution (pydub fully mocked)
# ---------------------------------------------------------------------------


class TestGenerateWithTts:
    SR = 22050

    def _mock_engine_manager(self):
        manager = MagicMock()
        audio = np.zeros(self.SR, dtype=np.float32)
        manager.synthesize_with_fallback.return_value = (audio, self.SR)
        manager.default_engine = MagicMock(value="dummy")
        return manager

    def test_generates_wav_output(self, tmp_path):
        adapter = _make_adapter()
        config = _make_config(voice_engine="dummy")
        script = [{"speaker_id": "s1", "text": "Hello!", "pause_after": 0.1,
                   "voice_profile": "anna_de"}]
        out_path = str(tmp_path / "out.wav")
        manager = self._mock_engine_manager()
        seg = _make_segment_mock()

        with patch("podcastforge.tts.ebook2audiobook_adapter.get_engine_manager",
                   return_value=manager), \
             patch("podcastforge.tts.ebook2audiobook_adapter.TTSEngine") as mock_tte, \
             patch("pydub.AudioSegment") as mock_as:
            mock_tte.side_effect = lambda v: MagicMock(value=v)
            mock_as.from_wav.return_value = seg
            mock_as.silent.return_value = seg
            seg.__add__.return_value = seg
            seg.__radd__.return_value = seg

            result = adapter._generate_with_tts(script, out_path, config)

        assert result == out_path
        seg.export.assert_called_once()

    def test_per_speaker_engine_used_first(self, tmp_path):
        """Speaker-level voice_engine takes priority over global engine."""
        speaker = _make_speaker(voice_engine="piper")
        config = _make_config(speakers=[speaker], voice_engine="xtts")
        adapter = _make_adapter()
        script = [{"speaker_id": "s1", "text": "Hi", "pause_after": 0.0,
                   "voice_profile": "anna_de"}]
        chains_seen = []

        def fake_synth_fallback(text, speaker, engines, **kwargs):
            chains_seen.append([e.value for e in engines])
            return np.zeros(self.SR, dtype=np.float32), self.SR

        manager = MagicMock()
        manager.synthesize_with_fallback.side_effect = fake_synth_fallback
        manager.default_engine = MagicMock(value="dummy")
        seg = _make_segment_mock()
        out_path = str(tmp_path / "speaker_engine.wav")

        with patch("podcastforge.tts.ebook2audiobook_adapter.get_engine_manager",
                   return_value=manager), \
             patch("podcastforge.tts.ebook2audiobook_adapter.TTSEngine") as mock_tte, \
             patch("pydub.AudioSegment") as mock_as:
            mock_tte.side_effect = lambda v: MagicMock(value=v)
            mock_as.from_wav.return_value = seg
            mock_as.silent.return_value = seg
            seg.__add__.return_value = seg
            seg.__radd__.return_value = seg
            adapter._generate_with_tts(script, out_path, config)

        assert chains_seen[0][0] == "piper"
        assert "xtts" in chains_seen[0]

    def test_temp_files_cleaned_up(self, tmp_path):
        """Temp segment WAV files must be removed after combining."""
        adapter = _make_adapter()
        config = _make_config(voice_engine="dummy")
        script = [{"speaker_id": "s1", "text": "Hi", "pause_after": 0.0,
                   "voice_profile": "anna_de"}]
        temp_files_created = []
        original_mkstemp = tempfile.mkstemp

        def tracking_mkstemp(**kwargs):
            fd, path = original_mkstemp(**kwargs)
            temp_files_created.append(path)
            return fd, path

        manager = self._mock_engine_manager()
        seg = _make_segment_mock()
        out_path = str(tmp_path / "cleanup_test.wav")

        with patch("podcastforge.tts.ebook2audiobook_adapter.get_engine_manager",
                   return_value=manager), \
             patch("podcastforge.tts.ebook2audiobook_adapter.TTSEngine") as mock_tte, \
             patch("pydub.AudioSegment") as mock_as, \
             patch("podcastforge.tts.ebook2audiobook_adapter.tempfile.mkstemp",
                   side_effect=tracking_mkstemp):
            mock_tte.side_effect = lambda v: MagicMock(value=v)
            mock_as.from_wav.return_value = seg
            mock_as.silent.return_value = seg
            seg.__add__.return_value = seg
            seg.__radd__.return_value = seg
            adapter._generate_with_tts(script, out_path, config)

        for path in temp_files_created:
            assert not Path(path).exists(), f"Temp file not cleaned up: {path}"
