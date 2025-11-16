"""
Audio Processing Module
"""

# Lightweight package init: avoid importing heavy submodules at package
# import time (e.g. pydub/ffmpeg). Submodules can be imported directly:
# `from podcastforge.audio.player import get_player`.

__all__ = [
    "AudioPostProcessor",
    "AudioPlayer",
    "get_player",
    "WaveformGenerator",
    "generate_waveform_tkinter",
]
