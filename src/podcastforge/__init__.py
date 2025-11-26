"""
PodcastForge AI - KI-gestützter Podcast-Generator

Hochwertige Podcast-Generierung mit natürlichen Sprechern und Sprecherinnen.
Einfacher und ansprechender Workflow für die Podcast-Erstellung.
"""

__version__ = "1.2.0"
__author__ = "makr-code"
__license__ = "MIT"

# Paketmetadaten exportieren, schwere Modul-Imports vermeiden
# Direkte Importe (z.B. PodcastForge) werden bewusst nicht beim
# Paket-Import ausgeführt, um Tests und leichte Imports schnell
# zu halten. Verwende direkte Imports wie
# `from podcastforge.core.forge import PodcastForge` wenn nötig.

__all__ = [
    # Core-Klassen
    "PodcastForge",
    "PodcastConfig",
    "PodcastStyle",
    "Speaker",
    # Qualitätsstufen
    "VoiceQuality",
    # Template-Funktionen
    "get_quality_preset",
    "get_podcast_template",
]
