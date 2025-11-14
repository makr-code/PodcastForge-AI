#!/usr/bin/env python3
"""
Launcher für PodcastForge GUI Editor
"""

import sys
from pathlib import Path

# Füge src zu Python-Path hinzu
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from podcastforge.gui import PodcastEditor

if __name__ == "__main__":
    print("🎙️ Starte PodcastForge Editor...")
    editor = PodcastEditor()
    editor.run()
