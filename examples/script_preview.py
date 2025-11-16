"""Beispiel: Erzeuge eine Script-Vorschau (headless).

Dieses Script demonstriert die Nutzung von `synthesize_script_preview`.
Es enthält einen eingebauten Dummy-TTS‑Manager wenn keine echte Engine verfügbar ist.
"""
from pathlib import Path
import json
import sys

from podcastforge.integrations.script_orchestrator import synthesize_script_preview
import podcastforge.tts.engine_manager as em


class DummyManager:
    def synthesize(self, text, speaker, engine_type=None, **kwargs):
        # 1 second of silence at 22050Hz
        import numpy as np
        sr = 22050
        samples = np.zeros(int(sr * 1.0), dtype=np.float32)
        return samples, sr


def ensure_sample_script(path: Path):
    if not path.exists():
        sample = [
            {"speaker": "Host", "text": "Willkommen zum Podcast."},
            {"speaker": "Guest", "text": "Danke, ich freue mich hier zu sein."},
        ]
        path.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    script_file = Path('examples/sample_script.json')
    ensure_sample_script(script_file)

    # Wenn env var USE_DUMMY_TTS gesetzt ist, injiziere DummyManager
    use_dummy = '--dummy' in sys.argv or 'USE_DUMMY_TTS' in os.environ
    if use_dummy:
        em.get_engine_manager = lambda *a, **k: DummyManager()

    res = synthesize_script_preview(str(script_file), out_dir='out', cache_dir='out/cache', max_workers=2)
    print(res)


if __name__ == '__main__':
    import os
    main()
