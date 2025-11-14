"""
PodcastForge AI - KI-gestützter Podcast-Generator
"""

__version__ = "1.0.0"
__author__ = "makr-code"
__license__ = "MIT"

from .core.forge import PodcastForge
from .core.config import PodcastConfig, PodcastStyle, Speaker

__all__ = [
    "PodcastForge",
    "PodcastConfig",
    "PodcastStyle",
    "Speaker",
]
