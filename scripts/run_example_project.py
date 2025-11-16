#!/usr/bin/env python3
"""Run the example podcast project from `projects/example_podcast_project.yaml`.

Usage examples:
  python scripts/run_example_project.py                       # uses defaults
  python scripts/run_example_project.py --project projects/example_podcast_project.yaml --out out/example --utterances 3
  python scripts/run_example_project.py --utterances 5 --max-workers 2 --engine PIPER

The script calls `synthesize_script_preview` from `podcastforge.integrations.script_orchestrator`.
It provides a simple `on_progress` callback that prints per‑utterance events.
"""
from __future__ import annotations

import argparse
import sys
import yaml
from pathlib import Path
from typing import Any
import json
from datetime import datetime, timezone


def default_on_progress(evt: Any) -> None:
    # Simple pretty print for progress events
    try:
        tid = evt.get("task_id") or evt.get("utterance_id") or evt.get("id")
    except Exception:
        tid = None
    print("[PROGRESS]", tid, evt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run example podcast project synthesis")
    parser.add_argument("--project", default="projects/example_podcast_project.yaml", help="Path to project YAML")
    parser.add_argument("--out", dest="out_dir", default="out/example", help="Output directory")
    parser.add_argument("--utterances", type=int, default=3, help="Number of first utterances to synthesize (per-chapter order)")
    parser.add_argument("--engine", default=None, help="Optional engine override (e.g. PIPER)")
    parser.add_argument("--max-workers", type=int, default=2, help="Max workers for synthesis")
    parser.add_argument("--keep-temp", action="store_true", help="If supported, keep temporary files from installer/extraction steps")
    parser.add_argument("--dry-run", action="store_true", help="Validate project and pipeline without running synthesis")
    parser.add_argument("--log", dest="log_file", default=None, help="Optional path to write a run log")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(argv)

    project_path = Path(args.project)
    if not project_path.exists():
        print(f"Project file not found: {project_path}")
        return 2


    # Load project YAML to allow potential pre-processing or filtering
    with project_path.open("r", encoding="utf-8") as fh:
        proj = yaml.safe_load(fh)

    # Prepare optional log file
    log_fh = None
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_fh = log_path.open("w", encoding="utf-8")

    def _log(msg: str):
        print(msg)
        if log_fh:
            log_fh.write(msg + "\n")

    # Dry-run: validate structure and environment without invoking heavy TTS
    if args.dry_run:
        import shutil

        _log(f"Dry-run validation for project: {project_path}")
        # Basic metadata
        _log(f"Title: {proj.get('title')}")
        speakers = {s["id"] for s in proj.get("speakers", []) if isinstance(s, dict) and s.get("id")}
        _log(f"Speakers defined: {len(speakers)} -> {', '.join(sorted(speakers)) if speakers else 'none'}")

        utterances = proj.get("script", [])
        _log(f"Utterances defined: {len(utterances)}")

        # Validate utterances refer to known speakers and have text
        errors = []
        for u in utterances:
            uid = u.get("id") if isinstance(u, dict) else None
            sp = u.get("speaker") if isinstance(u, dict) else None
            txt = u.get("text") if isinstance(u, dict) else None
            if not uid:
                errors.append(f"Utterance missing id: {u}")
            if not txt:
                errors.append(f"Utterance {uid or u} missing text")
            if sp and sp not in speakers:
                errors.append(f"Utterance {uid} references unknown speaker '{sp}'")

        # Background asset check
        bg = proj.get("background", {}) if isinstance(proj.get("background"), dict) else {}
        music = bg.get("music")
        if music:
            music_path = Path(music)
            exists = music_path.exists()
            _log(f"Background music: {music} -> exists: {exists}")
            if not exists:
                _log("Warning: background music file not found; background mixing tests will be skipped")

        # ffmpeg availability
        ff = shutil.which("ffmpeg")
        _log("ffmpeg found on PATH: " + (ff if ff else "NO"))

        if errors:
            _log("Dry-run validation failed with errors:")
            for e in errors:
                _log(" - " + e)
            if log_fh:
                log_fh.close()
            return 4

        _log("Dry-run validation passed — project structure looks OK.")
        if log_fh:
            log_fh.close()
        return 0

    # Optionally limit utterances: many orchestrators accept a project path and options; if not,
    # we still pass args and rely on the orchestrator to support them. We provide an on_progress callback.

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    options = {
        "out_dir": str(out_dir),
        "max_workers": args.max_workers,
        # placeholder, will be set below so we can attach jsonl logging when requested
        "on_progress": None,
    }
    if args.engine:
        options["engine"] = args.engine

    # Some orchestrator functions accept `utterances_limit` or similar; try common names
    options_candidates = ["utterances_limit", "num_utterances", "max_utterances", "limit"]
    for k in options_candidates:
        options.setdefault(k, args.utterances)

    if args.verbose:
        print("Running with options:", options)

    # Setup JSONL event logging if requested
    jsonl_fh = None
    if args.log_file:
        # create companion jsonl file for structured events
        log_path = Path(args.log_file)
        jsonl_path = log_path.with_name(log_path.name + ".jsonl")
        jsonl_fh = jsonl_path.open("w", encoding="utf-8")

    # create an on_progress wrapper that prints and optionally writes JSONL
    def make_on_progress(fh):
        def _on_progress(evt: Any, stage: Any = None) -> None:
            # Support being called with either (evt_dict) or (progress, stage)
            try:
                if isinstance(evt, dict):
                    payload = evt
                else:
                    # fallback: wrap positional progress and stage
                    payload = {'progress': evt, 'stage': stage}
                tid = payload.get("task_id") or payload.get("utterance_id") or payload.get("id")
            except Exception:
                tid = None
                payload = evt

            line = f"[PROGRESS] {tid} {payload}"
            print(line)
            if not fh:
                return

            # Normalize event into structured schema for JSONL logs
            try:
                timestamp = datetime.now(timezone.utc).isoformat()
            except Exception:
                timestamp = None

            normalized = {
                "timestamp": timestamp,
                "utterance_id": tid,
                "status": payload.get("status") if isinstance(payload, dict) and payload.get("status") else "progress",
                "payload": payload,
            }

            try:
                fh.write(json.dumps(normalized, default=str, ensure_ascii=False) + "\n")
                fh.flush()
            except Exception:
                # fallback: write minimal record
                try:
                    fh.write(json.dumps({"timestamp": timestamp, "utterance_id": tid, "payload_repr": repr(payload)}, ensure_ascii=False) + "\n")
                    fh.flush()
                except Exception:
                    pass

        return _on_progress

    options["on_progress"] = make_on_progress(jsonl_fh)

    try:
        # Try to import the orchestrator synthesis helper
        from podcastforge.integrations.script_orchestrator import synthesize_script_preview
        from podcastforge.core.events import get_event_bus

        # Only pass recognised options to avoid TypeError from unexpected kwargs.
        call_kwargs = {}
        call_kwargs['out_dir'] = options.get('out_dir')
        if options.get('engine'):
            call_kwargs['engine'] = options.get('engine')
        if options.get('max_workers') is not None:
            call_kwargs['max_workers'] = options.get('max_workers')
        # attach structured on_progress callback (may be None)
        call_kwargs['on_progress'] = options.get('on_progress')

        # If JSONL file present, also subscribe to EventBus as a fallback so
        # we capture events even if the orchestrator doesn't forward the
        # on_progress callback for some engines.
        bus = get_event_bus()
        bus_sub = None
        if jsonl_fh:
            def _bus_logger(evt: Any) -> None:
                try:
                    # reuse normalization logic: write a JSONL record per event
                    timestamp = datetime.now(timezone.utc).isoformat()
                except Exception:
                    timestamp = None
                try:
                    tid = evt.get('task_id') if isinstance(evt, dict) else None
                except Exception:
                    tid = None
                record = {'timestamp': timestamp, 'utterance_id': tid, 'status': (evt.get('status') if isinstance(evt, dict) and evt.get('status') else 'progress'), 'payload': evt}
                try:
                    jsonl_fh.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
                    jsonl_fh.flush()
                except Exception:
                    try:
                        jsonl_fh.write(json.dumps({'timestamp': timestamp, 'utterance_id': tid, 'payload_repr': repr(evt)}, ensure_ascii=False) + "\n")
                        jsonl_fh.flush()
                    except Exception:
                        pass

            bus.subscribe('script.tts_progress', _bus_logger)
            bus_sub = _bus_logger

        try:
            # The project YAML contains metadata and a `script` list. The
            # orchestrator expects a file whose root is a list of
            # utterances. Write the `script` portion to a temporary file in
            # the output directory and pass that path.
            script_list = proj.get('script') if isinstance(proj, dict) else None
            if not script_list or not isinstance(script_list, list):
                print('Project does not contain a `script` list to synthesize')
                return 4

            # write temporary script file
            tmp_script_path = Path(call_kwargs.get('out_dir', out_dir)) / 'project_script.yaml'
            tmp_script_path.parent.mkdir(parents=True, exist_ok=True)
            with tmp_script_path.open('w', encoding='utf-8') as fh:
                yaml.safe_dump(script_list, fh, allow_unicode=True)

            # build speaker_map from project speakers if present
            speakers = proj.get('speakers') if isinstance(proj.get('speakers'), list) else []
            speaker_map = {}
            for s in speakers:
                if isinstance(s, dict) and s.get('id'):
                    # allow explicit voice override or use id
                    speaker_map[s['id']] = s.get('voice') or s.get('id')
            if speaker_map:
                call_kwargs['speaker_map'] = speaker_map

            # prefer engine from CLI, otherwise project setting
            if not call_kwargs.get('engine') and proj.get('engine'):
                call_kwargs['engine'] = proj.get('engine')

            # call the orchestrator helper with cleaned kwargs
            res = synthesize_script_preview(str(tmp_script_path), **call_kwargs)
            if not isinstance(res, dict) or not res.get('ok'):
                print('Synthesis reported failure or no output:', res)
            else:
                print('Synthesis completed: preview ->', res.get('preview_path'))
        finally:
            # cleanup subscription
            try:
                if bus_sub:
                    bus.unsubscribe('script.tts_progress', bus_sub)
            except Exception:
                pass
    except TypeError:
        # Fallback: call with only canonical args (out_dir, max_workers, on_progress)
        try:
            synthesize_script_preview(str(project_path), str(out_dir), args.max_workers, default_on_progress)
        except Exception as e:
            print("synthesize_script_preview failed:", e)
            return 4
    except Exception as e:
        print("Error during synthesis:", e)
        return 5

    _log(f"Synthesis finished. Outputs are in: {out_dir}")
    if log_fh:
        log_fh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())