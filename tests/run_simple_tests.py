import importlib.util
import sys
from pathlib import Path

def run_module_tests(path):
    spec = importlib.util.spec_from_file_location('module_under_test', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    failures = 0
    for name in dir(mod):
        if name.startswith('test_') and callable(getattr(mod, name)):
            try:
                getattr(mod, name)()
                print(f"{name}: OK")
            except Exception as e:
                print(f"{name}: FAILED -> {e}")
                failures += 1
    return failures

if __name__ == '__main__':
    tests_dir = Path(__file__).parent
    test_file = tests_dir / 'test_prosody_and_breaths.py'
    if not test_file.exists():
        print('No tests found')
        sys.exit(0)
    failures = run_module_tests(test_file)
    if failures:
        print(f"{failures} tests failed")
        sys.exit(1)
    print('All tests passed')
