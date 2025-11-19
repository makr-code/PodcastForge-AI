"""
TTS (Text-to-Speech) Module
Multi-Engine TTS System mit Factory Pattern
"""

# Lightweight package init: avoid importing adapters or engine implementations
# at import time to keep tests and light imports fast. Import submodules
# directly when needed, e.g.:
# `from podcastforge.tts.engine_manager import TTSEngineManager`

__all__ = [
    "TTSEngineManager",
    "get_engine_manager",
    "TTSEngine",
    "BaseTTSEngine",
    "TTSEngineFactory",
]
__all__.extend(["discover_local_piper_models", "discover_local_hf_repo"]) 
