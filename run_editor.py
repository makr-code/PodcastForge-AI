#!/usr/bin/env python3
"""Launcher für PodcastForge GUI Editor mit Headless-Guard und Smoke-Test

Dieses Skript fügt `src` zum `PYTHONPATH` hinzu, prüft ob `tkinter` verfügbar ist
und startet die `MainWindow`-Klasse aus `podcastforge.gui.main_window`.

Verwendung:
  python run_editor.py         # startet das GUI
  python run_editor.py --smoke # führt einen kurzen Import-/Instantiierungs-Check durch
"""

import sys
import argparse
from pathlib import Path

# Füge src zu Python-Path hinzu (Projekt-root/src)
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


def _tk_available() -> bool:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True
    except Exception:
        return False


def _run_smoke() -> int:
    """Versuche, das GUI-Modul zu importieren und eine Instanz zu erzeugen (keine mainloop)."""
    print("Smoke test: Import and instantiate GUI (no mainloop)")
    if not _tk_available():
        print("Tkinter/Tcl nicht verfügbar — Smoke-Test übersprungen.")
        return 0
    try:
        from podcastforge.gui.main_window import MainWindow

        # instantiate and destroy quickly
        win = MainWindow()
        win.update_idletasks()
        win.destroy()
        print("Smoke test succeeded: MainWindow instantiated and destroyed.")
        return 0
    except Exception as e:
        print("Smoke test failed:", e)
        return 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run a smoke import/instantiate test and exit")
    args = parser.parse_args()

    if args.smoke:
        code = _run_smoke()
        sys.exit(code)

    # Normaler Start: prüfe Tkinter und starte das GUI
    if not _tk_available():
        print("Tkinter/Tcl nicht verfügbar. GUI kann nicht gestartet.")
        sys.exit(0)

    try:
        from podcastforge.gui.main_window import MainWindow

        print("🎙️ Starte PodcastForge Editor...")
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print("Fehler beim Starten der GUI:", e)
        raise


if __name__ == "__main__":
    main()
