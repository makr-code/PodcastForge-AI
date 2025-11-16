"""
Settings dialog for PodcastForge GUI.

Allows editing persisted UI settings (theme, editor font size, last project).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional

from ..core.settings import get_setting, set_setting


class SettingsDialog(simpledialog.Dialog):
    """Modal settings dialog.

    Usage:
        dlg = SettingsDialog(parent)
        if dlg.result: # dict of settings saved
            ...
    """

    def body(self, master):
        self.title("Settings")

        ttk.Label(master, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        self.theme_var = tk.StringVar(value=get_setting("ui.theme", "clam"))
        self.theme_combo = ttk.Combobox(master, values=["clam", "default", "classic"], textvariable=self.theme_var, state="readonly")
        self.theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=6)

        ttk.Label(master, text="Editor font size:").grid(row=1, column=0, sticky=tk.W, padx=6, pady=6)
        self.font_var = tk.IntVar(value=int(get_setting("ui.editor_font_size", 11)))
        self.font_spin = ttk.Spinbox(master, from_=8, to=28, textvariable=self.font_var)
        self.font_spin.grid(row=1, column=1, sticky=tk.W, padx=6, pady=6)

        ttk.Label(master, text="Last project:").grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        self.last_var = tk.StringVar(value=get_setting("ui.last_project", ""))
        self.last_entry = ttk.Entry(master, textvariable=self.last_var)
        self.last_entry.grid(row=2, column=1, sticky=tk.EW, padx=6, pady=6)

        master.columnconfigure(1, weight=1)
        return self.theme_combo

    def apply(self):
        # Save settings
        set_setting("ui.theme", self.theme_var.get())
        set_setting("ui.editor_font_size", int(self.font_var.get()))
        set_setting("ui.last_project", self.last_var.get().strip())
        self.result = {
            "ui.theme": self.theme_var.get(),
            "ui.editor_font_size": int(self.font_var.get()),
            "ui.last_project": self.last_var.get().strip(),
        }

    def buttonbox(self):
        # override to add Restore Defaults button
        box = ttk.Frame(self)

        w = ttk.Button(box, text="Restore Defaults", width=12, command=self._on_restore_defaults)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        box.pack()

    def _on_restore_defaults(self):
        # reset widget values to defaults and persist them
        try:
            defaults = {"ui.theme": "clam", "ui.editor_font_size": 11, "ui.last_project": ""}
            self.theme_var.set(defaults["ui.theme"])
            self.font_var.set(defaults["ui.editor_font_size"])
            self.last_var.set(defaults["ui.last_project"])
            # persist immediately
            set_setting("ui.theme", defaults["ui.theme"])
            set_setting("ui.editor_font_size", defaults["ui.editor_font_size"])
            set_setting("ui.last_project", defaults["ui.last_project"])
        except Exception:
            pass
