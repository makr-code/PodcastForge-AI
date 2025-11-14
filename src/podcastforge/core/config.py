"""
Konfigurationsklassen für PodcastForge
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PodcastStyle(Enum):
    """Podcast-Stil Optionen"""
    INTERVIEW = "interview"
    DISCUSSION = "discussion"
    EDUCATIONAL = "educational"
    NARRATIVE = "narrative"
    NEWS = "news"
    COMEDY = "comedy"
    DEBATE = "debate"


@dataclass
class Speaker:
    """Sprecher-Profil"""
    id: str
    name: str
    role: str
    personality: str
    voice_profile: str
    voice_sample: Optional[str] = None
    gender: str = "neutral"
    age: str = "adult"
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Speaker ID ist erforderlich")
        if not self.name:
            raise ValueError("Speaker Name ist erforderlich")


@dataclass
class PodcastConfig:
    """Konfiguration für Podcast-Generierung"""
    topic: str
    style: PodcastStyle
    duration_minutes: int = 10
    speakers: List[Speaker] = field(default_factory=list)
    language: str = "de"
    llm_model: str = "llama2"
    temperature: float = 0.7
    background_music: Optional[str] = None
    output_format: str = "mp3"
    voice_engine: str = "xtts"
    bitrate: str = "192k"
    sample_rate: int = 44100
    
    def __post_init__(self):
        if isinstance(self.style, str):
            self.style = PodcastStyle(self.style)
        
        if self.duration_minutes < 1:
            raise ValueError("Dauer muss mindestens 1 Minute sein")
        
        if not self.speakers:
            raise ValueError("Mindestens ein Sprecher erforderlich")


@dataclass
class ScriptLine:
    """Eine Zeile im Podcast-Drehbuch"""
    speaker_id: str
    speaker_name: str
    text: str
    emotion: str = "neutral"
    pause_after: float = 0.5
    voice_profile: str = ""
    
    def to_dict(self):
        return {
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "text": self.text,
            "emotion": self.emotion,
            "pause_after": self.pause_after,
            "voice_profile": self.voice_profile,
        }
