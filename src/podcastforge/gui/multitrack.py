#!/usr/bin/env python3
"""
Multi-Track Audio-Editor für PodcastForge
Professioneller Audio-Mixer mit Tracks für Voice, Music, SFX
"""

import logging
import tkinter as tk
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class TrackType(Enum):
    """Track-Typen"""

    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"  # Sound Effects
    MASTER = "master"


@dataclass
class AudioClip:
    """
    Audio-Clip auf Track

    Attributes:
        id: Eindeutige ID
        file: Pfad zur Audio-Datei
        start_time: Start-Position in Sekunden
        duration: Dauer in Sekunden
        volume: Lautstärke (0.0-1.0)
        fade_in: Fade-In Dauer in Sekunden
        fade_out: Fade-Out Dauer in Sekunden
    """

    id: str
    file: Path
    start_time: float
    duration: float
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    muted: bool = False
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def end_time(self) -> float:
        """Ende-Zeit des Clips"""
        return self.start_time + self.duration


@dataclass
class Track:
    """
    Audio-Track

    Attributes:
        id: Eindeutige ID
        name: Track-Name
        type: Track-Typ
        clips: Audio-Clips auf diesem Track
        volume: Track-Lautstärke (0.0-1.0)
        pan: Stereo-Pan (-1.0 links, 0.0 center, 1.0 rechts)
        muted: Track stummgeschaltet
        solo: Track solo (nur dieser hörbar)
    """

    id: str
    name: str
    type: TrackType
    clips: List[AudioClip] = field(default_factory=list)
    volume: float = 1.0
    pan: float = 0.0
    muted: bool = False
    solo: bool = False
    color: str = "#569cd6"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_clip(self, clip: AudioClip):
        """Füge Clip hinzu"""
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start_time)

    def remove_clip(self, clip_id: str):
        """Entferne Clip"""
        self.clips = [c for c in self.clips if c.id != clip_id]

    def get_duration(self) -> float:
        """Hole Track-Dauer"""
        if not self.clips:
            return 0.0
        return max(c.end_time for c in self.clips)


