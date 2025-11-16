#!/usr/bin/env python3
"""Batch spatializer: mix multiple speakers (per utterance) into a 44.1kHz stereo master.

Input: a JSON config or CLI arguments. The JSON format (example):
{
  "outputs_dir": "out/example/spatial_batch",
  "speakers": [
    {"name":"host", "utterances": ["out/example/cache/248...af.wav"], "azimuth": -30, "distance": 1.0},
    {"name":"guest", "utterances": ["out/example/cache/2f86...ca4.wav"], "azimuth": 30, "distance": 1.2}
  ],
  "master_wav": "out/example/spatial_batch_master.wav",
  "normalize_lufs": -16
}

The script will spatialize each utterance, sum into a stereo master, and run loudnorm (if requested).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

# allow importing scripts as a module by adding scripts/ to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'scripts'))
try:
    import spatialize as spatialize_mod
    spatialize_mono_to_stereo = spatialize_mod.spatialize_mono_to_stereo
    find_ffmpeg = spatialize_mod.find_ffmpeg
except Exception:
    # fallback: try import via package path
    from scripts.spatialize import spatialize_mono_to_stereo, find_ffmpeg


def mix_stereo_list(stereo_list):
    # stereo_list: list of (array Nx2)
    if not stereo_list:
        return None
    max_len = max(s.shape[0] for s in stereo_list)
    sr = None
    out = np.zeros((max_len, 2), dtype='float32')
    for s in stereo_list:
        if s.shape[0] < max_len:
            s2 = np.zeros((max_len, 2), dtype='float32')
            s2[: s.shape[0], :] = s
            s = s2
        out += s
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out = out / (peak + 1e-9)
    return out


def two_pass_loudnorm(ffmpeg, in_wav, out_wav, target_i=-16.0, target_tp=-1.0, lra=7.0):
    # reuse similar approach from spatialize.two_pass_loudnorm but simple here
    cmd1 = [ffmpeg, '-hide_banner', '-nostats', '-i', in_wav,
            '-af', f'loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:print_format=json', '-f', 'null', '-']
    p = subprocess.run(cmd1, capture_output=True, text=True)
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
        subprocess.run([ffmpeg, '-hide_banner', '-i', in_wav, '-af', f'loudnorm=I={target_i}:TP={target_tp}:LRA={lra}', out_wav, '-y'])
        return
    measured_I = j.get('input_i')
    measured_TP = j.get('input_tp')
    measured_LRA = j.get('input_lra')
    measured_thresh = j.get('input_thresh')
    cmd2 = [ffmpeg, '-hide_banner', '-nostats', '-i', in_wav,
            '-af', f"loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:measured_I={measured_I}:measured_TP={measured_TP}:measured_LRA={measured_LRA}:measured_thresh={measured_thresh}",
            out_wav, '-y']
    subprocess.run(cmd2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', help='JSON config file describing speakers and utterances', required=True)
    args = ap.parse_args()
    cfg = json.load(open(args.config, 'r'))
    outputs_dir = cfg.get('outputs_dir', 'out/example/spatial_batch')
    os.makedirs(outputs_dir, exist_ok=True)
    master_items = []
    sr = 44100
    for sp in cfg.get('speakers', []):
        name = sp.get('name')
        az = sp.get('azimuth', 0.0)
        dist = sp.get('distance', 1.0)
        ir = sp.get('ir', None)
        per_utts = []
        for utt in sp.get('utterances', []):
            stereo, srr = spatialize_mono_to_stereo(utt, azimuth=az, distance=dist, ir_left=None, ir_right=None)
            per_path = os.path.join(outputs_dir, f"{name}__{os.path.basename(utt)}")
            sf.write(per_path + '.wav', stereo, srr, subtype='PCM_16')
            per_utts.append(stereo)
        # sum this speaker's utterances into single stereo track (concatenate)
        if per_utts:
            # naive concat
            sp_track = np.concatenate(per_utts, axis=0)
            master_items.append(sp_track)
    master = mix_stereo_list(master_items)
    master_wav = cfg.get('master_wav', os.path.join(outputs_dir, 'master.wav'))
    sf.write(master_wav, master, sr, subtype='PCM_16')
    print('Wrote master WAV:', master_wav)
    if 'normalize_lufs' in cfg:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            print('ffmpeg not found; skip normalization')
            return
        out_norm = cfg.get('master_normalized', os.path.splitext(master_wav)[0] + '_norm.mp3')
        two_pass_loudnorm(ffmpeg, master_wav, out_norm, target_i=float(cfg.get('normalize_lufs', -16.0)))
        print('Wrote normalized master:', out_norm)
    # --- Microphone simulation ---
    mics = cfg.get('mics', [])
    mic_outputs = []
    for mic in mics:
        mic_name = mic.get('name')
        mic_az = mic.get('azimuth', 0.0)
        mic_dist = mic.get('distance', 1.0)
        # build mono mic track by summing speaker contributions
        # find max length
        if not speaker_tracks:
            continue
        max_len = max(v['track'].shape[0] for v in speaker_tracks.values())
        mic_track = np.zeros((max_len,), dtype='float32')
        for sname, info in speaker_tracks.items():
            tr = info['track']
            # compute relative azimuth from mic to speaker
            rel_az = info.get('az', 0.0) - mic_az
            # derive left/right gains and convert to mono pickup
            # simple model: mic picks sum of stereo with weighting
            l_gain = np.cos((np.clip(rel_az/90.0, -1, 1)+1.0)*(np.pi/4.0))
            r_gain = np.sin((np.clip(rel_az/90.0, -1, 1)+1.0)*(np.pi/4.0))
            # obtain speaker stereo channels
            left = tr[:, 0]
            right = tr[:, 1]
            pickup = left * l_gain + right * r_gain
            # apply distance attenuation between speaker and mic
            dist_factor = 1.0 / max((info.get('dist', 1.0) + mic_dist), 0.5)
            pickup *= dist_factor
            if pickup.shape[0] < max_len:
                tmp = np.zeros((max_len,), dtype='float32')
                tmp[: pickup.shape[0]] = pickup
                pickup = tmp
            mic_track += pickup
        # simple mic lowpass by distance
        cutoff = 20000.0 / (1.0 + mic_dist * 3.0)
        try:
            from scipy.signal import butter, lfilter

            if cutoff < sr / 2.0:
                b, a = butter(2, cutoff / (sr / 2.0), btype='low')
                mic_track = lfilter(b, a, mic_track)
        except Exception:
            pass
        # normalize mic track peak
        p = np.max(np.abs(mic_track))
        if p > 1.0:
            mic_track = mic_track / (p + 1e-9)
        mic_path = os.path.join(outputs_dir, f"mic_{mic_name}.wav")
        sf.write(mic_path, mic_track, sr, subtype='PCM_16')
        mic_outputs.append(mic_path)
        print('Wrote mic file:', mic_path)
    # optionally normalize mic outputs as mp3
    if cfg.get('normalize_mics') and mic_outputs:
        ffmpeg = find_ffmpeg()
        if ffmpeg:
            for m in mic_outputs:
                out_mp3 = os.path.splitext(m)[0] + '_norm.mp3'
                two_pass_loudnorm(ffmpeg, m, out_mp3, target_i=float(cfg.get('normalize_lufs', -16.0)))
                print('Wrote mic normalized:', out_mp3)


if __name__ == '__main__':
    main()
