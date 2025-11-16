"""Helpers to stream PCM data into an ffmpeg encoder subprocess.

Provides start_ffmpeg_encoder and feed_wav_to_pipe helpers used by the
script_orchestrator to perform inline conversion (streaming) from WAV
frames to MP3/MP4 without creating an intermediate large combined WAV.
"""
from pathlib import Path
import subprocess
import shutil
import wave
import sys
import numpy as np
import os


def find_ffmpeg(cli_path: str | None = None) -> str | None:
    if cli_path:
        p = Path(cli_path)
        if p.exists():
            return str(p)
        return None
    # First try system PATH
    ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    if ff:
        return ff

    # If not found, try again after ensuring a bundled third_party/ffmpeg/bin
    bundled = _ensure_third_party_ffmpeg_on_path()
    if bundled:
        ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
    return ff


def _ensure_third_party_ffmpeg_on_path() -> str | None:
    """Search repository parents for `third_party/ffmpeg/bin` and prepend it to PATH.

    Returns the path string if added/found, otherwise None.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / 'third_party' / 'ffmpeg' / 'bin'
        if candidate.exists() and candidate.is_dir():
            cand_str = str(candidate)
            cur_path = os.environ.get('PATH', '')
            paths = cur_path.split(os.pathsep) if cur_path else []
            if cand_str not in paths:
                os.environ['PATH'] = cand_str + os.pathsep + cur_path
            return cand_str
    return None


# Ensure bundled third_party/ffmpeg/bin is on PATH at import time so simple
# calls like `shutil.which('ffmpeg')` detect the local binary without extra steps.
_ensure_third_party_ffmpeg_on_path()


def start_ffmpeg_encoder(
    output_path: Path,
    sample_rate: int,
    channels: int,
    codec: str = 'aac',
    bitrate: str = '192k',
    ffmpeg_bin: str | None = None,
    output_to_stdout: bool = False,
    extra_flags: list | None = None,
):
    """Start ffmpeg to encode raw s16le PCM from stdin.

    If `output_to_stdout` is True, ffmpeg will write encoded bytes to stdout
    (pipe:1). Use this for HTTP/WebSocket streaming scenarios.

    `extra_flags` can include additional ffmpeg args (e.g. movflags for
    fragmented MP4).
    """
    ffmpeg = find_ffmpeg(ffmpeg_bin)
    if ffmpeg is None:
        raise FileNotFoundError('ffmpeg not found')

    out_target = 'pipe:1' if output_to_stdout else str(output_path)

    cmd = [
        ffmpeg,
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-f', 's16le',
        '-ar', str(sample_rate),
        '-ac', str(channels),
        '-i', 'pipe:0',
    ]

    if extra_flags:
        # insert extra flags before codec selection if provided
        cmd.extend(extra_flags)

    cmd.extend(['-c:a', codec, '-b:a', str(bitrate), out_target])

    # If writing to stdout, capture stdout; always open stdin for writing
    stdout_pipe = subprocess.PIPE if output_to_stdout else None
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stdout_pipe)
    return proc


def _wav_frames_as_s16(wav_path: Path):
    """Yield raw s16le PCM bytes for a WAV file, converting if needed."""
    with wave.open(str(wav_path), 'rb') as wf:
        nch = wf.getnchannels()
        sampw = wf.getsampwidth()
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

        if sampw == 2:
            # already int16 PCM
            return frames, sr, nch

        # Convert other widths (e.g., 1 byte unsigned, 3/4) to int16
        import numpy as _np

        if sampw == 1:
            # 8-bit unsigned PCM -> centered signed
            arr = _np.frombuffer(frames, dtype=_np.uint8).astype(_np.int16) - 128
            arr = (arr.astype(_np.int32) << 8).astype(_np.int16)
        elif sampw == 4:
            arr = _np.frombuffer(frames, dtype=_np.int32).astype(_np.float32)
            # assume 32-bit PCM int -> scale to int16
            arr = (_np.clip(arr / (2**15), -1.0, 1.0) * 32767.0).astype(_np.int16)
        else:
            # fallback: interpret as float32
            try:
                arr = _np.frombuffer(frames, dtype=_np.float32)
                arr = (_np.clip(arr, -1.0, 1.0) * 32767.0).astype(_np.int16)
            except Exception:
                # last resort: return original frames (may be wrong)
                return frames, sr, nch

        return arr.tobytes(), sr, nch


def feed_wav_to_pipe(proc, wav_path: Path):
    """Write WAV frames to ffmpeg stdin as s16le bytes.

    Raises if writing fails or process stdin is closed.
    """
    data, sr, nch = _wav_frames_as_s16(wav_path)
    if proc.stdin is None:
        raise RuntimeError('ffmpeg process has no stdin')
    try:
        proc.stdin.write(data)
        proc.stdin.flush()
    except BrokenPipeError:
        # ffmpeg died; let caller detect by waiting on proc
        pass
