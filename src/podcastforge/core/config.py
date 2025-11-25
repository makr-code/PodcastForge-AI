"""
Konfigurationsklassen für PodcastForge
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class PodcastStyle(Enum):
    """Podcast-Stil Optionen"""

    INTERVIEW = "interview"
    DISCUSSION = "discussion"
    EDUCATIONAL = "educational"
    NARRATIVE = "narrative"
    NEWS = "news"
    COMEDY = "comedy"
    DEBATE = "debate"
    DOCUMENTARY = "documentary"


class VoiceQuality(Enum):
    """Voice-Qualitätsstufen für natürliche Sprachsynthese"""

    PREVIEW = "preview"  # Schnell, niedriger Qualität für Vorschau
    STANDARD = "standard"  # Ausgewogen für normale Nutzung
    HIGH = "high"  # Hohe Qualität für finale Podcasts
    ULTRA = "ultra"  # Maximale Qualität mit längerer Generierungszeit


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
    voice_quality: VoiceQuality = VoiceQuality.STANDARD

    def __post_init__(self):
        if isinstance(self.style, str):
            self.style = PodcastStyle(self.style)

        if isinstance(self.voice_quality, str):
            self.voice_quality = VoiceQuality(self.voice_quality)

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


# Voice Quality Presets für unterschiedliche Anwendungsfälle
VOICE_QUALITY_PRESETS: Dict[VoiceQuality, Dict] = {
    VoiceQuality.PREVIEW: {
        "engine": "piper",
        "sample_rate": 22050,
        "bitrate": "128k",
        "description": "Schnelle Vorschau - niedriger Qualität, ideal zum Testen",
    },
    VoiceQuality.STANDARD: {
        "engine": "xtts",
        "sample_rate": 24000,
        "bitrate": "192k",
        "description": "Ausgewogene Qualität für normale Podcasts",
    },
    VoiceQuality.HIGH: {
        "engine": "xtts",
        "sample_rate": 44100,
        "bitrate": "256k",
        "description": "Hohe Qualität für professionelle Podcasts",
    },
    VoiceQuality.ULTRA: {
        "engine": "xtts",
        "sample_rate": 48000,
        "bitrate": "320k",
        "description": "Maximale Qualität für Studio-Produktionen",
    },
}


def get_quality_preset(quality: VoiceQuality) -> Dict:
    """Hole die Einstellungen für eine bestimmte Qualitätsstufe."""
    return VOICE_QUALITY_PRESETS.get(quality, VOICE_QUALITY_PRESETS[VoiceQuality.STANDARD])


# Podcast-Stil Vorlagen für schnellen Einstieg
PODCAST_TEMPLATES: Dict[PodcastStyle, Dict] = {
    PodcastStyle.INTERVIEW: {
        "name": "Interview",
        "description": "Klassisches Interview-Format mit Fragen und Antworten",
        "num_speakers": 2,
        "speaker_roles": ["Moderator", "Gast/Experte"],
        "suggested_duration": 15,
        "tone": "professionell, neugierig",
    },
    PodcastStyle.DISCUSSION: {
        "name": "Diskussion",
        "description": "Lebhafte Diskussion mit mehreren Teilnehmern",
        "num_speakers": 3,
        "speaker_roles": ["Moderator", "Diskutant 1", "Diskutant 2"],
        "suggested_duration": 20,
        "tone": "dynamisch, engagiert",
    },
    PodcastStyle.EDUCATIONAL: {
        "name": "Lehrreich",
        "description": "Erklärender Dialog für Wissensvermittlung",
        "num_speakers": 2,
        "speaker_roles": ["Dozent", "Assistent/Frager"],
        "suggested_duration": 15,
        "tone": "informativ, verständlich",
    },
    PodcastStyle.NEWS: {
        "name": "Nachrichten",
        "description": "Nachrichtenformat mit Analysen",
        "num_speakers": 2,
        "speaker_roles": ["Nachrichtensprecher", "Experte"],
        "suggested_duration": 10,
        "tone": "sachlich, aktuell",
    },
    PodcastStyle.NARRATIVE: {
        "name": "Erzählung",
        "description": "Story-basiertes Format mit Erzählern",
        "num_speakers": 2,
        "speaker_roles": ["Erzähler 1", "Erzähler 2"],
        "suggested_duration": 20,
        "tone": "atmosphärisch, fesselnd",
    },
    PodcastStyle.DOCUMENTARY: {
        "name": "Dokumentation",
        "description": "Dokumentarischer Stil mit Hintergrundinfos",
        "num_speakers": 1,
        "speaker_roles": ["Dokumentar-Sprecher"],
        "suggested_duration": 15,
        "tone": "informativ, tiefgründig",
    },
    PodcastStyle.COMEDY: {
        "name": "Comedy",
        "description": "Humorvolles Format mit Witzen",
        "num_speakers": 2,
        "speaker_roles": ["Comedian 1", "Comedian 2"],
        "suggested_duration": 10,
        "tone": "humorvoll, unterhaltsam",
    },
    PodcastStyle.DEBATE: {
        "name": "Debatte",
        "description": "Strukturierte Debatte mit Pro/Contra",
        "num_speakers": 3,
        "speaker_roles": ["Moderator", "Pro-Redner", "Contra-Redner"],
        "suggested_duration": 20,
        "tone": "argumentativ, strukturiert",
    },
}


def get_podcast_template(style: PodcastStyle) -> Dict:
    """Hole die Vorlage für einen bestimmten Podcast-Stil."""
    return PODCAST_TEMPLATES.get(style, PODCAST_TEMPLATES[PodcastStyle.DISCUSSION])
