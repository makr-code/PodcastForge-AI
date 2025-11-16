#!/usr/bin/env python3
"""Spatialize mono utterances to 44.1kHz stereo with ILD/ITD and optional IRs.

Usage:
  python scripts/spatialize.py --input <mono.wav> --out_wav <out.wav> [--azimuth -30] [--distance 1.0] [--ir-left left_ir.wav --ir-right right_ir.wav] [--normalize -16]

This script:
 - resamples input to 44100 Hz
 - applies panning (ILD) and small interaural delay (ITD)
 - applies a simple distance lowpass and attenuation
 - optionally convolves left/right with provided IR files
 - writes a 44.1 kHz stereo WAV
 - optionally runs ffmpeg loudnorm to produce a normalized MP3

Dependencies: numpy, soundfile, scipy
Optionally: ffmpeg in `third_party` (script will try to find it)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, lfilter, fftconvolve


def pan_gain(az_deg: float):
    # azimuth -90..90 -> left/right gains using equal-power pan
    a = float(np.clip(az_deg / 90.0, -1.0, 1.0))
    theta = (a + 1.0) * (np.pi / 4.0)
    left = np.cos(theta)
    right = np.sin(theta)
    return float(left), float(right)


def apply_itd(sig: np.ndarray, sr: int, itd_ms: float):
    # positive itd_ms delays right channel; negative delays left
    if abs(itd_ms) < 1e-6:
        return sig.copy(), sig.copy()
    delay_samples = int(round(sr * abs(itd_ms) / 1000.0))
    if delay_samples == 0:
        # fractional small delay: use linear interpolation shift
        frac = (sr * abs(itd_ms) / 1000.0)
        x = np.arange(len(sig))
        from scipy.interpolate import interp1d

        f = interp1d(x, sig, kind='linear', bounds_error=False, fill_value=0.0)
        if itd_ms > 0:
            left = sig
            right = f(x - frac)
        else:
            right = sig
            left = f(x - frac)
        return left, right
    if itd_ms > 0:
        left = sig
        right = np.concatenate((np.zeros(delay_samples, dtype=sig.dtype), sig))[: len(sig)]
    else:
        right = sig
        left = np.concatenate((np.zeros(delay_samples, dtype=sig.dtype), sig))[: len(sig)]
    return left, right


def lowpass(sig: np.ndarray, sr: int, cutoff_hz: float):
    if cutoff_hz >= sr / 2.0 or cutoff_hz <= 10:
        return sig
    b, a = butter(2, cutoff_hz / (sr / 2.0), btype='low')
    return lfilter(b, a, sig)


def resample_to(sig: np.ndarray, orig_sr: int, target_sr: int):
    if orig_sr == target_sr:
        return sig
    # prefer librosa if available for higher quality resampling
    try:
        import librosa

        return librosa.resample(sig, orig_sr=orig_sr, target_sr=target_sr)
    except Exception:
        # fallback to resample_poly
        g = np.gcd(orig_sr, target_sr)
        up = target_sr // g
        down = orig_sr // g
        return resample_poly(sig, up, down)


def spatialize_mono_to_stereo(input_path: str, azimuth: float = 0.0, distance: float = 1.0, itd_ms_max: float = 0.75, ir_left: str = None, ir_right: str = None, target_sr: int = 44100):
    """Spatialize a single mono file and return (stereo_array, sr).

    This is the programmatic variant of the CLI main flow.
    """
    sig, sr = sf.read(input_path, always_2d=False)
    if sig.ndim > 1:
        sig = sig.mean(axis=1)
    sig = sig.astype('float32')
    if sr != target_sr:
        sig = resample_to(sig, sr, target_sr)
        sr = target_sr

    max_itd = float(itd_ms_max)
    itd_ms = max_itd * (float(azimuth) / 90.0)
    left, right = apply_itd(sig, sr, itd_ms)
    g_l, g_r = pan_gain(azimuth)
    dist = max(0.1, float(distance))
    att = 1.0 / max(dist, 0.5)
    left = left * (g_l * att)
    right = right * (g_r * att)
    cutoff = 20000.0 / (1.0 + dist * 2.0)
    left = lowpass(left, sr, cutoff)
    right = lowpass(right, sr, cutoff)
    irl = load_ir(ir_left, sr) if ir_left else None
    irr = load_ir(ir_right, sr) if ir_right else None
    if irl is not None:
        left = fftconvolve(left, irl)[: len(left)]
    if irr is not None:
        right = fftconvolve(right, irr)[: len(right)]
    stereo = np.stack([left, right], axis=1)
    peak = np.max(np.abs(stereo))
    if peak > 1.0:
        stereo = stereo / (peak + 1e-9)
    return stereo, sr


def load_ir(path: str, target_sr: int):
    if not path or not os.path.exists(path):
        return None
    ir, sr = sf.read(path, always_2d=False)
    if ir.ndim > 1:
        # take mono by averaging
        ir = ir.mean(axis=1)
    if sr != target_sr:
        ir = resample_to(ir, sr, target_sr)
    return ir


def resolve_example_ir(name: str):
    """Map a short example name to a path under third_party/irs/"""
    if not name:
        return None
    base = os.path.join(os.getcwd(), 'third_party', 'irs')
    # allowed example names
    examples = ['small_room', 'large_room', 'hrtf_example']
    n = name.strip()
    if n in examples:
        left = os.path.join(base, f"{n}_left.wav")
        right = os.path.join(base, f"{n}_right.wav")
        return left if os.path.exists(left) else None, right if os.path.exists(right) else None
    return None


def find_ffmpeg():
    # look under third_party for ffmpeg.exe
    root = os.path.join(os.getcwd(), 'third_party')
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            if f.lower() == 'ffmpeg.exe':
                return os.path.join(dirpath, f)
    return shutil.which('ffmpeg')


def two_pass_loudnorm(ffmpeg, in_wav, out_mp3, target_i=-16.0, target_tp=-1.0, lra=7.0):
    # 1) get measured params
    cmd1 = [ffmpeg, '-hide_banner', '-nostats', '-i', in_wav,
            '-af', f'loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:print_format=json',
            '-f', 'null', '-']
    p = subprocess.run(cmd1, capture_output=True, text=True)
    # parse json from stderr
    stderr = p.stderr
    j = None
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith('{') and 'measured_' in line:
            try:
                j = json.loads(line)
                break
            except Exception:
                pass
    if not j:
        # fallback single-pass
        cmd_fallback = [ffmpeg, '-hide_banner', '-i', in_wav, '-af', f'loudnorm=I={target_i}:TP={target_tp}:LRA={lra}', '-ar', '44100', '-ac', '2', '-b:a', '128k', out_mp3, '-y']
        subprocess.run(cmd_fallback)
        return
    measured_I = j.get('input_i')
    measured_TP = j.get('input_tp')
    measured_LRA = j.get('input_lra')
    measured_thresh = j.get('input_thresh')
    cmd2 = [ffmpeg, '-hide_banner', '-nostats', '-i', in_wav,
            '-af', f"loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:measured_I={measured_I}:measured_TP={measured_TP}:measured_LRA={measured_LRA}:measured_thresh={measured_thresh}",
            '-ar', '44100', '-ac', '2', '-b:a', '128k', out_mp3, '-y']
    subprocess.run(cmd2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--out_wav', required=True)
    ap.add_argument('--azimuth', type=float, default=0.0, help='-90 left .. 0 center .. 90 right')
    ap.add_argument('--distance', type=float, default=1.0, help='meters, affects attenuation and lowpass')
    ap.add_argument('--itd_ms_max', type=float, default=0.75, help='max ITD in ms at 90deg')
    ap.add_argument('--ir_left', default=None)
    ap.add_argument('--ir_right', default=None)
    ap.add_argument('--normalize', type=float, default=None, help='target LUFS: if set, produce normalized MP3 with ffmpeg')
    ap.add_argument('--out_mp3', default=None, help='optional mp3 path (if normalize)')
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print('Input not found:', args.input)
        sys.exit(2)

    sig, sr = sf.read(args.input, always_2d=False)
    if sig.ndim > 1:
        sig = sig.mean(axis=1)
    # ensure float32
    sig = sig.astype('float32')

    target_sr = 44100
    if sr != target_sr:
        sig = resample_to(sig, sr, target_sr)
        sr = target_sr

    # apply ITD
    max_itd = float(args.itd_ms_max)
    itd_ms = max_itd * (float(args.azimuth) / 90.0)
    left, right = apply_itd(sig, sr, itd_ms)

    # apply panning gains (ILD)
    g_l, g_r = pan_gain(args.azimuth)

    # distance attenuation
    dist = max(0.1, float(args.distance))
    att = 1.0 / max(dist, 0.5)
    left = left * (g_l * att)
    right = right * (g_r * att)

    # distance lowpass mapping (simple)
    cutoff = 20000.0 / (1.0 + dist * 2.0)
    left = lowpass(left, sr, cutoff)
    right = lowpass(right, sr, cutoff)

    # optional IR convolution
    ir_l = load_ir(args.ir_left, sr) if args.ir_left else None
    ir_r = load_ir(args.ir_right, sr) if args.ir_right else None
    if ir_l is not None:
        left = fftconvolve(left, ir_l)[: len(left)]
    if ir_r is not None:
        right = fftconvolve(right, ir_r)[: len(right)]

    # mix into stereo and prevent clipping
    stereo = np.stack([left, right], axis=1)
    peak = np.max(np.abs(stereo))
    if peak > 1.0:
        stereo = stereo / (peak + 1e-9)

    # write WAV (float32)
    os.makedirs(os.path.dirname(args.out_wav), exist_ok=True)
    sf.write(args.out_wav, stereo, sr, subtype='PCM_16')
    print('Wrote stereo WAV:', args.out_wav)

    # optional normalize + mp3 encode via ffmpeg
    if args.normalize is not None:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            print('ffmpeg not found under third_party or PATH; cannot normalize')
            return
        out_mp3 = args.out_mp3 or os.path.splitext(args.out_wav)[0] + '_normalized.mp3'
        print('Normalizing with ffmpeg ->', out_mp3)
        two_pass_loudnorm(ffmpeg, args.out_wav, out_mp3, target_i=float(args.normalize))
        print('Created:', out_mp3)


if __name__ == '__main__':
    main()
