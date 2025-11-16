#!/usr/bin/env python3
"""
Runner to render the example podcast project using the script_orchestrator.

Usage (PowerShell):
$env:PYTHONPATH='src'; python .\examples\projects\ai_tts_podcast\render_project.py

Notes:
- This will attempt to synthesize audio using the default engine (PIPER). Depending
  on your environment, the TTS engine may require additional packages/models.
- For a quick dry-run, set `max_workers=1` and run in an environment where Piper
  or a fallback engine is available.
"""
from pathlib import Path
import tempfile
import shutil
import sys

# Make sure src is on sys.path when running directly
proj_root = Path(__file__).resolve().parent.parent.parent
src_path = proj_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from podcastforge.integrations.script_orchestrator import synthesize_script_preview
import importlib.util
import os
from typing import List


def _write_wav(path: Path, audio: List[float], sr: int = 22050):
  import wave
  import numpy as np

  arr = np.asarray(audio, dtype=np.float32)
  if arr.ndim > 1:
    arr = arr.mean(axis=1)
  clipped = np.clip(arr, -1.0, 1.0)
  int16 = (clipped * 32767).astype('int16')
  with wave.open(str(path), 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(int(sr))
    wf.writeframes(int16.tobytes())


def _concat_wavs(output_path: Path, paths: List[Path]):
  import wave

  if not paths:
    # write an empty short wav
    with wave.open(str(output_path), 'wb') as wf:
      wf.setnchannels(1)
      wf.setsampwidth(2)
      wf.setframerate(22050)
      wf.writeframes(b"")
    return

  params = None
  frames = []
  for p in paths:
    with wave.open(str(p), 'rb') as r:
      if params is None:
        params = r.getparams()
      frames.append(r.readframes(r.getnframes()))

  with wave.open(str(output_path), 'wb') as wf:
    wf.setnchannels(params.nchannels)
    wf.setsampwidth(params.sampwidth)
    wf.setframerate(params.framerate)
    for f in frames:
      wf.writeframes(f)


def _mock_synthesize(script_path: Path, out_dir: Path, cache_dir: Path):
  """Create mock per-utterance WAVs (simple sine tones) and a combined preview.

  This is a safe fallback for environments without TTS engines installed.
  """
  import json
  import numpy as np

  data = json.loads(script_path.read_text(encoding='utf-8'))
  clips = []
  sr = 22050
  t_base = 1.0
  for i, entry in enumerate(data, start=1):
    dur = min(3.0, t_base + (i % 3) * 0.5)
    freq = 220 + (i * 30)
    samples = int(sr * dur)
    tt = np.linspace(0, dur, samples, endpoint=False)
    audio = 0.15 * np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 0.5)
    cached = cache_dir / f"mock_{i:03d}.wav"
    _write_wav(cached, audio, sr)
    clips.append({'idx': i, 'speaker': entry.get('speaker', 'narrator'), 'file': str(cached), 'duration': dur})

  preview = out_dir / 'script_preview_mock.wav'
  paths = [Path(c['file']) for c in clips]
  _concat_wavs(preview, paths)
  return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips}


def main():
  base = Path(__file__).resolve().parent
  script = base / 'script.json'
  out_dir = base / 'out'
  cache_dir = base / 'cache'
  out_dir.mkdir(parents=True, exist_ok=True)
  cache_dir.mkdir(parents=True, exist_ok=True)

  print('Starting render for AI & TTS sample project')

  # Auto-detect available TTS engines by checking installed modules
  def _has_mod(name: str) -> bool:
    try:
      return importlib.util.find_spec(name) is not None
    except Exception:
      return False

  preferred = os.environ.get('PF_ENGINE')
  engine_choice = None
  if preferred:
    engine_choice = preferred
  else:
    # prefer Bark, then Piper, then XTTS
    if _has_mod('bark'):
      engine_choice = 'BARK'
    elif _has_mod('piper'):
      engine_choice = 'PIPER'
    elif _has_mod('TTS') or _has_mod('TTS.api'):
      engine_choice = 'XTTS'
    else:
      engine_choice = None

  print(f'Engine auto-detect -> {engine_choice or "(none detected), will use mock fallback"}')

  try:
    out_fmt = os.environ.get('PF_OUTPUT_FORMAT', 'mp4')
    if engine_choice:
      res = synthesize_script_preview(str(script), str(out_dir), engine=engine_choice, cache_dir=str(cache_dir), max_workers=2, output_format=out_fmt)
    else:
      raise RuntimeError('No engine detected')

    if not res.get('ok'):
      print('Orchestrator reported failure; falling back to mock synth:', res.get('message'))
      res = _mock_synthesize(script, out_dir, cache_dir)
  except Exception as e:
    print('Real synth failed or not available, using mock fallback:', e)
    res = _mock_synthesize(script, out_dir, cache_dir)

  print('Result:', res)


if __name__ == '__main__':
  main()
