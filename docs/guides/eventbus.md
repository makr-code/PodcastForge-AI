# EventBus — Kurzanleitung

Das Projekt verwendet einen einfachen, in‑process EventBus für lose Kopplung zwischen Komponenten (z. B. Integrationen → GUI).

Pfad: `src/podcastforge/core/events.py`

Grundkonzepte
- `get_event_bus()` gibt eine Singleton‑Instanz zurück.
- `publish(event_name: str, payload: dict)` versendet ein Event.
- `subscribe(event_name: str, handler: Callable[[dict], None])` registriert einen Listener.

Best Practices
- Verwende einfache, gut dokumentierte Event-Namen, z. B.:
  - `script.tts_progress` — Payload: `{ 'task_id', 'idx', 'status' }`
  - `script.preview_ready` — Payload: `{ 'preview': '<path>', 'clips': [...] }`
  - `ebook2audiobook.tts_progress`, `ebook2audiobook.project_ready`, `ebook2audiobook.open_project`
- Payloads sollten einfache, JSON‑serialisierbare Typen enthalten (strings, numbers, lists, dicts).
- Fehlerbehandlung: Event-Handler sollten Exceptions intern abfangen, damit ein fehlerhafter Listener nicht die Event‑Verteilung stoppt.

UI‑Integration
- GUI-Komponenten (z. B. `MainWindow`) sollten `get_event_bus().subscribe(...)` verwenden, um Events zu empfangen.
- GUI-Handler müssen UI‑sicher sein (keine Blocking-Operationen). Wenn ein Event aufwändige Arbeit auslöst, starte sie via `get_thread_manager().submit_task(...)`.

Beispiel — Publizieren eines Fortschritts:

```python
from podcastforge.core.events import get_event_bus

get_event_bus().publish('script.tts_progress', {'task_id': 's001', 'idx': 1, 'status': 'start'})
```

Beispiel — Subscription in `MainWindow`:

```python
from podcastforge.core.events import get_event_bus

bus = get_event_bus()
bus.subscribe('script.tts_progress', self._on_script_progress)

def _on_script_progress(self, data: dict):
    status = data.get('status')
    idx = data.get('idx')
    if status == 'start':
        self._set_status(f"TTS startet: {idx}")
    elif status == 'done':
        self._set_status(f"TTS fertig: {idx}")
```

Hinweis zu Unit Tests
- Für Unit Tests kannst du den EventBus normal verwenden; entferne ggf. Listener nach dem Test, um Seiteneffekte zu vermeiden.
- Alternativ: ersetze `get_event_bus()` temporär mit einer Test‑Instanz.
