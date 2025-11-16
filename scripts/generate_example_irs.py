#!/usr/bin/env python3
"""Generate a small set of example impulse responses (IRs) into `third_party/irs/`.

Creates:
- third_party/irs/small_room_left.wav
- third_party/irs/small_room_right.wav
- third_party/irs/large_room_left.wav
- third_party/irs/large_room_right.wav
- third_party/irs/hrtf_example_left.wav
- third_party/irs/hrtf_example_right.wav

These are synthetic IRs for prototyping spatialization and convolution.
"""
import os
import numpy as np
import soundfile as sf


def make_exponential_ir(length_s, sr, decay=0.5, pre_delay_ms=0.0):
    n = int(length_s * sr)
    t = np.arange(n) / sr
    ir = np.exp(-decay * t)
    # apply tiny noise to avoid perfect ringing
    ir *= (1.0 + 0.001 * np.random.randn(n))
    # add pre-delay
    if pre_delay_ms > 0:
        d = int(round(pre_delay_ms * sr / 1000.0))
        ir = np.concatenate((np.zeros(d), ir))
    # normalize
    ir /= np.max(np.abs(ir) + 1e-9)
    return ir.astype('float32')


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    sr = 44100
    out_dir = os.path.join(os.getcwd(), 'third_party', 'irs')
    ensure_dir(out_dir)

    # small room: short decay, small stereo difference
    ir_l = make_exponential_ir(0.6, sr, decay=6.0, pre_delay_ms=2.0)
    ir_r = make_exponential_ir(0.6, sr, decay=6.0, pre_delay_ms=3.5)
    sf.write(os.path.join(out_dir, 'small_room_left.wav'), ir_l, sr)
    sf.write(os.path.join(out_dir, 'small_room_right.wav'), ir_r, sr)

    # large room: longer decay
    ir_l = make_exponential_ir(1.2, sr, decay=1.8, pre_delay_ms=8.0)
    ir_r = make_exponential_ir(1.2, sr, decay=1.6, pre_delay_ms=9.5)
    sf.write(os.path.join(out_dir, 'large_room_left.wav'), ir_l, sr)
    sf.write(os.path.join(out_dir, 'large_room_right.wav'), ir_r, sr)

    # hrtf_example: very short IRs with tiny delays/filters
    ir_l = make_exponential_ir(0.08, sr, decay=40.0, pre_delay_ms=0.0)
    ir_r = make_exponential_ir(0.08, sr, decay=40.0, pre_delay_ms=0.4)
    sf.write(os.path.join(out_dir, 'hrtf_example_left.wav'), ir_l, sr)
    sf.write(os.path.join(out_dir, 'hrtf_example_right.wav'), ir_r, sr)

    print('Generated example IRs in', out_dir)


if __name__ == '__main__':
    main()
