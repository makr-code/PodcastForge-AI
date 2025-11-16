import os
import tempfile
import numpy as np
from pathlib import Path

from podcastforge.voices.manager import preview_voice


class DummyEngine:
    def synthesize(self, text, voice_id):
        # return 1 second of silence at 22050 Hz
        sr = 22050
        t = np.zeros(int(sr * 1.0), dtype=np.float32)
        return t, sr


class DummyPlayer:
    def __init__(self):
        self.played = []

    def play(self, path, on_complete=None):
        self.played.append(str(path))
        if on_complete:
            on_complete()


def test_preview_voice_creates_file(monkeypatch, tmp_path):
    # Arrange
    engine = DummyEngine()
    monkeypatch.setattr('podcastforge.voices.manager.get_engine_manager', lambda: engine)

    player = DummyPlayer()
    monkeypatch.setattr('podcastforge.voices.manager.get_player', lambda: player)

    # Ensure voice library has at least one voice; we'll mock get_voice to return a minimal object
    class V:
        id = 'dummy'
        name = 'dummy'
        display_name = 'Dummy Voice'
        repo = 'repo'
        sub_path = 'sub'
        sample_filename = 'sample.wav'
        style = None
        description = ''
        gender = type('G', (), {'value': 'neutral'})
        age = type('A', (), {'value': 'adult'})

    monkeypatch.setattr('podcastforge.voices.manager.get_voice_library', lambda: type('L', (), {'get_voice': lambda self, vid: V()})())

    # Act
    out = preview_voice('dummy', sample_text='test', play=True)

    # Assert
    assert out is not None
    assert Path(out).exists()

    # Cleanup
    try:
        os.remove(out)
    except Exception:
        pass


def test_preview_voice_no_play(monkeypatch):
    engine = DummyEngine()
    monkeypatch.setattr('podcastforge.voices.manager.get_engine_manager', lambda: engine)

    # Player that would raise if called
    def bad_player():
        raise AssertionError("Player should not be called when play=False")

    monkeypatch.setattr('podcastforge.voices.manager.get_player', lambda: bad_player())

    class V:
        id = 'dummy'
        name = 'dummy'
        display_name = 'Dummy Voice'
        repo = 'repo'
        sub_path = 'sub'
        sample_filename = 'sample.wav'
        style = None
        description = ''
        gender = type('G', (), {'value': 'neutral'})
        age = type('A', (), {'value': 'adult'})

    monkeypatch.setattr('podcastforge.voices.manager.get_voice_library', lambda: type('L', (), {'get_voice': lambda self, vid: V()})())

    out = preview_voice('dummy', sample_text='test', play=False)
    assert out is not None
    assert Path(out).exists()
    try:
        os.remove(out)
    except Exception:
        pass
