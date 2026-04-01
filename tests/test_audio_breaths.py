"""Tests for podcastforge.audio.postprocessors.breaths."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.audio.postprocessors.breaths import insert_breaths, _find_breath_samples
import podcastforge.audio.postprocessors.breaths as breaths_module


# ---------------------------------------------------------------------------
# _find_breath_samples
# ---------------------------------------------------------------------------


class TestFindBreathSamples:
    def test_returns_list(self, monkeypatch, tmp_path):
        # No third_party/breaths directory → empty list
        monkeypatch.chdir(tmp_path)
        breaths_module._BREATHS_CACHE = None
        result = _find_breath_samples()
        assert isinstance(result, list)

    def test_caches_result_after_first_call(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        breaths_module._BREATHS_CACHE = None
        r1 = _find_breath_samples()
        r2 = _find_breath_samples()
        assert r1 is r2  # same object (cached)

    def test_resets_cache_when_set_to_none(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        breaths_module._BREATHS_CACHE = None
        _find_breath_samples()
        breaths_module._BREATHS_CACHE = None
        result = _find_breath_samples()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# insert_breaths – no samples (most common CI scenario)
# ---------------------------------------------------------------------------


class TestInsertBreathsNoSamples:
    def setup_method(self):
        # Ensure no breath samples loaded
        breaths_module._BREATHS_CACHE = []

    def test_returns_original_audio_unchanged(self):
        audio = np.ones(22050, dtype=np.float32) * 0.3
        result = insert_breaths(audio, 22050, "Hello world. How are you?")
        np.testing.assert_array_equal(result, audio)

    def test_empty_audio_returned_as_is(self):
        audio = np.array([], dtype=np.float32)
        result = insert_breaths(audio, 22050, "Hello.")
        assert len(result) == 0

    def test_none_audio_returned_as_is(self):
        result = insert_breaths(None, 22050, "Hello.")
        assert result is None

    def test_single_sentence_returns_audio_unchanged(self):
        audio = np.zeros(10000, dtype=np.float32)
        result = insert_breaths(audio, 22050, "Just one sentence")
        np.testing.assert_array_equal(result, audio)


# ---------------------------------------------------------------------------
# insert_breaths – with mock samples
# ---------------------------------------------------------------------------


class TestInsertBreathsWithSamples:
    def setup_method(self):
        sr = 22050
        # Simple breath: 0.1s of sine wave at breath sample rate
        breath = np.sin(np.linspace(0, 2 * np.pi, int(sr * 0.1))).astype(np.float32) * 0.05
        breaths_module._BREATHS_CACHE = [(breath, sr)]

    def teardown_method(self):
        breaths_module._BREATHS_CACHE = None

    def test_multi_sentence_text_modifies_audio(self):
        sr = 22050
        audio = np.zeros(sr * 3, dtype=np.float32)  # 3 seconds
        text = "First sentence. Second sentence. Third sentence."
        result = insert_breaths(audio, sr, text)
        # Result should be same length and not identical to zeros
        assert len(result) == len(audio)
        # Not all zeros (breaths were mixed in)
        assert np.any(result != 0.0)

    def test_output_dtype_is_float32(self):
        sr = 22050
        audio = np.zeros(sr * 2, dtype=np.float32)
        result = insert_breaths(audio, sr, "One. Two. Three.")
        assert result.dtype == np.float32

    def test_no_clipping_after_mixing(self):
        sr = 22050
        audio = np.ones(sr * 2, dtype=np.float32) * 0.9  # near clip
        text = "Sentence one. Sentence two. Sentence three."
        result = insert_breaths(audio, sr, text)
        assert np.max(np.abs(result)) <= 1.0 + 1e-5

    def test_intensity_zero_has_no_effect(self):
        sr = 22050
        audio = np.zeros(sr, dtype=np.float32)
        result = insert_breaths(audio, sr, "One. Two. Three.", intensity=0.0)
        # intensity=0 → breath_gain=0 → no change
        np.testing.assert_array_almost_equal(result, audio, decimal=6)

    def test_intensity_high_clips_and_normalizes(self):
        sr = 22050
        audio = np.ones(sr * 2, dtype=np.float32) * 0.99
        text = "Part one. Part two. Part three."
        result = insert_breaths(audio, sr, text, intensity=2.0)
        # After normalization, peak must be ≤ 1.0
        assert np.max(np.abs(result)) <= 1.0 + 1e-5

    def test_sample_rate_mismatch_uses_interpolation(self):
        """Breath at different SR than audio should still be mixed in."""
        breath_sr = 44100
        audio_sr = 22050
        breath = np.sin(np.linspace(0, 2 * np.pi, int(breath_sr * 0.1))).astype(np.float32) * 0.05
        breaths_module._BREATHS_CACHE = [(breath, breath_sr)]

        audio = np.zeros(audio_sr * 3, dtype=np.float32)
        result = insert_breaths(audio, audio_sr, "First. Second. Third.")
        assert result is not None
        assert len(result) == len(audio)
