#!/usr/bin/env python3
"""
Test script: tries to load BarkEngine from the project and call load_model().
Exits with code 0 on success, 1 on failure.
"""
import os
import sys
from pathlib import Path

# Ensure project src is on sys.path
repo_root = Path(__file__).resolve().parents[1]
src = repo_root / 'src'
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

print('Repo root:', repo_root)
print('Using src:', src)

# Set PF_MODELS_DIR to local ./models if exists
models_dir = repo_root / 'models'
if models_dir.exists():
    os.environ.setdefault('PF_MODELS_DIR', str(models_dir))
    print('PF_MODELS_DIR ->', os.environ['PF_MODELS_DIR'])
else:
    print('No local models directory found at', models_dir)

try:
    from podcastforge.tts.engine_manager import BarkEngine
except Exception as e:
    print('Failed to import BarkEngine:', e)
    sys.exit(1)

try:
    engine = BarkEngine()
    print('Instantiated BarkEngine:', engine)
    print('Calling load_model() ... this may take some seconds')
    engine.load_model()
    print('load_model() completed; is_loaded =', engine.is_loaded)
    sys.exit(0 if engine.is_loaded else 1)
except Exception as e:
    print('BarkEngine.load_model() failed:', e)
    sys.exit(1)
