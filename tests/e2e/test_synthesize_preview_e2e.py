import json
import os
from pathlib import Path
import numpy as np
import pytest

from podcastforge.integrations import script_orchestrator as orch


class DummyManager:
    def synthesize(self, text, speaker, engine_type=None, **kwargs):
        # 0.5s of silence at 22050Hz
        sr = 22050
        samples = np.zeros(int(sr * 0.5), dtype=np.float32)
        return samples, sr


@pytest.fixture(autouse=True)
def patch_engine_manager(monkeypatch):
    monkeypatch.setattr(orch, 'get_engine_manager', lambda *a, **k: DummyManager())
    yield


def test_synthesize_preview_fallback_to_wav(tmp_path):
    # minimal script with two utterances
    script = [
        {"speaker": "Host", "text": "Hallo Welt."},
        {"speaker": "Guest", "text": "Dies ist ein Test."},
    ]

    script_path = tmp_path / 'script.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')

    out = tmp_path / 'out'
    out.mkdir()

    events = []

    def on_progress(data):
        events.append(data)

    # subscribe to progress events
    from podcastforge.core.events import get_event_bus

    eb = get_event_bus()
    eb.subscribe('script.tts_progress', on_progress)

    # Request mp3 output; system may not have ffmpeg so function should
    # fall back to WAV and return a warning in that case.
    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='mp3')

    assert res.get('ok') is True
    preview = Path(res.get('preview_path'))
    # If ffmpeg missing we expect a WAV preview and a warning
    assert preview.exists()
    assert preview.suffix.lower() in ('.wav', '.mp3', '.mp4')

    # Ensure progress events were published for both utterances
    assert any(e and e.get('idx') == 1 for e in events)
    assert any(e and e.get('idx') == 2 for e in events)

    eb.unsubscribe('script.tts_progress', on_progress)


def test_synthesize_preview_wav_direct(tmp_path):
    # same script, request wav output explicitly
    script = [
        {"speaker": "Host", "text": "Hallo Welt."},
    ]
    script_path = tmp_path / 'script2.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')

    out = tmp_path / 'out2'
    out.mkdir()

    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='wav')
    assert res.get('ok') is True
    preview = Path(res.get('preview_path'))
    assert preview.exists()
    assert preview.suffix.lower() == '.wav'


def test_synthesize_preview_streaming_with_ffmpeg(tmp_path):
    import shutil
    ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if not ff:
        pytest.skip('ffmpeg not found on PATH; streaming test skipped')

    # minimal script with two utterances
    script = [
        {"speaker": "Host", "text": "Hallo Welt."},
        {"speaker": "Guest", "text": "Dies ist ein Streaming Test."},
    ]

    script_path = tmp_path / 'script_stream.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')

    out = tmp_path / 'out_stream'
    out.mkdir()

    events = []

    def on_progress(data):
        events.append(data)

    # subscribe to progress events
    from podcastforge.core.events import get_event_bus

    eb = get_event_bus()
    eb.subscribe('script.tts_progress', on_progress)

    # Request mp3 output; ffmpeg is available so streaming conversion should run
    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='mp3')

    assert res.get('ok') is True
    preview = Path(res.get('preview_path'))
    assert preview.exists()
    assert preview.suffix.lower() in ('.mp3', '.mp4')
    # output file should be non-empty
    assert preview.stat().st_size > 0

    # Ensure progress events were published for both utterances
    assert any(e and e.get('idx') == 1 for e in events)
    assert any(e and e.get('idx') == 2 for e in events)

    eb.unsubscribe('script.tts_progress', on_progress)


def test_caching_prevents_repeated_synthesis(tmp_path, monkeypatch):
    # Manager that counts synth calls
    class CountingManager:
        def __init__(self):
            self.count = 0

        def synthesize(self, text, speaker, engine_type=None, **kwargs):
            self.count += 1
            sr = 22050
            samples = np.zeros(int(sr * 0.1), dtype=np.float32)
            return samples, sr

    cm = CountingManager()
    # patch get_engine_manager used by orchestrator
    monkeypatch.setattr(orch, 'get_engine_manager', lambda *a, **k: cm)

    script = [
        {"speaker": "Host", "text": "Alpha."},
        {"speaker": "Guest", "text": "Beta."},
    ]
    script_path = tmp_path / 'script_cache.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')

    out = tmp_path / 'out_cache'
    out.mkdir()

    # First run should call synthesize twice
    res1 = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='wav')
    assert res1.get('ok') is True
    assert cm.count == 2

    # Reset counter and run again; cached files should prevent new synth calls
    cm.count = 0
    res2 = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='wav')
    assert res2.get('ok') is True
    assert cm.count == 0


