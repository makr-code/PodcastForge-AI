"""
Hauptklasse für PodcastForge AI
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import PodcastConfig, PodcastStyle, Speaker, ScriptLine
from ..llm.ollama_client import OllamaClient
from ..tts.ebook2audiobook_adapter import Ebook2AudiobookAdapter
from ..audio.postprocessor import AudioPostProcessor
from ..voices.library import get_voice_library, VoiceGender, VoiceAge, VoiceStyle

console = Console()
logger = logging.getLogger(__name__)


class PodcastForge:
    """
    Hauptklasse die Ollama LLM und ebook2audiobook integriert
    """
    
    def __init__(self,
                 llm_model: str = "llama2",
                 ollama_host: str = "http://localhost:11434",
                 ebook2audiobook_path: str = "./ebook2audiobook",
                 language: str = "de"):
        """
        Initialisiert PodcastForge
        
        Args:
            llm_model: Ollama Modell für Drehbucherstellung
            ollama_host: Ollama Server URL
            ebook2audiobook_path: Pfad zu ebook2audiobook
            language: Sprache für Podcast
        """
        self.language = language
        self.llm_model = llm_model
        
        # Komponenten initialisieren
        console.print("[cyan]🚀 Initialisiere PodcastForge AI...[/cyan]")
        
        self.llm_client = OllamaClient(model=llm_model, host=ollama_host)
        self.tts_adapter = Ebook2AudiobookAdapter(ebook2audiobook_path)
        self.audio_processor = AudioPostProcessor()
        self.voice_library = get_voice_library()
        
        console.print("[green]✅ PodcastForge AI bereit![/green]")
    
    def create_podcast(self,
                      topic: str,
                      style: Union[str, PodcastStyle] = PodcastStyle.DISCUSSION,
                      speakers: Optional[List[Speaker]] = None,
                      duration: int = 10,
                      output: str = "podcast.mp3",
                      background_music: Optional[str] = None) -> str:
        """
        Erstellt einen kompletten Podcast von Thema bis Audio
        
        Args:
            topic: Podcast-Thema
            style: Podcast-Stil
            speakers: Liste von Sprechern (optional)
            duration: Dauer in Minuten
            output: Ausgabedatei
            background_music: Pfad zu Hintergrundmusik (optional)
            
        Returns:
            Pfad zur erstellten Audio-Datei
        """
        console.print(f"""
