"""Voices Module - Voice Library und Voice Management"""

from .library import (
    VoiceLibrary,
    VoiceProfile,
    VoiceGender,
    VoiceAge,
    VoiceStyle,
    get_voice_library
)

__all__ = [
    "VoiceLibrary",
    "VoiceProfile", 
    "VoiceGender",
    "VoiceAge",
    "VoiceStyle",
    "get_voice_library"
]
