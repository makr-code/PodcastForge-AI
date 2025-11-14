#!/usr/bin/env python3
"""
Timeline-Editor für PodcastForge
Canvas-basierter visueller Editor mit Drag&Drop
"""

import logging
import tkinter as tk
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Marker:
    """Timeline-Marker für Kapitel/Bookmarks"""

    id: str
    time: float
    label: str
    color: str = "#4a90e2"

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class Scene:
    """
    Einzelne Szene im Timeline

    Attributes:
        id: Eindeutige ID
        speaker: Sprecher-Name
        text: Gesprochener Text
        audio_file: Pfad zur Audio-Datei (optional)
        start_time: Start-Position in Sekunden
        duration: Dauer in Sekunden
        waveform_data: Wellenform-Daten (optional)
        color: Farbe für Visualisierung
    """

    id: str
    speaker: str
    text: str
    start_time: float
    duration: float = 1.0
    audio_file: Optional[Path] = None
    waveform_data: Optional[np.ndarray] = None
    color: str = "#569cd6"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def end_time(self) -> float:
        """Ende-Zeit der Szene"""
        return self.start_time + self.duration


class TimelineEditor(ttk.Frame):
    """
    Canvas-basierter Timeline-Editor

    Features:
    - Zoom In/Out (10s - 10min Ansicht)
    - Drag & Drop für Szenen
    - Visual Waveform-Anzeige
    - Szenen-Marker
    - Snap-to-Grid
    - Scrubbing (Audio-Position per Click)

    Architecture:
    - MVC-Pattern
    - Event-driven
    - Observer Pattern für Updates
    """

    # Constants
    TRACK_HEIGHT = 80
    HEADER_HEIGHT = 40
    MARKER_HEIGHT = 20
    MIN_ZOOM = 0.1  # 1px = 1s
    MAX_ZOOM = 100.0  # 1px = 0.01s
    SNAP_INTERVALS = [0.1, 0.5, 1.0]  # Snap-to-Grid intervals

    def __init__(
        self,
        parent,
        width: int = 1200,
        height: int = 300,
        on_scene_selected: Optional[Callable[[Scene], None]] = None,
        on_time_changed: Optional[Callable[[float], None]] = None,
    ):
        """
        Args:
            parent: Parent-Widget
            width: Canvas-Breite
            height: Canvas-Höhe
            on_scene_selected: Callback bei Szenen-Auswahl
            on_time_changed: Callback bei Zeit-Änderung
        """
        super().__init__(parent)

        self.width = width
        self.height = height
        self.on_scene_selected = on_scene_selected
        self.on_time_changed = on_time_changed

        # State
        self.scenes: List[Scene] = []
        self.markers: List[Marker] = []
        self.current_time: float = 0.0
        self.zoom_level: float = 10.0  # 1px = 0.1s (default)
        self.scroll_offset: float = 0.0
        self.selected_scene: Optional[Scene] = None
        self.dragging_scene: Optional[Scene] = None
        self.drag_start_x: Optional[int] = None
        self.snap_to_grid: bool = True
        self.snap_interval: float = 0.5  # 500ms

        # Colors
        self.colors = {
            "bg": "#1e1e1e",
            "grid": "#2d2d2d",
            "time_marker": "#4a90e2",
            "playhead": "#e74c3c",
            "selection": "#f39c12",
            "text": "#d4d4d4",
        }

        # UI Setup
        self._setup_ui()
        self._setup_bindings()

        logger.debug("TimelineEditor initialized")

    def _setup_ui(self):
        """Erstelle UI-Komponenten"""
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        # Playback Controls
        ttk.Button(toolbar, text="⏮️", width=3, command=self._goto_start).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="⏪", width=3, command=self._skip_backward).pack(
            side=tk.LEFT, padx=1
        )
        ttk.Button(toolbar, text="▶️", width=3, command=self._play).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="⏸️", width=3, command=self._pause).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="⏩", width=3, command=self._skip_forward).pack(
            side=tk.LEFT, padx=1
        )
        ttk.Button(toolbar, text="⏭️", width=3, command=self._goto_end).pack(side=tk.LEFT, padx=1)

        # Time Display
        self.time_label = ttk.Label(toolbar, text="00:00.0 / 00:00.0")
        self.time_label.pack(side=tk.LEFT, padx=10)

        # Zoom Controls
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="−", width=3, command=self._zoom_out).pack(side=tk.LEFT, padx=1)
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="+", width=3, command=self._zoom_in).pack(side=tk.LEFT, padx=1)

        # Snap-to-Grid Toggle
        self.snap_var = tk.BooleanVar(value=self.snap_to_grid)
        ttk.Checkbutton(
            toolbar, text="Snap", variable=self.snap_var, command=self._toggle_snap
        ).pack(side=tk.LEFT, padx=10)

        # Snap Interval
        ttk.Label(toolbar, text="Grid:").pack(side=tk.LEFT, padx=5)
        self.snap_combo = ttk.Combobox(
            toolbar, width=8, values=["0.1s", "0.5s", "1.0s"], state="readonly"
        )
        self.snap_combo.set("0.5s")
        self.snap_combo.bind("<<ComboboxSelected>>", self._on_snap_interval_changed)
        self.snap_combo.pack(side=tk.LEFT, padx=1)

        # Canvas mit Scrollbar
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.width,
            height=self.height,
            bg=self.colors["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Horizontal Scrollbar
        self.h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self._on_scroll
        )
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initial render
        self._render()

    def _setup_bindings(self):
        """Setup Event-Bindings"""
        # Mouse Events
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # Mouse Wheel für Zoom
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux scroll down

        # Keyboard
        self.canvas.bind("<space>", lambda e: self._play())
        self.canvas.bind("<Left>", lambda e: self._skip_backward())
        self.canvas.bind("<Right>", lambda e: self._skip_forward())
        self.canvas.bind("<Home>", lambda e: self._goto_start())
        self.canvas.bind("<End>", lambda e: self._goto_end())
        self.canvas.bind("<Delete>", lambda e: self._delete_selected())

        self.canvas.focus_set()

    def add_scene(self, scene: Scene, position: Optional[float] = None) -> Scene:
        """
        Füge Szene hinzu

        Args:
            scene: Scene-Objekt
            position: Position in Sekunden (None = ans Ende)

        Returns:
            Hinzugefügte Scene
        """
        if position is not None:
            scene.start_time = position
        else:
            # Ans Ende anfügen
            if self.scenes:
                last_scene = max(self.scenes, key=lambda s: s.end_time)
                scene.start_time = last_scene.end_time
            else:
                scene.start_time = 0.0

        self.scenes.append(scene)
        self._render()

        logger.debug(f"Scene added: {scene.id} at {scene.start_time}s")
        return scene

    def remove_scene(self, scene_id: str):
        """Entferne Szene"""
        self.scenes = [s for s in self.scenes if s.id != scene_id]
        if self.selected_scene and self.selected_scene.id == scene_id:
            self.selected_scene = None
        self._render()
        logger.debug(f"Scene removed: {scene_id}")

    def update_scene(self, scene: Scene):
        """Update Szene"""
        for i, s in enumerate(self.scenes):
            if s.id == scene.id:
                self.scenes[i] = scene
                break
        self._render()

    def add_marker(self, time: float, label: str) -> Marker:
        """
        Füge Marker hinzu

        Args:
            time: Zeit in Sekunden
            label: Marker-Label

        Returns:
            Marker-Objekt
        """
        marker = Marker(id=str(uuid.uuid4()), time=time, label=label)
        self.markers.append(marker)
        self._render()
        return marker

    def set_current_time(self, time: float):
        """Setze aktuelle Zeit"""
        self.current_time = max(0.0, time)
        self._update_time_display()
        self._render_playhead()

        if self.on_time_changed:
            self.on_time_changed(self.current_time)

    def _render(self):
        """Rendere gesamte Timeline"""
        self.canvas.delete("all")

        # Render Components
        self._render_grid()
        self._render_scenes()
        self._render_markers()
        self._render_playhead()

        # Update Scrollbar
        self._update_scrollbar()

    def _render_grid(self):
        """Rendere Zeit-Grid"""
        canvas_width = self.canvas.winfo_width() or self.width

        # Major gridlines (every second)
        major_interval = 1.0
        x = 0
        time = self.scroll_offset

        while x < canvas_width:
            x = int((time - self.scroll_offset) * self.zoom_level)

            if 0 <= x < canvas_width:
                # Gridline
                self.canvas.create_line(
                    x, 0, x, self.height, fill=self.colors["grid"], width=1, tags="grid"
                )

                # Time label
                time_str = self._format_time(time)
                self.canvas.create_text(
                    x,
                    5,
                    text=time_str,
                    fill=self.colors["text"],
                    anchor=tk.N,
                    font=("Arial", 8),
                    tags="grid",
                )

            time += major_interval

    def _render_scenes(self):
        """Rendere alle Szenen"""
        for scene in self.scenes:
            self._render_scene(scene)

    def _render_scene(self, scene: Scene):
        """Rendere einzelne Szene"""
        # Calculate position
        x1 = int((scene.start_time - self.scroll_offset) * self.zoom_level)
        x2 = int((scene.end_time - self.scroll_offset) * self.zoom_level)
        y1 = self.HEADER_HEIGHT
        y2 = y1 + self.TRACK_HEIGHT

        # Skip if outside visible area
        canvas_width = self.canvas.winfo_width() or self.width
        if x2 < 0 or x1 > canvas_width:
            return

        # Background
        fill_color = self.colors["selection"] if scene == self.selected_scene else scene.color
        rect_id = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=fill_color,
            outline="#ffffff",
            width=2 if scene == self.selected_scene else 1,
            tags=("scene", scene.id),
        )

        # Waveform (if available)
        if scene.waveform_data is not None:
            self._render_waveform(scene, x1, y1, x2 - x1, y2 - y1)

        # Text
        text_x = x1 + 5
        text_y = y1 + 5
        self.canvas.create_text(
            text_x,
            text_y,
            text=f"{scene.speaker}",
            fill="#ffffff",
            anchor=tk.NW,
            font=("Arial", 10, "bold"),
            tags=("scene", scene.id),
        )

        # Duration
        duration_str = self._format_time(scene.duration)
        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=duration_str,
            fill="#ffffff",
            font=("Arial", 9),
            tags=("scene", scene.id),
        )

    def _render_waveform(self, scene: Scene, x: int, y: int, width: int, height: int):
        """Rendere Wellenform innerhalb Szene"""
        if scene.waveform_data is None or len(scene.waveform_data) == 0:
            return

        # Resample waveform to fit width
        waveform = scene.waveform_data
        step = max(1, len(waveform) // width)
        samples = waveform[::step][:width]

        # Draw waveform
        center_y = y + height / 2
        for i, sample in enumerate(samples):
            sample_height = int(abs(sample) * height * 0.4)
            x_pos = x + i

            self.canvas.create_line(
                x_pos,
                center_y - sample_height,
                x_pos,
                center_y + sample_height,
                fill="#ffffff",
                width=1,
                tags="waveform",
            )

    def _render_markers(self):
        """Rendere Marker"""
        for marker in self.markers:
            x = int((marker.time - self.scroll_offset) * self.zoom_level)

            # Marker line
            self.canvas.create_line(
                x, 0, x, self.height, fill=marker.color, width=2, tags=("marker", marker.id)
            )

            # Marker label
            self.canvas.create_text(
                x + 3,
                self.MARKER_HEIGHT,
                text=marker.label,
                fill=marker.color,
                anchor=tk.W,
                font=("Arial", 9),
                tags=("marker", marker.id),
            )

    def _render_playhead(self):
        """Rendere Playhead (aktuelle Position)"""
        self.canvas.delete("playhead")

        x = int((self.current_time - self.scroll_offset) * self.zoom_level)

        self.canvas.create_line(
            x, 0, x, self.height, fill=self.colors["playhead"], width=3, tags="playhead"
        )

        # Triangle at top
        self.canvas.create_polygon(
            x - 5, 0, x + 5, 0, x, 10, fill=self.colors["playhead"], tags="playhead"
        )

    def _on_mouse_down(self, event):
        """Mouse-Down Event"""
        # Check if clicked on scene
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        for item in items:
            tags = self.canvas.gettags(item)
            if "scene" in tags:
                # Find scene
                for scene in self.scenes:
                    if scene.id in tags:
                        self.selected_scene = scene
                        self.dragging_scene = scene
                        self.drag_start_x = event.x

                        if self.on_scene_selected:
                            self.on_scene_selected(scene)

                        self._render()
                        return

        # Clicked on empty space - scrub to position
        time = self._x_to_time(event.x)
        self.set_current_time(time)
        self.selected_scene = None
        self._render()

    def _on_mouse_drag(self, event):
        """Mouse-Drag Event"""
        if self.dragging_scene and self.drag_start_x is not None:
            # Calculate new position
            dx = event.x - self.drag_start_x
            dt = dx / self.zoom_level

            new_start_time = self.dragging_scene.start_time + dt

            # Snap to grid
            if self.snap_to_grid:
                new_start_time = round(new_start_time / self.snap_interval) * self.snap_interval

            # Clamp to positive
            new_start_time = max(0.0, new_start_time)

            # Update scene
            self.dragging_scene.start_time = new_start_time
            self.drag_start_x = event.x

            self._render()

    def _on_mouse_up(self, event):
        """Mouse-Up Event"""
        self.dragging_scene = None
        self.drag_start_x = None

    def _on_double_click(self, event):
        """Double-Click Event"""
        # Add marker at position
        time = self._x_to_time(event.x)
        label = f"Marker {len(self.markers) + 1}"
        self.add_marker(time, label)

    def _on_mouse_wheel(self, event):
        """Mouse-Wheel Event (Zoom)"""
        if event.delta > 0 or event.num == 4:
            self._zoom_in()
        else:
            self._zoom_out()

    def _on_scroll(self, *args):
        """Scrollbar Event"""
        # TODO: Implement horizontal scrolling
        pass

    def _on_snap_interval_changed(self, event):
        """Snap-Interval ComboBox changed"""
        value = self.snap_combo.get()
        self.snap_interval = float(value[:-1])  # Remove 's'

    def _x_to_time(self, x: int) -> float:
        """Konvertiere X-Koordinate zu Zeit"""
        return (x / self.zoom_level) + self.scroll_offset

    def _time_to_x(self, time: float) -> int:
        """Konvertiere Zeit zu X-Koordinate"""
        return int((time - self.scroll_offset) * self.zoom_level)

    def _format_time(self, seconds: float) -> str:
        """Formatiere Zeit als MM:SS.s"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:04.1f}"

    def _update_time_display(self):
        """Update Zeit-Anzeige"""
        total_duration = max(s.end_time for s in self.scenes) if self.scenes else 0.0
        current = self._format_time(self.current_time)
        total = self._format_time(total_duration)
        self.time_label.config(text=f"{current} / {total}")

    def _update_scrollbar(self):
        """Update Scrollbar"""
        # TODO: Implement scrollbar update
        pass

    def _zoom_in(self):
        """Zoom In"""
        self.zoom_level = min(self.zoom_level * 1.5, self.MAX_ZOOM)
        self.zoom_label.config(text=f"{int(self.zoom_level * 10)}%")
        self._render()

    def _zoom_out(self):
        """Zoom Out"""
        self.zoom_level = max(self.zoom_level / 1.5, self.MIN_ZOOM)
        self.zoom_label.config(text=f"{int(self.zoom_level * 10)}%")
        self._render()

    def _toggle_snap(self):
        """Toggle Snap-to-Grid"""
        self.snap_to_grid = self.snap_var.get()

    def _play(self):
        """Play/Resume"""
        # TODO: Implement playback
        logger.info("Play")

    def _pause(self):
        """Pause"""
        # TODO: Implement pause
        logger.info("Pause")

    def _goto_start(self):
        """Gehe zum Start"""
        self.set_current_time(0.0)

    def _goto_end(self):
        """Gehe zum Ende"""
        if self.scenes:
            end_time = max(s.end_time for s in self.scenes)
            self.set_current_time(end_time)

    def _skip_forward(self):
        """Skip 5s vorwärts"""
        self.set_current_time(self.current_time + 5.0)

    def _skip_backward(self):
        """Skip 5s rückwärts"""
        self.set_current_time(self.current_time - 5.0)

    def _delete_selected(self):
        """Lösche ausgewählte Szene"""
        if self.selected_scene:
            self.remove_scene(self.selected_scene.id)

    def get_total_duration(self) -> float:
        """Hole Gesamt-Dauer"""
        if not self.scenes:
            return 0.0
        return max(s.end_time for s in self.scenes)

    def export_scenes(self) -> List[Scene]:
        """Exportiere Szenen sortiert nach Zeit"""
        return sorted(self.scenes, key=lambda s: s.start_time)
