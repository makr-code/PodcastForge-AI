import importlib
import sys
from pathlib import Path
src = Path(__file__).resolve().parent.parent / 'src'
sys.path.insert(0, str(src))
try:
    m = importlib.import_module('podcastforge.integrations.script_orchestrator')
    print('OK:', m)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
