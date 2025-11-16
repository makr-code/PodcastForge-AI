"""Launch the minimal Tkinter audio player from the repository.

Usage:
  python scripts/run_tk_player.py
"""
from __future__ import annotations

import sys
from podcastforge.audio.tk_player import run_app


def main():
    run_app()


if __name__ == '__main__':
    raise SystemExit(main())
