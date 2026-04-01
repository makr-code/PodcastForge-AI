"""Unit tests for podcastforge.core.script_model."""
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.core.script_model import normalize_script, blocks_to_script_dict


class TestNormalizeScript:
    def test_empty_dict_returns_empty(self):
        assert normalize_script({}) == []

    def test_non_dict_returns_empty(self):
        assert normalize_script("not a dict") == []
        assert normalize_script(None) == []

    def test_basic_utterance(self):
        data = {
            "script": [
                {"speaker": "Alice", "text": "Hello!", "type": "utterance"}
            ]
        }
        blocks = normalize_script(data)
        assert len(blocks) == 1
        b = blocks[0]
        assert b["speaker"] == "Alice"
        assert b["text"] == "Hello!"
        assert b["type"] == "utterance"

    def test_id_is_generated_when_missing(self):
        data = {"script": [{"text": "No id here"}]}
        blocks = normalize_script(data)
        assert len(blocks[0]["id"]) > 0
        # Should be a valid uuid
        uuid.UUID(blocks[0]["id"])

    def test_id_is_preserved_when_provided(self):
        data = {"script": [{"id": "custom-id", "text": "Hello"}]}
        blocks = normalize_script(data)
        assert blocks[0]["id"] == "custom-id"

    def test_type_inferred_from_speaker_presence(self):
        data = {"script": [{"speaker": "Bob", "text": "Hi"}]}
        blocks = normalize_script(data)
        assert blocks[0]["type"] == "utterance"

    def test_type_inferred_as_direction_without_speaker(self):
        data = {"script": [{"text": "Scene fades in"}]}
        blocks = normalize_script(data)
        assert blocks[0]["type"] == "direction"

    def test_prosody_defaults_to_empty_dict(self):
        data = {"script": [{"text": "Test"}]}
        blocks = normalize_script(data)
        assert blocks[0]["prosody"] == {}

    def test_pause_after_defaults_to_zero(self):
        data = {"script": [{"text": "Test"}]}
        blocks = normalize_script(data)
        assert blocks[0]["pause_after"] == 0.0

    def test_pause_after_coerced_to_float(self):
        data = {"script": [{"text": "Test", "pause_after": "1.5"}]}
        blocks = normalize_script(data)
        assert blocks[0]["pause_after"] == 1.5

    def test_preview_defaults_to_false(self):
        data = {"script": [{"text": "Test"}]}
        blocks = normalize_script(data)
        assert blocks[0]["preview"] is False

    def test_preview_true_when_set(self):
        data = {"script": [{"text": "Test", "preview": True}]}
        blocks = normalize_script(data)
        assert blocks[0]["preview"] is True

    def test_text_uses_content_as_fallback(self):
        data = {"script": [{"content": "Content field text"}]}
        blocks = normalize_script(data)
        assert blocks[0]["text"] == "Content field text"

    def test_legacy_string_items(self):
        data = {"script": ["plain string entry"]}
        blocks = normalize_script(data)
        assert blocks[0]["type"] == "direction"
        assert blocks[0]["text"] == "plain string entry"

    def test_multiple_blocks_order_preserved(self):
        data = {
            "script": [
                {"id": "a", "text": "first"},
                {"id": "b", "text": "second"},
                {"id": "c", "text": "third"},
            ]
        }
        blocks = normalize_script(data)
        assert [b["id"] for b in blocks] == ["a", "b", "c"]

    def test_annotations_preserved(self):
        data = {"script": [{"text": "Hi", "annotations": {"key": "val"}}]}
        blocks = normalize_script(data)
        assert blocks[0]["annotations"] == {"key": "val"}


class TestBlocksToScriptDict:
    def test_roundtrip(self):
        original = {
            "script": [
                {"id": "x1", "type": "utterance", "speaker": "Alice", "text": "Hi",
                 "chapter": None, "prosody": {}, "preview": False, "pause_after": 0.0,
                 "annotations": {}},
            ]
        }
        blocks = normalize_script(original)
        result = blocks_to_script_dict(blocks)
        assert "script" in result
        assert result["script"][0]["id"] == "x1"

    def test_empty_blocks(self):
        result = blocks_to_script_dict([])
        assert result == {"script": []}