[bold blue]📻 Erstelle Podcast[/bold blue]
Thema: {topic}
Stil: {style}
Dauer: {duration} Minuten
        """)
        
        # Standard-Sprecher wenn keine angegeben
        if not speakers:
            speakers = self._create_default_speakers(style)
        
        # Konfiguration erstellen
        config = PodcastConfig(
            topic=topic,
            style=style if isinstance(style, PodcastStyle) else PodcastStyle(style),
            duration_minutes=duration,
            speakers=speakers,
            language=self.language,
            llm_model=self.llm_model,
            background_music=background_music
        )
        
        # 1. Drehbuch generieren
        console.print("[cyan]📝 Generiere Drehbuch mit KI...[/cyan]")
        script = self.llm_client.generate_script(config)
        
        # Drehbuch speichern
        script_path = output.replace('.mp3', '_script.json')
        self._save_script(script, script_path)
        console.print(f"[dim]Drehbuch gespeichert: {script_path}[/dim]")
        
        # 2. Audio generieren
        console.print("[cyan]🎙️ Generiere Audio...[/cyan]")
        temp_audio = output.replace('.mp3', '_temp.wav')
        self.tts_adapter.generate_audio(script, temp_audio, config)
        
        # 3. Post-Processing
        console.print("[cyan]🎚️ Audio-Nachbearbeitung...[/cyan]")
        final_path = self.audio_processor.process(temp_audio, output, config)
        
        # Aufräumen
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        console.print(f"""
[bold green]✨ Podcast erfolgreich erstellt![/bold green]
📁 Audio: {final_path}
📝 Drehbuch: {script_path}
🎭 Sprecher: {len(speakers)}
⏱️ Geschätzte Dauer: {duration} Minuten
        """)
        
        return final_path
    
    def _create_default_speakers(self, style: Union[str, PodcastStyle]) -> List[Speaker]:
        """Erstellt Standard-Sprecher basierend auf Podcast-Stil mit Voice Library"""
        if isinstance(style, str):
            style = PodcastStyle(style)
        
        # Nutze Voice Library für intelligente Vorschläge
        num_speakers = 2 if style == PodcastStyle.INTERVIEW else 3
        suggested_voices = self.voice_library.suggest_for_podcast_style(
            style=style,
            language=self.language,
            num_speakers=num_speakers
        )
        
        # Erstelle Speaker aus Voice Library Vorschlägen
        speakers = []
        role_names = self._get_role_names_for_style(style)
        
        for i, voice_profile in enumerate(suggested_voices):
            if i < len(role_names):
                speaker = Speaker(
                    id=f"speaker_{i+1}",
                    name=role_names[i]["name"],
                    role=role_names[i]["role"],
                    personality=voice_profile.description or "professionell, klar",
                    voice_profile=voice_profile.id,
                    gender=voice_profile.gender.value,
                    age=voice_profile.age.value,
                    voice_sample=voice_profile.sample_path if voice_profile.sample_path else None
                )
                speakers.append(speaker)
        
        # Fallback wenn Voice Library keine Vorschläge hat
        if not speakers:
            speakers = self._create_fallback_speakers(style)
        
        return speakers
    
    def _get_role_names_for_style(self, style: PodcastStyle) -> List[Dict[str, str]]:
        """Rolle
    def _get_role_names_for_style(self, style: PodcastStyle) -> List[Dict[str, str]]:
        """Rollenbezeichnungen für verschiedene Podcast-Stile"""
        role_mappings = {
            PodcastStyle.INTERVIEW: [
                {"name": "Max Weber", "role": "Moderator"},
                {"name": "Dr. Anna Schmidt", "role": "Expertin"}
            ],
            PodcastStyle.DISCUSSION: [
                {"name": "Tom Fischer", "role": "Moderator"},
                {"name": "Lisa Müller", "role": "Diskutantin"},
                {"name": "Michael Schmidt", "role": "Diskutant"}
            ],
            PodcastStyle.NEWS: [
                {"name": "Sarah Klein", "role": "Nachrichtensprecherin"},
                {"name": "Prof. Dr. Martin Berg", "role": "Experte"}
            ],
            PodcastStyle.EDUCATIONAL: [
                {"name": "Laura Wolf", "role": "Dozentin"},
                {"name": "Tim Schulz", "role": "Assistent"}
            ],
            PodcastStyle.DOCUMENTARY: [
                {"name": "Werner Kraus", "role": "Erzähler"}
            ],
            PodcastStyle.NARRATIVE: [
                {"name": "Julia Stern", "role": "Erzählerin"},
                {"name": "Robert Klein", "role": "Erzähler"}
            ]
        }
        
        return role_mappings.get(style, [
            {"name": "Sprecher 1", "role": "Sprecher"},
            {"name": "Sprecher 2", "role": "Sprecher"}
        ])
    
    def _create_fallback_speakers(self, style: PodcastStyle) -> List[Speaker]:
        """Fallback-Sprecher wenn Voice Library keine Vorschläge hat"""
        if style == PodcastStyle.INTERVIEW:
            return [
                Speaker(
                    id="host",
                    name="Max",
                    role="Moderator",
                    personality="freundlich, neugierig, professionell",
                    voice_profile="de_male_1",
                    gender="male"
                ),
                Speaker(
                    id="guest",
                    name="Dr. Anna Schmidt",
                    role="Expertin",
                    personality="kompetent, enthusiastisch, detailliert",
                    voice_profile="de_female_1",
                    gender="female"
                )
            ]
        elif style == PodcastStyle.DISCUSSION:
            return [
                Speaker(
                    id="moderator",
                    name="Tom Weber",
                    role="Moderator",
                    personality="neutral, vermittelnd, strukturiert",
                    voice_profile="de_male_2",
                    gender="male"
                ),
                Speaker(
                    id="speaker1",
                    name="Lisa Müller",
                    role="Diskutantin",
                    personality="optimistisch, überzeugend, lebhaft",
                    voice_profile="de_female_2",
                    gender="female"
                ),
                Speaker(
                    id="speaker2",
                    name="Michael Schmidt",
                    role="Diskutant",
                    personality="analytisch, skeptisch, bedacht",
                    voice_profile="de_male_3",
                    gender="male"
                )
            ]
        else:
            # Standard
            return [
                Speaker(
                    id="speaker1",
                    name="Alex",
                    role="Sprecher 1",
                    personality="vielseitig, professionell",
                    voice_profile="de_neutral_1",
                    gender="neutral"
                ),
                Speaker(
                    id="speaker2",
                    name="Sarah",
                    role="Sprecher 2",
                    personality="vielseitig, freundlich",
                    voice_profile="de_neutral_2",
                    gender="neutral"
                )
            ]
    
    def _save_script(self, script: List[Dict], path: str):
        """Speichert Drehbuch als JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
    
    def load_script(self, path: str) -> List[Dict]:
        """Lädt Drehbuch aus JSON-Datei"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_from_script(self,
                          script_path: str,
                          output: str = "podcast.mp3",
                          speakers: Optional[List[Speaker]] = None) -> str:
        """
        Erstellt Podcast aus bestehendem Drehbuch
        
        Args:
            script_path: Pfad zum Drehbuch (JSON)
            output: Ausgabedatei
            speakers: Sprecher-Definitionen
            
        Returns:
            Pfad zur Audio-Datei
        """
        script = self.load_script(script_path)
        
        if not speakers:
            # Versuche Sprecher aus Script zu extrahieren
            speakers = self._extract_speakers_from_script(script)
        
        config = PodcastConfig(
            topic="Custom Script",
            style=PodcastStyle.DISCUSSION,
            speakers=speakers,
            language=self.language
        )
        
        temp_audio = output.replace('.mp3', '_temp.wav')
        self.tts_adapter.generate_audio(script, temp_audio, config)
        final_path = self.audio_processor.process(temp_audio, output, config)
        
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        return final_path
    
    def _extract_speakers_from_script(self, script: List[Dict]) -> List[Speaker]:
        """Extrahiert Sprecher-Informationen aus Drehbuch"""
        speakers = {}
        for line in script:
            speaker_id = line.get('speaker_id', '')
            if speaker_id and speaker_id not in speakers:
                speakers[speaker_id] = Speaker(
                    id=speaker_id,
                    name=line.get('speaker_name', speaker_id),
                    role="Sprecher",
                    personality="neutral",
                    voice_profile=line.get('voice_profile', 'de_neutral')
                )
        return list(speakers.values())
