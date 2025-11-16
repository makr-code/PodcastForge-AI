# Script Orchestrator — Anleitung

Pfad: `src/podcastforge/integrations/script_orchestrator.py`

Zweck
- Orchestriert TTS‑Rendering für ein Skript (JSON/YAML) mit mehreren Sprechern.
- Rendert per-Utterance WAVs (caching) und erzeugt eine kombinierte `script_preview.wav`.
- Publiziert Events:
  - `script.tts_progress` — während der Synthese einzelner Abschnitte
  - `script.preview_ready` — wenn die kombinierte Vorschau fertig ist

Script-Format
- JSON oder YAML: Liste von Objekten mit Feldern `speaker` und `text`.

Beispiel `sample_script.json`:

```json
[
  {"speaker": "Host", "text": "Willkommen zum Podcast."},
  {"speaker": "Guest", "text": "Danke, ich freue mich dabei zu sein."}
]
```

Haupteintrag

```python
from podcastforge.integrations.script_orchestrator import synthesize_script_preview

res = synthesize_script_preview('examples/sample_script.json', out_dir='out', cache_dir='out/cache')
print(res)
```

Optionen
- `speaker_map`: Optional dict mapping script speaker names → TTS voice ids.
- `engine`: Name des TTS‑Engines (z. B. `PIPER`).
- `max_workers`: Anzahl paralleler Synthese-Worker.

Tipps
- Verwende `speaker_map` wenn Skripternamen von internen TTS‑Stimmen abweichen.
- Die Funktion nutzt `get_engine_manager()` intern; falls du in einer Umgebung ohne echte TTS laufen willst, ersetze `podcastforge.tts.engine_manager.get_engine_manager` temporär durch einen Dummy (siehe `examples/script_preview.py`).

Manifest / Output
- `script_preview.wav` im `out_dir` wird erzeugt.
- `out_dir/cache` enthält per‑utterance WAV Dateien (SHA256-basiert benannt).

Events
- `script.tts_progress`: payload `{ 'task_id', 'idx', 'status' }` (`status` in `start|done|error`)
- `script.preview_ready`: payload `{ 'preview': '<abs-path>', 'clips': [ { idx, speaker, voice, file } ] }`

Fehlerbehandlung
- Die Funktion gibt `{'ok': False, 'message': '...'} ` zurück bei Fehlern.
- Prüfe die Rückgabe bevor du versuchst, die Preview zu öffnen.

Beispiel-Workflow (Headless)
1. Erzeuge/verwende `examples/sample_script.json`.
2. Führe `examples/script_preview.py` aus (siehe `examples/` für Demo).  
3. Öffne `out/script_preview.wav` in deinem Audioplayer.
