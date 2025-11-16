# ThreadManager — Kurzanleitung

Pfad: `src/podcastforge/gui/threading_base.py`

Zweck
- Kontrolliert Hintergrund-Tasks mit `ThreadPoolExecutor`.
- Bietet eine Observer API (`ITaskObserver` / `UITaskObserver`) für sichere UI‑Updates.

Wichtige Funktionen
- `get_thread_manager(max_workers=4)` — gibt Singleton `ThreadManager` zurück.
- `submit_task(task_fn, task_id, priority, metadata, callback)` — submitet eine Task-Funktion.
  - `task_fn` muss die Signatur `(task_id: str, progress_callback: Callable)` unterstützen.
  - `progress_callback(progress: float, message: str)` kann genutzt werden, um Fortschritt an die Observer zu melden.
- `cancel_task(task_id)` — versucht, eine laufende Task zu canceln.

UI‑sichere Observer
- `UITaskObserver(root_widget)` ermöglicht die Registrierung von Callbacks, die via `root.after(...)` im UI‑Thread ausgeführt werden.
  - Methoden: `on_started`, `on_progress`, `on_completed`, `on_failed`.

Best Practices
- Verwende `get_thread_manager()` statt eigener ThreadPools, damit Beobachter/Status zentralisiert sind.
- Halte `task_fn` kurz und meldet regelmäßig Fortschritt via `progress_callback`.
- Für lange Tasks: implementiere Timeouts / Abbruchlogik und sichere Cleanup‑Hooks.

Beispiel — Task Submission:

```python
from podcastforge.gui.threading_base import get_thread_manager, TaskPriority

mgr = get_thread_manager(max_workers=4)

def my_task(task_id, progress_callback):
    for i in range(5):
        # lange Arbeit simuliert
        time.sleep(0.5)
        if progress_callback:
            progress_callback((i+1)/5.0, f"step {i+1}")
    return {'ok': True}

mgr.submit_task(my_task, task_id='job-1', priority=TaskPriority.NORMAL, metadata={'what': 'demo'})
```

Beispiel — UI Observer:

```python
from podcastforge.gui.threading_base import UITaskObserver, get_thread_manager

mgr = get_thread_manager()
observer = UITaskObserver(root_widget)

observer.on_progress(lambda tid, pct, msg: statusbar.set(f"{tid}: {pct*100:.0f}%"))

mgr.add_observer(observer)
```

Testing
- In Unit Tests kannst du `get_thread_manager()` verwenden; wenn du einen frischen Manager brauchst, rufe `shutdown_thread_manager()` (oder setze `get_thread_manager`-Singleton zurück) und initialisiere neu.
- Achte auf race conditions in Tests: warte auf Ergebnisse oder verwende `callback`-Mechanismus.
