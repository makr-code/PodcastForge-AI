"""Helpers to load/normalize script files into block-based structure.
"""
from pathlib import Path
import uuid
from typing import List, Dict, Any, Optional


def normalize_script(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize incoming project data to a list of blocks.

    Accepts dict parsed from YAML/JSON and returns a list of blocks where each
    block is a dict with keys: id, type, speaker (optional), text, chapter, prosody, preview, pause_after.
    """
    out: List[Dict[str, Any]] = []
    if not isinstance(data, dict):
        return out

    script = data.get('script') or []
    for item in script:
        if isinstance(item, dict):
            b = {}
            b['id'] = item.get('id') or str(uuid.uuid4())
            b['type'] = item.get('type') or ('utterance' if 'speaker' in item else 'direction')
            b['chapter'] = item.get('chapter')
            b['speaker'] = item.get('speaker')
            b['text'] = item.get('text') or item.get('content') or ''
            b['prosody'] = item.get('prosody') or {}
            b['preview'] = bool(item.get('preview', False))
            b['pause_after'] = float(item.get('pause_after', 0.0) or 0.0)
            b['annotations'] = item.get('annotations', {})
            out.append(b)
        else:
            # legacy structured lines: treat as direction or simple utterance
            out.append({'id': str(uuid.uuid4()), 'type': 'direction', 'text': str(item), 'preview': False})

    return out


def blocks_to_script_dict(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert blocks back to a simple script dict for saving/export.
    """
    return {'script': blocks}
