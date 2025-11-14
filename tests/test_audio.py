#!/usr/bin/env python3
"""
Test Audio-Player und Wellenform-Generator
"""

import sys
from pathlib import Path

# Füge src zu Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.audio.player import get_player
from podcastforge.audio.waveform import WaveformGenerator


def test_player():
    """Teste Audio-Player"""
    print("🔊 Teste Audio-Player...")

    player = get_player()
    print(f"  Backend: {player.get_backend()}")

    if player.get_backend():
        print("  ✅ Audio-Player verfügbar")
    else:
        print("  ⚠️ Kein Audio-Backend - installiere pygame oder simpleaudio")

    return player.get_backend() is not None


def test_waveform():
    """Teste Wellenform-Generator"""
    print("\n📊 Teste Wellenform-Generator...")

    try:
        generator = WaveformGenerator(width=400, height=100)

        # Teste Platzhalter-Generierung
        placeholder = generator._generate_placeholder("Test")
        print(f"  Größe: {placeholder.size}")
        print("  ✅ Wellenform-Generator funktioniert")

        return True
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return False


def main():
    """Hauptfunktion"""
    print("🎙️ PodcastForge Audio-Modul Test\n")
    print("=" * 50)

    player_ok = test_player()
    waveform_ok = test_waveform()

    print("\n" + "=" * 50)
    print("\n📋 Ergebnis:")
    print(f"  Audio-Player: {'✅' if player_ok else '❌'}")
    print(f"  Wellenform:   {'✅' if waveform_ok else '❌'}")

    if player_ok and waveform_ok:
        print("\n🎉 Alle Tests bestanden!")
        return 0
    else:
        print("\n⚠️ Einige Tests fehlgeschlagen")
        print("\nInstallation:")
        print("  pip install pygame Pillow numpy pydub")
        return 1


if __name__ == "__main__":
    sys.exit(main())
