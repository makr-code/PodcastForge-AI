"""
Main GUI window for PodcastForge editor.
Provides Menubar, Toolbar, Left Sidebar, Content area, Right Sidebar,
AI Chat / Audio / Spectrum panes, and Statusbar.

Implements OOP structure, uses existing threading_base ThreadManager for background tasks
and a Queue for communicating long-running task progress to the UI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import queue
import threading
import time
import tempfile
import wave
import os
from pathlib import Path
import numpy as _np
import json

from ..gui.threading_base import get_thread_manager
from ..core.events import get_event_bus
from ..core.settings import get_setting, set_setting
from ..tts.engine_manager import get_engine_manager, TTSEngine
from .components import StatusBar, apply_theme
from ..audio.player import get_player
from .settings_dialog import SettingsDialog
import tkinter.font as tkfont

try:
    from ..llm.ollama_client import OllamaClient
except Exception:
    OllamaClient = None


class MainWindow(tk.Tk):
    """Main application window composed of UI regions.

    Regions:
    - menubar
    - toolbar
    - left sidebar (voices, speakers)
    - content (editor/timeline)
    - right sidebar (properties, AI chat, audio controls, spectrum)
    - statusbar
    """

    def __init__(self):
        super().__init__()
        self.title("PodcastForge Editor")
        self.geometry("1200x800")

        # Threading and queue for background task updates
        self._task_queue: "queue.Queue[tuple[str, dict]]" = queue.Queue()
        self.thread_manager = get_thread_manager(max_workers=4)

        # Playback state (init early so toolbar can read it)
        self._last_preview_file: Optional[Path] = None
        self.auto_play = True

        # Apply common theme and build layout frames
        apply_theme(self)
        # Apply persisted theme if present
        try:
            theme = get_setting("ui.theme", None)
            if theme:
                try:
                    ttk.Style().theme_use(theme)
                except Exception:
                    pass
        except Exception:
            pass
        self._create_menu()
        self._create_toolbar()
        self._create_main_panes()
        # status bar (shared component)
        self.statusbar = StatusBar(self)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Playback state
        self._last_preview_file: Optional[Path] = None
        self.auto_play = True

        # Start periodic UI update loop to consume queue
        self.after(100, self._process_task_queue)

        # Apply persisted editor font size if present
        try:
            fsz = int(get_setting("ui.editor_font_size", 11))
            try:
                cur_font = tkfont.Font(font=self.editor_text["font"]) if hasattr(self, "editor_text") else None
                if cur_font:
                    cur_font.configure(size=fsz)
                    self.editor_text.configure(font=cur_font)
            except Exception:
                pass
        except Exception:
            pass

        # Show last project in status bar if available
        try:
            last = get_setting("ui.last_project", "")
            if last:
                self._set_status(f"Letztes Projekt: {last}")
        except Exception:
            pass

        # Subscribe to integration events (ebook2audiobook)
        try:
            bus = get_event_bus()
            bus.subscribe("ebook2audiobook.tts_progress", self._on_ebook_tts_progress)
            bus.subscribe("ebook2audiobook.project_ready", self._on_ebook_project_ready)
            bus.subscribe("ebook2audiobook.open_project", self._on_ebook_open_project)
        except Exception:
            pass

    # -------------------- UI Construction --------------------
    def _create_menu(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open...", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo")
        edit_menu.add_command(label="Redo")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # TTS menu
        tts_menu = tk.Menu(menubar, tearoff=0)
        tts_menu.add_command(label="Preload Engines", command=self._on_preload_engines)
        tts_menu.add_command(label="Unload Engines", command=self._on_unload_engines)
        menubar.add_cascade(label="TTS", menu=tts_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Settings...", command=self._on_settings)
        help_menu.add_command(label="About", command=self._on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(4, 2))
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_new = ttk.Button(toolbar, text="New", command=self._on_new)
        btn_open = ttk.Button(toolbar, text="Open", command=self._on_open)
        btn_save = ttk.Button(toolbar, text="Save", command=self._on_save)
        btn_preview = ttk.Button(toolbar, text="Preview", command=self._on_preview)
        btn_play = ttk.Button(toolbar, text="Play", command=self._on_play_audio)
        btn_stop = ttk.Button(toolbar, text="Stop", command=self._on_stop_audio)

        # load persisted auto_play setting
        persisted = get_setting("ui.auto_play", True)
        self.auto_play = bool(persisted)

        auto_var = tk.BooleanVar(value=self.auto_play)

        def _on_toggle_auto():
            self.auto_play = bool(auto_var.get())
            try:
                set_setting("ui.auto_play", self.auto_play)
            except Exception:
                pass

        auto_check = ttk.Checkbutton(toolbar, text="Auto-Play", variable=auto_var, command=_on_toggle_auto)

        for w in (btn_new, btn_open, btn_save, btn_preview, btn_play, btn_stop, auto_check):
            w.pack(side=tk.LEFT, padx=2)

    def _create_main_panes(self):
        # Paned window to create resizable regions
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left sidebar frame
        left_frame = ttk.Frame(paned, width=220)
        self._populate_left_sidebar(left_frame)

        # Center content frame
        center_frame = ttk.Frame(paned)
        self._populate_center_content(center_frame)

        # Right sidebar frame
        right_frame = ttk.Frame(paned, width=320)
        self._populate_right_sidebar(right_frame)

        paned.add(left_frame, weight=1)
        paned.add(center_frame, weight=4)
        paned.add(right_frame, weight=2)

    def _create_statusbar(self):
        # kept for backwards compatibility; new code uses StatusBar
        self.statusbar = StatusBar(self)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_ebook_tts_progress(self, data: dict):
        try:
            # data: {task_id, chapter, paragraph, status}
            status = data.get("status")
            tid = data.get("task_id")
            ch = data.get("chapter")
            para = data.get("paragraph")
            if status == "start":
                self._set_status(f"TTS started: {tid} (ch{ch} p{para})")
            elif status == "done":
                self._set_status(f"TTS done: {tid} (ch{ch} p{para})")
            elif status == "error":
                self._set_status(f"TTS error: {tid} - {data.get('error')}")
        except Exception:
            pass

    def _on_ebook_project_ready(self, data: dict):
        try:
            manifest = data.get("manifest")
            total = data.get("total_duration")
            self._set_status(f"Projekt fertig: {Path(manifest).name} ({total:.1f}s)")
        except Exception:
            pass

    def _on_ebook_open_project(self, data: dict):
        try:
            project_path = data.get("project") or data.get("manifest")
            if not project_path:
                return
            p = Path(project_path)
            if not p.exists():
                self._set_status(f"Import-Projekt nicht gefunden: {p.name}")
                return

            # Open full editor and attempt to load the imported project
            editor = self._open_full_editor()
            # If the editor was created and exposes `load_project_data`, load it
            try:
                content = p.read_text(encoding="utf-8")
                data = json.loads(content)
            except Exception:
                data = None

            if editor and data:
                try:
                    # PodcastEditor provides load_project_data
                    if hasattr(editor, 'load_project_data'):
                        editor.load_project_data(data)
                        self._set_status(f"Projekt importiert: {p.name}")
                except Exception:
                    self._set_status(f"Import fehlgeschlagen: {p.name}")
        except Exception:
            pass

    # -------------------- Populate Regions --------------------
    def _populate_left_sidebar(self, parent: ttk.Frame):
        # Voices / Speakers list
        lbl = ttk.Label(parent, text="Voices / Speakers")
        lbl.pack(anchor=tk.W, padx=6, pady=(6, 0))

        self.voice_list = tk.Listbox(parent, height=20)
        self.voice_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # quick search
        self.voice_search_var = tk.StringVar()
        search = ttk.Entry(parent, textvariable=self.voice_search_var)
        search.pack(fill=tk.X, padx=6)
        search.bind("<KeyRelease>", self._on_voice_search)

    def _populate_center_content(self, parent: ttk.Frame):
        # Top: editor / timeline tabs
        tabs = ttk.Notebook(parent)
        tabs.pack(fill=tk.BOTH, expand=True)

        editor_frame = ttk.Frame(tabs)
        content_frame = ttk.Frame(tabs)
        timeline_frame = ttk.Frame(tabs)

        # Simple Text editor (lightweight placeholder)
        self.editor_text = tk.Text(editor_frame)
        self.editor_text.pack(fill=tk.BOTH, expand=True)

        # Button to open the full-featured PodcastEditor in a separate window
        open_btn = ttk.Button(
            editor_frame, text="Open Full Editor", command=self._open_full_editor
        )
        open_btn.pack(side=tk.BOTTOM, pady=6)

        # Timeline: embed the real MultiTrackEditor component
        try:
            from .multitrack import MultiTrackEditor

            self.multitrack = MultiTrackEditor(timeline_frame)
            self.multitrack.pack(fill=tk.BOTH, expand=True)
        except Exception:
            # Fallback placeholder if import fails
            timeline_label = ttk.Label(timeline_frame, text="Timeline / Multitrack Editor")
            timeline_label.pack(fill=tk.BOTH, expand=True)

        tabs.add(editor_frame, text="Editor")
        tabs.add(content_frame, text="Content")
        tabs.add(timeline_frame, text="Timeline")

        # Content tab: load text/pdf and highlight passages
        self._setup_content_tab(content_frame)

    def _setup_content_tab(self, parent: ttk.Frame):
        # layout: left = content text, right = highlights list
        paned = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned, width=260)
        paned.add(left, weight=3)
        paned.add(right, weight=1)

        ctl_frame = ttk.Frame(left)
        ctl_frame.pack(fill=tk.X, padx=6, pady=6)

        btn_load = ttk.Button(ctl_frame, text="Load File", command=self._on_load_content_file)
        btn_load.pack(side=tk.LEFT, padx=4)

        btn_highlight = ttk.Button(ctl_frame, text="Highlight Selection", command=self._on_highlight_selection)
        btn_highlight.pack(side=tk.LEFT, padx=4)

        btn_clear = ttk.Button(ctl_frame, text="Clear Highlights", command=self._on_clear_highlights)
        btn_clear.pack(side=tk.LEFT, padx=4)

        btn_insert = ttk.Button(ctl_frame, text="Insert into Script", command=self._on_insert_into_script)
        btn_insert.pack(side=tk.RIGHT, padx=4)

        btn_send_sel = ttk.Button(ctl_frame, text="Send Selection to AI", command=self._on_send_selection_to_ai)
        btn_send_sel.pack(side=tk.RIGHT, padx=4)

        btn_send_all = ttk.Button(ctl_frame, text="Send Whole to AI", command=self._on_send_whole_content_to_ai)
        btn_send_all.pack(side=tk.RIGHT, padx=4)
        
        btn_export = ttk.Button(ctl_frame, text="Export Highlights", command=self._on_export_highlights)
        btn_export.pack(side=tk.RIGHT, padx=4)

        # Text display for content (left)
        self.content_text = tk.Text(left, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))
        # highlight tag
        try:
            self.content_text.tag_configure("highlight", background="#fff176")
        except Exception:
            pass

        # Right: highlights listbox
        ttk.Label(right, text="Highlights").pack(anchor=tk.W, padx=6, pady=(6,0))
        self.highlights_listbox = tk.Listbox(right, height=20)
        self.highlights_listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.highlights_listbox.bind("<<ListboxSelect>>", self._on_highlight_selected)

        # store highlights as list of (start, end, snippet)
        self.content_highlights = []
        # context menu for quick actions
        try:
            self._content_menu = tk.Menu(self.content_text, tearoff=0)
            self._content_menu.add_command(label="Highlight Selection", command=self._on_highlight_selection)
            self._content_menu.add_command(label="Insert into Script", command=self._on_insert_into_script)
            self._content_menu.add_command(label="Send Selection to AI", command=self._on_send_selection_to_ai)
            self._content_menu.add_separator()
            self._content_menu.add_command(label="Clear Highlights", command=self._on_clear_highlights)
            self.content_text.bind("<Button-3>", self._on_content_right_click)
        except Exception:
            self._content_menu = None

    def _on_load_content_file(self):
        path = filedialog.askopenfilename(title="Open content file", filetypes=[("Text/Markdown", "*.txt;*.md"), ("PDF", "*.pdf"), ("All files", "*")])
        if not path:
            return

        try:
            text = ""
            if path.lower().endswith(".pdf"):
                try:
                    import PyPDF2

                    with open(path, "rb") as fh:
                        reader = PyPDF2.PdfReader(fh)
                        pages = []
                        for p in reader.pages:
                            try:
                                pages.append(p.extract_text() or "")
                            except Exception:
                                pages.append("")
                        text = "\n\n".join(pages)
                except Exception:
                    messagebox.showwarning("PDF not supported", "PyPDF2 is not installed or PDF parsing failed. Only .txt/.md supported in this environment.")
                    return
            else:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()

            self.content_text.delete("1.0", tk.END)
            self.content_text.insert(tk.END, text)
            set_setting("ui.last_project", path)
            self._set_status(f"Content geladen: {Path(path).name}")
        except Exception as e:
            self._set_status(f"Fehler beim Laden: {e}")

    def _on_highlight_selection(self):
        try:
            sel = self.content_text.tag_ranges(tk.SEL)
            if not sel:
                self._set_status("Keine Auswahl zum Markieren")
                return
            start = sel[0]
            end = sel[1]
            snippet = self.content_text.get(start, end).strip()
            # apply tag
            self.content_text.tag_add("highlight", start, end)
            self.content_highlights.append((str(start), str(end), snippet))
            self._update_highlight_list()
            self._set_status("Auswahl markiert")
        except Exception:
            self._set_status("Fehler beim Markieren")

    def _on_clear_highlights(self):
        try:
            self.content_text.tag_remove("highlight", "1.0", tk.END)
            self.content_highlights.clear()
            self._update_highlight_list()
            self._set_status("Highlights gelöscht")
        except Exception:
            self._set_status("Fehler beim Löschen der Highlights")

    def _on_content_right_click(self, event):
        try:
            if self._content_menu:
                # position the click and show menu
                self.content_text.focus_set()
                self._content_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self._content_menu.grab_release()
            except Exception:
                pass

    def _on_export_highlights(self):
        if not self.content_highlights:
            messagebox.showinfo("Keine Highlights", "Es sind keine Highlights vorhanden, die exportiert werden können.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json"), ("Markdown", "*.md"), ("All files", "*")], title="Export Highlights")
        if not path:
            return

        try:
            if path.lower().endswith(".json"):
                import json

                payload = []
                for start, end, snippet in self.content_highlights:
                    payload.append({"start": start, "end": end, "text": snippet})
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
            else:
                # markdown
                with open(path, "w", encoding="utf-8") as fh:
                    for i, (_, _, snippet) in enumerate(self.content_highlights, start=1):
                        fh.write(f"### Highlight {i}\n\n")
                        fh.write(snippet + "\n\n---\n\n")

            self._set_status(f"Highlights exportiert: {Path(path).name}")
        except Exception as e:
            self._set_status(f"Fehler beim Exportieren: {e}")

    def _on_send_selection_to_ai(self):
        try:
            sel_text = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except Exception:
            sel_text = ""

        if not sel_text:
            messagebox.showinfo("Keine Auswahl", "Bitte markieren Sie zuerst einen Textabschnitt, oder verwenden Sie 'Send Whole to AI'.")
            return

        prompt = (
            "Nutze den folgenden Quelltext als Grundlage für die Entwicklung eines Gesprächs. "
            "Erzeuge: 1) Kernaussagen als Stichpunkte, 2) Diskussionsfragen, 3) Ein grobes Skript-Outline.\n\n" + sel_text
        )

        # submit background task
        self._set_status("Sende Auswahl an LLM...")
        self.thread_manager.submit_task(task_fn=lambda task_id, progress_callback: self._llm_task(task_id, prompt, progress_callback), task_id="llm_selection")

    def _on_send_whole_content_to_ai(self):
        text = self.content_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Kein Inhalt", "Lade zuerst eine Datei mit Inhalt.")
            return

        prompt = (
            "Nutze den folgenden Quelltext als Grundlage für die Entwicklung eines Gesprächs. "
            "Erzeuge: 1) Kernaussagen als Stichpunkte, 2) Diskussionsfragen, 3) Ein grobes Skript-Outline.\n\n" + text
        )

        self._set_status("Sende gesamtes Dokument an LLM...")
        self.thread_manager.submit_task(task_fn=lambda task_id, progress_callback: self._llm_task(task_id, prompt, progress_callback), task_id="llm_whole")

    def _update_highlight_list(self):
        try:
            self.highlights_listbox.delete(0, tk.END)
            for i, (_, _, snippet) in enumerate(self.content_highlights):
                # keep snippet short in list
                label = snippet.replace("\n", " ")
                if len(label) > 80:
                    label = label[:77] + "..."
                self.highlights_listbox.insert(tk.END, f"{i+1}: {label}")
        except Exception:
            pass

    def _on_highlight_selected(self, event=None):
        try:
            sel = self.highlights_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            start, end, snippet = self.content_highlights[idx]
            # focus text and scroll to start
            try:
                self.content_text.see(start)
                # select range visually
                self.content_text.tag_remove(tk.SEL, "1.0", tk.END)
                self.content_text.tag_add(tk.SEL, start, end)
                self.content_text.mark_set(tk.INSERT, end)
                self.content_text.focus_set()
            except Exception:
                pass
        except Exception:
            pass

    def _on_insert_into_script(self):
        # Insert selected text or selected highlight into the main script editor at cursor
        try:
            # prefer current selection in content_text
            try:
                sel = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except Exception:
                sel = None

            if not sel:
                # if no selection, use currently selected highlight from listbox
                sel_idx = None
                try:
                    cur = self.highlights_listbox.curselection()
                    if cur:
                        sel_idx = cur[0]
                except Exception:
                    sel_idx = None

                if sel_idx is not None:
                    sel = self.content_highlights[sel_idx][2]

            if not sel:
                self._set_status("Keine Auswahl zum Einfügen")
                return

            # insert at editor cursor
            try:
                self.editor_text.insert(tk.INSERT, sel + "\n")
                self._set_status("Einfügen in Script erfolgreich")
            except Exception:
                self._set_status("Fehler beim Einfügen ins Script")
        except Exception:
            self._set_status("Fehler beim Insert-into-Script")

    def _llm_task(self, task_id: str, prompt: str, progress_callback=None):
        # Run LLM request and post result to queue
        if OllamaClient is None:
            self._task_queue.put(("done", {"task": task_id, "result": "llm_failed", "error": "Ollama client not available"}))
            return

        try:
            client = OllamaClient()
            try:
                resp = client._query_ollama(prompt, 0.7)
            except Exception as e:
                self._task_queue.put(("done", {"task": task_id, "result": "llm_failed", "error": str(e)}))
                return

            # deliver result to AI chat
            self._task_queue.put(("ai_reply", {"text": f"LLM ({task_id}):\n{resp}\n"}))
            self._task_queue.put(("done", {"task": task_id, "result": "llm_ok"}))
        except Exception as e:
            self._task_queue.put(("done", {"task": task_id, "result": "llm_failed", "error": str(e)}))
    def _populate_right_sidebar(self, parent: ttk.Frame):
        # Split right sidebar vertically into properties, AI chat, audio controls
        top = ttk.Frame(parent)
        top.pack(fill=tk.BOTH, expand=True)

        # Properties section
        prop_lbl = ttk.Label(top, text="Properties")
        prop_lbl.pack(anchor=tk.W, padx=6, pady=(6, 0))
        self.prop_tree = ttk.Treeview(top, columns=("value",), show="tree")
        self.prop_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # AI Chat section
        chat_frame = ttk.LabelFrame(parent, text="AI Chat")
        chat_frame.pack(fill=tk.BOTH, expand=False, padx=6, pady=6)
        self.chat_text = tk.Text(chat_frame, height=8)
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        chat_entry = ttk.Entry(chat_frame)
        chat_entry.pack(fill=tk.X)
        chat_entry.bind("<Return>", lambda e: self._on_chat_send(chat_entry.get()))

        # Audio controls + spectrum placeholder
        audio_frame = ttk.LabelFrame(parent, text="Audio")
        audio_frame.pack(fill=tk.X, padx=6, pady=6)
        play_btn = ttk.Button(audio_frame, text="Play", command=self._on_play_audio)
        stop_btn = ttk.Button(audio_frame, text="Stop", command=self._on_stop_audio)
        play_btn.pack(side=tk.LEFT, padx=2)
        stop_btn.pack(side=tk.LEFT, padx=2)

        spectrum_canvas = tk.Canvas(parent, height=100, bg="#111")
        spectrum_canvas.pack(fill=tk.X, padx=6, pady=6)
        self._spectrum_canvas = spectrum_canvas

    # -------------------- Event Handlers / Actions --------------------
    def _on_new(self):
        self.editor_text.delete("1.0", tk.END)
        self._set_status("New project")

    def _on_open(self):
        self._set_status("Open project (not implemented)")

    def _on_save(self):
        self._set_status("Save project (not implemented)")

    def _on_exit(self):
        self.thread_manager.shutdown()
        self.destroy()

    def _on_about(self):
        self._set_status("PodcastForge Editor — Demo")

    def _on_preview(self):
        # Submit a background preview task that uses the engine manager
        self._set_status("Generating preview (TTS engine)...")
        self.thread_manager.submit_task(task_fn=self._bg_tts_preview_task, task_id="preview_tts")

    def _on_settings(self):
        try:
            dlg = SettingsDialog(self)
            if getattr(dlg, "result", None):
                # Apply theme immediately
                try:
                    theme = get_setting("ui.theme", None)
                    if theme:
                        try:
                            ttk.Style().theme_use(theme)
                            apply_theme(self)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Apply editor font size if possible
                try:
                    fsz = int(get_setting("ui.editor_font_size", 11))
                    try:
                        cur_font = tkfont.Font(font=self.editor_text["font"]) if hasattr(self, "editor_text") else None
                        if cur_font:
                            cur_font.configure(size=fsz)
                            self.editor_text.configure(font=cur_font)
                    except Exception:
                        pass
                except Exception:
                    pass

                # update status with last project
                try:
                    last = get_setting("ui.last_project", "")
                    if last:
                        self._set_status(f"Letztes Projekt: {last}")
                except Exception:
                    pass
        except Exception as e:
            self._set_status(f"Fehler beim Öffnen der Einstellungen: {e}")

    def _on_preload_engines(self):
        # Example background job to preload engines
        self._set_status("Preloading engines...")
        self.thread_manager.submit_task(task_fn=self._bg_preload_task, task_id="preload")

    def _on_unload_engines(self):
        self._set_status("Unloading engines...")
        self.thread_manager.submit_task(task_fn=self._bg_unload_task, task_id="unload")

    def _on_voice_search(self, event=None):
        query = self.voice_search_var.get().lower()
        # placeholder: in real code query voice library
        self.voice_list.delete(0, tk.END)
        sample = ["Thorsten", "Anna", "Lisa", "Michael"]
        for v in sample:
            if query in v.lower():
                self.voice_list.insert(tk.END, v)

    def _on_chat_send(self, text: str):
        if not text:
            return
        self.chat_text.insert(tk.END, f"You: {text}\n")
        self._set_status("Sending to AI...")
        # background call to AI (placeholder)
        self.thread_manager.submit_task(task_fn=lambda task_id, progress_callback: self._simulate_ai_reply(text), task_id="ai")

    def _on_play_audio(self):
        if self._last_preview_file and Path(self._last_preview_file).exists():
            player = get_player()
            player.play(self._last_preview_file)
            self._set_status(f"Playing preview: {self._last_preview_file}")
        else:
            self._set_status("No preview available to play")

    def _on_stop_audio(self):
        player = get_player()
        player.stop()
        self._set_status("Playback stopped")

    # -------------------- Background Tasks --------------------
    def _bg_preview_task(self, task_id: str, progress_callback=None):
        # Simulate long-running TTS preview
        for i in range(5):
            time.sleep(0.6)
            self._task_queue.put(("progress", {"task": task_id, "percent": (i + 1) * 20}))
        self._task_queue.put(("done", {"task": task_id}))

    def _bg_tts_preview_task(self, task_id: str, progress_callback=None):
        """Background TTS preview using the TTSEngineManager.use_engine context manager.

        This demonstrates proper acquire/release of engines and reports simple
        progress messages to the UI queue. Engines may not be available in the
        test environment; errors are caught and reported as done with error.
        """
        mgr = get_engine_manager()
        # A short demo text; in real code use selected line text
        demo_text = self.editor_text.get("1.0", "1.0 lineend").strip() or "Hello from PodcastForge"
        # simple speaker placeholder
        speaker = "0"

        try:
            self._task_queue.put(("progress", {"task": task_id, "percent": 5, "msg": "acquiring engine"}))
            with mgr.use_engine(TTSEngine.PIPER, config={}):
                self._task_queue.put(("progress", {"task": task_id, "percent": 20, "msg": "engine acquired"}))

                # Simulate stepwise synthesis progress
                for i in range(4):
                    time.sleep(0.4)
                    self._task_queue.put(("progress", {"task": task_id, "percent": 20 + (i + 1) * 15}))
                # Perform a real synthesize call if engine implements it
                try:
                    engine = mgr.get_engine(TTSEngine.PIPER, config={})

                    # Start a reporter thread that sends incremental progress while synth runs.
                    finished = threading.Event()

                    def _progress_reporter():
                        # progress will ramp from 30 -> 95 in small steps until finished
                        pct = 30
                        while not finished.is_set() and pct < 95:
                            pct += 3
                            self._task_queue.put(("progress", {"task": task_id, "percent": pct}))
                            time.sleep(0.2)
                        # if finished not set, push a high percent
                        if not finished.is_set():
                            self._task_queue.put(("progress", {"task": task_id, "percent": 95}))

                    reporter = threading.Thread(target=_progress_reporter, daemon=True)
                    reporter.start()

                    audio = engine.synthesize(demo_text, speaker)
                    finished.set()
                    # ensure reporter thread ends
                    reporter.join(timeout=1.0)

                    # final progress update
                    self._task_queue.put(("progress", {"task": task_id, "percent": 100}))

                    # write audio (numpy float32) to temporary WAV (int16)
                    try:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                        tmp_name = tmp.name
                        tmp.close()

                        # Ensure numpy array
                        arr = _np.asarray(audio, dtype=_np.float32)
                        # normalize/clamp
                        arr = _np.clip(arr, -1.0, 1.0)
                        int16 = (arr * 32767).astype(_np.int16)

                        with wave.open(tmp_name, "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(engine.sample_rate)
                            wf.writeframes(int16.tobytes())


                        # Report the path to the UI thread; do not autoplay here unconditionally
                        self._task_queue.put(("done", {"task": task_id, "result": "synth_success", "samples": len(audio), "path": tmp_name}))

                        # optionally remove temp file after a delay in background
                        def _cleanup(path):
                            try:
                                time.sleep(5)
                                os.unlink(path)
                            except Exception:
                                pass

                        threading.Thread(target=_cleanup, args=(tmp_name,), daemon=True).start()

                    except Exception as write_err:
                        self._task_queue.put(("done", {"task": task_id, "result": "synth_failed", "error": str(write_err)}))

                except Exception as synth_err:
                    # If synthesis failed (missing deps), report and fallback
                    self._task_queue.put(("done", {"task": task_id, "result": "synth_failed", "error": str(synth_err)}))

        except Exception as e:
            self._task_queue.put(("done", {"task": task_id, "result": "error", "error": str(e)}))

    def _bg_preload_task(self, task_id: str, progress_callback=None):
        # Placeholder: call engine_manager.preload_engines([...])
        for i in range(3):
            time.sleep(0.4)
            self._task_queue.put(("progress", {"task": task_id, "percent": (i + 1) * 33}))
        self._task_queue.put(("done", {"task": task_id}))

    def _bg_unload_task(self, task_id: str, progress_callback=None):
        time.sleep(0.2)
        self._task_queue.put(("done", {"task": task_id}))

    def _simulate_ai_reply(self, text: str):
        time.sleep(0.8)
        reply = f"AI: (simulated reply to '{text[:40]}')\n"
        self._task_queue.put(("ai_reply", {"text": reply}))

    # -------------------- Integration Helpers --------------------
    def _open_full_editor(self):
        """Open the full PodcastEditor in a separate Toplevel window.

        When embedding we request `embedded=True` so the editor skips creating its
        own menu/toolbar (avoids duplicated chrome when hosting editor in the
        application's window).
        """
        try:
            from .editor import PodcastEditor

            top = tk.Toplevel(self)
            # PodcastEditor expects a Tk-like root; Toplevel provides the necessary API
            # Pass embedded=True to avoid duplicate menus/toolbars when opened from the app
            editor = PodcastEditor(root=top, embedded=True)
            # keep last editor reference so event handlers can access it
            try:
                self._last_editor = editor
            except Exception:
                pass
            return editor
        except Exception as e:
            self._set_status(f"Fehler beim Öffnen des Editors: {e}")
            return None

    # -------------------- Queue Processing --------------------
    def _process_task_queue(self):
        try:
            while True:
                typ, data = self._task_queue.get_nowait()
                if typ == "progress":
                    # update status text and progressbar if provided
                    msg = data.get("msg")
                    percent = data.get("percent")
                    if msg:
                        self._set_status(f"{data['task']}: {msg}")
                    elif percent is not None:
                        self._set_status(f"{data['task']}: {percent}%")
                    if percent is not None:
                        try:
                            self.statusbar.set_progress(percent)
                        except Exception:
                            pass
                elif typ == "done":
                    # Show final state and clear progress
                    result = data.get("result")
                    if result == "synth_success":
                        self._set_status(f"{data['task']} completed: synth OK ({data.get('samples',0)} samples)")
                        # remember last preview file
                        path = data.get("path")
                        if path:
                            try:
                                self._last_preview_file = Path(path)
                                if self.auto_play:
                                    player = get_player()
                                    player.play(self._last_preview_file)
                            except Exception:
                                pass
                    elif result == "synth_failed":
                        self._set_status(f"{data['task']} failed: {data.get('error')}")
                    elif result == "error":
                        self._set_status(f"{data['task']} error: {data.get('error')}")
                    else:
                        self._set_status(f"{data['task']} completed")
                    try:
                        self.statusbar.set_progress(None)
                    except Exception:
                        pass
                elif typ == "ai_reply":
                    self.chat_text.insert(tk.END, data["text"]) 
                self._task_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_task_queue)

    # -------------------- Helpers --------------------
    def _set_status(self, text: str):
        try:
            self.statusbar.set(text)
        except Exception:
            # fallback to printing when statusbar unavailable
            print(text)


if __name__ == "__main__":
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print("GUI failed to start:", e)
