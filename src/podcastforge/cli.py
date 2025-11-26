#!/usr/bin/env python3
"""
Command Line Interface für PodcastForge AI
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core.config import PodcastStyle
from .core.forge import PodcastForge
from .voices.library import get_voice_library

console = Console()


class AliasedGroup(click.Group):
    """Unterstützt Befehlsaliase für bessere UX."""

    def get_command(self, ctx, cmd_name):
        # Aliase definieren
        aliases = {
            "g": "generate",
            "q": "quick",
            "t": "templates",
            "v": "voices",
            "e": "edit",
            "s": "status",
            "w": "wizard",
        }
        cmd_name = aliases.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)


@click.group(cls=AliasedGroup)
@click.version_option(version="1.2.0")
def cli():
    """
    🎙️ PodcastForge AI - KI-gestützter Podcast-Generator

    \b
    Generiert Podcasts mit Ollama LLMs und natürlichen TTS-Stimmen.

    \b
    🚀 SCHNELLSTART:
        podcastforge wizard              Interaktiver Assistent
        podcastforge quick -t "Thema"    Ein-Befehl-Podcast

    \b
    📋 BEFEHLE (Kurzform in Klammern):
        wizard (w)     Interaktiver Einrichtungsassistent
        quick (q)      Schnellstart-Podcast
        generate (g)   Podcast mit allen Optionen
        templates (t)  Verfügbare Stile anzeigen
        voices (v)     Stimmen durchsuchen
        edit (e)       GUI-Editor öffnen
        status (s)     Systemstatus prüfen
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

    except ImportError:
        console.print("[red]Fehler: tkinter nicht installiert![/red]")
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

        console.print("\n[bold green]🎉 Erfolg![/bold green]")
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
    except Exception:
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
    from .core.config import PODCAST_TEMPLATES

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
    from .core.config import get_podcast_template

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

        console.print("\n[bold green]🎉 Erfolg![/bold green]")
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
    from .core.config import VOICE_QUALITY_PRESETS

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


