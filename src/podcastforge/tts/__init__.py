"""
TTS (Text-to-Speech) Module
Multi-Engine TTS System mit Factory Pattern
"""

from .adapter import ebook2audiobookAdapter
from .engine_manager import (
    TTSEngineManager,
    get_engine_manager,
    TTSEngine,
    BaseTTSEngine,
    TTSEngineFactory
)

__all__ = [
    'ebook2audiobookAdapter',
    'TTSEngineManager',
    'get_engine_manager',
    'TTSEngine',
    'BaseTTSEngine',
    'TTSEngineFactory',
]

