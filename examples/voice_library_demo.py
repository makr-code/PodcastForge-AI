#!/usr/bin/env python3
"""
Voice Library Demo
Zeigt wie die Voice Library funktioniert und Stimmen vorschlägt
"""

from podcastforge import PodcastForge, PodcastStyle
from podcastforge.voices import get_voice_library, VoiceGender, VoiceStyle
from rich.console import Console

console = Console()

def main():
    console.print("\n[bold cyan]🎙️ Voice Library Demo[/bold cyan]\n")
    
    # 1. Voice Library laden
    voice_lib = get_voice_library()
    
    console.print(f"[green]✓[/green] Voice Library geladen")
    console.print(f"[dim]Verfügbare Stimmen: {voice_lib.get_voice_count()}[/dim]\n")
    
    # 2. Alle deutschen Stimmen anzeigen
    console.print("[bold]Deutsche Stimmen:[/bold]")
    de_voices = voice_lib.search(language="de")
    for voice in de_voices:
        console.print(f"  • {voice.display_name} - {voice.description}")
    
    # 3. Englische Stimmen nach Stil filtern
    console.print("\n[bold]Englische Documentary-Stimmen:[/bold]")
    doc_voices = voice_lib.search(
        language="en",
        style=VoiceStyle.DOCUMENTARY
    )
    for voice in doc_voices:
        console.print(f"  • {voice.display_name} - {voice.description}")
    
    # 4. Professionelle männliche Stimmen
    console.print("\n[bold]Professionelle männliche Stimmen (EN):[/bold]")
    prof_male = voice_lib.search(
        language="en",
        gender=VoiceGender.MALE,
        style=VoiceStyle.PROFESSIONAL
    )
    for voice in prof_male:
        console.print(f"  • {voice.display_name}")
    
    # 5. Stimmen-Vorschläge für verschiedene Podcast-Stile
    console.print("\n[bold]Stimmen-Vorschläge für Podcast-Stile:[/bold]\n")
    
    styles = [
        PodcastStyle.INTERVIEW,
        PodcastStyle.DOCUMENTARY,
        PodcastStyle.DISCUSSION,
        PodcastStyle.NEWS
    ]
    
    for style in styles:
        console.print(f"[yellow]{style.value.upper()}:[/yellow]")
        suggestions = voice_lib.suggest_for_podcast_style(
            style=style,
            language="en",
            num_speakers=2
        )
        for i, voice in enumerate(suggestions, 1):
            console.print(f"  {i}. {voice.display_name} ({voice.style.value})")
        console.print()
    
    # 6. Komplett formatierte Ausgabe
    console.print("\n[bold]Komplette Voice Library:[/bold]")
    voice_lib.print_library(language="en")
    
    # 7. Podcast mit Voice Library erstellen
    console.print("\n[bold cyan]Erstelle Demo-Podcast mit automatischer Stimmen-Auswahl...[/bold cyan]\n")
    
    forge = PodcastForge(language="en")
    
    # Stimmen werden automatisch von Voice Library vorgeschlagen!
    podcast = forge.create_podcast(
        topic="The Future of Artificial Intelligence",
        style=PodcastStyle.INTERVIEW,
        duration=3,  # Kurzer Demo
        output="voice_library_demo.mp3"
    )
    
    console.print(f"\n[green]✓ Demo-Podcast erstellt: {podcast}[/green]")
    console.print("[dim]Die Stimmen wurden automatisch von der Voice Library ausgewählt![/dim]\n")

if __name__ == "__main__":
    main()