def test_incompatible_wavs_fallback_to_concat_conversion(tmp_path, monkeypatch):
    # This manager returns different sample rates for two utterances
    class VarSRManager:
        def __init__(self):
            self.calls = 0

        def synthesize(self, text, speaker, engine_type=None, **kwargs):
            # alternate sample rates 22050 and 24000
            self.calls += 1
            if self.calls % 2 == 1:
                sr = 22050
            else:
                sr = 24000
            samples = np.zeros(int(sr * 0.1), dtype=np.float32)
            return samples, sr

    vm = VarSRManager()
    monkeypatch.setattr(orch, 'get_engine_manager', lambda *a, **k: vm)

    script = [
        {"speaker": "A", "text": "One."},
        {"speaker": "B", "text": "Two."},
    ]
    script_path = tmp_path / 'script_varsr.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')

    out = tmp_path / 'out_varsr'
    out.mkdir()

    import shutil
    ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if not ff:
        pytest.skip('ffmpeg not available for conversion test')

    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='mp3')
    assert res.get('ok') is True
    preview = Path(res.get('preview_path'))
    assert preview.exists()
    assert preview.suffix.lower() in ('.mp3', '.mp4')


def test_progress_events_have_done_for_each_utterance(tmp_path):
    # Using the autouse DummyManager; capture events and ensure done status
    script = [
        {"speaker": "Host", "text": "Hi."},
        {"speaker": "Guest", "text": "Hello."},
        {"speaker": "Narrator", "text": "End."},
    ]

    script_path = tmp_path / 'script_events.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')
    out = tmp_path / 'out_events'
    out.mkdir()

    events = []

    def on_progress(data):
        events.append(data)

    from podcastforge.core.events import get_event_bus
    eb = get_event_bus()
    eb.subscribe('script.tts_progress', on_progress)

    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=2, output_format='wav')
    assert res.get('ok') is True

    # For each idx ensure at least one 'done' or final progress >=1.0
    for idx in (1, 2, 3):
        assert any((e.get('idx') == idx and (e.get('progress') and e.get('progress') >= 1.0)) or (e.get('idx') == idx and e.get('status') == 'done') for e in events)

    eb.unsubscribe('script.tts_progress', on_progress)


def test_streaming_path_invoked_for_mp3_and_mp4(tmp_path, monkeypatch):
    import shutil
    ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if not ff:
        pytest.skip('ffmpeg not available for streaming invocation test')

    # ensure we can observe start_ffmpeg_encoder being called
    from importlib import import_module
    ffmod = import_module('podcastforge.audio.ffmpeg_pipe')
    orig_start = ffmod.start_ffmpeg_encoder
    called = {'mp3': False, 'mp4': False}

    def make_wrapper(fmt_key):
        def wrapper(*args, **kwargs):
            called[fmt_key] = True
            return orig_start(*args, **kwargs)
        return wrapper

    # Test mp3
    monkeypatch.setattr(ffmod, 'start_ffmpeg_encoder', make_wrapper('mp3'))
    script = [{"speaker": "X", "text": "one."}, {"speaker": "Y", "text": "two."}]
    script_path = tmp_path / 's_mp3.json'
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')
    out = tmp_path / 'out_mp3'
    out.mkdir()
    res = orch.synthesize_script_preview(str(script_path), str(out), cache_dir=str(out / 'cache'), max_workers=1, output_format='mp3')
    assert res.get('ok') is True
    assert called['mp3'] is True

    # Test mp4
    monkeypatch.setattr(ffmod, 'start_ffmpeg_encoder', make_wrapper('mp4'))
    script_path2 = tmp_path / 's_mp4.json'
    script_path2.write_text(json.dumps(script, ensure_ascii=False), encoding='utf-8')
    out2 = tmp_path / 'out_mp4'
    out2.mkdir()
    res2 = orch.synthesize_script_preview(str(script_path2), str(out2), cache_dir=str(out2 / 'cache'), max_workers=1, output_format='mp4')
    assert res2.get('ok') is True
    assert called['mp4'] is True