class MultiTrackEditor(ttk.Frame):
    """
    Multi-Track Audio-Editor

    Features:
    - Mehrere Tracks (Voice, Music, SFX)
    - Volume-Mixer für jeden Track
    - Drag & Drop Clips
    - Fade In/Out
    - Solo/Mute
    - Export zu finaler Audio-Datei

    UI-Layout:
    ┌─────────────────────────────────────────────┐
    │ Track 1 (Voice)  : [████████████████]       │
    │ 🔊 ▓▓▓▓▓░░░░ 80%  [M] [S]                   │
    │ Track 2 (Music)  : [░░░░░░░░░░░░░░░░]  -6dB │
    │ 🔊 ▓▓▓░░░░░░ 60%  [M] [S]                   │
    │ Track 3 (SFX)    : [  ███    ███    ]  -12dB│
    │ 🔊 ▓▓░░░░░░░ 40%  [M] [S]                   │
    └─────────────────────────────────────────────┘
    """

    TRACK_HEIGHT = 100
    CLIP_HEIGHT = 60
    MIXER_WIDTH = 200

    # Track Colors
    TRACK_COLORS = {
        TrackType.VOICE: "#569cd6",
        TrackType.MUSIC: "#4ec9b0",
        TrackType.SFX: "#ce9178",
        TrackType.MASTER: "#c586c0",
    }

    def __init__(self, parent, width: int = 1200, height: int = 600):
        """
        Args:
            parent: Parent-Widget
            width: Editor-Breite
            height: Editor-Höhe
        """
        super().__init__(parent)

        self.width = width
        self.height = height

        # State
        self.tracks: List[Track] = []
        self.selected_clip: Optional[AudioClip] = None
        self.current_time: float = 0.0
        self.zoom_level: float = 10.0

        # Setup UI
        self._setup_ui()

        # Add default tracks
        self._add_default_tracks()

        logger.debug("MultiTrackEditor initialized")

    def _setup_ui(self):
        """Erstelle UI-Komponenten"""
        # Main Layout: Mixer | Timeline
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Mixer Panel (links)
        mixer_frame = ttk.Frame(main_paned, width=self.MIXER_WIDTH)
        main_paned.add(mixer_frame, weight=0)

        self.mixer_panel = self._create_mixer_panel(mixer_frame)

        # Timeline Panel (rechts)
        timeline_frame = ttk.Frame(main_paned)
        main_paned.add(timeline_frame, weight=1)

        self.timeline_canvas = self._create_timeline_canvas(timeline_frame)

        # Toolbar
        self._create_toolbar()

    def _create_toolbar(self):
        """Erstelle Toolbar"""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add Track
        ttk.Button(
            toolbar,
            text="➕ Voice Track",
            command=lambda: self.add_track("Voice Track", TrackType.VOICE),
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🎵 Music Track",
            command=lambda: self.add_track("Music Track", TrackType.MUSIC),
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar, text="🔊 SFX Track", command=lambda: self.add_track("SFX Track", TrackType.SFX)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Import Clip
        ttk.Button(toolbar, text="📁 Import Clip", command=self.import_clip).pack(
            side=tk.LEFT, padx=2
        )

        # Export
        ttk.Button(toolbar, text="💾 Export Audio", command=self.export_audio).pack(
            side=tk.LEFT, padx=2
        )

    def _create_mixer_panel(self, parent) -> ttk.Frame:
        """Erstelle Mixer-Panel"""
        mixer_frame = ttk.Frame(parent)
        mixer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(mixer_frame, text="MIXER", font=("Arial", 12, "bold")).pack(side=tk.TOP, pady=5)

        # Scrollable mixer
        mixer_canvas = tk.Canvas(mixer_frame, width=self.MIXER_WIDTH)
        mixer_scrollbar = ttk.Scrollbar(mixer_frame, orient=tk.VERTICAL, command=mixer_canvas.yview)

        self.mixer_inner = ttk.Frame(mixer_canvas)

        mixer_canvas.create_window((0, 0), window=self.mixer_inner, anchor=tk.NW)
        mixer_canvas.configure(yscrollcommand=mixer_scrollbar.set)

        mixer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mixer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return mixer_frame

    def _create_timeline_canvas(self, parent) -> tk.Canvas:
        """Erstelle Timeline-Canvas"""
        canvas = tk.Canvas(parent, bg="#1e1e1e", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Bindings
        canvas.bind("<Button-1>", self._on_timeline_click)
        canvas.bind("<B1-Motion>", self._on_timeline_drag)
        canvas.bind("<Double-Button-1>", self._on_timeline_double_click)

        return canvas

    def _add_default_tracks(self):
        """Füge Standard-Tracks hinzu"""
        self.add_track("Voice", TrackType.VOICE)
        self.add_track("Music", TrackType.MUSIC)
        self.add_track("Sound Effects", TrackType.SFX)

    def add_track(self, name: str, track_type: TrackType) -> Track:
        """
        Füge neuen Track hinzu

        Args:
            name: Track-Name
            track_type: Track-Typ

        Returns:
            Track
        """
        track = Track(
            id=str(uuid.uuid4()),
            name=name,
            type=track_type,
            color=self.TRACK_COLORS.get(track_type, "#569cd6"),
        )

        self.tracks.append(track)

        # Add mixer controls
        self._add_mixer_strip(track)

        # Render
        self._render_timeline()

        logger.info(f"Track added: {name} ({track_type.value})")
        return track

    def remove_track(self, track_id: str):
        """Entferne Track"""
        self.tracks = [t for t in self.tracks if t.id != track_id]
        self._rebuild_mixer()
        self._render_timeline()
        logger.info(f"Track removed: {track_id}")

    def _add_mixer_strip(self, track: Track):
        """Füge Mixer-Strip für Track hinzu"""
        strip_frame = ttk.LabelFrame(self.mixer_inner, text=track.name, padding=5)
        strip_frame.pack(fill=tk.X, pady=5)

        # Volume Slider
        volume_frame = ttk.Frame(strip_frame)
        volume_frame.pack(fill=tk.X, pady=2)

        ttk.Label(volume_frame, text="🔊").pack(side=tk.LEFT)

        volume_var = tk.DoubleVar(value=track.volume * 100)
        volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=volume_var,
            command=lambda v: self._on_volume_changed(track.id, float(v)),
        )
        volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        volume_label = ttk.Label(volume_frame, text="100%", width=5)
        volume_label.pack(side=tk.LEFT)

        # Pan Slider
        pan_frame = ttk.Frame(strip_frame)
        pan_frame.pack(fill=tk.X, pady=2)

        ttk.Label(pan_frame, text="L").pack(side=tk.LEFT)

        pan_var = tk.DoubleVar(value=(track.pan + 1.0) * 50)  # -1..1 -> 0..100
        pan_slider = ttk.Scale(
            pan_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=pan_var,
            command=lambda v: self._on_pan_changed(track.id, float(v)),
        )
        pan_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(pan_frame, text="R").pack(side=tk.LEFT)

        # Mute/Solo Buttons
        control_frame = ttk.Frame(strip_frame)
        control_frame.pack(fill=tk.X, pady=2)

        mute_btn = ttk.Button(
            control_frame, text="M", width=3, command=lambda: self._toggle_mute(track.id)
        )
        mute_btn.pack(side=tk.LEFT, padx=2)

        solo_btn = ttk.Button(
            control_frame, text="S", width=3, command=lambda: self._toggle_solo(track.id)
        )
        solo_btn.pack(side=tk.LEFT, padx=2)

        # Store references
        track.metadata["mixer_frame"] = strip_frame
        track.metadata["volume_var"] = volume_var
        track.metadata["volume_label"] = volume_label
        track.metadata["pan_var"] = pan_var
        track.metadata["mute_btn"] = mute_btn
        track.metadata["solo_btn"] = solo_btn

    def _rebuild_mixer(self):
        """Rebuild Mixer-Panel"""
        # Clear
        for widget in self.mixer_inner.winfo_children():
            widget.destroy()

        # Rebuild
        for track in self.tracks:
            self._add_mixer_strip(track)

    def _render_timeline(self):
        """Rendere Timeline"""
        self.timeline_canvas.delete("all")

        # Render tracks
        y = 0
        for track in self.tracks:
            self._render_track(track, y)
            y += self.TRACK_HEIGHT

        # Update canvas scroll region
        self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox("all"))

    def _render_track(self, track: Track, y: int):
        """Rendere einzelnen Track"""
        canvas_width = self.timeline_canvas.winfo_width() or self.width

        # Track background
        self.timeline_canvas.create_rectangle(
            0,
            y,
            canvas_width,
            y + self.TRACK_HEIGHT,
            fill="#2d2d2d",
            outline="#3d3d3d",
            tags=("track", track.id),
        )

        # Track label
        self.timeline_canvas.create_text(
            5,
            y + 5,
            text=track.name,
            fill="#ffffff",
            anchor=tk.NW,
            font=("Arial", 10, "bold"),
            tags=("track", track.id),
        )

        # Render clips
        for clip in track.clips:
            self._render_clip(clip, track, y)

    def _render_clip(self, clip: AudioClip, track: Track, track_y: int):
        """Rendere Clip auf Track"""
        x1 = int(clip.start_time * self.zoom_level)
        x2 = int(clip.end_time * self.zoom_level)
        y1 = track_y + (self.TRACK_HEIGHT - self.CLIP_HEIGHT) // 2
        y2 = y1 + self.CLIP_HEIGHT

        # Clip background
        fill_color = track.color if not clip.muted else "#555555"
        self.timeline_canvas.create_rectangle(
            x1, y1, x2, y2, fill=fill_color, outline="#ffffff", width=2, tags=("clip", clip.id)
        )

        # Clip label
        self.timeline_canvas.create_text(
            x1 + 5,
            y1 + 5,
            text=clip.file.name,
            fill="#ffffff",
            anchor=tk.NW,
            font=("Arial", 9),
            tags=("clip", clip.id),
        )

        # Fade indicators
        if clip.fade_in > 0:
            fade_in_x = x1 + int(clip.fade_in * self.zoom_level)
            self.timeline_canvas.create_line(
                x1, y2, fade_in_x, y1, fill="#ffffff", width=2, tags=("clip", clip.id)
            )

        if clip.fade_out > 0:
            fade_out_x = x2 - int(clip.fade_out * self.zoom_level)
            self.timeline_canvas.create_line(
                fade_out_x, y1, x2, y2, fill="#ffffff", width=2, tags=("clip", clip.id)
            )

    def import_clip(self):
        """Importiere Audio-Clip"""
        file_path = filedialog.askopenfilename(
            title="Import Audio Clip",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac"), ("All Files", "*.*")],
        )

        if not file_path:
            return

        # Select track
        # TODO: Show track selection dialog
        if not self.tracks:
            logger.warning("No tracks available")
            return

        track = self.tracks[0]

        # Create clip
        clip = AudioClip(
            id=str(uuid.uuid4()),
            file=Path(file_path),
            start_time=0.0,
            duration=10.0,  # TODO: Get actual duration
        )

        track.add_clip(clip)
        self._render_timeline()

        logger.info(f"Clip imported: {file_path}")

    def export_audio(self):
        """Exportiere gemischtes Audio"""
        output_file = filedialog.asksaveasfilename(
            title="Export Audio",
            defaultextension=".wav",
            filetypes=[("WAV Files", "*.wav"), ("MP3 Files", "*.mp3"), ("All Files", "*.*")],
        )

        if not output_file:
            return

        try:
            # TODO: Implement audio mixing and export
            logger.info(f"Exporting to: {output_file}")

            # Placeholder implementation
            from tkinter import messagebox

            messagebox.showinfo("Export", "Export functionality coming soon!")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            from tkinter import messagebox

            messagebox.showerror("Error", f"Export failed: {e}")

    def _on_volume_changed(self, track_id: str, value: float):
        """Volume-Slider geändert"""
        track = next((t for t in self.tracks if t.id == track_id), None)
        if track:
            track.volume = value / 100.0
            volume_label = track.metadata.get("volume_label")
            if volume_label:
                db = 20 * np.log10(track.volume) if track.volume > 0 else -np.inf
                volume_label.config(text=f"{int(value)}%")

    def _on_pan_changed(self, track_id: str, value: float):
        """Pan-Slider geändert"""
        track = next((t for t in self.tracks if t.id == track_id), None)
        if track:
            track.pan = (value / 50.0) - 1.0  # 0..100 -> -1..1

    def _toggle_mute(self, track_id: str):
        """Toggle Track Mute"""
        track = next((t for t in self.tracks if t.id == track_id), None)
        if track:
            track.muted = not track.muted
            self._render_timeline()
            logger.debug(f"Track {track.name} muted: {track.muted}")

    def _toggle_solo(self, track_id: str):
        """Toggle Track Solo"""
        track = next((t for t in self.tracks if t.id == track_id), None)
        if track:
            track.solo = not track.solo
            logger.debug(f"Track {track.name} solo: {track.solo}")

    def _on_timeline_click(self, event):
        """Timeline Click"""
        # TODO: Implement clip selection
        pass

    def _on_timeline_drag(self, event):
        """Timeline Drag"""
        # TODO: Implement clip dragging
        pass

    def _on_timeline_double_click(self, event):
        """Timeline Double-Click"""
        # TODO: Implement clip editing
        pass
