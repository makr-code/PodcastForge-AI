"""
PodcastForge AI - KI-gestützter Podcast-Generator
"""

__version__ = "1.0.0"
__author__ = "makr-code"
__license__ = "MIT"

# Paketmetadaten exportieren, schwere Modul-Imports vermeiden
# Direkte Importe (z.B. PodcastForge) werden bewusst nicht beim
# Paket-Import ausgeführt, um Tests und leichte Imports schnell
# zu halten. Verwende direkte Imports wie
# `from podcastforge.core.forge import PodcastForge` wenn nötig.

__all__ = [
    "PodcastForge",
    "PodcastConfig",
    "PodcastStyle",
    "Speaker",
]
