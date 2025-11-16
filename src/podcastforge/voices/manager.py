"""Voice manager helpers: preview and speaker helpers.

Provides a small API to preview a voice (synthesize a sample text and play it)
and helpers to map voice profiles to project speaker entries.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import time
import json
from typing import Optional

import numpy as np

from ..tts.engine_manager import get_engine_manager
from ..audio.player import get_player
from .library import get_voice_library
from ..core.config import Speaker


def preview_voice(voice_id: str, sample_text: str = "Hallo, dies ist eine Vorschau.", play: bool = True) -> Optional[str]:
    """Synthesize a short preview for `voice_id` and optionally play it.

    Returns the path to the generated wav/mp3 file or None on failure.
    """
    vl = get_voice_library()
    v = vl.get_voice(voice_id)
    if v is None:
        return None

    manager = get_engine_manager()
    try:
        audio_np, sr = manager.synthesize(sample_text, v.id)
    except Exception:
        # fall back: try with name
        try:
            audio_np, sr = manager.synthesize(sample_text, v.name)
        except Exception:
            return None

    # write wav to temp
    out_dir = Path(tempfile.gettempdir()) / "podcastforge_voice_previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    out_path = out_dir / f"preview_{v.id}_{ts}.wav"

    # write 16-bit PCM
    arr = np.asarray(audio_np)
    if arr.ndim > 1:
        arr = arr.mean(axis=1)
    clipped = np.clip(arr, -1.0, 1.0)
    int16 = (clipped * 32767).astype('int16')

    try:
        import wave

        with wave.open(str(out_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(int(sr))
            wf.writeframes(int16.tobytes())
    except Exception:
        try:
            out_path.write_bytes(int16.tobytes())
        except Exception:
            return None

    if play:
        try:
            player = get_player()
            player.play(out_path)
        except Exception:
            pass

    return str(out_path)


def speaker_from_voice(voice_id: str, speaker_name: Optional[str] = None) -> Speaker:
    """Create a `Speaker` dataclass from a voice profile.

    The returned Speaker uses `voice_profile` and `voice_sample` fields populated.
    """
    vl = get_voice_library()
    v = vl.get_voice(voice_id)
    if v is None:
        raise ValueError("Voice not found")

    sid = voice_id
    name = speaker_name or v.display_name
    sp = Speaker(
        id=sid,
        name=name,
        role="guest",
        personality="",
        voice_profile=v.id,
        voice_sample=f"{v.repo}/{v.sub_path}/{v.sample_filename}",
        gender=v.gender.value,
        age=v.age.value,
    )
    return sp


__all__ = ["preview_voice", "speaker_from_voice"]
