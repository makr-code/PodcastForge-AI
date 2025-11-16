"""Orchestrator for script-driven multi-speaker TTS previews.

Accepts a simple JSON/YAML script where each entry maps a speaker to text.
Renders per-utterance TTS (with caching), optionally combines them into a single
preview file, and publishes progress events via the EventBus so the GUI can
play previews on the fly.
"""
from __future__ import annotations

from pathlib import Path
import threading
from typing import List, Dict, Optional
import json
import hashlib
import time
import wave

import numpy as np

from ..tts.engine_manager import get_engine_manager, TTSEngine
from ..core.events import get_event_bus
import concurrent.futures

try:
    import yaml
except Exception:
    yaml = None


def _cache_key(text: str, speaker: str, engine: Optional[str]) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"|")
    h.update(str(speaker).encode("utf-8"))
    h.update(b"|")
    h.update(str(engine or "").encode("utf-8"))
    return h.hexdigest()


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    arr = np.asarray(audio)
    if arr.ndim > 1:
        arr = arr.mean(axis=1)
    clipped = np.clip(arr, -1.0, 1.0)
    int16 = (clipped * 32767).astype('int16')
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(int16.tobytes())


def _concat_wavs(output_path: Path, paths: List[Path]):
    if not paths:
        # create empty short wav
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"")
        return

    first = paths[0]
    params = None
    frames = []
    for p in paths:
        with wave.open(str(p), 'rb') as r:
            if params is None:
                params = r.getparams()
            else:
                if r.getparams()[:3] != params[:3]:
                    # incompatible, fallback to first
                    with first.open('rb') as fh_in, output_path.open('wb') as fh_out:
                        fh_out.write(fh_in.read())
                    return
            frames.append(r.readframes(r.getnframes()))

    with wave.open(str(output_path), 'wb') as wf:
        wf.setnchannels(params.nchannels)
        wf.setsampwidth(params.sampwidth)
        wf.setframerate(params.framerate)
        for f in frames:
            wf.writeframes(f)


