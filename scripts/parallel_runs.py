#!/usr/bin/env python3
"""Run multiple engine syntheses in parallel threads and log outputs.

Creates per-engine output dirs under `out/parallel_<engine>` and per-engine
logs under `logs/run_<engine>.log` and `logs/run_<engine>.jsonl`.
"""
from __future__ import annotations

import threading
import traceback
import json
from pathlib import Path
from datetime import datetime, timezone

import sys
from pathlib import Path as _Path
# Ensure repository root is on sys.path so `podcastforge` imports resolve when
# running this script from the `scripts/` directory.
_repo_root = _Path(__file__).resolve().parents[1]
# The repository's Python package sources live under `src/` so ensure that
# `repo_root/src` is on sys.path so `import podcastforge` resolves.
_src_path = _repo_root / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from podcastforge.integrations.script_orchestrator import synthesize_script_preview
from podcastforge.core.events import get_event_bus
import yaml

ENGINES = ["BARK", "PIPER", "XTTS"]
PROJECT = Path("projects/example_podcast_project.yaml")
BASE_OUT = Path("out")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load project and extract script list
with PROJECT.open("r", encoding="utf-8") as fh:
    proj = yaml.safe_load(fh)
script_list = proj.get("script") if isinstance(proj, dict) else None
if not script_list or not isinstance(script_list, list):
    print("Project does not contain a 'script' list; aborting")
    raise SystemExit(2)

# Write a temporary canonical script file under a shared tmp dir
TMP_ROOT = BASE_OUT / "parallel_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
TMP_SCRIPT = TMP_ROOT / "project_script.yaml"
with TMP_SCRIPT.open("w", encoding="utf-8") as fh:
    yaml.safe_dump(script_list, fh, allow_unicode=True)

# Build a speaker_map from project speakers (if any)
speaker_map = {}
speakers = proj.get("speakers") if isinstance(proj.get("speakers"), list) else []
for s in speakers:
    if isinstance(s, dict) and s.get("id"):
        speaker_map[s["id"]] = s.get("voice") or s.get("id")

bus = get_event_bus()

results = {}


def run_engine(engine: str):
    out_dir = BASE_OUT / f"parallel_{engine.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    text_log = LOGS_DIR / f"run_{engine.lower()}.log"
    jsonl_log = LOGS_DIR / f"run_{engine.lower()}.jsonl"

    # open jsonl file for append
    jf = open(jsonl_log, "a", encoding="utf-8")

    def bus_logger(evt):
        try:
            ts = datetime.now(timezone.utc).isoformat()
        except Exception:
            ts = None
        try:
            tid = evt.get("task_id") if isinstance(evt, dict) else None
        except Exception:
            tid = None
        rec = {"timestamp": ts, "utterance_id": tid, "payload": evt}
        try:
            jf.write(json.dumps(rec, default=str, ensure_ascii=False) + "\n")
            jf.flush()
        except Exception:
            pass

    bus.subscribe("script.tts_progress", bus_logger)
    bus.subscribe("script.preview_ready", bus_logger)

    def log(msg: str):
        with open(text_log, "a", encoding="utf-8") as lf:
            lf.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")

    try:
        log(f"Starting engine {engine} -> out: {out_dir}")
        kwargs = {
            "out_dir": str(out_dir),
            "max_workers": 2,
            "on_progress": None,
        }
        if speaker_map:
            kwargs["speaker_map"] = speaker_map
        # prefer project engine unless overridden
        kwargs["engine"] = engine

        res = synthesize_script_preview(str(TMP_SCRIPT), **kwargs)
        log(f"Result: {res}")
        results[engine] = res
    except Exception as e:
        log(f"Exception: {e}\n" + traceback.format_exc())
        results[engine] = {"ok": False, "message": str(e)}
    finally:
        try:
            bus.unsubscribe("script.tts_progress", bus_logger)
            bus.unsubscribe("script.preview_ready", bus_logger)
        except Exception:
            pass
        try:
            jf.close()
        except Exception:
            pass


threads = []
for eng in ENGINES:
    t = threading.Thread(target=run_engine, args=(eng,), daemon=False)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Parallel runs finished. Summaries:")
for e, r in results.items():
    print(e, r)

print("Output dirs:")
for eng in ENGINES:
    p = BASE_OUT / f"parallel_{eng.lower()}"
    print(eng, p, "exists:", p.exists())

# exit with non-zero if any failed
ok_all = all(results.get(e, {}).get("ok") for e in ENGINES)
raise SystemExit(0 if ok_all else 1)
