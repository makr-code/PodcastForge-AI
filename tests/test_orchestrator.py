import tempfile
import shutil
import os
import numpy as np
import pytest
from pathlib import Path
import json

import podcastforge.integrations.ebook2audiobook.orchestrator as orch


class DummyManager:
    def __init__(self, succeed=True):
        self.succeed = succeed

    def synthesize(self, text, speaker, engine_type=None, **kwargs):
        if not self.succeed:
            raise RuntimeError("TTS backend failure")
        # return 1 second of silence at 22050Hz
        sr = 22050
        samples = np.zeros(int(sr * 1.0), dtype=np.float32)
        return samples, sr


@pytest.fixture(autouse=True)
def patch_engine_manager(monkeypatch):
    # Patch get_engine_manager to return our dummy
    def _get_manager(*args, **kwargs):
        return DummyManager(succeed=True)

    monkeypatch.setattr(orch, "get_engine_manager", _get_manager)
    yield


def test_create_project_success(monkeypatch, tmp_path):
    # Patch chapter extraction to return two short chapters
    chapters = [
        {"title": "Ch1", "content": "First paragraph."},
        {"title": "Ch2", "content": "Second paragraph."},
    ]

    monkeypatch.setattr(orch, "extract_chapters_from_epub", lambda path: chapters)

    out = tmp_path / "out"
    res = orch.create_podcast_project_from_ebook("dummy.epub", str(out), speaker="narrator", engine="PIPER", cache_dir=str(out / "cache"))

    assert res["ok"] is True
    manifest_path = Path(res["manifest_path"])
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "chapters" in manifest
    assert len(manifest["chapters"]) == 2


def test_tts_failure_returns_error(monkeypatch, tmp_path):
    # Patch chapter extraction
    monkeypatch.setattr(orch, "extract_chapters_from_epub", lambda path: [{"title": "Ch1", "content": "Text"}])

    # Patch manager to raise
    class BadManager:
        def synthesize(self, *a, **k):
            raise RuntimeError("backend down")

    monkeypatch.setattr(orch, "get_engine_manager", lambda: BadManager())

    out = tmp_path / "out2"
    res = orch.create_podcast_project_from_ebook("dummy.epub", str(out), speaker="narrator", engine="PIPER", cache_dir=str(out / "cache"))

    assert res["ok"] is False
    assert "TTS synth failed" in res["message"]
