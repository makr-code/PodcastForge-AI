"""
GUI Components für PodcastForge

Enthält:
- PodcastEditor: Haupt-Editor für Podcast-Skripte
- UI-Komponenten: Tooltips, StatusBar, WelcomePanel, etc.
- Threading: Hintergrund-Task-Management
- Timeline & Multitrack: Audio-Bearbeitung
"""

from .editor import PodcastEditor
from .multitrack import AudioClip, MultiTrackEditor, Track, TrackType
from .threading_base import (
    TaskPriority,
    TaskStatus,
    ThreadManager,
    UITaskObserver,
    get_thread_manager,
    shutdown_thread_manager,
)
from .timeline import Marker, Scene, TimelineEditor
from .components import (
    apply_theme,
    get_theme_colors,
    THEMES,
    Tooltip,
    IconButton,
    StatusBar,
    WelcomePanel,
    QuickActionBar,
    VoiceCard,
)
from .settings_dialog import SettingsDialog

__all__ = [
    # Editor
    "PodcastEditor",
    # Threading
    "ThreadManager",
    "get_thread_manager",
    "shutdown_thread_manager",
    "UITaskObserver",
    "TaskStatus",
    "TaskPriority",
    # Timeline/Multitrack
    "TimelineEditor",
    "Scene",
    "Marker",
    "MultiTrackEditor",
    "Track",
    "AudioClip",
    "TrackType",
    # UI Components
    "apply_theme",
    "get_theme_colors",
    "THEMES",
    "Tooltip",
    "IconButton",
    "StatusBar",
    "WelcomePanel",
    "QuickActionBar",
    "VoiceCard",
    "SettingsDialog",
]
