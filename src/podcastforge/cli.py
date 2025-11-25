#!/usr/bin/env python3
"""
Command Line Interface für PodcastForge AI
"""

import sys
from pathlib import Path

import click
from rich.console import Console

from .core.config import PodcastStyle
from .core.forge import PodcastForge
from .voices.library import get_voice_library

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🎙️ PodcastForge AI - KI-gestützter Podcast-Generator

    Generiert Podcasts mit Ollama LLMs und ebook2audiobook TTS
    """
    pass


@cli.command()
@click.argument("file", required=False)
def edit(file):
    """
    Öffnet den GUI-Editor für Podcast-Skripte

    Beispiel:

        podcastforge edit                    # Neues Projekt
        podcastforge edit podcast.yaml       # Existierendes Projekt öffnen
    """
    console.print("[bold cyan]🎙️ Starte PodcastForge Editor...[/bold cyan]\n")

    try:
        import tkinter as tk

        from .gui import PodcastEditor

        root = tk.Tk()
        editor = PodcastEditor(root)

        # Lade Datei falls angegeben
        if file:
            filepath = Path(file)
            if filepath.exists():
                console.print(f"[green]Lade Projekt: {filepath}[/green]")
                # Editor wird Datei automatisch laden
                # TODO: Implementiere auto-load in Editor
            else:
                console.print(f"[yellow]Warnung: Datei nicht gefunden: {filepath}[/yellow]")

        editor.run()

    except ImportError as e:
        console.print(f"[red]Fehler: tkinter nicht installiert![/red]")
        console.print("\n[yellow]Installation:[/yellow]")
        console.print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        console.print("  macOS: brew install python-tk")
        console.print("  Windows: tkinter ist normalerweise vorinstalliert\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fehler beim Starten des Editors: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--topic", "-t", required=True, help="Podcast-Thema")
@click.option(
    "--style",
    "-s",
    type=click.Choice([s.value for s in PodcastStyle]),
    default="discussion",
    help="Podcast-Stil",
)
@click.option("--duration", "-d", default=10, type=int, help="Dauer in Minuten")
@click.option("--language", "-l", default="de", help="Sprache (de, en, etc.)")
@click.option("--llm", default="llama2", help="Ollama LLM Modell")
@click.option("--output", "-o", default="podcast.mp3", help="Ausgabedatei")
@click.option("--music", help="Pfad zu Hintergrundmusik (optional)")
def generate(topic, style, duration, language, llm, output, music):
    """
    Generiert einen neuen Podcast

    Beispiel:

        podcastforge generate --topic "KI in der Medizin" --duration 15
    """
    console.print(
        """
