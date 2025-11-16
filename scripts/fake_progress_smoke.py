#!/usr/bin/env python3
r"""
Smoke script to open the PodcastForge Editor and simulate `script.tts_progress`
events so you can visually verify per-row progress bars and watchdog behavior.

Run from repository root with (PowerShell):

    $env:PYTHONPATH='src'; python .\scripts\fake_progress_smoke.py

"""

import threading
import time
from pathlib import Path
import sys

# Ensure imports work: add project `src` to sys.path like `run_editor.py` does
proj_root = Path(__file__).resolve().parent.parent
src_path = proj_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from podcastforge.gui.main_window import MainWindow
from podcastforge.core.events import get_event_bus


def simulate_events(eb, count=5, delay_between=0.6, on_complete=None):
    for idx in range(1, count + 1):
        tid = f"sim{idx:03d}"
        # start
        eb.publish('script.tts_progress', {'task_id': tid, 'idx': idx, 'status': 'start', 'progress': 0.0})
        # emit a few intermediate updates
        for p in (0.05, 0.12, 0.25, 0.42, 0.6, 0.78):
            time.sleep(0.25)
            eb.publish('script.tts_progress', {'task_id': tid, 'idx': idx, 'progress': p, 'stage': 'sim'})
        time.sleep(0.25)
        eb.publish('script.tts_progress', {'task_id': tid, 'idx': idx, 'progress': 1.0, 'status': 'done'})
        # small pause between utterances
        time.sleep(delay_between)

    # call completion callback if provided
    try:
        if on_complete:
            on_complete()
    except Exception:
        pass


def open_and_simulate(app):
    # open full editor window via MainWindow helper
    editor = None
    try:
        editor = app._open_full_editor()
    except Exception:
        pass

    # create fake draft items and open progress modal on the editor
    drafts = [{'id': i, 'speaker': 'Host', 'text': f'Sample utterance {i}'} for i in range(1, 6)]
    if editor:
        try:
            editor._open_progress_modal(drafts)
        except Exception:
            pass

    eb = get_event_bus()
    # schedule auto-close after events complete
    def _finish():
        try:
            # close the app after a short delay to allow GUI updates
            app.after(600, app.destroy)
        except Exception:
            try:
                app.destroy()
            except Exception:
                pass

    threading.Thread(target=simulate_events, args=(eb, len(drafts), 0.6, _finish), daemon=True).start()


def main():
    app = MainWindow()
    # schedule the modal+events slightly after the UI loop starts
    app.after(800, lambda: open_and_simulate(app))
    app.mainloop()


if __name__ == '__main__':
    main()
