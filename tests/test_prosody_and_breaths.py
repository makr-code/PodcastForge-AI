import numpy as np
from src.podcastforge.tts.prosody_adapters import adapt_for_engine
from src.podcastforge.audio.postprocessors.breaths import insert_breaths
import os


def test_prosody_adapter_piper():
    prosody = {'rate': 0.8, 'pitch_cents': 50, 'energy': 1.2}
    adapted = adapt_for_engine('PIPER', prosody)
    assert 'length_scale' in adapted
    assert 0.5 <= adapted['length_scale'] <= 2.0
    assert adapted.get('pitch_shift_cents') == 50
    assert 0.0 <= adapted.get('energy', 0) <= 2.0


def test_prosody_adapter_bark():
    prosody = {'rate': 1.3, 'pitch_cents': -20, 'energy': 0.7}
    adapted = adapt_for_engine('BARK', prosody)
    assert 'tempo' in adapted
    assert 0.5 <= adapted['tempo'] <= 2.0
    assert adapted.get('pitch_cents') == -20


def test_insert_breaths_basic():
    # Create a short 1s tone as audio
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.1 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
    text = "Hello. This is a test. Please insert breaths." 

    out = insert_breaths(audio, sr, text, intensity=0.5)
    assert out is not None
    assert len(out) == len(audio)
    # If breath samples exist, audio should be different
    breaths_dir = os.path.join(os.getcwd(), 'third_party', 'breaths')
    if os.path.isdir(breaths_dir) and any(p.endswith('.wav') for p in os.listdir(breaths_dir)):
        # Expect at least one sample mix changed the array
        assert not np.allclose(out, audio)
