#!/usr/bin/env python3
"""
Demo-Skript für PodcastForge AI
Generiert einen kurzen Demo-Podcast über KI
"""

from podcastforge import PodcastForge, PodcastStyle

def main():
    print("🎙️ PodcastForge AI - Demo")
    print("=" * 50)
    
    # Initialisiere PodcastForge
    forge = PodcastForge(
        llm_model="llama2",
        language="de"
    )
    
    # Generiere Demo-Podcast
    podcast_file = forge.create_podcast(
        topic="Künstliche Intelligenz im Alltag",
        style=PodcastStyle.DISCUSSION,
        duration=5,  # 5 Minuten für Demo
        output="demo_podcast.mp3"
    )
    
    print(f"\n✨ Demo-Podcast erstellt: {podcast_file}")
    print("\nHöre dir den Podcast an oder erstelle einen eigenen mit:")
    print("  podcastforge generate --topic 'Dein Thema' --duration 10")

if __name__ == "__main__":
    main()
