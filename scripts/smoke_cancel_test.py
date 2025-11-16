"""Smoke test to simulate generation + cancellation without heavy TTS deps.

This script monkeypatches the orchestrator's engine manager with a dummy
that sleeps for a moment per utterance and respects cancel_event.
"""
import threading
import time
import json
import tempfile
from pathlib import Path

class DummyManager:
    def synthesize(self, text, speaker, **kwargs):
        cancel_event = kwargs.get('cancel_event')
        if cancel_event and cancel_event.is_set():
            raise Exception('cancelled')
        for i in range(20):
            time.sleep(0.05)
            if cancel_event and cancel_event.is_set():
                raise Exception('cancelled')
        import numpy as np

        sr = 22050
        audio = np.zeros(int(sr * 0.5), dtype=np.float32)
        return audio, sr


def run_test():
    tmp = tempfile.mkdtemp(prefix='pf_smoke_')
    script_path = Path(tmp) / 'script.json'
    items = [
        {'speaker': 'A', 'text': 'Hello world 1'},
        {'speaker': 'B', 'text': 'Hello world 2'},
        {'speaker': 'A', 'text': 'Hello world 3'},
        {'speaker': 'B', 'text': 'Hello world 4'},
    ]
    script_path.write_text(json.dumps(items, ensure_ascii=False), encoding='utf-8')

    cancel_event = threading.Event()

    manager = DummyManager()

    results = {}

    def make_worker(idx, entry):
        def _w():
            try:
                print(f"[worker {idx}] start")
                # check before
                if cancel_event.is_set():
                    print(f"[worker {idx}] cancelled before start")
                    results[idx] = 'cancelled'
                    return
                audio, sr = manager.synthesize(entry['text'], entry['speaker'], cancel_event=cancel_event)
                if cancel_event.is_set():
                    print(f"[worker {idx}] cancelled after synth")
                    results[idx] = 'cancelled'
                    return
                # simulate write
                out = Path(tmp) / f"clip_{idx}.wav"
                out.write_bytes(b"RIFF")
                print(f"[worker {idx}] done")
                results[idx] = 'done'
            except Exception as e:
                print(f"[worker {idx}] exception: {e}")
                results[idx] = 'failed'

        return _w

    threads = []
    for i, it in enumerate(items, start=1):
        t = threading.Thread(target=make_worker(i, it), daemon=True)
        threads.append(t)
        t.start()

    # cancel shortly after
    time.sleep(0.3)
    print('Setting cancel event')
    cancel_event.set()

    for t in threads:
        t.join(timeout=5)

    print('Results:', results)


if __name__ == '__main__':
    run_test()
