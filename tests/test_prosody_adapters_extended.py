"""Extended tests for podcastforge.tts.prosody_adapters — covering XTTS, generic, and edge cases."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.tts.prosody_adapters import adapt_for_engine


class TestAdaptForEngineXTTS:
    def test_xtts_rate_mapped_to_tempo(self):
        prosody = {"rate": 1.0, "pitch_cents": 0, "energy": 1.0}
        result = adapt_for_engine("XTTS", prosody)
        assert "tempo" in result
        assert result["tempo"] == pytest.approx(1.0)

    def test_xtts_rate_clamped_high(self):
        result = adapt_for_engine("XTTS", {"rate": 5.0})
        assert result["tempo"] == pytest.approx(2.0)

    def test_xtts_rate_clamped_low(self):
        result = adapt_for_engine("XTTS", {"rate": 0.1})
        assert result["tempo"] == pytest.approx(0.5)

    def test_xtts_pitch_cents_preserved(self):
        result = adapt_for_engine("XTTS", {"pitch_cents": -100})
        assert result["pitch_cents"] == pytest.approx(-100)

    def test_xtts_energy_clamped(self):
        result = adapt_for_engine("XTTS", {"energy": 3.0})
        assert result["energy"] == pytest.approx(2.0)


class TestAdaptForEngineGeneric:
    def test_generic_rate_mapped_directly(self):
        result = adapt_for_engine("GENERIC_ENGINE", {"rate": 1.2})
        assert "rate" in result
        assert result["rate"] == pytest.approx(1.2)

    def test_generic_rate_clamped(self):
        result = adapt_for_engine("SOMETHING", {"rate": 0.0})
        assert result["rate"] == pytest.approx(0.5)

    def test_generic_pitch_cents(self):
        result = adapt_for_engine("VITS", {"pitch_cents": 50})
        assert result["pitch_cents"] == pytest.approx(50)

    def test_generic_energy_clamped(self):
        result = adapt_for_engine("CUSTOM", {"energy": -1.0})
        assert result["energy"] == pytest.approx(0.0)

    def test_generic_all_fields(self):
        result = adapt_for_engine("STYLETTS2", {"rate": 1.5, "pitch_cents": -20, "energy": 0.8})
        assert "rate" in result
        assert "pitch_cents" in result
        assert "energy" in result


class TestAdaptForEngineEdgeCases:
    def test_none_prosody_returns_empty(self):
        assert adapt_for_engine("PIPER", None) == {}

    def test_empty_prosody_returns_empty(self):
        assert adapt_for_engine("PIPER", {}) == {}

    def test_non_dict_prosody_returns_empty(self):
        assert adapt_for_engine("PIPER", "not a dict") == {}

    def test_none_engine_name_uses_generic(self):
        result = adapt_for_engine(None, {"rate": 1.0, "pitch_cents": 0, "energy": 1.0})
        assert isinstance(result, dict)

    def test_engine_with_name_attribute(self):
        """Accepts enum-like objects with .name property."""
        class FakeEnum:
            name = "PIPER"
        result = adapt_for_engine(FakeEnum(), {"rate": 1.0})
        assert "length_scale" in result

    def test_piper_zero_rate_treated_as_one(self):
        """Zero rate should not cause division by zero — falls back to 1.0."""
        result = adapt_for_engine("PIPER", {"rate": 0.0})
        # rate=0 is treated as 1.0 inside piper branch → length_scale = 1.0
        assert "length_scale" in result
        assert result["length_scale"] == pytest.approx(1.0)

    def test_piper_negative_rate_treated_as_one(self):
        result = adapt_for_engine("PIPER", {"rate": -0.5})
        assert result["length_scale"] == pytest.approx(1.0)

    def test_invalid_string_rate_ignored(self):
        result = adapt_for_engine("PIPER", {"rate": "fast"})
        assert "length_scale" not in result

    def test_only_pitch_no_rate(self):
        result = adapt_for_engine("PIPER", {"pitch_cents": 100})
        assert result.get("pitch_shift_cents") == pytest.approx(100)
        assert "length_scale" not in result

    def test_only_energy_no_rate(self):
        result = adapt_for_engine("BARK", {"energy": 0.5})
        assert result.get("energy") == pytest.approx(0.5)
        assert "tempo" not in result

    def test_bark_name_variant_lower(self):
        result = adapt_for_engine("bark", {"rate": 1.0})
        # 'bark'.upper() == 'BARK' → should trigger BARK branch
        assert "tempo" in result
