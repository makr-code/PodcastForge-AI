"""Small example showing how to use the integration adapter.

This script demonstrates calling the lightweight adapters. It intentionally
keeps operations minimal so it can run in constrained environments.
"""
from pathlib import Path
from podcastforge.integrations.ebook2audiobook import api
import sys


def main():
    print("ebook2audiobook integration demo")
    print("available:", api.is_available())

    if not api.is_available():
        print("The upstream library is not importable. Ensure that `third_party/ebook2audiobook` is cloned and dependencies are installed.")
        sys.exit(1)

    # list supported formats
    fmts = api.list_supported_formats()
    print("supported formats:", fmts[:10])

    # quick CLI-run demo (doesn't run heavy pipeline unless you provide a real ebook path)
    sample = Path("examples/sample.epub")
    if sample.exists():
        print("Running upstream CLI on sample... (this may be slow and require dependencies)")
        try:
            ok = api.quick_demo_convert(str(sample), str(Path("output").resolve()))
            print("success:", ok)
        except Exception as e:
            print("CLI run failed:", e)
    else:
        print("No sample.epub found; place a test epub at examples/sample.epub to try full pipeline.")


if __name__ == '__main__':
    main()
