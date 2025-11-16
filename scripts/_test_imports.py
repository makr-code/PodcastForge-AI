import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

try:
    from podcastforge.integrations import ebook2audiobook as wrapper
    print('wrapper.__file__=', getattr(wrapper, '__file__', None))
    print('wrapper.is_available() ->', wrapper.is_available())
except Exception as e:
    print('wrapper import failed:', e)

try:
    from podcastforge.integrations.ebook2audiobook import api
    print('api.is_available() ->', api.is_available())
    print('list_supported_formats() ->', api.list_supported_formats()[:10])
except Exception as e:
    print('api import failed:', e)

# Extra diagnostics: direct import of upstream 'lib' module
print('\nDiagnostics: direct import attempts')
try:
    import lib as _lib
    print('lib __file__ =', getattr(_lib, '__file__', None))
    print('has functions attr?', hasattr(_lib, 'functions'))
    try:
        import importlib
        funcs = importlib.import_module('functions')
        print('functions module loaded via bare name, file=', getattr(funcs, '__file__', None))
    except Exception as ex:
        print('importlib.import_module("functions") failed:', ex)
except Exception as ex:
    print('direct import lib failed:', ex)
