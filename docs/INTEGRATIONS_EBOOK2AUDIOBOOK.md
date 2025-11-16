**Integration: ebook2audiobook**

Kurzbeschreibung
- Das Projekt `DrewThomasson/ebook2audiobook` wurde in `third_party/ebook2audiobook` geklont.
- Zur einfachen Nutzung gibt es einen Laufzeit-Wrapper (`src/podcastforge/integrations/ebook2audiobook/__init__.py`) und eine Adapter-API (`src/podcastforge/integrations/ebook2audiobook/api.py`).

Wie es funktioniert
- Recommended: Der Wrapper fügt das geklonte `lib` zur Laufzeit in `sys.path` ein. Dadurch können Utilities aus `lib` importiert werden ohne Quellcode zu duplizieren.
- Optional: `scripts/import_ebook2audiobook.sh` kann die `lib`-Module physisch ins Projekt kopieren (falls du eine vollständige, eigenständige Kopie bevorzugst).

Wichtige Funktionen (Adapter)
- `is_available()` — prüft, ob die upstream `lib` importierbar ist.
- `list_supported_formats()` — gibt eine Liste unterstützter Eingabeformate zurück.
- `analyze_zip(zip_path, required_files)` — Wrapper für `lib.functions.analyze_uploaded_file`.
- `run_upstream_cli(src_path, output_dir, extra_args)` — startet das upstream CLI-Skript (`ebook2audiobook.sh` / `.cmd`).
- `quick_demo_convert(src_path, output_dir)` — Komfort-Helfer, ruft das CLI und gibt Erfolg/Fehler zurück.

Beispiel
1. Klone das upstream-Repo (falls noch nicht geschehen):

```bash
cd <repo-root>
bash setup.sh
```

2. Prüfe Verfügbarkeit in Python:

```python
from podcastforge.integrations.ebook2audiobook import api
print(api.is_available())
```

3. Vollpipeline (CLI) ausführen:

```bash
# auf Linux/macOS
third_party/ebook2audiobook/ebook2audiobook.sh path/to/book.epub output_dir

# oder mit Adapter (Python)
python -c "from podcastforge.integrations.ebook2audiobook import api; api.quick_demo_convert('path/to/book.epub','out')"
```

Hinweise & Abhängigkeiten
- Das Upstream-Projekt hat mehrere native und Python-Abhängigkeiten (z. B. `ffmpeg`, `pydub`, `ebooklib`, etc.). Stelle sicher, dass diese installiert sind bevor du die volle Pipeline benutzt.
- Für einfache Utility-Aufrufe (z. B. `analyze_uploaded_file`) sind weniger Abhängigkeiten nötig.

Weiteres
- Beispielskript: `examples/ebook2audiobook_demo.py`.
- Import-Skript: `scripts/import_ebook2audiobook.sh` (kopiert `lib`-Module falls gewünscht).
