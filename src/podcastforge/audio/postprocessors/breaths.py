"""Simple breath insertion postprocessor.

This module looks for short breath samples under `third_party/breaths/` and
provides `insert_breaths(audio, sr, text)` which inserts short breath
sounds at phrase boundaries derived from punctuation in `text`.

This is intentionally simple and conservative: it mixes low-volume breath
samples at computed insertion points rather than doing fancy alignment.
"""
from pathlib import Path
import numpy as np
import soundfile as sf
import random
import os

_BREATHS_CACHE = None


def _find_breath_samples():
    global _BREATHS_CACHE
    if _BREATHS_CACHE is not None:
        return _BREATHS_CACHE
    base = Path(os.getcwd()) / 'third_party' / 'breaths'
    samples = []
    try:
        if base.exists() and base.is_dir():
            for p in base.glob('*.wav'):
                try:
                    data, sr = sf.read(str(p), always_2d=False)
                    if data.ndim > 1:
                        data = data.mean(axis=1)
                    samples.append((np.asarray(data, dtype=np.float32), int(sr)))
                except Exception:
                    continue
    except Exception:
        pass
    _BREATHS_CACHE = samples
    return samples


def insert_breaths(audio: np.ndarray, sr: int, text: str, intensity: float = 0.5):
    """Insert breath samples into `audio` at phrase boundaries derived from `text`.

    Args:
        audio: mono float32 numpy array
        sr: sample rate
        text: original utterance text used to infer phrase splits
        intensity: mixing gain for breath (0..1), default 0.5

    Returns:
        new_audio: numpy array with breaths mixed in (float32)
    """
    if audio is None or len(audio) == 0:
        return audio

    breaths = _find_breath_samples()
    if not breaths:
        return audio

    # simple phrase split: split on .,!? and long commas
    import re

    parts = re.split(r'[\.!?]+\s*', text)
    # ignore empty and very short parts
    parts = [p for p in parts if p and len(p.strip()) > 3]
    if len(parts) <= 1:
        # nothing to insert
        return audio

    # compute approximate insertion indices proportional to phrase lengths
    total_len = sum(len(p) for p in parts)
    if total_len == 0:
        return audio

    insert_positions = []
    cumulative = 0
    for p in parts[:-1]:
        cumulative += len(p)
        frac = cumulative / total_len
        idx = int(frac * len(audio))
        insert_positions.append(idx)

    out = audio.astype(np.float32).copy()

    for pos in insert_positions:
        sample, s_sr = random.choice(breaths)
        if s_sr != sr:
            # naive resample if needed (simple decimation / repeat)
            # prefer scipy if present
            try:
                import librosa

                sample = librosa.resample(sample, orig_sr=s_sr, target_sr=sr)
            except Exception:
                # fallback: nearest neighbour stretch/trim
                factor = sr / s_sr
                new_len = int(len(sample) * factor)
                sample = np.interp(np.linspace(0, len(sample), new_len), np.arange(len(sample)), sample).astype(np.float32)

        # scale breath by intensity and a small factor to keep subtle
        breath_gain = 0.15 * float(intensity)
        b = sample * breath_gain

        # mix (add) at position, handle bounds
        start = max(0, pos - len(b)//2)
        end = min(len(out), start + len(b))
        blen = end - start
        if blen <= 0:
            continue
        out[start:end] = out[start:end] + b[:blen]

    # prevent clipping
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out = out / (peak + 1e-9)

    return out
