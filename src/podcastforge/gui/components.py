"""
Wiederverwendbare GUI-Komponenten für PodcastForge

Enthält eine kleine `StatusBar`-Klasse und `apply_theme`-Hilfsfunktion,
die in mehreren Fenstern verwendet werden können.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk | tk.Toplevel | tk.Widget) -> None:
    """Apply a lightweight theme and common colors to a root widget.

    This centralizes theme configuration so multiple windows share the same
    look without duplicating code.
    """
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        # fallback to default theme if 'clam' isn't available
        pass

    # Basic color palette (kept minimal so tests/headless envs are fine)
    colors = {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "accent": "#4a90e2",
        "editor_bg": "#1e1e1e",
        "editor_fg": "#d4d4d4",
    }

    try:
        root.configure(bg=colors["bg"])
    except Exception:
        # some widget roots may not support configure(bg=...)
        pass

    # expose colors for callers
    if not hasattr(root, "theme_colors"):
        try:
            setattr(root, "theme_colors", colors)
        except Exception:
            # ignore if attribute cannot be set
            pass


class StatusBar(ttk.Frame):
    """Simple status bar with a single left-aligned label.

    Usage:
        sb = StatusBar(parent)
        sb.pack(side=tk.BOTTOM, fill=tk.X)
        sb.set("Ready")
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._label = ttk.Label(self, text="Ready")
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=2)

        # progressbar (hidden by default)
        self._progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=180, mode="determinate")
        self._progress.pack(side=tk.RIGHT, padx=6)
        self._progress['value'] = 0
        try:
            # hide by default
            self._progress.pack_forget()
        except Exception:
            pass

    def set(self, text: str) -> None:
        try:
            self._label.config(text=text)
        except Exception:
            # ignore errors from destroyed widgets
            pass

    def set_progress(self, percent: int | float | None) -> None:
        """Set progress bar percentage (0-100). Pass `None` to hide the bar."""
        try:
            if percent is None:
                try:
                    self._progress.pack_forget()
                except Exception:
                    pass
                return

            pct = max(0, min(100, int(percent)))
            # show if not packed
            try:
                if not self._progress.winfo_ismapped():
                    self._progress.pack(side=tk.RIGHT, padx=6)
            except Exception:
                pass

            self._progress['value'] = pct
            if pct >= 100:
                # auto-hide after a short delay - leave to caller to clear
                pass
        except Exception:
            pass
