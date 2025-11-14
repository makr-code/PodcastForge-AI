"""
Ollama Client für LLM-Integration
"""

import json
import logging
from typing import List, Dict, Optional

import requests
from rich.console import Console

from ..core.config import PodcastConfig, PodcastStyle

console = Console()
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client für Ollama LLM API zur Drehbucherstellung
    """
    
    def __init__(self, model: str = "llama2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"
        self._verify_connection()
    
    def _verify_connection(self):
        """Überprüft Verbindung zu Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Ollama nicht erreichbar")
            
            models = response.json()
            available = [m['name'] for m in models.get('models', [])]
            
            if not any(self.model in m for m in available):
                console.print(f"[yellow]⚠️ Model '{self.model}' nicht gefunden[/yellow]")
                console.print(f"[yellow]Verfügbare Modelle: {', '.join(available)}[/yellow]")
                console.print(f"[yellow]Führe aus: ollama pull {self.model}[/yellow]")
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Ollama-Verbindungsfehler: {e}[/red]")
            console.print("[yellow]Stelle sicher, dass Ollama läuft: ollama serve[/yellow]")
            raise
    
    def generate_script(self, config: PodcastConfig) -> List[Dict]:
        """
        Generiert Podcast-Drehbuch mit LLM
        
        Args:
            config: Podcast-Konfiguration
            
        Returns:
            Liste von Dialog-Zeilen
        """
        console.print(f"[cyan]🤖 Generiere Drehbuch mit {self.model}...[/cyan]")
        
        prompt = self._create_prompt(config)
        response = self._query_ollama(prompt, config.temperature)
        script = self._parse_response(response, config)
        
        console.print(f"[green]✅ {len(script)} Dialog-Zeilen generiert[/green]")
        return script
    
    def _create_prompt(self, config: PodcastConfig) -> str:
        """Erstellt Prompt für LLM"""
        speakers_desc = "\n".join([
            f"- {s.name} ({s.role}): {s.personality}"
            for s in config.speakers
        ])
        
        style_instructions = {
            PodcastStyle.INTERVIEW: "Erstelle ein Interview mit Fragen und ausführlichen Antworten.",
            PodcastStyle.DISCUSSION: "Erstelle eine lebhafte Diskussion mit verschiedenen Meinungen.",
            PodcastStyle.EDUCATIONAL: "Erstelle einen lehrreichen Dialog mit klaren Erklärungen.",
            PodcastStyle.NARRATIVE: "Erstelle eine erzählende Geschichte mit Dialogen.",
            PodcastStyle.NEWS: "Erstelle einen Nachrichtenbeitrag mit Moderator und Experten.",
            PodcastStyle.COMEDY: "Erstelle einen humorvollen Dialog mit Witzen.",
            PodcastStyle.DEBATE: "Erstelle eine strukturierte Debatte mit Pro- und Contra-Argumenten.",
        }
        
        estimated_words = config.duration_minutes * 150
        
        prompt = f"""Du bist ein professioneller Podcast-Drehbuchautor. Erstelle ein {config.duration_minutes}-minütiges Podcast-Drehbuch zum Thema "{config.topic}".

Stil: {config.style.value}
{style_instructions.get(config.style, "")}

Sprecher:
{speakers_desc}

Anforderungen:
1. Das Drehbuch soll natürlich und authentisch klingen
2. Jeder Sprecher soll seiner Persönlichkeit entsprechend sprechen
3. Füge natürliche Pausen und Füllwörter ein für Realismus
4. Die Sprecher sollen aufeinander reagieren und interagieren
5. Sprache: {config.language}
6. Zieldauer: etwa {config.duration_minutes} Minuten (ca. {estimated_words} Wörter)
7. Verwende eine lebendige, authentische Sprache

Format: Gib das Drehbuch als JSON-Array zurück:
[
  {{"speaker": "Name", "text": "Dialog-Text", "emotion": "neutral/happy/excited/thoughtful/serious"}},
  ...
]

Wichtig: Beginne direkt mit dem JSON-Array ohne weitere Erklärungen oder Markdown-Formatierung."""
        
        return prompt
    
    def _query_ollama(self, prompt: str, temperature: float) -> str:
        """Sendet Anfrage an Ollama"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=data,
                timeout=180
            )
            response.raise_for_status()
            return response.json()['response']
        
        except requests.exceptions.Timeout:
            logger.error("Ollama API Timeout")
            raise RuntimeError("LLM-Anfrage zu langsam - versuche kleineres Modell")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API Fehler: {e}")
            raise
    
    def _parse_response(self, response: str, config: PodcastConfig) -> List[Dict]:
        """Parst LLM-Antwort zu strukturiertem Script"""
        try:
            # Entferne potenzielle Markdown-Formatierung
            response = response.strip()
            if response.startswith("```"):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            
            script_data = json.loads(response)
            
            # Validiere und erweitere
            validated_script = []
            for entry in script_data:
                speaker_name = entry.get('speaker', '')
                speaker = next(
                    (s for s in config.speakers if s.name == speaker_name),
                    None
                )
                
                if speaker:
                    validated_script.append({
                        'speaker_id': speaker.id,
                        'speaker_name': speaker.name,
                        'text': entry.get('text', '').strip(),
                        'emotion': entry.get('emotion', 'neutral'),
                        'voice_profile': speaker.voice_profile,
                        'pause_after': 0.5
                    })
            
            return validated_script
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Fehler: {e}")
            logger.debug(f"Response war: {response[:500]}")
            return self._fallback_parse(response, config)
    
    def _fallback_parse(self, response: str, config: PodcastConfig) -> List[Dict]:
        """Fallback-Parser wenn JSON fehlschlägt"""
        lines = [l.strip() for l in response.split('\n') if l.strip()]
        script = []
        
        for i, line in enumerate(lines):
            speaker = config.speakers[i % len(config.speakers)]
            
            # Entferne potenzielle Sprecher-Präfixe
            for s in config.speakers:
                if line.startswith(f"{s.name}:"):
                    line = line[len(s.name)+1:].strip()
                    speaker = s
                    break
            
            if line:
                script.append({
                    'speaker_id': speaker.id,
                    'speaker_name': speaker.name,
                    'text': line,
                    'emotion': 'neutral',
                    'voice_profile': speaker.voice_profile,
                    'pause_after': 0.5
                })
        
        return script
