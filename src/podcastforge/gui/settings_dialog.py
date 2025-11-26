"""
Settings dialog for PodcastForge GUI.

Allows editing persisted UI settings (theme, editor font size, last project).
Enhanced with multiple tabs and more options.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog

from ..core.settings import get_setting, set_setting
from .components import THEMES


class SettingsDialog(simpledialog.Dialog):
    """Modal settings dialog with tabs for different setting categories.

    Usage:
        dlg = SettingsDialog(parent)
        if dlg.result: # dict of settings saved
            ...
    """

    def body(self, master):
        self.title("⚙️ Einstellungen")
        self.geometry("450x400")

        # Create notebook for tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Tab 1: Appearance
        self._create_appearance_tab()

        # Tab 2: Editor
        self._create_editor_tab()

        # Tab 3: Audio/TTS
        self._create_audio_tab()

        # Tab 4: Advanced
        self._create_advanced_tab()

        return self.notebook

    def _create_appearance_tab(self):
        """Tab für Erscheinungsbild-Einstellungen."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="🎨 Erscheinung")

        # Theme selection
        ttk.Label(frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.theme_var = tk.StringVar(value=get_setting("ui.theme", "dark"))
        theme_frame = ttk.Frame(frame)
        theme_frame.grid(row=0, column=1, sticky=tk.W, pady=8)

        for theme_id, theme_data in THEMES.items():
            rb = ttk.Radiobutton(
                theme_frame,
                text=theme_data["name"],
                variable=self.theme_var,
                value=theme_id,
            )
            rb.pack(side=tk.LEFT, padx=8)

        # Window size
        ttk.Label(frame, text="Fenstergröße:").grid(row=1, column=0, sticky=tk.W, pady=8)
        size_frame = ttk.Frame(frame)
        size_frame.grid(row=1, column=1, sticky=tk.W, pady=8)

        self.width_var = tk.IntVar(value=int(get_setting("ui.window_width", 1400)))
        self.height_var = tk.IntVar(value=int(get_setting("ui.window_height", 900)))

        ttk.Entry(size_frame, textvariable=self.width_var, width=6).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=" x ").pack(side=tk.LEFT)
        ttk.Entry(size_frame, textvariable=self.height_var, width=6).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=" px").pack(side=tk.LEFT)

        # Show welcome screen
        ttk.Label(frame, text="Willkommensbildschirm:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.welcome_var = tk.BooleanVar(value=get_setting("ui.show_welcome", True))
        ttk.Checkbutton(
            frame,
            text="Beim Start anzeigen",
            variable=self.welcome_var,
        ).grid(row=2, column=1, sticky=tk.W, pady=8)

        # Show tooltips
        ttk.Label(frame, text="Tooltips:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.tooltips_var = tk.BooleanVar(value=get_setting("ui.show_tooltips", True))
        ttk.Checkbutton(
            frame,
            text="Tooltips anzeigen",
            variable=self.tooltips_var,
        ).grid(row=3, column=1, sticky=tk.W, pady=8)

        frame.columnconfigure(1, weight=1)

    def _create_editor_tab(self):
        """Tab für Editor-Einstellungen."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="📝 Editor")

        # Font size
        ttk.Label(frame, text="Schriftgröße:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.font_var = tk.IntVar(value=int(get_setting("ui.editor_font_size", 11)))
        font_frame = ttk.Frame(frame)
        font_frame.grid(row=0, column=1, sticky=tk.W, pady=8)
        ttk.Spinbox(font_frame, from_=8, to=28, textvariable=self.font_var, width=5).pack(side=tk.LEFT)
        ttk.Label(font_frame, text=" pt").pack(side=tk.LEFT)

        # Font family
        ttk.Label(frame, text="Schriftart:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.font_family_var = tk.StringVar(value=get_setting("ui.editor_font_family", "Consolas"))
        font_combo = ttk.Combobox(
            frame,
            textvariable=self.font_family_var,
            values=["Consolas", "Courier New", "Monaco", "Source Code Pro", "Fira Code"],
            state="readonly",
            width=18,
        )
        font_combo.grid(row=1, column=1, sticky=tk.W, pady=8)

        # Line numbers
        ttk.Label(frame, text="Zeilennummern:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.line_numbers_var = tk.BooleanVar(value=get_setting("ui.show_line_numbers", True))
        ttk.Checkbutton(
            frame,
            text="Anzeigen",
            variable=self.line_numbers_var,
        ).grid(row=2, column=1, sticky=tk.W, pady=8)

        # Auto-save
        ttk.Label(frame, text="Automatisches Speichern:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.autosave_var = tk.BooleanVar(value=get_setting("ui.auto_save", False))
        ttk.Checkbutton(
            frame,
            text="Aktivieren",
            variable=self.autosave_var,
        ).grid(row=3, column=1, sticky=tk.W, pady=8)

        # Word wrap
        ttk.Label(frame, text="Zeilenumbruch:").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.word_wrap_var = tk.BooleanVar(value=get_setting("ui.word_wrap", True))
        ttk.Checkbutton(
            frame,
            text="Automatischer Umbruch",
            variable=self.word_wrap_var,
        ).grid(row=4, column=1, sticky=tk.W, pady=8)

        frame.columnconfigure(1, weight=1)

    def _create_audio_tab(self):
        """Tab für Audio/TTS-Einstellungen."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="🔊 Audio")

        # Auto-play preview
        ttk.Label(frame, text="Vorschau:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.autoplay_var = tk.BooleanVar(value=get_setting("ui.auto_play", True))
        ttk.Checkbutton(
            frame,
            text="Automatisch abspielen nach Generierung",
            variable=self.autoplay_var,
        ).grid(row=0, column=1, sticky=tk.W, pady=8)

        # Default TTS engine
        ttk.Label(frame, text="Standard TTS-Engine:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.engine_var = tk.StringVar(value=get_setting("tts.default_engine", "xtts"))
        engine_combo = ttk.Combobox(
            frame,
            textvariable=self.engine_var,
            values=["xtts", "piper", "bark", "styletts2"],
            state="readonly",
            width=15,
        )
        engine_combo.grid(row=1, column=1, sticky=tk.W, pady=8)

        # Quality preset
        ttk.Label(frame, text="Qualitätsstufe:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.quality_var = tk.StringVar(value=get_setting("tts.quality", "standard"))
        quality_combo = ttk.Combobox(
            frame,
            textvariable=self.quality_var,
            values=["preview", "standard", "high", "ultra"],
            state="readonly",
            width=15,
        )
        quality_combo.grid(row=2, column=1, sticky=tk.W, pady=8)

        # Default language
        ttk.Label(frame, text="Standardsprache:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.language_var = tk.StringVar(value=get_setting("tts.default_language", "de"))
        lang_combo = ttk.Combobox(
            frame,
            textvariable=self.language_var,
            values=["de", "en", "fr", "es", "it"],
            state="readonly",
            width=15,
        )
        lang_combo.grid(row=3, column=1, sticky=tk.W, pady=8)

        frame.columnconfigure(1, weight=1)

    def _create_advanced_tab(self):
        """Tab für erweiterte Einstellungen."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="⚙️ Erweitert")

        # Last project
        ttk.Label(frame, text="Letztes Projekt:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.last_var = tk.StringVar(value=get_setting("ui.last_project", ""))
        last_entry = ttk.Entry(frame, textvariable=self.last_var, width=35)
        last_entry.grid(row=0, column=1, sticky=tk.EW, pady=8)

        # Cache directory
        ttk.Label(frame, text="Cache-Verzeichnis:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.cache_var = tk.StringVar(value=get_setting("paths.cache", "cache/"))
        cache_entry = ttk.Entry(frame, textvariable=self.cache_var, width=35)
        cache_entry.grid(row=1, column=1, sticky=tk.EW, pady=8)

        # Debug mode
        ttk.Label(frame, text="Debug-Modus:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.debug_var = tk.BooleanVar(value=get_setting("debug.enabled", False))
        ttk.Checkbutton(
            frame,
            text="Aktivieren (zeigt zusätzliche Logs)",
            variable=self.debug_var,
        ).grid(row=2, column=1, sticky=tk.W, pady=8)

        # Threading workers
        ttk.Label(frame, text="Hintergrund-Threads:").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.workers_var = tk.IntVar(value=int(get_setting("threading.max_workers", 4)))
        workers_spin = ttk.Spinbox(frame, from_=1, to=8, textvariable=self.workers_var, width=5)
        workers_spin.grid(row=3, column=1, sticky=tk.W, pady=8)

        frame.columnconfigure(1, weight=1)

    def apply(self):
        """Save all settings."""
        # Appearance
        set_setting("ui.theme", self.theme_var.get())
        set_setting("ui.window_width", self.width_var.get())
        set_setting("ui.window_height", self.height_var.get())
        set_setting("ui.show_welcome", self.welcome_var.get())
        set_setting("ui.show_tooltips", self.tooltips_var.get())

        # Editor
        set_setting("ui.editor_font_size", int(self.font_var.get()))
        set_setting("ui.editor_font_family", self.font_family_var.get())
        set_setting("ui.show_line_numbers", self.line_numbers_var.get())
        set_setting("ui.auto_save", self.autosave_var.get())
        set_setting("ui.word_wrap", self.word_wrap_var.get())

        # Audio
        set_setting("ui.auto_play", self.autoplay_var.get())
        set_setting("tts.default_engine", self.engine_var.get())
        set_setting("tts.quality", self.quality_var.get())
        set_setting("tts.default_language", self.language_var.get())

        # Advanced
        set_setting("ui.last_project", self.last_var.get().strip())
        set_setting("paths.cache", self.cache_var.get().strip())
        set_setting("debug.enabled", self.debug_var.get())
        set_setting("threading.max_workers", self.workers_var.get())

        self.result = {"saved": True}

    def buttonbox(self):
        """Override to add Restore Defaults button."""
        box = ttk.Frame(self)

        w = ttk.Button(box, text="Standard wiederherstellen", width=20, command=self._on_restore_defaults)
        w.pack(side=tk.LEFT, padx=5, pady=10)

        # Spacer
        ttk.Frame(box, width=50).pack(side=tk.LEFT)

        w = ttk.Button(box, text="Abbrechen", width=10, command=self.cancel)
        w.pack(side=tk.RIGHT, padx=5, pady=10)

        w = ttk.Button(box, text="Speichern", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.RIGHT, padx=5, pady=10)

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        box.pack(fill=tk.X)

    def _on_restore_defaults(self):
        """Reset all settings to defaults."""
        try:
            defaults = {
                # Appearance
                "ui.theme": "dark",
                "ui.window_width": 1400,
                "ui.window_height": 900,
                "ui.show_welcome": True,
                "ui.show_tooltips": True,
                # Editor
                "ui.editor_font_size": 11,
                "ui.editor_font_family": "Consolas",
                "ui.show_line_numbers": True,
                "ui.auto_save": False,
                "ui.word_wrap": True,
                # Audio
                "ui.auto_play": True,
                "tts.default_engine": "xtts",
                "tts.quality": "standard",
                "tts.default_language": "de",
                # Advanced
                "ui.last_project": "",
                "paths.cache": "cache/",
                "debug.enabled": False,
                "threading.max_workers": 4,
            }

            # Update UI
            self.theme_var.set(defaults["ui.theme"])
            self.width_var.set(defaults["ui.window_width"])
            self.height_var.set(defaults["ui.window_height"])
            self.welcome_var.set(defaults["ui.show_welcome"])
            self.tooltips_var.set(defaults["ui.show_tooltips"])

            self.font_var.set(defaults["ui.editor_font_size"])
            self.font_family_var.set(defaults["ui.editor_font_family"])
            self.line_numbers_var.set(defaults["ui.show_line_numbers"])
            self.autosave_var.set(defaults["ui.auto_save"])
            self.word_wrap_var.set(defaults["ui.word_wrap"])

            self.autoplay_var.set(defaults["ui.auto_play"])
            self.engine_var.set(defaults["tts.default_engine"])
            self.quality_var.set(defaults["tts.quality"])
            self.language_var.set(defaults["tts.default_language"])

            self.last_var.set(defaults["ui.last_project"])
            self.cache_var.set(defaults["paths.cache"])
            self.debug_var.set(defaults["debug.enabled"])
            self.workers_var.set(defaults["threading.max_workers"])

            # Persist immediately
            for key, value in defaults.items():
                set_setting(key, value)

        except Exception:
            pass
