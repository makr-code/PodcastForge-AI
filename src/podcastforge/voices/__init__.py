"""
Voice Management Module
Voice Library + Voice Cloning System
"""

from .cloner import (
    ClonedVoiceProfile,
    VoiceCloner,
    VoiceExtractionEngine,
    VoiceQuality,
    get_voice_cloner,
)
from .library import (
    VoiceAge,
    VoiceGender,
    VoiceLibrary,
    VoiceProfile,
    VoiceStyle,
    get_voice_library,
)

__all__ = [
    "VoiceLibrary",
    "get_voice_library",
    "VoiceProfile",
    "VoiceGender",
    "VoiceAge",
    "VoiceStyle",
    "VoiceCloner",
    "get_voice_cloner",
    "ClonedVoiceProfile",
    "VoiceQuality",
    "VoiceExtractionEngine",
]