[bold cyan]╔══════════════════════════════════════╗
║       🎙️ PodcastForge AI 🤖          ║
║   KI-gestützte Podcast-Generierung    ║
╚══════════════════════════════════════╝[/bold cyan]
    """
    )

    try:
        # Initialisiere PodcastForge
        forge = PodcastForge(llm_model=llm, language=language)

        # Generiere Podcast
        podcast_file = forge.create_podcast(
            topic=topic, style=style, duration=duration, output=output, background_music=music
        )

        console.print(f"\n[bold green]🎉 Erfolg![/bold green]")
        console.print(f"[green]Podcast erstellt: {podcast_file}[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Fehler: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="podcast.mp3", help="Ausgabedatei")
def from_script(script_path, output):
    """
    Erstellt Podcast aus bestehendem Drehbuch

    Beispiel:

        podcastforge from-script mein_script.json
    """
    try:
        forge = PodcastForge()
        podcast_file = forge.create_from_script(script_path, output)

        console.print(f"[bold green]✅ Podcast erstellt: {podcast_file}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Fehler: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
def test():
    """
    Testet die Installation und Konfiguration
    """
    console.print("[cyan]🔍 Teste PodcastForge Installation...[/cyan]\n")

    # Test 1: Python-Pakete
    console.print("[bold]1. Python-Pakete[/bold]")
    packages = ["click", "rich", "pydub", "requests"]

    for pkg in packages:
        try:
            __import__(pkg)
            console.print(f"  [green]✓[/green] {pkg}")
        except ImportError:
            console.print(f"  [red]✗[/red] {pkg} - Nicht installiert")

    # Test 2: Ollama
    console.print("\n[bold]2. Ollama Verbindung[/bold]")
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            console.print("  [green]✓[/green] Ollama läuft")
            models = response.json().get("models", [])
            console.print(f"  Verfügbare Modelle: {', '.join([m['name'] for m in models[:3]])}")
        else:
            console.print("  [yellow]⚠[/yellow] Ollama antwortet nicht korrekt")
    except:
        console.print("  [red]✗[/red] Ollama nicht erreichbar")
        console.print("  [dim]Starte Ollama mit: ollama serve[/dim]")

    # Test 3: FFmpeg
    console.print("\n[bold]3. FFmpeg[/bold]")
    import subprocess

    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=2)
        if result.returncode == 0:
            console.print("  [green]✓[/green] FFmpeg installiert")
        else:
            console.print("  [yellow]⚠[/yellow] FFmpeg gefunden aber Fehler")
    except FileNotFoundError:
        console.print("  [red]✗[/red] FFmpeg nicht gefunden")
        console.print("  [dim]Installiere mit: apt-get install ffmpeg[/dim]")

    console.print("\n[bold green]Test abgeschlossen![/bold green]")


@cli.command()
def models():
    """
    Zeigt verfügbare Ollama Modelle
    """
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags")

        if response.status_code == 200:
            models = response.json().get("models", [])

            console.print("\n[bold]Verfügbare Ollama Modelle:[/bold]\n")

            for model in models:
                name = model["name"]
                size = model.get("size", 0) / (1024**3)  # GB
                console.print(f"  • [cyan]{name}[/cyan] ({size:.1f} GB)")

            console.print(f"\n[dim]Gesamt: {len(models)} Modelle[/dim]")
        else:
            console.print("[red]Ollama nicht erreichbar[/red]")

    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")



@cli.command()
@click.option("--language", "-l", default=None, help="Filter nach Sprache (de, en, etc.)")
@click.option(
    "--gender",
    "-g",
    type=click.Choice(["male", "female", "neutral"]),
    help="Filter nach Geschlecht",
)
@click.option("--style", "-s", help="Filter nach Stil (professional, documentary, etc.)")
def voices(language, gender, style):
    """
    Zeigt verfügbare Voice Library Stimmen

    Beispiele:

        podcastforge voices
        podcastforge voices --language de
        podcastforge voices --gender male --style professional
    """
    from .voices.library import VoiceGender, VoiceStyle

    voice_lib = get_voice_library()

    # Filter anwenden
    filters = {}
    if language:
        filters["language"] = language
    if gender:
        filters["gender"] = VoiceGender(gender)
    if style:
        try:
            filters["style"] = VoiceStyle(style.upper())
        except ValueError:
            console.print(f"[yellow]Unbekannter Stil: {style}[/yellow]")
            console.print("Verfügbare Stile: professional, documentary, dramatic, etc.")
            return

    voices_list = voice_lib.search(**filters)

    if not voices_list:
        console.print("[yellow]Keine Stimmen gefunden mit den angegebenen Filtern[/yellow]")
        return

    # Tabelle erstellen
    from rich.table import Table

    table = Table(title=f"Voice Library{f' ({language})' if language else ''}")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Sprache", style="yellow")
    table.add_column("Geschlecht", style="magenta")
    table.add_column("Stil", style="blue")
    table.add_column("Beschreibung", style="dim")

    for voice in voices_list:
        table.add_row(
            voice.id,
            voice.display_name,
            voice.language,
            voice.gender.value,
            voice.style.value,
            voice.description[:50] + "..." if len(voice.description) > 50 else voice.description,
        )

    console.print("\n")
    console.print(table)
    console.print(f"\n[bold]Gefunden: {len(voices_list)} Stimmen[/bold]")
    console.print(f"[dim]Gesamt in Bibliothek: {voice_lib.get_voice_count()} Stimmen[/dim]\n")


@cli.command()
def templates():
    """
    Zeigt verfügbare Podcast-Vorlagen und Stile

    Beispiel:

        podcastforge templates
    """
    from rich.table import Table
    from .core.config import PODCAST_TEMPLATES, PodcastStyle

    console.print("\n[bold cyan]📋 Verfügbare Podcast-Vorlagen[/bold cyan]\n")

    table = Table(title="Podcast-Stile")
    table.add_column("Stil", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Sprecher", style="yellow")
    table.add_column("Dauer", style="magenta")
    table.add_column("Beschreibung", style="dim")

    for style, template in PODCAST_TEMPLATES.items():
        table.add_row(
            style.value,
            template["name"],
            str(template["num_speakers"]),
            f"{template['suggested_duration']} min",
            template["description"][:50] + "..." if len(template["description"]) > 50 else template["description"],
        )

    console.print(table)
    console.print("\n[dim]Nutze: podcastforge generate --style <stil> --topic 'Dein Thema'[/dim]\n")


@cli.command()
@click.option("--topic", "-t", required=True, help="Podcast-Thema")
@click.option(
    "--style",
    "-s",
    type=click.Choice([s.value for s in PodcastStyle]),
    default="discussion",
    help="Podcast-Stil (nutze 'podcastforge templates' für Übersicht)",
)
@click.option("--language", "-l", default="de", help="Sprache (de, en, etc.)")
@click.option("--output", "-o", default=None, help="Ausgabedatei (optional)")
def quick(topic, style, language, output):
    """
    🚀 Schnellstart: Erstellt einen Podcast mit Standardeinstellungen

    Einfachster Weg um einen Podcast zu generieren.
    Nutzt automatisch optimale Stimmen und Einstellungen.

    Beispiele:

        podcastforge quick --topic "Künstliche Intelligenz"

        podcastforge quick -t "Klimawandel" -s interview

        podcastforge quick -t "Gesundheit" --language en
    """
    from .core.config import PODCAST_TEMPLATES, get_podcast_template

    console.print(
        """
