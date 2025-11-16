AI & TTS Deep Dive — Beispielprojekt

Inhalt:
- `manifest.yaml`: Projektmetadaten und strukturierte Utterances
- `script.json`: Lineares Skript (Liste von {speaker, text})
- `render_project.py`: Einfache Runner-Datei, die `synthesize_script_preview` aufruft

Schnellstart (PowerShell):

$env:PYTHONPATH='src'; python .\examples\projects\ai_tts_podcast\render_project.py

Hinweis: Die Runner-Datei verwendet die Standard-Engine `PIPER`. Stelle sicher,
falls nötig, dass die benötigten TTS-Modelle/Packages installiert sind, oder
ändere `engine='PIPER'` zu einer verfügbaren Engine in deiner Umgebung.