def synthesize_script_preview(
    script_path: str,
    out_dir: str,
    speaker_map: Optional[Dict[str, str]] = None,
    engine: str = 'PIPER',
    cache_dir: Optional[str] = None,
    max_workers: int = 2,
    cancel_event: Optional[threading.Event] = None,
    output_format: str = 'mp4',
    audio_bitrate: str = '192k',
) -> Dict:
    """Render a script (JSON/YAML) into per-utterance WAV previews and a combined preview.

    script format: list of { 'speaker': 'Name', 'text': '...' }
    `speaker_map` maps script speaker names to TTS speaker ids.

    Publishes events on `script.tts_progress` and `script.preview_ready`.
    Returns: { ok: bool, preview_path: str, clips: [ {speaker,file,duration} ] }
    """
    spath = Path(script_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cache = Path(cache_dir) if cache_dir else out / 'cache'
    cache.mkdir(parents=True, exist_ok=True)

    if not spath.exists():
        return {'ok': False, 'message': 'script not found'}

    # Load script
    try:
        if spath.suffix.lower() in ('.json',):
            content = json.loads(spath.read_text(encoding='utf-8'))
        else:
            if yaml is None:
                return {'ok': False, 'message': 'yaml not available; install pyyaml or use json'}
            content = yaml.safe_load(spath.read_text(encoding='utf-8'))
    except Exception as e:
        return {'ok': False, 'message': f'failed to parse script: {e}'}

    if not isinstance(content, list):
        return {'ok': False, 'message': 'script must be a list of {speaker,text} entries'}

    speaker_map = speaker_map or {}
    manager = get_engine_manager()

    clips: List[Dict] = []
    to_synth = []
    # Prepare tasks
    for idx, entry in enumerate(content, start=1):
        speaker = entry.get('speaker', 'narrator')
        text = entry.get('text', '')
        voice = speaker_map.get(speaker, speaker)
        key = _cache_key(text, voice, engine)
        cached = cache / f"{key}.wav"
        clips.append({'idx': idx, 'speaker': speaker, 'voice': voice, 'text': text, 'file': str(cached)})
        if not cached.exists():
            to_synth.append((idx, text, voice, cached))

    # Submit synthesis tasks
    results = {}
    if to_synth:
        # Use a local ThreadPoolExecutor to avoid importing GUI threading helpers
        # at module import time (prevents circular imports when this module is
        # used from CLI/runner scripts).
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

        def make_task_fn(idx, text, voice, cached_file):
            def task_fn(task_id: str, progress_callback=None):
                try:
                    # respect cooperative cancellation before starting
                    if cancel_event is not None and cancel_event.is_set():
                        try:
                            get_event_bus().publish('script.tts_progress', {'task_id': task_id, 'idx': idx, 'status': 'failed'})
                        except Exception:
                            pass
                        return {'idx': idx, 'file': str(cached_file), 'cancelled': True}

                    # build an engine_progress callback that publishes percentage progress
                    progress_state = {'value': 0.0, 'done': False}

                    def engine_progress(percent: float, stage: Optional[str] = None):
                        # clamp and normalize percent
                        try:
                            p = float(percent)
                        except Exception:
                            p = 0.0
                        if p < 0.0:
                            p = 0.0
                        if p > 1.0:
                            p = 1.0

                        payload = {'task_id': task_id, 'idx': idx, 'progress': p}
                        if stage is not None:
                            payload['stage'] = stage

                        # publish to EventBus
                        try:
                            get_event_bus().publish('script.tts_progress', payload)
                        except Exception:
                            pass

                        # record into shared state
                        try:
                            progress_state['value'] = p
                            if p >= 1.0:
                                progress_state['done'] = True
                        except Exception:
                            pass

                        # forward to thread-manager provided callback if present
                        try:
                            if progress_callback:
                                progress_callback(p, stage)
                        except Exception:
                            pass

                    # initial publish
                    try:
                        engine_progress(0.0, 'start')
                    except Exception:
                        pass

                    # Start a watchdog thread that simulates incremental progress
                    # if the engine doesn't emit frequent updates. This keeps the UI
                    # responsive for blocking engines. The watchdog will not exceed
                    # 95% so real 'done' events still set completion.
                    def _watchdog():
                        try:
                            last = progress_state.get('value', 0.0)
                            while not progress_state.get('done'):
                                # respect cancellation
                                if cancel_event is not None and cancel_event.is_set():
                                    return
                                time.sleep(0.5)
                                cur = progress_state.get('value', 0.0)
                                if progress_state.get('done'):
                                    return
                                if cur <= last:
                                    # bump by small delta up to 0.95
                                    try:
                                        nxt = min(0.95, cur + 0.02)
                                        if nxt > cur:
                                            engine_progress(nxt, 'simulated')
                                    except Exception:
                                        pass
                                last = progress_state.get('value', 0.0)
                        except Exception:
                            pass

                    try:
                        threading.Thread(target=_watchdog, daemon=True).start()
                    except Exception:
                        pass

                except Exception:
                    pass

                try:
                    # perform synthesis; engine may be blocking — cooperative cancel is best-effort
                    # Respect the `engine` parameter passed to synthesize_script_preview by
                    # converting the string name to the TTSEngine enum when present.
                    engine_type = None
                    try:
                        if engine:
                            # allow both enum or string values (e.g. 'BARK' or TTSEngine.BARK)
                            engine_type = engine if isinstance(engine, TTSEngine) else TTSEngine[engine]
                    except Exception:
                        engine_type = None

                    audio, sr = manager.synthesize(
                        text,
                        voice,
                        engine_type=engine_type,
                        cancel_event=cancel_event,
                        progress_callback=engine_progress,
                    )

                    # If cancel requested after synthesis, mark as cancelled (best-effort)
                    if cancel_event is not None and cancel_event.is_set():
                        try:
                            get_event_bus().publish('script.tts_progress', {'task_id': task_id, 'idx': idx, 'status': 'cancelled'})
                        except Exception:
                            pass
                        return {'idx': idx, 'file': str(cached_file), 'cancelled': True}

                    _write_wav(cached_file, audio, sr)
                except Exception as e:
                    # Distinguish cancellation vs other failures if possible
                    try:
                        from ..tts.engine_manager import CancelledError

                        if isinstance(e, CancelledError):
                            try:
                                get_event_bus().publish('script.tts_progress', {'task_id': task_id, 'idx': idx, 'status': 'cancelled'})
                            except Exception:
                                pass
                            return {'idx': idx, 'file': str(cached_file), 'cancelled': True}
                    except Exception:
                        pass

                    # publish failure
                    try:
                        get_event_bus().publish('script.tts_progress', {'task_id': task_id, 'idx': idx, 'status': 'failed'})
                    except Exception:
                        pass
                    raise

                try:
                    engine_progress(1.0, 'done')
                except Exception:
                    pass

                try:
                    get_event_bus().publish('script.tts_progress', {'task_id': task_id, 'idx': idx, 'status': 'done'})
                except Exception:
                    pass

                return {'idx': idx, 'file': str(cached_file)}

            return task_fn

        futures = {}

        def _run_task(fn, tid):
            # wrapper to call the task function with expected signature
            return fn(task_id=tid, progress_callback=None)

        for idx, text, voice, cached_file in to_synth:
            tid = f"s{idx:03d}"
            fn = make_task_fn(idx, text, voice, cached_file)
            fut = executor.submit(_run_task, fn, tid)
            futures[tid] = fut

        # wait for completion with timeout
        timeout = max(30, len(futures) * 5)
        done, not_done = concurrent.futures.wait(futures.values(), timeout=timeout)
        if not_done:
            missing = [tid for tid, f in futures.items() if not f.done()]
            return {'ok': False, 'message': f'timeout waiting for synth tasks: {missing}'}

        # collect results and check exceptions
        for tid, fut in futures.items():
            try:
                res_item = fut.result()
                # store result under task id similar to previous behaviour
                results[tid] = res_item
            except Exception as e:
                return {'ok': False, 'message': f'TTS synth failed: {e}'}

        executor.shutdown(wait=True)

    # All clips available, build combined preview or stream into encoder
    ordered_files = [Path(c['file']) for c in clips]
    final_preview = None
    fmt = (output_format or 'mp4').lower()
    # normalize common aliases
    if fmt in ('m4a',):
        fmt = 'mp4'

    if fmt != 'wav':
        # Try streaming the per-utterance WAVs into ffmpeg to encode on-the-fly.
        import shutil
        import subprocess
        from ..audio.ffmpeg_pipe import start_ffmpeg_encoder, feed_wav_to_pipe, find_ffmpeg

        out_path = out / f'script_preview.{fmt}'
        ffmpeg_bin = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
        if ffmpeg_bin is None:
            # No ffmpeg available — fall back to WAV+warning
            preview = out / 'script_preview.wav'
            _concat_wavs(preview, ordered_files)
            try:
                get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips], 'warning': 'ffmpeg not found; output is WAV'})
            except Exception:
                pass
            return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips, 'warning': 'ffmpeg not found; output is WAV'}

        # Choose codec
        if fmt == 'mp4':
            codec = 'aac'
        elif fmt == 'mp3':
            codec = 'libmp3lame'
        else:
            codec = 'aac'

        # Inspect first WAV for sample rate and channels; ensure compatibility
        try:
            import wave as _wave
            first = ordered_files[0]
            with _wave.open(str(first), 'rb') as wf:
                sr = wf.getframerate()
                nch = wf.getnchannels()

            # Verify all files have same sample rate and channels; otherwise fallback
            compatible = True
            for p in ordered_files[1:]:
                try:
                    with _wave.open(str(p), 'rb') as wf:
                        if wf.getframerate() != sr or wf.getnchannels() != nch:
                            compatible = False
                            break
                except Exception:
                    compatible = False
                    break

            if not compatible:
                # Fallback to concatenation then normal ffmpeg conversion
                preview = out / 'script_preview.wav'
                _concat_wavs(preview, ordered_files)
                cmd = [ffmpeg_bin, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(preview), '-c:a', codec, '-b:a', str(audio_bitrate), str(out_path)]
                try:
                    subprocess.run(cmd, check=True)
                    final_preview = out_path
                    try:
                        preview.unlink()
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips], 'warning': f'ffmpeg conversion failed: {e}'})
                    except Exception:
                        pass
                    return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips, 'warning': f'ffmpeg conversion failed: {e}'}
            else:
                # Start encoder and feed WAVs sequentially
                try:
                    # For MP4 we prefer fragmented+faststart flags to make the
                    # resulting file streamable/progressively playable.
                    extra = None
                    if fmt == 'mp4':
                        extra = ['-movflags', '+faststart+frag_keyframe+empty_moov']
                    proc = start_ffmpeg_encoder(
                        out_path,
                        sample_rate=sr,
                        channels=nch,
                        codec=codec,
                        bitrate=audio_bitrate,
                        ffmpeg_bin=ffmpeg_bin,
                        extra_flags=extra,
                    )
                except Exception as e:
                    # If starting encoder fails, fallback to concatenation + conversion
                    preview = out / 'script_preview.wav'
                    _concat_wavs(preview, ordered_files)
                    try:
                        subprocess.run([ffmpeg_bin, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(preview), '-c:a', codec, '-b:a', str(audio_bitrate), str(out_path)], check=True)
                        final_preview = out_path
                        try:
                            preview.unlink()
                        except Exception:
                            pass
                    except Exception as e2:
                        try:
                            get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips], 'warning': f'ffmpeg conversion failed: {e2}'})
                        except Exception:
                            pass
                        return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips, 'warning': f'ffmpeg conversion failed: {e2}'}

                # Feed files in order
                try:
                    for p in ordered_files:
                        feed_wav_to_pipe(proc, p)

                    # close stdin to let ffmpeg finalize
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
                    ret = proc.wait()
                    if ret != 0:
                        raise RuntimeError(f'ffmpeg exited with code {ret}')

                    final_preview = out_path
                    # do not remove per-utterance cached files; optional cleanup could be added
                except Exception as e:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    # fallback to concatenation approach
                    preview = out / 'script_preview.wav'
                    _concat_wavs(preview, ordered_files)
                    try:
                        subprocess.run([ffmpeg_bin, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(preview), '-c:a', codec, '-b:a', str(audio_bitrate), str(out_path)], check=True)
                        final_preview = out_path
                        try:
                            preview.unlink()
                        except Exception:
                            pass
                    except Exception as e2:
                        try:
                            get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips], 'warning': f'ffmpeg conversion failed: {e2}'})
                        except Exception:
                            pass
                        return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips, 'warning': f'ffmpeg conversion failed: {e2}'}

        except Exception as e:
            # unexpected error during streaming attempt; fallback to existing flow
            preview = out / 'script_preview.wav'
            _concat_wavs(preview, ordered_files)
            try:
                get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips], 'warning': f'streaming conversion failed: {e}'})
            except Exception:
                pass
            return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips, 'warning': f'streaming conversion failed: {e}'}
    else:
        # Output requested as WAV: concatenate per-utterance files into one WAV preview
        try:
            preview = out / 'script_preview.wav'
            _concat_wavs(preview, ordered_files)
            final_preview = preview
            try:
                get_event_bus().publish('script.preview_ready', {'preview': str(preview.resolve()), 'clips': [c for c in clips]})
            except Exception:
                pass
            return {'ok': True, 'preview_path': str(preview.resolve()), 'clips': clips}
        except Exception as e:
            try:
                get_event_bus().publish('script.preview_ready', {'preview': str((out / 'script_preview.wav').resolve()), 'clips': [c for c in clips], 'warning': f'wav concat failed: {e}'})
            except Exception:
                pass
            return {'ok': True, 'preview_path': str((out / 'script_preview.wav').resolve()), 'clips': clips, 'warning': f'wav concat failed: {e}'}
    # Publish preview ready
    try:
        get_event_bus().publish('script.preview_ready', {'preview': str(final_preview.resolve()), 'clips': [c for c in clips]})
    except Exception:
        pass

    return {'ok': True, 'preview_path': str(final_preview.resolve()), 'clips': clips}


__all__ = ['synthesize_script_preview']
