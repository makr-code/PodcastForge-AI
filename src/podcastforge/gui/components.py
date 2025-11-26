"""
Wiederverwendbare GUI-Komponenten für PodcastForge

Enthält verbesserte UI-Komponenten:
- `StatusBar` - Statusleiste mit Fortschrittsanzeige
- `apply_theme` - Zentralisierte Theme-Konfiguration
- `Tooltip` - Kontextuelle Tooltips für Widgets
- `WelcomePanel` - Willkommens-/Schnellstart-Panel für neue Benutzer
- `IconButton` - Button mit Emoji-Icon
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


# =============================================================================
# Theme-Konfiguration
# =============================================================================

# Verfügbare Themes mit Farbpaletten
THEMES = {
    "dark": {
        "name": "Dunkel",
        "bg": "#2b2b2b",
        "bg_secondary": "#333333",
        "fg": "#ffffff",
        "fg_secondary": "#b0b0b0",
        "accent": "#4a90e2",
        "accent_hover": "#5ba0f2",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "editor_bg": "#1e1e1e",
        "editor_fg": "#d4d4d4",
        "editor_line_bg": "#252526",
        "editor_selection": "#264f78",
        "border": "#3c3c3c",
    },
    "light": {
        "name": "Hell",
        "bg": "#f5f5f5",
        "bg_secondary": "#ffffff",
        "fg": "#212121",
        "fg_secondary": "#757575",
        "accent": "#1976d2",
        "accent_hover": "#1565c0",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "editor_bg": "#ffffff",
        "editor_fg": "#333333",
        "editor_line_bg": "#f0f0f0",
        "editor_selection": "#b3d9ff",
        "border": "#e0e0e0",
    },
    "blue": {
        "name": "Blau",
        "bg": "#1a237e",
        "bg_secondary": "#283593",
        "fg": "#ffffff",
        "fg_secondary": "#c5cae9",
        "accent": "#448aff",
        "accent_hover": "#82b1ff",
        "success": "#69f0ae",
        "warning": "#ffd740",
        "error": "#ff5252",
        "editor_bg": "#0d1b2a",
        "editor_fg": "#e0e0e0",
        "editor_line_bg": "#1b2838",
        "editor_selection": "#3949ab",
        "border": "#3f51b5",
    },
}

# Standard-Theme
DEFAULT_THEME = "dark"


def get_theme_colors(theme_name: str = None) -> dict:
    """Hole Farbpalette für ein Theme."""
    if theme_name is None:
        theme_name = DEFAULT_THEME
    return THEMES.get(theme_name, THEMES[DEFAULT_THEME]).copy()


def apply_theme(root: tk.Tk | tk.Toplevel | tk.Widget, theme_name: str = None) -> None:
    """Apply a theme with colors to a root widget.

    This centralizes theme configuration so multiple windows share the same
    look without duplicating code.
    """
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        # fallback to default theme if 'clam' isn't available
        pass

    colors = get_theme_colors(theme_name)

    try:
        root.configure(bg=colors["bg"])
    except Exception:
        # some widget roots may not support configure(bg=...)
        pass

    # Configure ttk styles
    try:
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TButton", padding=6)
        style.configure("Accent.TButton", background=colors["accent"])
        style.configure("TLabelframe", background=colors["bg"])
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])
        style.configure("TNotebook", background=colors["bg"])
        style.configure("TNotebook.Tab", padding=[12, 4])
    except Exception:
        pass

    # expose colors for callers
    if not hasattr(root, "theme_colors"):
        try:
            setattr(root, "theme_colors", colors)
        except Exception:
            # ignore if attribute cannot be set
            pass


# =============================================================================
# Tooltip-Klasse
# =============================================================================

class Tooltip:
    """Einfacher Tooltip für Widgets.
    
    Usage:
        btn = ttk.Button(parent, text="Save")
        Tooltip(btn, "Speichert das aktuelle Projekt (Ctrl+S)")
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None

        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event=None):
        self._schedule_show()

    def _on_leave(self, event=None):
        self._cancel_schedule()
        self._hide()

    def _schedule_show(self):
        self._cancel_schedule()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel_schedule(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self.tooltip_window:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Tooltip-Styling
        frame = tk.Frame(
            self.tooltip_window,
            bg="#333333",
            highlightbackground="#555555",
            highlightthickness=1,
        )
        frame.pack()

        label = tk.Label(
            frame,
            text=self.text,
            bg="#333333",
            fg="#ffffff",
            padx=8,
            pady=4,
            font=("TkDefaultFont", 9),
        )
        label.pack()

    def _hide(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# =============================================================================
# Icon-Button
# =============================================================================

class IconButton(ttk.Button):
    """Button mit Emoji-Icon und optionalem Tooltip.
    
    Usage:
        btn = IconButton(parent, icon="▶️", text="Play", tooltip="Audio abspielen")
        btn.pack()
    """

    def __init__(
        self,
        parent,
        icon: str = "",
        text: str = "",
        tooltip: str = None,
        command: Callable = None,
        **kwargs
    ):
        display_text = f"{icon} {text}".strip() if icon else text
        super().__init__(parent, text=display_text, command=command, **kwargs)
        
        if tooltip:
            Tooltip(self, tooltip)


# =============================================================================
# StatusBar (verbessert)
# =============================================================================

class StatusBar(ttk.Frame):
    """Verbesserte Statusleiste mit mehreren Bereichen.

    Features:
    - Linker Bereich: Statusmeldungen
    - Mittlerer Bereich: Zusatzinformationen
    - Rechter Bereich: Fortschrittsanzeige

    Usage:
        sb = StatusBar(parent)
        sb.pack(side=tk.BOTTOM, fill=tk.X)
        sb.set("Ready")
        sb.set_info("21 Stimmen | 8 Stile")
        sb.set_progress(50)
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Linker Bereich: Hauptstatus
        self._label = ttk.Label(self, text="Bereit")
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=2)

        # Separator
        sep = ttk.Separator(self, orient=tk.VERTICAL)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=2)

        # Mittlerer Bereich: Info
        self._info_label = ttk.Label(self, text="", foreground="#888888")
        self._info_label.pack(side=tk.LEFT, padx=8, pady=2)

        # Rechter Bereich: Fortschrittsanzeige
        self._progress = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, length=150, mode="determinate"
        )
        self._progress.pack(side=tk.RIGHT, padx=6, pady=2)
        self._progress['value'] = 0
        try:
            self._progress.pack_forget()
        except Exception:
            pass

        # Prozentanzeige
        self._percent_label = ttk.Label(self, text="")
        self._percent_label.pack(side=tk.RIGHT, padx=2, pady=2)

    def set(self, text: str) -> None:
        """Setzt den Hauptstatus-Text."""
        try:
            self._label.config(text=text)
        except Exception:
            pass

    def set_info(self, text: str) -> None:
        """Setzt den Info-Text im mittleren Bereich."""
        try:
            self._info_label.config(text=text)
        except Exception:
            pass

    def set_progress(self, percent: int | float | None) -> None:
        """Set progress bar percentage (0-100). Pass `None` to hide."""
        try:
            if percent is None:
                try:
                    self._progress.pack_forget()
                    self._percent_label.config(text="")
                except Exception:
                    pass
                return

            pct = max(0, min(100, int(percent)))
            
            # Show if not packed
            try:
                if not self._progress.winfo_ismapped():
                    self._progress.pack(side=tk.RIGHT, padx=6, pady=2)
            except Exception:
                pass

            self._progress['value'] = pct
            self._percent_label.config(text=f"{pct}%")

            if pct >= 100:
                # Auto-hide after completion (caller can clear)
                pass
        except Exception:
            pass


# =============================================================================
# Welcome Panel
# =============================================================================

class WelcomePanel(ttk.Frame):
    """Willkommens-Panel mit Schnellstart-Aktionen.
    
    Zeigt eine übersichtliche Startseite mit häufigen Aktionen.
    
    Usage:
        panel = WelcomePanel(parent, on_new=new_func, on_open=open_func)
        panel.pack(fill=tk.BOTH, expand=True)
    """

    def __init__(
        self,
        parent,
        on_new: Callable = None,
        on_open: Callable = None,
        on_wizard: Callable = None,
        on_recent: Callable = None,
        recent_files: list = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_new = on_new
        self.on_open = on_open
        self.on_wizard = on_wizard
        self.on_recent = on_recent
        self.recent_files = recent_files or []

        self._create_ui()

    def _create_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(20, 10))

        title = ttk.Label(
            header,
            text="🎙️ PodcastForge AI",
            font=("TkDefaultFont", 24, "bold"),
        )
        title.pack()

        subtitle = ttk.Label(
            header,
            text="Professioneller Podcast-Editor mit KI-Unterstützung",
            font=("TkDefaultFont", 11),
        )
        subtitle.pack(pady=5)

        # Separator
        sep = ttk.Separator(self, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=10, padx=40)

        # Quick Actions
        actions_frame = ttk.Frame(self)
        actions_frame.pack(pady=20)

        ttk.Label(
            actions_frame,
            text="🚀 Schnellstart",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(pady=(0, 15))

        # Action Buttons
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack()

        if self.on_new:
            btn_new = IconButton(
                btn_frame,
                icon="📄",
                text="Neues Projekt",
                tooltip="Erstellt ein neues leeres Podcast-Projekt",
                command=self.on_new,
                width=20,
            )
            btn_new.pack(pady=5)

        if self.on_open:
            btn_open = IconButton(
                btn_frame,
                icon="📂",
                text="Projekt öffnen",
                tooltip="Öffnet ein bestehendes Projekt",
                command=self.on_open,
                width=20,
            )
            btn_open.pack(pady=5)

        if self.on_wizard:
            btn_wizard = IconButton(
                btn_frame,
                icon="🧙",
                text="Assistent starten",
                tooltip="Interaktiver Schritt-für-Schritt-Assistent",
                command=self.on_wizard,
                width=20,
            )
            btn_wizard.pack(pady=5)

        # Recent Files (if any)
        if self.recent_files and self.on_recent:
            recent_frame = ttk.LabelFrame(self, text="📋 Zuletzt geöffnet", padding=10)
            recent_frame.pack(pady=20, padx=40, fill=tk.X)

            for filepath in self.recent_files[:5]:
                btn = ttk.Button(
                    recent_frame,
                    text=f"  {filepath}",
                    command=lambda p=filepath: self.on_recent(p),
                )
                btn.pack(fill=tk.X, pady=2)

        # Tips
        tips_frame = ttk.LabelFrame(self, text="💡 Tipps", padding=10)
        tips_frame.pack(pady=10, padx=40, fill=tk.X)

        tips = [
            "Drücke F5 um eine Zeile vorzuhören",
            "Verwende Ctrl+S zum Speichern",
            "Im CLI: 'podcastforge wizard' für den Assistenten",
        ]

        for tip in tips:
            ttk.Label(tips_frame, text=f"• {tip}").pack(anchor=tk.W, pady=2)


# =============================================================================
# Quick Action Bar
# =============================================================================

class QuickActionBar(ttk.Frame):
    """Schnellzugriffs-Leiste mit häufig genutzten Aktionen.
    
    Usage:
        bar = QuickActionBar(parent)
        bar.add_action("▶️", "Play", play_func, "Audio abspielen (F5)")
        bar.pack(fill=tk.X)
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._buttons = []

    def add_action(
        self,
        icon: str,
        text: str,
        command: Callable,
        tooltip: str = None,
    ) -> IconButton:
        """Fügt eine Aktion zur Leiste hinzu."""
        btn = IconButton(
            self,
            icon=icon,
            text=text,
            command=command,
            tooltip=tooltip,
        )
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        self._buttons.append(btn)
        return btn

    def add_separator(self):
        """Fügt einen Trenner hinzu."""
        sep = ttk.Separator(self, orient=tk.VERTICAL)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)


# =============================================================================
# Voice Preview Card
# =============================================================================

class VoiceCard(ttk.Frame):
    """Karte zur Anzeige einer Stimme mit Preview-Button.
    
    Usage:
        card = VoiceCard(parent, voice_name="Anna", voice_style="Professional")
        card.pack()
    """

    def __init__(
        self,
        parent,
        voice_id: str,
        voice_name: str,
        voice_style: str = "",
        voice_language: str = "de",
        on_preview: Callable = None,
        on_select: Callable = None,
        **kwargs
    ):
        super().__init__(parent, relief=tk.RAISED, padding=8, **kwargs)

        self.voice_id = voice_id
        self.on_preview = on_preview
        self.on_select = on_select

        # Voice Info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X)

        # Name
        name_label = ttk.Label(
            info_frame,
            text=voice_name,
            font=("TkDefaultFont", 11, "bold"),
        )
        name_label.pack(anchor=tk.W)

        # Style & Language
        meta = f"{voice_style} • {voice_language.upper()}"
        meta_label = ttk.Label(
            info_frame,
            text=meta,
            foreground="#888888",
        )
        meta_label.pack(anchor=tk.W)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        if on_preview:
            preview_btn = IconButton(
                btn_frame,
                icon="▶️",
                text="Preview",
                tooltip="Stimme anhören",
                command=lambda: on_preview(voice_id),
            )
            preview_btn.pack(side=tk.LEFT, padx=2)

        if on_select:
            select_btn = IconButton(
                btn_frame,
                icon="✓",
                text="Wählen",
                tooltip="Diese Stimme verwenden",
                command=lambda: on_select(voice_id),
            )
            select_btn.pack(side=tk.LEFT, padx=2)