[bold cyan]╔══════════════════════════════════════╗
║     🚀 PodcastForge Schnellstart      ║
╚══════════════════════════════════════╝[/bold cyan]
    """
    )

    # Hole Template für den Stil
    template = get_podcast_template(PodcastStyle(style))

    # Generiere Ausgabedatei wenn nicht angegeben
    if not output:
        # Erstelle sicheren Dateinamen aus Thema
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
        output = f"podcast_{safe_topic.lower()}.mp3"

    console.print(f"[green]📻 Podcast:[/green] {template['name']}")
    console.print(f"[green]📝 Thema:[/green] {topic}")
    console.print(f"[green]👥 Sprecher:[/green] {template['num_speakers']}")
    console.print(f"[green]⏱️ Geschätzte Dauer:[/green] {template['suggested_duration']} min")
    console.print(f"[green]🎨 Tonalität:[/green] {template['tone']}")
    console.print()

    try:
        # Initialisiere PodcastForge mit Standardeinstellungen
        forge = PodcastForge(llm_model="llama2", language=language)

        # Generiere Podcast
        podcast_file = forge.create_podcast(
            topic=topic,
            style=style,
            duration=template['suggested_duration'],
            output=output,
        )

        console.print(f"\n[bold green]🎉 Erfolg![/bold green]")
        console.print(f"[green]Podcast erstellt: {podcast_file}[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Fehler: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
def quality():
    """
    Zeigt verfügbare Qualitätsstufen für die Sprachsynthese

    Beispiel:

        podcastforge quality
    """
    from rich.table import Table
    from .core.config import VOICE_QUALITY_PRESETS, VoiceQuality

    console.print("\n[bold cyan]🎚️ Qualitätsstufen[/bold cyan]\n")

    table = Table(title="Voice-Qualität")
    table.add_column("Stufe", style="cyan")
    table.add_column("Engine", style="green")
    table.add_column("Sample Rate", style="yellow")
    table.add_column("Bitrate", style="magenta")
    table.add_column("Beschreibung", style="dim")

    for quality_level, settings in VOICE_QUALITY_PRESETS.items():
        table.add_row(
            quality_level.value,
            settings["engine"],
            f"{settings['sample_rate']} Hz",
            settings["bitrate"],
            settings["description"],
        )

    console.print(table)
    console.print("\n[dim]Standard: 'standard' - Ausgewogene Qualität für normale Podcasts[/dim]\n")


def main():
    """Haupteinstiegspunkt"""
    cli()


if __name__ == "__main__":
    main()
