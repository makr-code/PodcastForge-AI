"""Beispiel: Erzeuge ein minimal manifest und importiere es via Importer.

Demonstriert `import_manifest_to_project` und das Event-basiertes Öffnen in Editor.
"""
from pathlib import Path
import json

from podcastforge.integrations.ebook2audiobook.importer import import_manifest_to_project


def main():
    out = Path('out')
    out.mkdir(exist_ok=True)
    manifest = {
        'source': 'dummy.epub',
        'chapters': [
            {
                'index': 1,
                'title': 'Ch1',
                'file': str((out / 'chapter_01.wav').resolve()),
                'start_time': 0.0,
                'duration': 1.0,
            }
        ],
        'total_duration': 1.0,
    }
    manifest_path = out / 'project_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

    res = import_manifest_to_project(str(manifest_path), str(out), open_in_editor=False)
    print(res)


if __name__ == '__main__':
    main()