@cli.command()
def status():
    """
    🔍 Zeigt den Systemstatus auf einen Blick

    Prüft alle wichtigen Komponenten:
    - Python-Pakete
    - Ollama-Verbindung
    - TTS-Engines
    - FFmpeg
    - Voice Library

    Beispiel:

        podcastforge status
    """
    from rich.panel import Panel

    console.print(Panel.fit(
        "[bold cyan]🎙️ PodcastForge AI - Systemstatus[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    all_ok = True

    # 1. Python-Pakete
    console.print("[bold]📦 Pakete[/bold]")
    packages = {
        "click": "CLI Framework",
        "rich": "Terminal UI",
        "pydub": "Audio Processing",
        "requests": "HTTP Client",
        "yaml": "YAML Support",
    }

    for pkg, desc in packages.items():
        try:
            __import__(pkg if pkg != "yaml" else "yaml")
            console.print(f"  [green]✓[/green] {pkg} ({desc})")
        except ImportError:
            console.print(f"  [red]✗[/red] {pkg} ({desc}) - [dim]Nicht installiert[/dim]")
            all_ok = False

    # 2. Ollama
    console.print("\n[bold]🤖 Ollama LLM[/bold]")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            console.print(f"  [green]✓[/green] Ollama läuft ({len(models)} Modelle)")
            if models:
                console.print(f"  [dim]    Modelle: {', '.join([m['name'] for m in models[:3]])}{'...' if len(models) > 3 else ''}[/dim]")
        else:
            console.print("  [yellow]⚠[/yellow] Ollama antwortet nicht korrekt")
            all_ok = False
    except Exception:
        console.print("  [red]✗[/red] Ollama nicht erreichbar")
        console.print("  [dim]    Starte mit: ollama serve[/dim]")
        all_ok = False

    # 3. FFmpeg
    console.print("\n[bold]🎬 FFmpeg[/bold]")
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=2)
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.decode().split('\n')[0]
            version = version_line.split()[2] if len(version_line.split()) > 2 else "unbekannt"
            console.print(f"  [green]✓[/green] FFmpeg installiert (v{version})")
        else:
            console.print("  [yellow]⚠[/yellow] FFmpeg gefunden aber Fehler")
            all_ok = False
    except FileNotFoundError:
        console.print("  [red]✗[/red] FFmpeg nicht gefunden")
        console.print("  [dim]    Installiere: apt-get install ffmpeg[/dim]")
        all_ok = False
    except Exception:
        console.print("  [yellow]⚠[/yellow] FFmpeg-Test fehlgeschlagen")

    # 4. Voice Library
    console.print("\n[bold]🎤 Voice Library[/bold]")
    try:
        voice_lib = get_voice_library()
        de_count = voice_lib.get_voice_count("de")
        en_count = voice_lib.get_voice_count("en")
        total = voice_lib.get_voice_count()
        console.print(f"  [green]✓[/green] {total} Stimmen verfügbar")
        console.print(f"  [dim]    Deutsch: {de_count}, Englisch: {en_count}[/dim]")
    except Exception as e:
        console.print(f"  [red]✗[/red] Fehler: {e}")
        all_ok = False

    # 5. TTS Engines
    console.print("\n[bold]🔊 TTS Engines[/bold]")
    engines_status = []
    try:
        # Check for torch (needed for most TTS)
        import torch
        engines_status.append(("PyTorch", True, f"v{torch.__version__}"))
    except ImportError:
        engines_status.append(("PyTorch", False, "Für XTTS/Bark benötigt"))

    for name, available, note in engines_status:
        if available:
            console.print(f"  [green]✓[/green] {name} ({note})")
        else:
            console.print(f"  [yellow]⚠[/yellow] {name} - {note}")

    # Zusammenfassung
    console.print()
    if all_ok:
        console.print(Panel.fit(
            "[bold green]✅ Alle Systeme bereit![/bold green]\n"
            "[dim]Starte mit: podcastforge quick --topic 'Dein Thema'[/dim]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]⚠️ Einige Komponenten fehlen[/bold yellow]\n"
            "[dim]Führe 'podcastforge test' für Details aus[/dim]",
            border_style="yellow"
        ))


@cli.command()
def wizard():
    """
    🧙 Interaktiver Assistent für Podcast-Erstellung

    Führt Schritt für Schritt durch die Podcast-Erstellung:
    1. Thema eingeben
    2. Stil wählen
    3. Sprache wählen
    4. Podcast generieren

    Beispiel:

        podcastforge wizard
    """
    from rich.prompt import Prompt, Confirm
    from .core.config import PODCAST_TEMPLATES

    console.print(Panel.fit(
        "[bold cyan]🧙 PodcastForge Wizard[/bold cyan]\n"
        "[dim]Interaktiver Assistent für Podcast-Erstellung[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Schritt 1: Thema
    console.print("[bold]Schritt 1/4: Thema[/bold]")
    topic = Prompt.ask(
        "  📝 Worüber soll dein Podcast handeln?",
        default="Künstliche Intelligenz"
    )
    console.print()

    # Schritt 2: Stil
    console.print("[bold]Schritt 2/4: Podcast-Stil[/bold]")
    styles_table = Table(show_header=True, header_style="bold")
    styles_table.add_column("#", style="cyan", width=3)
    styles_table.add_column("Stil", style="green")
    styles_table.add_column("Beschreibung")

    style_list = list(PODCAST_TEMPLATES.keys())
    for i, style in enumerate(style_list, 1):
        template = PODCAST_TEMPLATES[style]
        styles_table.add_row(str(i), template["name"], template["description"][:40] + "...")

    console.print(styles_table)

    style_choice = Prompt.ask(
        "  🎨 Wähle einen Stil (1-8)",
        default="2",
        choices=[str(i) for i in range(1, len(style_list) + 1)]
    )
    selected_style = style_list[int(style_choice) - 1]
    template = PODCAST_TEMPLATES[selected_style]
    console.print(f"  [green]✓[/green] {template['name']} ausgewählt")
    console.print()

    # Schritt 3: Sprache
    console.print("[bold]Schritt 3/4: Sprache[/bold]")
    language = Prompt.ask(
        "  🌍 Sprache",
        default="de",
        choices=["de", "en"]
    )
    console.print()

    # Schritt 4: Bestätigung
    console.print("[bold]Schritt 4/4: Bestätigung[/bold]")
    console.print(f"  📻 Podcast: [cyan]{template['name']}[/cyan]")
    console.print(f"  📝 Thema: [cyan]{topic}[/cyan]")
    console.print(f"  👥 Sprecher: [cyan]{template['num_speakers']}[/cyan]")
    console.print(f"  ⏱️ Dauer: [cyan]{template['suggested_duration']} min[/cyan]")
    console.print(f"  🌍 Sprache: [cyan]{language}[/cyan]")
    console.print()

    if not Confirm.ask("  🚀 Podcast jetzt generieren?", default=True):
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        console.print("[dim]Tipp: Nutze 'podcastforge quick' für schnelle Erstellung[/dim]")
        return

    # Generiere Ausgabedatei
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
    output = f"podcast_{safe_topic.lower()}.mp3"

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🎙️ Generiere Podcast...[/bold cyan]",
        border_style="cyan"
    ))

    try:
        forge = PodcastForge(llm_model="llama2", language=language)
        podcast_file = forge.create_podcast(
            topic=topic,
            style=selected_style.value,
            duration=template['suggested_duration'],
            output=output,
        )

        console.print()
        console.print(Panel.fit(
            f"[bold green]🎉 Erfolg![/bold green]\n"
            f"[green]Podcast erstellt: {podcast_file}[/green]\n\n"
            f"[dim]Nächste Schritte:[/dim]\n"
            f"  • Abspielen: [cyan]ffplay {podcast_file}[/cyan]\n"
            f"  • Bearbeiten: [cyan]podcastforge edit[/cyan]",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[bold red]❌ Fehler: {str(e)}[/bold red]")
        console.print("[dim]Tipp: Prüfe mit 'podcastforge status' ob alle Systeme laufen[/dim]")
        sys.exit(1)


@cli.command()
def info():
    """
    ℹ️ Zeigt Informationen über PodcastForge AI

    Beispiel:

        podcastforge info
    """
    from rich.panel import Panel
    from .core.config import PODCAST_TEMPLATES, VOICE_QUALITY_PRESETS

    voice_lib = get_voice_library()

    info_text = f"""[bold cyan]🎙️ PodcastForge AI[/bold cyan]

[bold]Version:[/bold] 1.2.0
[bold]Lizenz:[/bold] MIT

[bold]📊 Statistiken:[/bold]
  • {voice_lib.get_voice_count()} Stimmen verfügbar
  • {voice_lib.get_voice_count('de')} deutsche Stimmen
  • {len(PODCAST_TEMPLATES)} Podcast-Stile
  • {len(VOICE_QUALITY_PRESETS)} Qualitätsstufen

[bold]🔗 Links:[/bold]
  • GitHub: [link]https://github.com/makr-code/PodcastForge-AI[/link]
  • Docs: [link]https://github.com/makr-code/PodcastForge-AI/docs[/link]

[bold]🚀 Schnellstart:[/bold]
  podcastforge wizard     # Interaktiver Assistent
  podcastforge quick -t "Thema"  # Ein-Befehl-Podcast"""

    console.print(Panel(info_text, border_style="cyan", padding=(1, 2)))


def main():
    """Haupteinstiegspunkt"""
    cli()


if __name__ == "__main__":
    main()
