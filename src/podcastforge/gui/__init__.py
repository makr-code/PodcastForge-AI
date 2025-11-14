"""
GUI Components
"""

from .editor import PodcastEditor
from .threading_base import (
    ThreadManager,
    get_thread_manager,
    shutdown_thread_manager,
    UITaskObserver,
    TaskStatus,
    TaskPriority
)
from .timeline import TimelineEditor, Scene, Marker
from .multitrack import MultiTrackEditor, Track, AudioClip, TrackType

__all__ = [
    'PodcastEditor',
    'ThreadManager',
    'get_thread_manager',
    'shutdown_thread_manager',
    'UITaskObserver',
    'TaskStatus',
    'TaskPriority',
    'TimelineEditor',
    'Scene',
    'Marker',
    'MultiTrackEditor',
    'Track',
    'AudioClip',
    'TrackType',
]
