"""
Voice Management Module
Voice Library + Voice Cloning System
"""

from .library import (
    VoiceLibrary,
    get_voice_library,
    VoiceProfile,
    VoiceGender,
    VoiceAge,
    VoiceStyle
)
from .cloner import (
    VoiceCloner,
    get_voice_cloner,
    ClonedVoiceProfile,
    VoiceQuality,
    VoiceExtractionEngine
)

__all__ = [
    'VoiceLibrary',
    'get_voice_library',
    'VoiceProfile',
    'VoiceGender',
    'VoiceAge',
    'VoiceStyle',
    'VoiceCloner',
    'get_voice_cloner',
    'ClonedVoiceProfile',
    'VoiceQuality',
    'VoiceExtractionEngine',
]
