"""Generiere kurze Breath‑WAVs für die Breath‑Inserter‑Demo.

Läuft lokal und legt drei WAVs in `third_party/breaths/` an.
"""
from pathlib import Path
import numpy as np
import soundfile as sf


def _make_breath(duration_s=0.20, sr=22050, intensity=0.3, tone=200.0):
    # White noise with simple lowpass via convolution and an amplitude envelope
    n = int(duration_s * sr)
    # white noise
    noise = np.random.randn(n)

    # simple 3-sample moving average lowpass to mellow the sound
    kernel = np.ones(5) / 5.0
    smooth = np.convolve(noise, kernel, mode='same')

    # amplitude envelope: quick attack, exponential decay
    t = np.linspace(0.0, 1.0, n)
    env = (1.0 - np.exp(5.0 * (t - 1.0)))  # gentle decay curve
    env = env * (t < 0.6) + 0.4 * (t >= 0.6)

    sig = smooth * env * intensity

    # small low-frequency tone component to add warmth
    sig += 0.02 * np.sin(2.0 * np.pi * tone * t)

    # normalize
    mx = max(1e-9, np.max(np.abs(sig)))
    sig = sig / mx * (0.9 * intensity)
    return sig.astype(np.float32)


def generate(out_dir: str = 'third_party/breaths'):
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)

    samples = [
        ('breath_soft.wav', 0.14, 0.22),
        ('breath_medium.wav', 0.22, 0.35),
        ('breath_hard.wav', 0.34, 0.6),
    ]

    sr = 22050
    for name, dur, intensity in samples:
        out = p / name
        if out.exists():
            print(f"Skipping existing: {out}")
            continue
        sig = _make_breath(duration_s=dur, sr=sr, intensity=float(intensity), tone=150.0 + 60.0 * (intensity))
        sf.write(str(out), sig, sr, subtype='PCM_16')
        print(f"Wrote {out} ({dur}s, intensity={intensity})")

    # Also generate higher-quality CC0-like variants (44.1k, stereo) for out-of-the-box realism
    variants = [
        ('breath_soft_cc0.wav', 0.14, 0.22, 44100, True),
        ('breath_medium_cc0.wav', 0.22, 0.35, 44100, True),
        ('breath_hard_cc0.wav', 0.34, 0.6, 44100, True),
    ]

    for name, dur, intensity, sr_v, stereo in variants:
        out = p / name
        if out.exists():
            print(f"Skipping existing: {out}")
            continue
        sig = _make_breath(duration_s=dur, sr=sr_v, intensity=float(intensity), tone=140.0 + 80.0 * (intensity))
        if stereo:
            # simple stereo spread: slight delay and level difference
            left = sig
            right = np.roll(sig, int(0.002 * sr_v)) * 0.95
            stereo_sig = np.stack([left, right], axis=1)
            sf.write(str(out), stereo_sig, sr_v, subtype='PCM_16')
        else:
            sf.write(str(out), sig, sr_v, subtype='PCM_16')
        print(f"Wrote {out} ({dur}s, intensity={intensity}, sr={sr_v}, stereo={stereo})")


if __name__ == '__main__':
    generate()
