#!/usr/bin/env python3
"""
Command Line Interface für PodcastForge AI
"""

import sys
import click
from rich.console import Console
from pathlib import Path

from .core.forge import PodcastForge
from .core.config import PodcastStyle

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
@click.option('--topic', '-t', required=True, help='Podcast-Thema')
@click.option('--style', '-s',
              type=click.Choice([s.value for s in PodcastStyle]),
              default='discussion',
              help='Podcast-Stil')
@click.option('--duration', '-d', default=10, type=int, help='Dauer in Minuten')
@click.option('--language', '-l', default='de', help='Sprache (de, en, etc.)')
@click.option('--llm', default='llama2', help='Ollama LLM Modell')
@click.option('--output', '-o', default='podcast.mp3', help='Ausgabedatei')
@click.option('--music', help='Pfad zu Hintergrundmusik (optional)')
def generate(topic, style, duration, language, llm, output, music):
    """
    Generiert einen neuen Podcast
    
    Beispiel:
    
        podcastforge generate --topic "KI in der Medizin" --duration 15
    """
    console.print("""
[bold cyan]╔══════════════════════════════════════╗
║       🎙️ PodcastForge AI 🤖          ║
║   KI-gestützte Podcast-Generierung    ║
╚══════════════════════════════════════╝[/bold cyan]
    """)
    
    try:
        # Initialisiere PodcastForge
        forge = PodcastForge(
            llm_model=llm,
            language=language
        )
        
        # Generiere Podcast
        podcast_file = forge.create_podcast(
            topic=topic,
            style=style,
            duration=duration,
            output=output,
            background_music=music
        )
        
        console.print(f"\n[bold green]🎉 Erfolg![/bold green]")
        console.print(f"[green]Podcast erstellt: {podcast_file}[/green]")
    
    except Exception as e:
        console.print(f"[bold red]❌ Fehler: {str(e)}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='podcast.mp3', help='Ausgabedatei')
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
    packages = ['click', 'rich', 'pydub', 'requests']
    
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
            models = response.json().get('models', [])
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
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=2)
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
            models = response.json().get('models', [])
            
            console.print("\n[bold]Verfügbare Ollama Modelle:[/bold]\n")
            
            for model in models:
                name = model['name']
                size = model.get('size', 0) / (1024**3)  # GB
                console.print(f"  • [cyan]{name}[/cyan] ({size:.1f} GB)")
            
            console.print(f"\n[dim]Gesamt: {len(models)} Modelle[/dim]")
        else:
            console.print("[red]Ollama nicht erreichbar[/red]")
    
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")


def main():
    """Haupteinstiegspunkt"""
    cli()


if __name__ == "__main__":
    main()
