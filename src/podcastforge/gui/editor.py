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
    from ..core.config import PodcastConfig, PodcastStyle, Speaker
    from ..core.forge import PodcastForge
    from ..voices import VoiceGender, VoiceStyle, get_voice_library
except ImportError:
    # Fallback für direkte Ausführung
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..core.settings import get_setting
from ..core.events import get_event_bus
from ..integrations.script_orchestrator import synthesize_script_preview
import tempfile
import shutil
from ..gui.threading_base import get_thread_manager
from ..core.script_model import normalize_script
from ..tts.engine_manager import get_engine_manager
import uuid
import soundfile as sf
import tempfile as _tempfile


class PodcastEditor:
    """Haupt-Editor-Klasse für Podcast-Skripte

    When `embedded=True`, the editor will not create its own menu or toolbar
    so it can be embedded into a host window or frame without duplicating
    UI chrome.
    """

    def __init__(self, root: Optional[tk.Tk] = None, embedded: bool = False):
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
        # Wenn eingebettet, skippe Menü/Toolbar um doppelte UI zu vermeiden.
        if not embedded:
            self.setup_menu()
            self.setup_toolbar()
        self.setup_main_layout()
        self.setup_status_bar()

        # Keyboard Shortcuts
        self.setup_shortcuts()

        # Projekt initialisieren
        self.new_project()

        # Subscribe to generation events
        try:
            eb = get_event_bus()
            eb.subscribe('script.generate.request', self._on_generate_request)
            eb.subscribe('script.tts_progress', self._on_script_progress)
            eb.subscribe('script.preview_ready', self._on_script_preview_ready)
        except Exception:
            pass

    def setup_theme(self):
        """Konfiguriere moderne Themes (delegiert an `components.apply_theme`)."""
        try:
            from .components import apply_theme

            apply_theme(self.root)
            # read back palette if present
            self.colors = getattr(self.root, "theme_colors", {})
        except Exception:
            # fallback to minimal palette
            self.colors = {"bg": "#2b2b2b", "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4"}

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
            ("⚙️ Generate", self.open_generate_dialog),
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
        btn_frame = ttk.Frame(voice_frame)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Als Sprecher verwenden", command=self.use_voice_as_speaker).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Vorschau", command=self._on_preview_selected_voice).pack(side=tk.LEFT, padx=4)

        # Drag & Drop helpers: start drag on press, handle drop on editor
        self.voice_listbox.bind('<ButtonPress-1>', self._voice_drag_start)
        self.voice_listbox.bind('<B1-Motion>', self._voice_drag_motion)
        # Right-click context menu for preview
        self.voice_listbox.bind('<Button-3>', self._on_voice_right_click)
        # track drag index
        self._dragged_voice_index = None

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

        # Draft Pane: list of ingested utterances / draft manifest
        self.setup_draft_pane(parent)

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
            font=("Consolas", int(get_setting("ui.editor_font_size", 11))),
            wrap=tk.WORD,
            undo=True,
            maxundo=-1,
            yscrollcommand=scrollbar.set,
        )
        self.script_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.script_editor.yview)

        # Block view toggle and container (hidden until block view enabled)
        toggle_frame = ttk.Frame(editor_frame)
        toggle_frame.pack(fill=tk.X, pady=(4, 0))
        self.block_view_var = tk.BooleanVar(value=False)
        def _toggle_block_view():
            if self.block_view_var.get():
                # hide text editor and show block canvas
                try:
                    self.script_editor.pack_forget()
                except Exception:
                    pass
                self.block_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                self.block_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                self.block_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                self.render_blocks()
            else:
                try:
                    self.block_container.pack_forget()
                except Exception:
                    pass
                self.script_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Checkbutton(toggle_frame, text='Block View', variable=self.block_view_var, command=_toggle_block_view).pack(side=tk.LEFT, padx=6)

        # Prepare block container but do not pack by default
        self.block_container = ttk.Frame(editor_frame)
        self.block_canvas = tk.Canvas(self.block_container, borderwidth=0, highlightthickness=0)
        self.block_scroll = ttk.Scrollbar(self.block_container, orient=tk.VERTICAL, command=self.block_canvas.yview)
        self.block_inner = ttk.Frame(self.block_canvas)
        self.block_inner.bind('<Configure>', lambda e: self.block_canvas.configure(scrollregion=self.block_canvas.bbox('all')))
        self.block_canvas.create_window((0,0), window=self.block_inner, anchor='nw')
        self.block_canvas.configure(yscrollcommand=self.block_scroll.set)

        # Syntax-Highlighting Tags
        self.setup_syntax_tags()

        # Drag highlight tag for DnD feedback
        try:
            hl_color = self.colors.get("accent", "#3a7")
        except Exception:
            hl_color = "#3a7"
        self.script_editor.tag_configure("drag_highlight", background=hl_color)
        self._drag_highlight_line = None

        # Bindings
        self.script_editor.bind("<KeyRelease>", self.on_text_change)
        self.script_editor.bind("<Control-Return>", lambda e: self.insert_line())
        self.script_editor.bind("<<Modified>>", self.on_modified)
        # Allow dropping a voice onto the editor (mouse release triggers drop)
        self.script_editor.bind('<ButtonRelease-1>', self._voice_drop_on_editor)
        # Ensure widget supports undo for drag/drop recover
        try:
            self.script_editor.config(undo=True, maxundo=-1)
        except Exception:
            pass

    def setup_draft_pane(self, parent):
        """Create a small Draft pane above the editor for ingested utterances."""
        draft_frame = ttk.LabelFrame(parent, text="Draft / Ingested Utterances", padding=6)
        draft_frame.pack(fill=tk.X, padx=5, pady=(0, 6))

        # Listbox with simple summary
        self.draft_listbox = tk.Listbox(draft_frame, height=4, font=("Consolas", 10))
        self.draft_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.draft_listbox.bind('<Double-1>', self._on_draft_double_click)

        btns = ttk.Frame(draft_frame)
        btns.pack(side=tk.RIGHT)

        ttk.Button(btns, text="Import Draft", command=self._import_draft).pack(side=tk.TOP, pady=2)
        ttk.Button(btns, text="Save Draft", command=self._save_draft).pack(side=tk.TOP, pady=2)
        ttk.Button(btns, text="Generate", command=self.open_generate_dialog).pack(side=tk.TOP, pady=2)

        # Internal draft model: list of dicts (utterance summaries)
        self._draft_items = []

    def _import_draft(self):
        """Import a draft manifest (YAML/JSON) and populate the draft pane."""
        path = filedialog.askopenfilename(title="Import Draft Manifest", filetypes=[("YAML", "*.yaml;*.yml"), ("JSON", "*.json"), ("All", "*")])
        if not path:
            return
        try:
            data = None
            if path.lower().endswith(('.yaml', '.yml')):
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # Extract utterances for list display
            items = []
            for sec in data.get('sections', []) if isinstance(data, dict) else []:
                for it in sec.get('items', []):
                    if it.get('type') == 'utterance':
                        items.append({'id': it.get('id'), 'speaker': it.get('speaker'), 'text': it.get('text')})

            self._draft_items = items
            self.draft_listbox.delete(0, tk.END)
            for u in items:
                display = f"{u.get('id') or '---'} | {u.get('speaker') or 'unspecified'}: { (u.get('text') or '')[:60] }"
                self.draft_listbox.insert(tk.END, display)

            # Publish event that a draft was ingested so editor can open in draft mode
            try:
                eb = get_event_bus()
                eb.publish('script.ingested', {'manifest': path})
            except Exception:
                pass

            self.update_status(f"Draft manifest importiert: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("Import fehlgeschlagen", str(e))

    def _save_draft(self):
        """Save current draft items to a YAML manifest."""
        if not self._draft_items:
            messagebox.showwarning("Keine Drafts", "Keine Draft-Utterances vorhanden")
            return
        path = filedialog.asksaveasfilename(title="Save Draft Manifest", defaultextension='.yaml', filetypes=[('YAML','*.yaml'),('All','*.*')])
        if not path:
            return
        try:
            # Create a minimal manifest container
            manifest = {'project': {'title': self.current_file.name if self.current_file else 'untitled'}, 'sections': [{'id': 'draft', 'title': 'Draft', 'items': []}]}
            for u in self._draft_items:
                manifest['sections'][0]['items'].append({'type': 'utterance', 'id': u.get('id'), 'speaker': u.get('speaker'), 'text': u.get('text')})

            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)

            self.update_status(f"Draft gespeichert: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("Save fehlgeschlagen", str(e))

    def _on_draft_double_click(self, event):
        """Open the selected draft item in the main editor for inline editing."""
        try:
            sel = self.draft_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if idx < 0 or idx >= len(self._draft_items):
                return
            item = self._draft_items[idx]
            speaker = item.get('speaker') or ''
            text = item.get('text') or ''
            emotion = item.get('emotion') or ''
            pause = item.get('pause_after') or item.get('pause') or ''

            # Ensure speaker exists in speakers list
            if speaker and speaker not in self.speakers:
                try:
                    self.speakers[speaker] = Speaker(name=speaker, voice_sample='', description='')
                    self.update_speakers_list()
                except Exception:
                    pass

            # Build structured line: Speaker [Emotion]: Text [0.5s]
            parts = [f"{speaker}"]
            if emotion:
                parts.append(f"[{emotion}]")

            main = f": {text}"
            if pause:
                try:
                    p = float(pause)
                    main = f": {text} [{p}s]"
                except Exception:
                    main = f": {text} [{pause}]"

            insert_line = " ".join(parts) + main + "\n"

            # Prepare inspector fields
            try:
                if speaker:
                    # refresh prop_speaker values
                    self.prop_speaker['values'] = list(self.speakers.keys())
                    self.prop_speaker.set(speaker)
                if emotion:
                    self.prop_emotion.set(emotion)
                if pause:
                    self.prop_pause.set(str(pause))
            except Exception:
                pass

            # Insert at current cursor position or append at end, with undo separators
            try:
                self.script_editor.edit_separator()
            except Exception:
                pass

            try:
                cursor_index = self.script_editor.index(tk.INSERT)
                line_no = cursor_index.split('.')[0]
                # insert new line after current
                self.script_editor.insert(f"{line_no}.end+1c", '\n' + insert_line)
                # move cursor to the newly inserted line
                new_index = f"{int(line_no)+1}.0"
                self.script_editor.mark_set(tk.INSERT, new_index)
                self.script_editor.focus_set()
                self.update_status(f"Draft geladen: {item.get('id') or idx}")
            except Exception:
                # fallback: append at end
                self.script_editor.insert(tk.END, insert_line)
                self.script_editor.see(tk.END)
                self.script_editor.focus_set()
                self.update_status(f"Draft angehängt: {item.get('id') or idx}")

            try:
                self.script_editor.edit_separator()
            except Exception:
                pass

        except Exception as e:
            print('Draft open failed:', e)

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

        # Near-realtime toggle: play utterances as they finish
        self.near_realtime_var = tk.BooleanVar(value=False)
        try:
            nr = ttk.Checkbutton(control_frame, text='Near‑Realtime', variable=self.near_realtime_var)
            nr.pack(side=tk.LEFT, padx=6)
        except Exception:
            # fallback if themed widget missing
            cb = tk.Checkbutton(control_frame, text='Near‑Realtime', variable=self.near_realtime_var)
            cb.pack(side=tk.LEFT, padx=6)

        # Spatialize toggle + simple params (azimuth, distance)
        self.spatialize_var = tk.BooleanVar(value=False)
        try:
            sp_cb = ttk.Checkbutton(control_frame, text='Spatialize', variable=self.spatialize_var)
            sp_cb.pack(side=tk.LEFT, padx=6)
        except Exception:
            sp_cb = tk.Checkbutton(control_frame, text='Spatialize', variable=self.spatialize_var)
            sp_cb.pack(side=tk.LEFT, padx=6)

        # small param controls
        self.spatial_az_var = tk.DoubleVar(value=0.0)
        self.spatial_dist_var = tk.DoubleVar(value=1.0)
        try:
            ttk.Label(control_frame, text='Az:').pack(side=tk.LEFT, padx=(8,0))
            az_entry = ttk.Entry(control_frame, width=6, textvariable=self.spatial_az_var)
            az_entry.pack(side=tk.LEFT, padx=2)
            ttk.Label(control_frame, text='Dist:').pack(side=tk.LEFT, padx=(6,0))
            dist_entry = ttk.Entry(control_frame, width=6, textvariable=self.spatial_dist_var)
            dist_entry.pack(side=tk.LEFT, padx=2)
        except Exception:
            pass

        # Prosody controls: rate, pitch (cents), energy
        self.prosody_rate_var = tk.DoubleVar(value=1.0)
        self.prosody_pitch_var = tk.DoubleVar(value=0.0)
        self.prosody_energy_var = tk.DoubleVar(value=1.0)
        try:
            ttk.Label(control_frame, text='Rate:').pack(side=tk.LEFT, padx=(8,0))
            rate_entry = ttk.Entry(control_frame, width=6, textvariable=self.prosody_rate_var)
            rate_entry.pack(side=tk.LEFT, padx=2)
            ttk.Label(control_frame, text='Pitch(cents):').pack(side=tk.LEFT, padx=(6,0))
            pitch_entry = ttk.Entry(control_frame, width=6, textvariable=self.prosody_pitch_var)
            pitch_entry.pack(side=tk.LEFT, padx=2)
            ttk.Label(control_frame, text='Energy:').pack(side=tk.LEFT, padx=(6,0))
            energy_entry = ttk.Entry(control_frame, width=6, textvariable=self.prosody_energy_var)
            energy_entry.pack(side=tk.LEFT, padx=2)
        except Exception:
            pass

        # Insert breaths toggle
        self.insert_breaths_var = tk.BooleanVar(value=False)
        try:
            b_cb = ttk.Checkbutton(control_frame, text='Insert Breaths', variable=self.insert_breaths_var)
            b_cb.pack(side=tk.LEFT, padx=6)
        except Exception:
            cb = tk.Checkbutton(control_frame, text='Insert Breaths', variable=self.insert_breaths_var)
            cb.pack(side=tk.LEFT, padx=6)
        # Breath intensity slider
        self.breath_intensity_var = tk.DoubleVar(value=0.5)
        try:
            ttk.Label(control_frame, text='Breath Int:').pack(side=tk.LEFT, padx=(6,0))
            breath_slider = ttk.Scale(control_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.breath_intensity_var)
            breath_slider.pack(side=tk.LEFT, padx=2)
            ttk.Label(control_frame, textvariable=self.breath_intensity_var, width=4).pack(side=tk.LEFT, padx=(2,6))
            # Breath presets combobox
            self.breath_preset_var = tk.StringVar(value='Normal')
            preset_combo = ttk.Combobox(control_frame, textvariable=self.breath_preset_var, values=['Subtle', 'Normal', 'Pronounced', 'Custom'], width=10, state='readonly')
            preset_combo.pack(side=tk.LEFT, padx=(4,6))
            # map presets to values
            def _apply_preset(event=None):
                mapping = {'Subtle': 0.25, 'Normal': 0.5, 'Pronounced': 0.85}
                p = self.breath_preset_var.get()
                if p in mapping:
                    self.breath_intensity_var.set(mapping[p])
                else:
                    # Custom: leave current value
                    pass

            preset_combo.bind('<<ComboboxSelected>>', _apply_preset)
            # when slider is moved manually, set preset to Custom if it no longer matches
            def _on_slider_change(*args):
                try:
                    v = float(self.breath_intensity_var.get())
                    if abs(v - 0.25) < 0.01:
                        self.breath_preset_var.set('Subtle')
                    elif abs(v - 0.5) < 0.01:
                        self.breath_preset_var.set('Normal')
                    elif abs(v - 0.85) < 0.01:
                        self.breath_preset_var.set('Pronounced')
                    else:
                        self.breath_preset_var.set('Custom')
                except Exception:
                    pass

            self.breath_intensity_var.trace_add('write', _on_slider_change)
        except Exception:
            pass

        # Status
        self.audio_status = ttk.Label(audio_frame, text="Bereit", foreground=self.colors["success"])
        self.audio_status.pack(pady=5)

        # Wellenform-Canvas (Platzhalter)
        self.waveform_canvas = tk.Canvas(audio_frame, bg=self.colors["editor_bg"], height=100)
        self.waveform_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        # Playlist (near-realtime queue)
        playlist_frame = ttk.LabelFrame(audio_frame, text="Playlist (Near‑Realtime)", padding=6)
        playlist_frame.pack(fill=tk.BOTH, expand=False, pady=(6,0))

        self.playlist_listbox = tk.Listbox(playlist_frame, height=4)
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pl_ctrl = ttk.Frame(playlist_frame)
        pl_ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(pl_ctrl, text="Skip", command=self._playlist_skip).pack(fill=tk.X, pady=2)
        ttk.Button(pl_ctrl, text="Remove", command=self._playlist_remove).pack(fill=tk.X, pady=2)

        # Crossfade control
        cf_frame = ttk.Frame(audio_frame)
        cf_frame.pack(fill=tk.X, pady=(6,0))
        ttk.Label(cf_frame, text="Crossfade (s):").pack(side=tk.LEFT)
        self.crossfade_seconds = tk.DoubleVar(value=0.5)
        cf_slider = ttk.Scale(cf_frame, from_=0.0, to=2.0, variable=self.crossfade_seconds, orient=tk.HORIZONTAL)
        cf_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

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
        """Erstelle Status-Leiste (verwende `components.StatusBar`)."""
        try:
            from .components import StatusBar

            self.statusbar = StatusBar(self.root)
            self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        except Exception:
            # fallback to original simplistic status frame
            status_frame = ttk.Frame(self.root)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X)

            self.status_label = ttk.Label(status_frame, text="Bereit", relief=tk.SUNKEN, anchor=tk.W)
            self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=200)

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
        """Lade Projekt-Daten

        Zusätzlich zu bisherigen Feldern unterstützt diese Methode jetzt
        optional ein `tracks`-Feld, das eine Liste von Tracks/Clips enthält.
        Das ermöglicht Importer-Workflows (z.B. `project_manifest.json`) die
        Timeline direkt zu befüllen.
        """
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

        # Tracks/Clips laden (optional)
        try:
            tracks = data.get("tracks")
            if tracks and hasattr(self, "multitrack") and self.multitrack:
                # Clear existing tracks and re-create defaults
                self.multitrack.tracks = []
                # Add named tracks from project
                from .multitrack import TrackType, Track, AudioClip

                for t in tracks:
                    tname = t.get("name", "Imported Track")
                    ttype_str = t.get("type", "voice").upper()
                    try:
                        ttype = TrackType[ttype_str]
                    except Exception:
                        ttype = TrackType.VOICE

                    track_obj = Track(id=t.get("id", ""), name=tname, type=ttype)
                    # Add clips
                    for c in t.get("clips", []):
                        try:
                            clip = AudioClip(
                                id=c.get("id", ""),
                                file=Path(c.get("file")),
                                start_time=float(c.get("start_time", 0.0)),
                                duration=float(c.get("duration", 0.0)),
                                volume=float(c.get("volume", 1.0)),
                                fade_in=float(c.get("fade_in", 0.0)),
                                fade_out=float(c.get("fade_out", 0.0)),
                                metadata=c.get("metadata", {}),
                            )
                            track_obj.add_clip(clip)
                        except Exception:
                            # Skip malformed clips
                            continue

                    self.multitrack.tracks.append(track_obj)

                # Rebuild UI for multitrack
                try:
                    self.multitrack._rebuild_mixer()
                    self.multitrack._render_timeline()
                except Exception:
                    pass
        except Exception:
            # Non-fatal: keep proceeding with remaining data
            pass

        self.update_speakers_list()
        self.update_info()
        # If structured script present, normalize into blocks and render
        try:
            blocks = normalize_script(data)
            if blocks:
                self.script_data = blocks
                try:
                    if getattr(self, 'block_view_var', tk.BooleanVar(value=False)).get():
                        self.render_blocks()
                except Exception:
                    pass
        except Exception:
            pass
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

    def _on_preview_selected_voice(self):
        """Preview the currently selected voice from the voice list."""
        sel = self.voice_listbox.curselection()
        if not sel:
            messagebox.showwarning("Keine Auswahl", "Bitte eine Stimme auswählen")
            return
        idx = sel[0]
        language = self.lang_var.get()
        style = self.style_var.get() or None
        voices = self.voice_library.search(language=language, style=style)
        if idx >= len(voices):
            return
        voice = voices[idx]
        try:
            # Run preview off the UI thread to avoid blocking
            from ..voices.manager import preview_voice

            def _run_preview():
                try:
                    preview_voice(voice.id, sample_text="Hallo, dies ist eine Vorschau der Stimme.")
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Vorschau fehlgeschlagen", str(e)))

            threading.Thread(target=_run_preview, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Vorschau fehlgeschlagen", str(e))

    def _voice_drag_start(self, event):
        try:
            idx = self.voice_listbox.nearest(event.y)
            self.voice_listbox.selection_clear(0, tk.END)
            self.voice_listbox.selection_set(idx)
            self._dragged_voice_index = idx
        except Exception:
            self._dragged_voice_index = None

    def _on_voice_right_click(self, event):
        """Show context menu for voice list (Preview)."""
        try:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Vorschau", command=lambda: self._on_preview_selected_voice())
            menu.add_command(label="Als Sprecher verwenden", command=self.use_voice_as_speaker)
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _voice_drag_motion(self, event):
        # Provide visual feedback: highlight the line under the mouse
        try:
            x_root = self.root.winfo_pointerx() - self.script_editor.winfo_rootx()
            y_root = self.root.winfo_pointery() - self.script_editor.winfo_rooty()
            index = self.script_editor.index(f"@{x_root},{y_root}")
            line_no = index.split('.')[0]

            if self._drag_highlight_line != line_no:
                # remove previous
                if self._drag_highlight_line is not None:
                    try:
                        self.script_editor.tag_remove("drag_highlight", f"{self._drag_highlight_line}.0", f"{self._drag_highlight_line}.end")
                    except Exception:
                        pass

                # add new
                try:
                    self.script_editor.tag_add("drag_highlight", f"{line_no}.0", f"{line_no}.end")
                    self._drag_highlight_line = line_no
                except Exception:
                    self._drag_highlight_line = None
        except Exception:
            pass

    def _voice_drop_on_editor(self, event):
        """Handle drop of a voice onto the editor: assign that voice as speaker for the line under cursor."""
        if self._dragged_voice_index is None:
            return
        try:
            # Determine which voice was dragged
            idx = self._dragged_voice_index
            language = self.lang_var.get()
            style = self.style_var.get() or None
            voices = self.voice_library.search(language=language, style=style)
            if idx >= len(voices):
                return
            voice = voices[idx]

            # Determine line index under mouse
            x_root = self.root.winfo_pointerx() - self.script_editor.winfo_rootx()
            y_root = self.root.winfo_pointery() - self.script_editor.winfo_rooty()
            try:
                index = self.script_editor.index(f"@{x_root},{y_root}")
            except Exception:
                index = self.script_editor.index(tk.INSERT)

            line_no = index.split('.')[0]
            # Get current line text
            line_text = self.script_editor.get(f"{line_no}.0", f"{line_no}.end")

            # Create Speaker object from voice and add to speakers list
            try:
                from ..voices.manager import speaker_from_voice

                new_speaker = speaker_from_voice(voice.id, speaker_name=voice.display_name)
                # insert into speakers dict keyed by name
                self.speakers[new_speaker.name] = new_speaker
                self.update_speakers_list()
            except Exception as e:
                print("Could not create speaker from voice:", e)

            # Use structured prefix for the line
            speaker_label = voice.display_name
            if ':' in line_text and line_text.split(':', 1)[0].strip() in self.speakers:
                parts = line_text.split(':', 1)
                new_line = f"{speaker_label}: {parts[1].lstrip()}"
            else:
                new_line = f"{speaker_label}: {line_text}"

            # mark undo boundary so text widget undo handles this as single action
            try:
                self.script_editor.edit_separator()
            except Exception:
                pass

            # Replace line
            self.script_editor.delete(f"{line_no}.0", f"{line_no}.end")
            self.script_editor.insert(f"{line_no}.0", new_line)
            self.update_status(f"Zugeordnet: {speaker_label} -> Zeile {line_no}")

            # cleanup highlight
            if self._drag_highlight_line is not None:
                try:
                    self.script_editor.tag_remove("drag_highlight", f"{self._drag_highlight_line}.0", f"{self._drag_highlight_line}.end")
                except Exception:
                    pass
                self._drag_highlight_line = None

        except Exception as e:
            print("Drag&Drop assign failed:", e)
        finally:
            self._dragged_voice_index = None

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

    def _playlist_skip(self):
        """Skip current item by stopping playback; queue worker will continue."""
        try:
            self.audio_player.stop()
            # remove first item in listbox
            try:
                if self.playlist_listbox.size() > 0:
                    self.playlist_listbox.delete(0)
            except Exception:
                pass
        except Exception:
            pass

    def _playlist_remove(self):
        """Remove selected playlist item without playing."""
        try:
            sel = self.playlist_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            self.playlist_listbox.delete(idx)
            # Note: For simplicity we don't remove from internal queue; queue will skip when popped if file missing
        except Exception:
            pass

    def open_generate_dialog(self):
        """Open the Generate Project dialog (skeleton)."""
        dlg = GenerateProjectDialog(self.root)
        self.root.wait_window(dlg.window)
        if getattr(dlg, 'result', None):
            cfg = dlg.result
            # For now: just show a simple confirmation and publish an event
            self.update_status(f"Generate requested: engine={cfg.get('engine')} workers={cfg.get('max_workers')}")
            try:
                eb = get_event_bus()
                eb.publish('script.generate.request', cfg)
            except Exception:
                pass

    def _on_generate_request(self, cfg):
        """Event handler: start a real generation run in background."""
        # remember last generate config (used for Retry engine selection)
        try:
            self._last_generate_cfg = cfg
        except Exception:
            self._last_generate_cfg = None

        threading.Thread(target=self._run_generate, args=(cfg,), daemon=True).start()

    def _run_generate(self, cfg):
        """Perform generation: write a simple script from draft items and call orchestrator."""
        try:
            if not self._draft_items:
                self.root.after(0, lambda: messagebox.showwarning('No Draft', 'Bitte zuerst Draft importieren oder erstellen.'))
                return

            # Ask user for output directory
            out_dir = filedialog.askdirectory(title='Select output directory for generation')
            if not out_dir:
                return

            # Create a temp script file (JSON list expected by synthesize_script_preview)
            tmpdir = tempfile.mkdtemp(prefix='pf_script_')
            script_path = Path(tmpdir) / 'script.json'
            content = []
            for u in self._draft_items:
                content.append({'speaker': u.get('speaker') or 'narrator', 'text': u.get('text') or ''})
            script_path.write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')


            # Open progress modal
            self.root.after(0, lambda: self._open_progress_modal(self._draft_items))
            self.root.after(0, lambda: self.update_status('Starte Generierung...'))

            # cooperative cancellation event (shared with UI)
            try:
                self._generation_cancel_event = threading.Event()
            except Exception:
                self._generation_cancel_event = None

            res = synthesize_script_preview(
                str(script_path),
                out_dir,
                engine=cfg.get('engine'),
                max_workers=cfg.get('max_workers', 2),
                cache_dir=str(Path(out_dir) / 'cache'),
                cancel_event=self._generation_cancel_event,
                spatialize=bool(getattr(self, 'spatialize_var', tk.BooleanVar(value=False)).get()),
                spatial_params={'default': {'azimuth': float(getattr(self, 'spatial_az_var', tk.DoubleVar(value=0.0)).get()), 'distance': float(getattr(self, 'spatial_dist_var', tk.DoubleVar(value=1.0)).get())}},
                spatial_target_sr=44100,
                prosody={'rate': float(getattr(self, 'prosody_rate_var', tk.DoubleVar(value=1.0)).get()), 'pitch_cents': float(getattr(self, 'prosody_pitch_var', tk.DoubleVar(value=0.0)).get()), 'energy': float(getattr(self, 'prosody_energy_var', tk.DoubleVar(value=1.0)).get())},
                insert_breaths=bool(getattr(self, 'insert_breaths_var', tk.BooleanVar(value=False)).get()),
                breath_intensity=float(getattr(self, 'breath_intensity_var', tk.DoubleVar(value=0.5)).get()),
            )

            if res.get('ok'):
                preview = res.get('preview_path') or res.get('preview')
                self.root.after(0, lambda: messagebox.showinfo('Fertig', f"Generierung fertig: {preview}"))
                # attempt to play preview
                try:
                    self.audio_player.play(Path(preview))
                except Exception:
                    pass
            else:
                self.root.after(0, lambda: messagebox.showerror('Generierung fehlgeschlagen', res.get('message', 'unknown')))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Generierung Fehler', str(e)))
        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
            # close progress modal if open
            try:
                self.root.after(0, lambda: self._close_progress_modal())
            except Exception:
                pass
            # clear cancel event
            try:
                self._generation_cancel_event = None
            except Exception:
                pass

    def _on_script_progress(self, data):
        """Receive per-utterance progress events and update UI."""
        try:
            idx = data.get('idx')
            status = data.get('status')
            task_id = data.get('task_id')
            progress_val = data.get('progress')

            def _update():
                # Update status bar
                try:
                    self.update_status(f"TTS [{idx}]: {status}")
                except Exception:
                    pass

                # Update progress tree if present
                try:
                    if getattr(self, '_progress_map', None) and idx is not None:
                        # idx may be integer-like or string; normalize
                        try:
                            key = int(idx)
                        except Exception:
                            # try to parse trailing digits
                            try:
                                key = int(''.join([c for c in str(idx) if c.isdigit()]))
                            except Exception:
                                key = None

                        if key is not None and key in self._progress_map:
                            node = self._progress_map.get(key)
                            # map statuses to user-friendly states / tags
                            disp = str(status)
                            tag = 'idle'
                            if disp in ('start', 'processing'):
                                tag = 'processing'
                                disp = 'processing'
                                # record start time
                                try:
                                    self._progress_start_times[key] = time.time()
                                    # set progress column to 0%
                                    self._progress_tree.set(node, 'progress', '0%')
                                except Exception:
                                    pass
                            elif disp == 'done':
                                tag = 'done'
                                disp = 'done'
                                # compute duration
                                try:
                                    start = self._progress_start_times.get(key)
                                    if start:
                                        elapsed = time.time() - start
                                        self._progress_tree.set(node, 'duration', f"{elapsed:.1f}s")
                                    self._progress_tree.set(node, 'progress', '100%')
                                except Exception:
                                    pass
                            elif disp == 'failed':
                                tag = 'failed'
                                disp = 'failed'
                                try:
                                    self._progress_tree.set(node, 'progress', '0%')
                                except Exception:
                                    pass
                            elif disp == 'retrying':
                                tag = 'retrying'
                                try:
                                    # append retry history note
                                    self._progress_retry_history.setdefault(key, []).append(('retry', time.time()))
                                    if getattr(self, '_progress_log', None):
                                        self._progress_log.insert(tk.END, f"Retry started for idx {key}\n")
                                        self._progress_log.see(tk.END)
                                except Exception:
                                    pass
                            elif disp == 'cancelled':
                                tag = 'cancelled'
                                disp = 'cancelled'
                                try:
                                    self._progress_tree.set(node, 'progress', '0%')
                                    self._progress_tree.set(node, 'duration', 'cancelled')
                                    if getattr(self, '_progress_log', None):
                                        self._progress_log.insert(tk.END, f"Utterance {key} cancelled\n")
                                        self._progress_log.see(tk.END)
                                except Exception:
                                    pass

                            # set the 'status' column
                            try:
                                self._progress_tree.set(node, 'status', disp)
                                # set visual tag
                                try:
                                    self._progress_tree.item(node, tags=(tag,))
                                except Exception:
                                    pass
                            except Exception:
                                pass

                            # remember task id for cancellation attempts
                            try:
                                if task_id:
                                    if not hasattr(self, '_progress_task_ids'):
                                        self._progress_task_ids = {}
                                    self._progress_task_ids[key] = task_id
                            except Exception:
                                pass
                            # update progressbar if we have a numeric progress value
                            try:
                                if progress_val is not None:
                                    try:
                                        p = float(progress_val)
                                    except Exception:
                                        p = None
                                    if p is not None:
                                        # tree cell text
                                        try:
                                            self._progress_tree.set(node, 'progress', f"{int(p*100)}%")
                                        except Exception:
                                            pass
                                        # progressbar widget
                                        try:
                                            pb = getattr(self, '_progress_bars', {}).get(key)
                                            if pb:
                                                pb['value'] = max(0, min(100, int(p*100)))
                                        except Exception:
                                            pass
                                # If near-realtime is enabled and this utterance finished, play it
                                try:
                                    if self.near_realtime_var.get() and status == 'done':
                                        f = data.get('file')
                                        spk = data.get('speaker')
                                        # If a speaker filter is active, only play matching speaker
                                        try:
                                            current_speaker = (self.prop_speaker.get() or '').strip()
                                        except Exception:
                                            current_speaker = ''

                                        if f:
                                            # If speaker filter is set and doesn't match, skip
                                            if current_speaker and spk and current_speaker != spk:
                                                pass
                                            else:
                                                try:
                                                    # enqueue into playlist so crossfade/queueing works
                                                    self.audio_player.enqueue(Path(f), crossfade_sec=self.crossfade_seconds.get())
                                                    # update UI playlist listbox
                                                    try:
                                                        display = f"{spk}: {Path(f).name}"
                                                        self.playlist_listbox.insert(tk.END, display)
                                                    except Exception:
                                                        pass
                                                except Exception:
                                                    # fallback to immediate play
                                                    try:
                                                        self.audio_player.play(Path(f))
                                                    except Exception:
                                                        pass
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        # update playlist UI when utterance removed/finished
                        try:
                            if status in ('done', 'failed', 'cancelled'):
                                # remove first matching item from playlist listbox if present
                                try:
                                    for i in range(self.playlist_listbox.size()):
                                        val = self.playlist_listbox.get(i)
                                        if data.get('file') and Path(val.split(': ')[-1]).name == Path(data.get('file')).name:
                                            self.playlist_listbox.delete(i)
                                            break
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass

            self.root.after(0, _update)
        except Exception:
            pass

    def _on_script_preview_ready(self, data):
        """When the orchestrator publishes preview_ready, play and show waveform."""
        try:
            preview = data.get('preview') or data.get('preview_path')
            if not preview:
                return
            p = Path(preview)
            self.root.after(0, lambda: self.update_status(f"Preview ready: {p.name}"))
            try:
                self.audio_player.play(p)
            except Exception:
                pass
            try:
                self._update_waveform(p)
            except Exception:
                pass
        except Exception:
            pass

    # ========== Progress Modal for Generation ==========
    def _open_progress_modal(self, draft_items):
        try:
            if getattr(self, '_progress_win', None) and tk.Toplevel.winfo_exists(self._progress_win):
                return
        except Exception:
            pass

        self._progress_win = tk.Toplevel(self.root)
        self._progress_win.title('Generation Progress')
        self._progress_win.geometry('640x360')
        self._progress_win.transient(self.root)
        self._progress_win.grab_set()

        frame = ttk.Frame(self._progress_win, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        cols = ('idx', 'speaker', 'text', 'progress', 'duration', 'status')
        self._progress_tree = ttk.Treeview(frame, columns=cols, show='headings', height=10)
        for c in cols:
            self._progress_tree.heading(c, text=c.capitalize())
            if c == 'text':
                width = 240
            elif c == 'status':
                width = 100
            elif c in ('progress', 'duration'):
                width = 90
            else:
                width = 50
            self._progress_tree.column(c, width=width)
        self._progress_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Configure visual tags for status coloring
        try:
            self._progress_tree.tag_configure('idle', background='white')
            self._progress_tree.tag_configure('processing', background='#fff2cc')
            self._progress_tree.tag_configure('done', background='#d4ffd4')
            self._progress_tree.tag_configure('failed', background='#ffd4d4')
            self._progress_tree.tag_configure('retrying', background='#d0e0ff')
            self._progress_tree.tag_configure('cancelled', background='#e0e0e0')
        except Exception:
            pass

        # populate
        self._progress_map = {}
        for i, it in enumerate(draft_items, start=1):
            idx = it.get('id') or f"i{i}"
            speaker = it.get('speaker') or 'narrator'
            text = (it.get('text') or '')[:120]
            node = self._progress_tree.insert('', tk.END, values=(i, speaker, text, '0%', '', 'idle'), tags=('idle',))
            self._progress_map[i] = node

        # create per-row progressbars (overlayed on Treeview)
        self._progress_bars = {}
        for key, node in self._progress_map.items():
            try:
                pb = ttk.Progressbar(self._progress_tree, orient=tk.HORIZONTAL, mode='determinate')
                # default 0-100
                pb['maximum'] = 100
                pb['value'] = 0
                self._progress_bars[key] = pb
            except Exception:
                self._progress_bars[key] = None

        # Position bars initially and on widget changes
        def _position_bars(event=None):
            try:
                for k, node in self._progress_map.items():
                    pb = self._progress_bars.get(k)
                    if not pb:
                        continue
                    try:
                        bbox = self._progress_tree.bbox(node, 'progress')
                        if not bbox:
                            # hide offscreen
                            pb.place_forget()
                            continue
                        x, y, w, h = bbox
                        # small padding
                        px = x + 4
                        py = y + 2
                        pw = max(40, w - 8)
                        ph = max(12, h - 4)
                        pb.place(x=px, y=py, width=pw, height=ph)
                    except Exception:
                        try:
                            pb.place_forget()
                        except Exception:
                            pass
            except Exception:
                pass

        # bind repositioning
        try:
            self._progress_tree.bind('<Configure>', _position_bars)
            self._progress_tree.bind('<Expose>', _position_bars)
            # mouse wheel / scroll - reposition after scroll events
            self._progress_tree.bind('<MouseWheel>', _position_bars)
            self._progress_tree.bind('<Button-4>', _position_bars)
            self._progress_tree.bind('<Button-5>', _position_bars)
        except Exception:
            pass

        # ensure initial placement
        try:
            self.root.after(100, _position_bars)
        except Exception:
            pass

        # Attach a vertical scrollbar and hook its commands to reposition bars robustly
        try:
            vscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=lambda *a: (self._progress_tree.yview(*a), self.root.after(0, _position_bars)))
            vscroll.pack(side=tk.RIGHT, fill=tk.Y)
            # ensure treeview updates scrollbar and repositions bars on scroll
            self._progress_tree.configure(yscrollcommand=lambda *a: (vscroll.set(*a), self.root.after(0, _position_bars)))
        except Exception:
            pass

        # map of idx -> task_id for cancellation
        self._progress_task_ids = {}
        # start times for duration calculation
        self._progress_start_times = {}
        # retry history per idx
        self._progress_retry_history = {}

        # Log area
        self._progress_log = scrolledtext.ScrolledText(frame, height=6, state=tk.NORMAL)
        self._progress_log.pack(fill=tk.BOTH, expand=False, side=tk.BOTTOM, pady=(6, 0))
        try:
            self._progress_log.insert(tk.END, 'Generation log:\n')
        except Exception:
            pass

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, side=tk.BOTTOM, pady=6)

        ttk.Button(btns, text='Retry Selected', command=self._retry_selected).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btns, text='Cancel', command=self._cancel_generation).pack(side=tk.RIGHT, padx=4)

        self._generation_cancelled = False

    def _close_progress_modal(self):
        try:
            if getattr(self, '_progress_win', None):
                try:
                    self._progress_win.grab_release()
                except Exception:
                    pass
                try:
                    self._progress_win.destroy()
                except Exception:
                    pass
                self._progress_win = None
        except Exception:
            pass

    def _cancel_generation(self):
        self._generation_cancelled = True
        # set cooperative cancel event if present
        try:
            if hasattr(self, '_generation_cancel_event') and self._generation_cancel_event is not None:
                try:
                    self._generation_cancel_event.set()
                except Exception:
                    pass
        except Exception:
            pass
        # Attempt to cancel running/pending synth tasks via ThreadManager
        try:
            tm = get_thread_manager()
            if hasattr(self, '_progress_task_ids'):
                for idx, tid in list(self._progress_task_ids.items()):
                    try:
                        cancelled = tm.cancel_task(tid)
                        if cancelled:
                            # update UI row
                            try:
                                node = self._progress_map.get(idx)
                                if node:
                                    self._progress_tree.set(node, 'status', 'cancelled')
                                    self._progress_tree.item(node, tags=('cancelled',))
                                    # log cancellation
                                    try:
                                        if getattr(self, '_progress_log', None):
                                            self._progress_log.insert(tk.END, f"Task {tid} cancelled (idx {idx})\n")
                                            self._progress_log.see(tk.END)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception:
            pass

        self.update_status('Generation cancelled')

    def _retry_selected(self):
        sel = self._progress_tree.selection()
        if not sel:
            messagebox.showinfo('Retry', 'Bitte eine Utterance auswählen')
            return
        item = sel[0]
        vals = self._progress_tree.item(item, 'values')
        try:
            idx = int(vals[0])
        except Exception:
            messagebox.showerror('Retry', 'Konnte Index nicht bestimmen')
            return

        # Build a single-entry script for retry
        try:
            di = None
            if idx-1 < len(self._draft_items):
                di = self._draft_items[idx-1]
            if di is None:
                messagebox.showerror('Retry', 'Utterance nicht gefunden')
                return

            tmpdir = tempfile.mkdtemp(prefix='pf_retry_')
            script_path = Path(tmpdir) / 'script.json'
            content = [{'speaker': di.get('speaker') or 'narrator', 'text': di.get('text') or ''}]
            script_path.write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')

            out_dir = filedialog.askdirectory(title='Select output directory for retry')
            if not out_dir:
                shutil.rmtree(tmpdir)
                return

            # run synthesize for single utterance in a background thread
            def _retry_thread():
                try:
                    self.root.after(0, lambda: self._progress_tree.set(self._progress_map[idx], 'status', 'retrying'))
                    # choose engine from last generate config if available
                    engine_choice = 'PIPER'
                    try:
                        engine_choice = (self._last_generate_cfg.get('engine') if getattr(self, '_last_generate_cfg', None) else 'PIPER') or 'PIPER'
                    except Exception:
                        engine_choice = 'PIPER'
                    # log retry
                    try:
                        if getattr(self, '_progress_log', None):
                            self._progress_log.insert(tk.END, f"Retry idx {idx} using engine {engine_choice}\n")
                            self._progress_log.see(tk.END)
                    except Exception:
                        pass

                    res = synthesize_script_preview(
                        str(script_path),
                        out_dir,
                        engine=engine_choice,
                        max_workers=1,
                        cache_dir=str(Path(out_dir)/'cache'),
                        spatialize=bool(getattr(self, 'spatialize_var', tk.BooleanVar(value=False)).get()),
                        spatial_params={'default': {'azimuth': float(getattr(self, 'spatial_az_var', tk.DoubleVar(value=0.0)).get()), 'distance': float(getattr(self, 'spatial_dist_var', tk.DoubleVar(value=1.0)).get())}},
                        spatial_target_sr=44100,
                        prosody={'rate': float(getattr(self, 'prosody_rate_var', tk.DoubleVar(value=1.0)).get()), 'pitch_cents': float(getattr(self, 'prosody_pitch_var', tk.DoubleVar(value=0.0)).get()), 'energy': float(getattr(self, 'prosody_energy_var', tk.DoubleVar(value=1.0)).get())},
                        insert_breaths=bool(getattr(self, 'insert_breaths_var', tk.BooleanVar(value=False)).get()),
                        breath_intensity=float(getattr(self, 'breath_intensity_var', tk.DoubleVar(value=0.5)).get()),
                    )
                    if res.get('ok'):
                        self.root.after(0, lambda: self._progress_tree.set(self._progress_map[idx], 'status', 'done'))
                        message = 'Retry successful'
                        self.root.after(0, lambda: self.update_status(message))
                    else:
                        self.root.after(0, lambda: self._progress_tree.set(self._progress_map[idx], 'status', 'failed'))
                finally:
                    try:
                        shutil.rmtree(tmpdir)
                    except Exception:
                        pass

            threading.Thread(target=_retry_thread, daemon=True).start()

        except Exception as e:
            messagebox.showerror('Retry failed', str(e))


class GenerateProjectDialog:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Generate Project")
        self.window.geometry("420x220")
        self.result = None

        frame = ttk.Frame(self.window, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Engine:").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.engine_var = tk.StringVar(value="PIPER")
        ttk.Combobox(frame, textvariable=self.engine_var, values=["PIPER", "BARK", "XTTS"], width=16).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(frame, text="Max Workers:").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.workers_var = tk.IntVar(value=2)
        ttk.Spinbox(frame, from_=1, to=16, textvariable=self.workers_var, width=6).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Mix Policy:").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.mix_var = tk.StringVar(value="concat")
        ttk.Combobox(frame, textvariable=self.mix_var, values=["concat", "crossfade", "ducking"], width=16).grid(row=2, column=1, sticky=tk.W)

        self.dry_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Dry Run (no heavy deps)", variable=self.dry_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=6)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=8)
        ttk.Button(btn_frame, text="Start", command=self._on_start).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)

    def _on_start(self):
        self.result = {
            'engine': self.engine_var.get(),
            'max_workers': int(self.workers_var.get()),
            'mix_policy': self.mix_var.get(),
            'dry_run': bool(self.dry_var.get()),
        }
        self.window.destroy()

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
