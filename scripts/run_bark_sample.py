#!/usr/bin/env python3
"""
Run a short Bark synth using the project's BarkEngine and save to outputs/bark_sample.wav
Exits with 0 on success, non-zero on failure.
"""
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src = repo_root / 'src'
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

# Use local models dir if present
models_dir = repo_root / 'models'
if models_dir.exists():
    os.environ.setdefault('PF_MODELS_DIR', str(models_dir))

print('Repo root:', repo_root)
print('Using src:', src)
print('PF_MODELS_DIR ->', os.environ.get('PF_MODELS_DIR'))

try:
    from podcastforge.tts.engine_manager import BarkEngine
except Exception as e:
    print('Failed to import BarkEngine:', e)
    sys.exit(2)

try:
    engine = BarkEngine()
    print('Instantiated BarkEngine:', engine)
    if not engine.is_loaded:
        print('Calling load_model() ... this may take some seconds')
        engine.load_model()
    print('engine.is_loaded =', engine.is_loaded)

    text = 'Hallo Welt. Dies ist ein kurzer Test von Bark über PodcastForge.'
    print('Synthesizing sample text...')
    audio = engine.synthesize(text, speaker='v2/en_speaker_6')

    # audio: numpy float32, sample_rate in engine.sample_rate
    sr = engine.sample_rate

    out_dir = repo_root / 'outputs'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / 'bark_sample.wav'

    # Write PCM16 WAV using scipy
    try:
        from scipy.io import wavfile
    except Exception:
        print('scipy not available; cannot write WAV')
        sys.exit(3)

    import numpy as np
    # Ensure float32 in [-1,1]
    clipped = np.clip(audio, -1.0, 1.0)
    int16 = (clipped * 32767.0).astype(np.int16)

    wavfile.write(str(out_path), sr, int16)

    print('Wrote sample to', out_path)
    sys.exit(0)

except Exception as e:
    print('Synthesis failed:', e)
    sys.exit(1)
