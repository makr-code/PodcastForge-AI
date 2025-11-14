#!/usr/bin/env python3
"""
PodcastForge Editor
Professioneller tkinter-basierter Editor für Podcast-Skripte und TTS-Generierung
"""

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, List, Optional

import yaml

try:
    from ..audio.player import get_player
    from ..audio.waveform import WaveformGenerator
    from ..core.config import PodcastConfig, PodcastStyle
    from ..core.forge import PodcastForge
    from ..core.models import Speaker
    from ..voices import VoiceGender, VoiceStyle, get_voice_library
except ImportError:
    # Fallback für direkte Ausführung
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PodcastEditor:
    """Haupt-Editor-Klasse für Podcast-Skripte"""

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root or tk.Tk()
        self.root.title("PodcastForge Editor - Professioneller Podcast-Skript-Editor")
        self.root.geometry("1400x900")

        # State
        self.current_file: Optional[Path] = None
        self.script_data: List[Dict] = []
        self.speakers: Dict[str, Speaker] = {}
        self.voice_library = get_voice_library()
        self.forge = None
        self.is_modified = False

        # Audio
        self.audio_player = get_player()
        self.waveform_generator = WaveformGenerator(width=300, height=100)
        self.current_preview_file: Optional[Path] = None
        self.preview_cache = Path("cache/editor_preview")
        self.preview_cache.mkdir(parents=True, exist_ok=True)

        # Themes
        self.setup_theme()

        # UI aufbauen
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_layout()
        self.setup_status_bar()

        # Keyboard Shortcuts
        self.setup_shortcuts()

        # Projekt initialisieren
        self.new_project()

    def setup_theme(self):
        """Konfiguriere moderne Themes"""
        style = ttk.Style()
        style.theme_use("clam")

        # Farb-Schema
        self.colors = {
            "bg": "#2b2b2b",
            "fg": "#ffffff",
            "accent": "#4a90e2",
            "success": "#5cb85c",
            "warning": "#f0ad4e",
            "error": "#d9534f",
            "editor_bg": "#1e1e1e",
            "editor_fg": "#d4d4d4",
            "speaker1": "#569cd6",  # Blau
            "speaker2": "#ce9178",  # Orange
            "speaker3": "#4ec9b0",  # Türkis
            "emotion": "#c586c0",  # Lila
            "pause": "#6a9955",  # Grün
        }

        self.root.configure(bg=self.colors["bg"])

    def setup_menu(self):
        """Erstelle Menüleiste"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neu", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Öffnen...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Speichern", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(
            label="Speichern als...", command=self.save_project_as, accelerator="Ctrl+Shift+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exportieren...", command=self.export_audio, accelerator="Ctrl+E"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.quit_app, accelerator="Ctrl+Q")

        # Bearbeiten-Menü
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
        edit_menu.add_command(label="Rückgängig", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Wiederholen", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Zeile einfügen", command=self.insert_line, accelerator="Ctrl+Enter"
        )
        edit_menu.add_command(label="Zeile löschen", command=self.delete_line, accelerator="Ctrl+D")
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Sprecher hinzufügen...", command=self.add_speaker, accelerator="Ctrl+Shift+S"
        )

        # TTS-Menü
        tts_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="TTS", menu=tts_menu)
        tts_menu.add_command(label="Zeile vorhören", command=self.preview_line, accelerator="F5")
        tts_menu.add_command(label="Alles vorhören", command=self.preview_all, accelerator="F6")
        tts_menu.add_separator()
        tts_menu.add_command(label="TTS-Engine wählen...", command=self.select_tts_engine)

        # Ansicht-Menü
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ansicht", menu=view_menu)
        view_menu.add_checkbutton(label="Timeline", command=self.toggle_timeline)
        view_menu.add_checkbutton(label="Voice Library", command=self.toggle_voice_library)
        view_menu.add_checkbutton(label="Audio-Wellenform", command=self.toggle_waveform)

        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Dokumentation", command=self.show_docs)
        help_menu.add_command(label="Über PodcastForge", command=self.show_about)

    def setup_toolbar(self):
        """Erstelle Toolbar mit Schnellzugriff-Buttons"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Icons (Text-basiert für Kompatibilität)
        buttons = [
            ("📄 Neu", self.new_project),
            ("📂 Öffnen", self.open_project),
            ("💾 Speichern", self.save_project),
            ("|", None),
            ("➕ Zeile", self.insert_line),
            ("➖ Löschen", self.delete_line),
            ("|", None),
            ("▶️ Vorhören", self.preview_line),
            ("⏸️ Stop", self.stop_playback),
            ("|", None),
            ("🎤 Sprecher", self.add_speaker),
            ("🎨 Stimmen", self.show_voice_library),
            ("|", None),
            ("💿 Export", self.export_audio),
        ]

        for label, command in buttons:
            if label == "|":
                ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
            else:
                btn = ttk.Button(toolbar, text=label, command=command, width=10)
                btn.pack(side=tk.LEFT, padx=2)

    def setup_main_layout(self):
        """Erstelle Haupt-Layout mit PanedWindow"""
        # Haupt-Container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Linkes Panel: Sprecher & Voice Library
        left_panel = ttk.Frame(main_container, width=300)
        main_container.add(left_panel, weight=1)
        self.setup_left_panel(left_panel)

        # Mittleres Panel: Skript-Editor
        center_panel = ttk.Frame(main_container)
        main_container.add(center_panel, weight=3)
        self.setup_center_panel(center_panel)

        # Rechtes Panel: Eigenschaften & Vorschau
        right_panel = ttk.Frame(main_container, width=300)
        main_container.add(right_panel, weight=1)
        self.setup_right_panel(right_panel)

    def setup_left_panel(self, parent):
        """Linkes Panel: Sprecher-Management"""
        # Überschrift
        ttk.Label(parent, text="🎤 Sprecher", font=("Arial", 12, "bold")).pack(pady=5)

        # Sprecher-Liste
        speakers_frame = ttk.LabelFrame(parent, text="Aktive Sprecher", padding=10)
        speakers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Listbox mit Scrollbar
        list_frame = ttk.Frame(speakers_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.speakers_listbox = tk.Listbox(
            list_frame,
            bg=self.colors["editor_bg"],
            fg=self.colors["editor_fg"],
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
        )
        self.speakers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.speakers_listbox.yview)

        # Sprecher-Buttons
        btn_frame = ttk.Frame(speakers_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="➕ Hinzufügen", command=self.add_speaker).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="✏️ Bearbeiten", command=self.edit_speaker).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="🗑️ Entfernen", command=self.remove_speaker).pack(
            side=tk.LEFT, padx=2
        )

        # Voice Library Panel
        voice_frame = ttk.LabelFrame(parent, text="🎨 Voice Library", padding=10)
        voice_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Filter
        filter_frame = ttk.Frame(voice_frame)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Sprache:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="de")
        lang_combo = ttk.Combobox(
            filter_frame, textvariable=self.lang_var, values=["de", "en"], width=8
        )
        lang_combo.pack(side=tk.LEFT, padx=5)
        lang_combo.bind("<<ComboboxSelected>>", self.update_voice_list)

        ttk.Label(filter_frame, text="Stil:").pack(side=tk.LEFT)
        self.style_var = tk.StringVar(value="")
        style_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.style_var,
            values=["", "professional", "documentary", "dramatic", "casual"],
            width=12,
        )
        style_combo.pack(side=tk.LEFT, padx=5)
        style_combo.bind("<<ComboboxSelected>>", self.update_voice_list)

        # Voice-Liste
        voice_list_frame = ttk.Frame(voice_frame)
        voice_list_frame.pack(fill=tk.BOTH, expand=True)

        voice_scrollbar = ttk.Scrollbar(voice_list_frame)
        voice_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.voice_listbox = tk.Listbox(
            voice_list_frame,
            bg=self.colors["editor_bg"],
            fg=self.colors["editor_fg"],
            yscrollcommand=voice_scrollbar.set,
            font=("Consolas", 9),
        )
        self.voice_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        voice_scrollbar.config(command=self.voice_listbox.yview)

        self.update_voice_list()

        # Voice verwenden Button
        ttk.Button(
            voice_frame, text="Als Sprecher verwenden", command=self.use_voice_as_speaker
        ).pack(pady=5)

    def setup_center_panel(self, parent):
        """Mittleres Panel: Skript-Editor"""
        # Überschrift mit Format-Auswahl
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=5)

        ttk.Label(header, text="📝 Podcast-Skript", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        ttk.Label(header, text="Format:").pack(side=tk.RIGHT, padx=5)
        self.format_var = tk.StringVar(value="structured")
        format_combo = ttk.Combobox(
            header,
            textvariable=self.format_var,
            values=["structured", "yaml", "json"],
            state="readonly",
            width=12,
        )
        format_combo.pack(side=tk.RIGHT)
        format_combo.bind("<<ComboboxSelected>>", self.update_editor_view)

        # Editor mit Syntax-Highlighting
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Line Numbers
        self.line_numbers = tk.Text(
            editor_frame,
            width=4,
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            state=tk.DISABLED,
            font=("Consolas", 10),
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Scrollbar
        scrollbar = ttk.scrollbar(editor_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text-Editor
        self.script_editor = scrolledtext.ScrolledText(
            editor_frame,
            bg=self.colors["editor_bg"],
            fg=self.colors["editor_fg"],
            insertbackground=self.colors["accent"],
            font=("Consolas", 11),
            wrap=tk.WORD,
            undo=True,
            maxundo=-1,
            yscrollcommand=scrollbar.set,
        )
        self.script_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.script_editor.yview)

        # Syntax-Highlighting Tags
        self.setup_syntax_tags()

        # Bindings
        self.script_editor.bind("<KeyRelease>", self.on_text_change)
        self.script_editor.bind("<Control-Return>", lambda e: self.insert_line())
        self.script_editor.bind("<<Modified>>", self.on_modified)

        # Timeline (optional)
        self.timeline_frame = ttk.LabelFrame(parent, text="⏱️ Timeline", padding=5)
        # Initial versteckt

    def setup_right_panel(self, parent):
        """Rechtes Panel: Eigenschaften & Audio-Vorschau"""
        # Zeilen-Eigenschaften
        props_frame = ttk.LabelFrame(parent, text="⚙️ Zeilen-Eigenschaften", padding=10)
        props_frame.pack(fill=tk.X, padx=5, pady=5)

        # Sprecher
        ttk.Label(props_frame, text="Sprecher:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.prop_speaker = ttk.Combobox(props_frame, state="readonly")
        self.prop_speaker.grid(row=0, column=1, sticky=tk.EW, pady=3)

        # Emotion
        ttk.Label(props_frame, text="Emotion:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.prop_emotion = ttk.Combobox(
            props_frame,
            values=["neutral", "excited", "thoughtful", "serious", "humorous", "dramatic"],
            state="readonly",
        )
        self.prop_emotion.grid(row=1, column=1, sticky=tk.EW, pady=3)
        self.prop_emotion.set("neutral")

        # Pause danach
        ttk.Label(props_frame, text="Pause (s):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.prop_pause = ttk.Spinbox(props_frame, from_=0.0, to=5.0, increment=0.1, format="%.1f")
        self.prop_pause.grid(row=2, column=1, sticky=tk.EW, pady=3)
        self.prop_pause.set(0.5)

        # Speed
        ttk.Label(props_frame, text="Geschw.:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.prop_speed = ttk.Scale(props_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL)
        self.prop_speed.grid(row=3, column=1, sticky=tk.EW, pady=3)
        self.prop_speed.set(1.0)

        ttk.Label(props_frame, text="1.0x").grid(row=3, column=2, pady=3)

        props_frame.columnconfigure(1, weight=1)

        # Übernehmen-Button
        ttk.Button(props_frame, text="✓ Übernehmen", command=self.apply_properties).grid(
            row=4, column=0, columnspan=3, pady=10
        )

        # Audio-Vorschau
        audio_frame = ttk.LabelFrame(parent, text="🔊 Audio-Vorschau", padding=10)
        audio_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Playback-Controls
        control_frame = ttk.Frame(audio_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.play_btn = ttk.Button(control_frame, text="▶️ Play", command=self.preview_line)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(control_frame, text="⏸️ Stop", command=self.stop_playback)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Volume
        ttk.Label(control_frame, text="🔉").pack(side=tk.LEFT, padx=5)
        self.volume_scale = ttk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.volume_scale.set(80)

        # Status
        self.audio_status = ttk.Label(audio_frame, text="Bereit", foreground=self.colors["success"])
        self.audio_status.pack(pady=5)

        # Wellenform-Canvas (Platzhalter)
        self.waveform_canvas = tk.Canvas(audio_frame, bg=self.colors["editor_bg"], height=100)
        self.waveform_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        # Podcast-Info
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Podcast-Info", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.info_lines = ttk.Label(info_frame, text="Zeilen: 0")
        self.info_lines.pack(anchor=tk.W)

        self.info_speakers = ttk.Label(info_frame, text="Sprecher: 0")
        self.info_speakers.pack(anchor=tk.W)

        self.info_duration = ttk.Label(info_frame, text="≈ Dauer: 0:00")
        self.info_duration.pack(anchor=tk.W)

    def setup_status_bar(self):
        """Erstelle Status-Leiste"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(status_frame, text="Bereit", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=200)
        # Initial versteckt

        self.cursor_pos = ttk.Label(status_frame, text="Zeile: 1, Spalte: 0", relief=tk.SUNKEN)
        self.cursor_pos.pack(side=tk.RIGHT)

    def setup_syntax_tags(self):
        """Konfiguriere Syntax-Highlighting Tags"""
        # Sprecher-Tags (dynamisch erstellt)
        colors = [self.colors["speaker1"], self.colors["speaker2"], self.colors["speaker3"]]
        for i, color in enumerate(colors, 1):
            self.script_editor.tag_config(
                f"speaker{i}", foreground=color, font=("Consolas", 11, "bold")
            )

        # Emotion-Tag
        self.script_editor.tag_config(
            "emotion", foreground=self.colors["emotion"], font=("Consolas", 10, "italic")
        )

        # Pause-Tag
        self.script_editor.tag_config("pause", foreground=self.colors["pause"])

        # Kommentar-Tag
        self.script_editor.tag_config(
            "comment", foreground="#6a9955", font=("Consolas", 10, "italic")
        )

        # Highlight current line
        self.script_editor.tag_config("current_line", background="#3a3a3a")

    def setup_shortcuts(self):
        """Konfiguriere Tastatur-Shortcuts"""
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-o>", lambda e: self.open_project())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_project_as())
        self.root.bind("<Control-e>", lambda e: self.export_audio())
        self.root.bind("<Control-q>", lambda e: self.quit_app())

        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-d>", lambda e: self.delete_line())

        self.root.bind("<F5>", lambda e: self.preview_line())
        self.root.bind("<F6>", lambda e: self.preview_all())

    # ========== Projekt-Management ==========

    def new_project(self):
        """Neues Projekt erstellen"""
        if self.is_modified:
            if not messagebox.askyesno("Ungespeicherte Änderungen", "Änderungen verwerfen?"):
                return

        self.current_file = None
        self.script_data = []
        self.speakers = {
            "Host": Speaker(
                name="Host",
                voice_sample="voices/de/professional_male.wav",
                description="Podcast-Moderator",
            ),
            "Gast": Speaker(
                name="Gast",
                voice_sample="voices/de/professional_female.wav",
                description="Interview-Gast",
            ),
        }

        self.update_speakers_list()
        self.script_editor.delete("1.0", tk.END)
        self.script_editor.insert("1.0", self.get_template())
        self.is_modified = False
        self.update_status("Neues Projekt erstellt")

    def get_template(self) -> str:
        """Gibt Template für neues Skript zurück"""
        if self.format_var.get() == "yaml":
            return """# PodcastForge Skript
title: Mein Podcast
style: interview
language: de

speakers:
  - name: Host
    voice: professional_male
  - name: Gast
    voice: professional_female

script:
  - speaker: Host
    text: Willkommen zu unserem Podcast!
    emotion: excited
    pause_after: 0.8
    
  - speaker: Gast
    text: Vielen Dank für die Einladung!
    emotion: neutral
    pause_after: 0.5
"""
        elif self.format_var.get() == "json":
            return json.dumps(
                {
                    "title": "Mein Podcast",
                    "style": "interview",
                    "language": "de",
                    "speakers": [
                        {"name": "Host", "voice": "professional_male"},
                        {"name": "Gast", "voice": "professional_female"},
                    ],
                    "script": [
                        {
                            "speaker": "Host",
                            "text": "Willkommen zu unserem Podcast!",
                            "emotion": "excited",
                            "pause_after": 0.8,
                        }
                    ],
                },
                indent=2,
            )
        else:  # structured
            return """Host [excited]: Willkommen zu unserem Podcast! [0.8s]
Gast [neutral]: Vielen Dank für die Einladung! [0.5s]

# Kommentar: Weitere Zeilen hier einfügen...
"""

    def open_project(self):
        """Projekt öffnen"""
        filepath = filedialog.askopenfilename(
            title="Podcast-Projekt öffnen",
            filetypes=[
                ("Projekt-Dateien", "*.yaml *.yml *.json"),
                ("YAML", "*.yaml *.yml"),
                ("JSON", "*.json"),
                ("Alle Dateien", "*.*"),
            ],
        )

        if not filepath:
            return

        try:
            path = Path(filepath)
            content = path.read_text(encoding="utf-8")

            # Auto-detect Format
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
                self.format_var.set("yaml")
            elif path.suffix == ".json":
                data = json.loads(content)
                self.format_var.set("json")

            # Daten laden
            self.load_project_data(data)
            self.script_editor.delete("1.0", tk.END)
            self.script_editor.insert("1.0", content)

            self.current_file = path
            self.is_modified = False
            self.update_status(f"Projekt geladen: {path.name}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Projekt konnte nicht geöffnet werden:\n{e}")

    def save_project(self):
        """Projekt speichern"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_project_as()

    def save_project_as(self):
        """Projekt speichern als..."""
        format_type = self.format_var.get()
        ext = ".yaml" if format_type in ["yaml", "structured"] else ".json"

        filepath = filedialog.asksaveasfilename(
            title="Projekt speichern als",
            defaultextension=ext,
            filetypes=[("YAML", "*.yaml *.yml"), ("JSON", "*.json"), ("Alle Dateien", "*.*")],
        )

        if filepath:
            self._save_to_file(Path(filepath))

    def _save_to_file(self, filepath: Path):
        """Speichere zu Datei"""
        try:
            content = self.script_editor.get("1.0", tk.END)
            filepath.write_text(content, encoding="utf-8")

            self.current_file = filepath
            self.is_modified = False
            self.update_status(f"Gespeichert: {filepath.name}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}")

    def load_project_data(self, data: dict):
        """Lade Projekt-Daten"""
        # Sprecher laden
        if "speakers" in data:
            self.speakers = {}
            for speaker_data in data["speakers"]:
                name = speaker_data["name"]
                self.speakers[name] = Speaker(
                    name=name,
                    voice_sample=speaker_data.get("voice", ""),
                    description=speaker_data.get("description", ""),
                )

        self.update_speakers_list()
        self.update_info()

    # ========== Editor-Funktionen ==========

    def on_text_change(self, event=None):
        """Wird bei Text-Änderung aufgerufen"""
        self.apply_syntax_highlighting()
        self.update_line_numbers()
        self.update_cursor_position()
        self.update_info()

    def on_modified(self, event=None):
        """Wird bei Änderung aufgerufen"""
        if self.script_editor.edit_modified():
            self.is_modified = True
            self.script_editor.edit_modified(False)

    def apply_syntax_highlighting(self):
        """Wende Syntax-Highlighting an"""
        # TODO: Implementiere Regex-basiertes Highlighting
        pass

    def update_line_numbers(self):
        """Aktualisiere Zeilennummern"""
        line_count = int(self.script_editor.index("end-1c").split(".")[0])
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))

        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.config(state=tk.DISABLED)

    def update_cursor_position(self):
        """Aktualisiere Cursor-Position"""
        cursor_pos = self.script_editor.index(tk.INSERT)
        line, col = cursor_pos.split(".")
        self.cursor_pos.config(text=f"Zeile: {line}, Spalte: {col}")

    def update_info(self):
        """Aktualisiere Podcast-Info"""
        content = self.script_editor.get("1.0", tk.END)
        lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]

        self.info_lines.config(text=f"Zeilen: {len(lines)}")
        self.info_speakers.config(text=f"Sprecher: {len(self.speakers)}")

        # Geschätzte Dauer (200 Wörter/Minute)
        words = sum(len(line.split()) for line in lines)
        duration_min = words / 200
        mins = int(duration_min)
        secs = int((duration_min - mins) * 60)
        self.info_duration.config(text=f"≈ Dauer: {mins}:{secs:02d}")

    def insert_line(self):
        """Füge neue Zeile ein"""
        cursor_pos = self.script_editor.index(tk.INSERT)
        template = "\nHost [neutral]: Text hier eingeben... [0.5s]\n"
        self.script_editor.insert(cursor_pos, template)
        self.update_status("Zeile eingefügt")

    def delete_line(self):
        """Lösche aktuelle Zeile"""
        cursor_line = self.script_editor.index(tk.INSERT).split(".")[0]
        self.script_editor.delete(f"{cursor_line}.0", f"{cursor_line}.end+1c")
        self.update_status("Zeile gelöscht")

    def undo(self):
        """Rückgängig"""
        try:
            self.script_editor.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        """Wiederholen"""
        try:
            self.script_editor.edit_redo()
        except tk.TclError:
            pass

    # ========== Sprecher-Management ==========

    def update_speakers_list(self):
        """Aktualisiere Sprecher-Liste"""
        self.speakers_listbox.delete(0, tk.END)
        self.prop_speaker["values"] = []

        speaker_names = []
        for name, speaker in self.speakers.items():
            display = f"{name} - {speaker.description or 'Keine Beschreibung'}"
            self.speakers_listbox.insert(tk.END, display)
            speaker_names.append(name)

        self.prop_speaker["values"] = speaker_names
        if speaker_names:
            self.prop_speaker.set(speaker_names[0])

    def add_speaker(self):
        """Füge neuen Sprecher hinzu"""
        dialog = SpeakerDialog(self.root, self.voice_library)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            name = dialog.result["name"]
            self.speakers[name] = Speaker(
                name=name,
                voice_sample=dialog.result["voice"],
                description=dialog.result["description"],
            )
            self.update_speakers_list()
            self.update_status(f"Sprecher '{name}' hinzugefügt")

    def edit_speaker(self):
        """Bearbeite ausgewählten Sprecher"""
        selection = self.speakers_listbox.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte einen Sprecher auswählen")
            return

        idx = selection[0]
        name = list(self.speakers.keys())[idx]
        speaker = self.speakers[name]

        dialog = SpeakerDialog(self.root, self.voice_library, speaker)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            # Update speaker
            new_name = dialog.result["name"]
            if new_name != name:
                del self.speakers[name]

            self.speakers[new_name] = Speaker(
                name=new_name,
                voice_sample=dialog.result["voice"],
                description=dialog.result["description"],
            )
            self.update_speakers_list()

    def remove_speaker(self):
        """Entferne ausgewählten Sprecher"""
        selection = self.speakers_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        name = list(self.speakers.keys())[idx]

        if messagebox.askyesno("Bestätigen", f"Sprecher '{name}' entfernen?"):
            del self.speakers[name]
            self.update_speakers_list()
            self.update_status(f"Sprecher '{name}' entfernt")

    # ========== Voice Library ==========

    def update_voice_list(self, event=None):
        """Aktualisiere Voice-Liste"""
        self.voice_listbox.delete(0, tk.END)

        language = self.lang_var.get()
        style = self.style_var.get() or None

        voices = self.voice_library.search(language=language, style=style)

        for voice in voices:
            display = f"{voice.display_name} ({voice.style.value if voice.style else 'neutral'})"
            self.voice_listbox.insert(tk.END, display)

    def use_voice_as_speaker(self):
        """Verwende ausgewählte Voice als Sprecher"""
        selection = self.voice_listbox.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte eine Stimme auswählen")
            return

        idx = selection[0]
        language = self.lang_var.get()
        style = self.style_var.get() or None
        voices = self.voice_library.search(language=language, style=style)

        if idx < len(voices):
            voice = voices[idx]

            # Erstelle Sprecher
            speaker_name = voice.display_name
            self.speakers[speaker_name] = Speaker(
                name=speaker_name,
                voice_sample=f"{voice.repo}/{voice.sub_path}/{voice.sample_filename}",
                description=voice.description,
            )

            self.update_speakers_list()
            self.update_status(f"Stimme '{speaker_name}' als Sprecher hinzugefügt")

    def show_voice_library(self):
        """Zeige Voice Library Dialog"""
        # TODO: Eigener Dialog mit Details
        messagebox.showinfo(
            "Voice Library", f"Verfügbare Stimmen: {self.voice_library.get_voice_count()}"
        )

    # ========== TTS & Audio ==========

    def preview_line(self):
        """Generiere Vorschau für aktuelle Zeile"""
        self.update_status("Generiere Audio-Vorschau...")
        self.audio_status.config(text="Generiere...", foreground=self.colors["warning"])
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start()

        # Parse aktuelle Zeile
        current_line = self._get_current_line_text()
        if not current_line:
            self.audio_status.config(text="Keine Zeile", foreground=self.colors["error"])
            self.progress.stop()
            self.progress.pack_forget()
            return

        # Starte TTS-Generierung in Thread
        threading.Thread(target=self._generate_preview, args=(current_line,), daemon=True).start()

    def _get_current_line_text(self) -> Optional[str]:
        """Hole Text der aktuellen Zeile"""
        try:
            cursor_line = self.script_editor.index(tk.INSERT).split(".")[0]
            line_text = self.script_editor.get(f"{cursor_line}.0", f"{cursor_line}.end")
            return line_text.strip() if line_text.strip() else None
        except:
            return None

    def _parse_line(self, line_text: str) -> Optional[Dict]:
        """Parse Zeile im Structured-Format"""
        # Format: Sprecher [Emotion]: Text [Pause]
        import re

        # Regex für Structured Format
        pattern = r"^([\w]+)\s*\[([\w]+)\]\s*:\s*(.+?)(?:\s*\[([\d.]+)s\])?$"
        match = re.match(pattern, line_text)

        if match:
            speaker, emotion, text, pause = match.groups()
            return {
                "speaker": speaker,
                "emotion": emotion,
                "text": text,
                "pause_after": float(pause) if pause else 0.5,
            }

        # Fallback: Einfacher Text
        return {
            "speaker": self.prop_speaker.get() or "Host",
            "emotion": self.prop_emotion.get() or "neutral",
            "text": line_text,
            "pause_after": float(self.prop_pause.get() or 0.5),
        }

    def _generate_preview(self, line_text: str):
        """Generiere TTS-Vorschau (läuft in Thread)"""
        try:
            # Parse Zeile
            line_data = self._parse_line(line_text)
            if not line_data:
                raise ValueError("Konnte Zeile nicht parsen")

            # Prüfe ob Sprecher existiert
            speaker_name = line_data["speaker"]
            if speaker_name not in self.speakers:
                raise ValueError(f"Sprecher '{speaker_name}' nicht gefunden")

            # Generiere TTS (Simulation für jetzt)
            # TODO: Echte TTS-Integration
            import time

            time.sleep(1.5)  # Simuliere TTS-Generierung

            # Erstelle Demo-Audio-Datei (Platzhalter)
            preview_file = self.preview_cache / f"preview_{int(time.time())}.mp3"

            # Für Demo: Kopiere existierende Audio-Datei falls vorhanden
            # In Produktion: Nutze echte TTS-Engine
            sample_audio = Path("examples/sample.mp3")
            if sample_audio.exists():
                import shutil

                shutil.copy(sample_audio, preview_file)
            else:
                # Erstelle stille Audio-Datei als Fallback
                self._create_silent_audio(preview_file, duration=2.0)

            self.current_preview_file = preview_file

            # Aktualisiere UI (Thread-safe)
            self.root.after(0, self._on_preview_ready, preview_file, line_data)

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._on_preview_error, error_msg)

    def _create_silent_audio(self, output_file: Path, duration: float = 1.0):
        """Erstelle stille Audio-Datei als Fallback"""
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine

            # Erstelle kurzen Ton (440 Hz, sehr leise)
            tone = Sine(440).to_audio_segment(duration=int(duration * 1000))
            tone = tone - 40  # Sehr leise

            # Exportiere
            tone.export(output_file, format="mp3")
        except:
            # Wenn pydub nicht verfügbar, erstelle leere Datei
            output_file.write_bytes(b"")

    def _on_preview_ready(self, audio_file: Path, line_data: Dict):
        """Callback wenn Vorschau fertig (UI-Thread)"""
        self.progress.stop()
        self.progress.pack_forget()

        # Update Status
        speaker = line_data["speaker"]
        text_preview = (
            line_data["text"][:30] + "..." if len(line_data["text"]) > 30 else line_data["text"]
        )
        self.audio_status.config(text=f"Bereit: {speaker}", foreground=self.colors["success"])
        self.update_status(f"Vorschau: {text_preview}")

        # Generiere Wellenform
        self._update_waveform(audio_file)

        # Spiele Audio ab
        self.audio_player.play(
            audio_file,
            on_complete=lambda: self.audio_status.config(
                text="Bereit ✓", foreground=self.colors["success"]
            ),
        )
        self.audio_status.config(text="Spielt ab ▶️", foreground=self.colors["accent"])

    def _on_preview_error(self, error_msg: str):
        """Callback bei Fehler (UI-Thread)"""
        self.progress.stop()
        self.progress.pack_forget()
        self.audio_status.config(text=f"Fehler: {error_msg}", foreground=self.colors["error"])
        self.update_status(f"Fehler: {error_msg}")

    def _update_waveform(self, audio_file: Path):
        """Aktualisiere Wellenform-Anzeige"""
        try:
            from PIL import ImageTk

            # Generiere Wellenform
            waveform_img = self.waveform_generator.generate(audio_file)

            if waveform_img:
                # Konvertiere für tkinter
                photo = ImageTk.PhotoImage(waveform_img)

                # Zeige in Canvas
                self.waveform_canvas.delete("all")
                self.waveform_canvas.create_image(0, 0, image=photo, anchor=tk.NW)

                # Speichere Referenz (wichtig für tkinter!)
                self.waveform_canvas.image = photo
        except Exception as e:
            print(f"⚠️ Wellenform-Update fehlgeschlagen: {e}")

    def preview_all(self):
        """Generiere Vorschau für gesamtes Skript"""
        if not messagebox.askyesno(
            "Komplett-Vorschau",
            "Möchten Sie das gesamte Skript als Audio generieren?\nDies kann einige Minuten dauern.",
        ):
            return

        self.update_status("Generiere Komplett-Vorschau...")
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start()

        # TODO: Implementiere vollständige Podcast-Generierung
        threading.Thread(target=self._generate_full_preview, daemon=True).start()

    def _generate_full_preview(self):
        """Generiere vollständigen Podcast (Thread)"""
        try:
            # Parse komplettes Skript
            content = self.script_editor.get("1.0", tk.END)

            # TODO: Nutze PodcastForge für Generierung
            import time

            time.sleep(3)  # Simulation

            self.root.after(0, self._on_full_preview_ready)

        except Exception as e:
            self.root.after(0, self._on_preview_error, str(e))

    def _on_full_preview_ready(self):
        """Callback wenn Komplett-Vorschau fertig"""
        self.progress.stop()
        self.progress.pack_forget()
        self.update_status("Komplett-Vorschau bereit")
        messagebox.showinfo("Fertig", "Podcast-Vorschau wurde generiert!")

    def stop_playback(self):
        """Stoppe Audio-Wiedergabe"""
        self.audio_player.stop()
        self.audio_status.config(text="Gestoppt ⏸️", foreground=self.colors["warning"])
        self.update_status("Wiedergabe gestoppt")

    def apply_properties(self):
        """Wende Eigenschaften auf aktuelle Zeile an"""
        try:
            cursor_line = self.script_editor.index(tk.INSERT).split(".")[0]
            current_text = self.script_editor.get(f"{cursor_line}.0", f"{cursor_line}.end")

            # Hole Eigenschaften
            speaker = self.prop_speaker.get()
            emotion = self.prop_emotion.get()
            pause = self.prop_pause.get()

            # Parse existierende Zeile
            import re

            text_match = re.search(r":\s*(.+?)(?:\s*\[|$)", current_text)
            text = text_match.group(1).strip() if text_match else current_text

            # Erstelle neue Zeile
            new_line = f"{speaker} [{emotion}]: {text} [{pause}s]"

            # Ersetze Zeile
            self.script_editor.delete(f"{cursor_line}.0", f"{cursor_line}.end")
            self.script_editor.insert(f"{cursor_line}.0", new_line)

            self.update_status("Eigenschaften übernommen")

        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Eigenschaften nicht übernehmen:\n{e}")

    def select_tts_engine(self):
        """Wähle TTS-Engine"""
        # TODO: Dialog mit Engine-Auswahl
        messagebox.showinfo("TTS-Engine", "Aktuell: XTTS v2")

    # ========== Export ==========

    def export_audio(self):
        """Exportiere Podcast als Audio-Datei"""
        filepath = filedialog.asksaveasfilename(
            title="Podcast exportieren",
            defaultextension=".mp3",
            filetypes=[("MP3", "*.mp3"), ("WAV", "*.wav"), ("OGG", "*.ogg")],
        )

        if not filepath:
            return

        self.update_status("Exportiere Podcast...")
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start()

        # TODO: Implementiere Export in Thread
        threading.Thread(target=self._export_thread, args=(filepath,), daemon=True).start()

    def _export_thread(self, filepath: str):
        """Export-Thread"""
        try:
            # Parse Skript
            # Generiere Audio mit PodcastForge
            # Speichere zu Datei

            import time

            time.sleep(3)  # Simulation

            self.progress.stop()
            self.progress.pack_forget()
            self.update_status(f"Exportiert: {Path(filepath).name}")
            messagebox.showinfo("Export", f"Podcast erfolgreich exportiert:\n{filepath}")

        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            messagebox.showerror("Export-Fehler", f"Export fehlgeschlagen:\n{e}")

    # ========== UI-Hilfsfunktionen ==========

    def update_status(self, message: str):
        """Aktualisiere Status-Leiste"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def toggle_timeline(self):
        """Toggle Timeline-Ansicht"""
        # TODO: Implementieren
        pass

    def toggle_voice_library(self):
        """Toggle Voice Library"""
        # TODO: Implementieren
        pass

    def toggle_waveform(self):
        """Toggle Wellenform-Anzeige"""
        # TODO: Implementieren
        pass

    def update_editor_view(self, event=None):
        """Update Editor-Ansicht basierend auf Format"""
        # TODO: Format konvertieren
        pass

    def show_docs(self):
        """Zeige Dokumentation"""
        messagebox.showinfo(
            "Dokumentation",
            "PodcastForge Editor - Hilfe\n\n"
            "Shortcuts:\n"
            "Ctrl+N - Neu\n"
            "Ctrl+O - Öffnen\n"
            "Ctrl+S - Speichern\n"
            "Ctrl+Enter - Zeile einfügen\n"
            "F5 - Zeile vorhören\n"
            "F6 - Alles vorhören\n\n"
            "Format:\n"
            "Sprecher [Emotion]: Text [Pause]\n\n"
            "Beispiel:\n"
            "Host [excited]: Hallo! [0.8s]",
        )

    def show_about(self):
        """Zeige Über-Dialog"""
        messagebox.showinfo(
            "Über PodcastForge",
            "PodcastForge Editor v1.0\n\n"
            "Professioneller Podcast-Editor\n"
            "mit KI-basierter TTS-Generierung\n\n"
            "© 2024 PodcastForge\n"
            "Open Source - MIT License",
        )

    def quit_app(self):
        """Beende Anwendung"""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                "Ungespeicherte Änderungen", "Möchten Sie vor dem Beenden speichern?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()

        self.root.quit()

    def run(self):
        """Starte Editor"""
        self.root.mainloop()


class SpeakerDialog:
    """Dialog zum Hinzufügen/Bearbeiten von Sprechern"""

    def __init__(self, parent, voice_library, speaker: Optional[Speaker] = None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Sprecher bearbeiten" if speaker else "Sprecher hinzufügen")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.voice_library = voice_library
        self.result = None

        # Form
        form_frame = ttk.Frame(self.dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        if speaker:
            self.name_entry.insert(0, speaker.name)

        # Beschreibung
        ttk.Label(form_frame, text="Beschreibung:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(form_frame, width=30)
        self.desc_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        if speaker:
            self.desc_entry.insert(0, speaker.description or "")

        # Voice
        ttk.Label(form_frame, text="Stimme:").grid(row=2, column=0, sticky=tk.W, pady=5)

        voice_frame = ttk.Frame(form_frame)
        voice_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)

        self.voice_var = tk.StringVar()
        if speaker:
            self.voice_var.set(speaker.voice_sample)

        voice_entry = ttk.Entry(voice_frame, textvariable=self.voice_var, width=25)
        voice_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(voice_frame, text="📂", command=self.browse_voice, width=3).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(voice_frame, text="🎨", command=self.select_from_library, width=3).pack(
            side=tk.LEFT
        )

        form_frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(btn_frame, text="✓ OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="✗ Abbrechen", command=self.cancel).pack(side=tk.RIGHT)

    def browse_voice(self):
        """Durchsuche Voice-Datei"""
        filepath = filedialog.askopenfilename(
            title="Voice-Sample auswählen", filetypes=[("Audio", "*.wav *.mp3"), ("Alle", "*.*")]
        )
        if filepath:
            self.voice_var.set(filepath)

    def select_from_library(self):
        """Wähle aus Voice Library"""
        # TODO: Dialog mit Voice Library
        messagebox.showinfo("Voice Library", "Voice Library öffnen...")

    def ok(self):
        """OK geklickt"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte Namen eingeben")
            return

        self.result = {
            "name": name,
            "voice": self.voice_var.get(),
            "description": self.desc_entry.get().strip(),
        }
        self.dialog.destroy()

    def cancel(self):
        """Abbrechen geklickt"""
        self.dialog.destroy()


def main():
    """Hauptfunktion"""
    editor = PodcastEditor()
    editor.run()


if __name__ == "__main__":
    main()
