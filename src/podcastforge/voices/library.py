"""
Voice Library - Professionelle Stimmen-Verwaltung
Basierend auf ebook2audiobook Voice-Sammlung
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import PodcastStyle


class VoiceGender(Enum):
    """Geschlecht der Stimme"""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceAge(Enum):
    """Altersgruppe der Stimme"""

    CHILD = "child"
    YOUNG = "young"
    ADULT = "adult"
    ELDER = "elder"


class VoiceStyle(Enum):
    """Stimm-Stil"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    AUTHORITATIVE = "authoritative"
    DOCUMENTARY = "documentary"
    DRAMATIC = "dramatic"
    ENERGETIC = "energetic"
    CALM = "calm"
    NEWS = "news"
    STORYTELLING = "storytelling"


@dataclass
class VoiceProfile:
    """Vollständiges Voice-Profil"""

    id: str
    name: str
    display_name: str
    language: str
    gender: VoiceGender
    age: VoiceAge
    style: VoiceStyle
    description: str = ""
    repo: str = "drewThomasson/fineTunedTTSModels"
    sub_path: str = ""
    sample_filename: str = ""
    engine: str = "xtts"
    samplerate: int = 24000
    accent: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def sample_path(self) -> str:
        """Vollständiger Pfad zum Voice-Sample"""
        if self.sample_filename:
            return os.path.join(
                "voices", self.language, self.age.value, self.gender.value, self.sample_filename
            )
        return ""

    def matches_criteria(
        self,
        language: Optional[str] = None,
        gender: Optional[VoiceGender] = None,
        age: Optional[VoiceAge] = None,
        style: Optional[VoiceStyle] = None,
    ) -> bool:
        """Prüfe ob Stimme den Kriterien entspricht"""
        if language and self.language != language:
            return False
        if gender and self.gender != gender:
            return False
        if age and self.age != age:
            return False
        if style and self.style != style:
            return False
        return True


class VoiceLibrary:
    """
    Professionelle Voice-Bibliothek
    Basiert auf ebook2audiobook's umfassender Stimmen-Sammlung
    """

    # Deutsche Stimmen
    GERMAN_VOICES = [
        VoiceProfile(
            id="thorsten_de",
            name="Thorsten",
            display_name="Thorsten (Professionell)",
            language="de",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
            description="Professionelle deutsche Stimme, klar und deutlich",
            engine="vits",
            tags=["german", "news", "professional"],
        ),
        # Weitere deutsche Stimmen können hier ergänzt werden
    ]

    # Englische Stimmen (aus ebook2audiobook)
    ENGLISH_VOICES = [
        # Dokumentarfilm-Stimmen
        VoiceProfile(
            id="david_attenborough",
            name="DavidAttenborough",
            display_name="David Attenborough Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ELDER,
            style=VoiceStyle.DOCUMENTARY,
            description="Ikonische Dokumentarfilm-Stimme, ruhig und autoritativ",
            sub_path="xtts-v2/eng/DavidAttenborough/",
            sample_filename="DavidAttenborough.wav",
            tags=["documentary", "nature", "authoritative", "british"],
        ),
        # Professionelle Sprecher
        VoiceProfile(
            id="morgan_freeman",
            name="MorganFreeman",
            display_name="Morgan Freeman Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.AUTHORITATIVE,
            description="Tiefe, vertrauenswürdige Stimme mit Autorität",
            sub_path="xtts-v2/eng/MorganFreeman/",
            sample_filename="MorganFreeman.wav",
            tags=["authoritative", "deep", "trustworthy", "narrator"],
        ),
        VoiceProfile(
            id="neil_gaiman",
            name="NeilGaiman",
            display_name="Neil Gaiman Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.STORYTELLING,
            description="Storytelling-Stimme, fesselnd und atmosphärisch",
            sub_path="xtts-v2/eng/NeilGaiman/",
            sample_filename="NeilGaiman.wav",
            tags=["storytelling", "fantasy", "british", "narrator"],
        ),
        VoiceProfile(
            id="ray_porter",
            name="RayPorter",
            display_name="Ray Porter Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
            description="Professionelle Audiobook-Stimme, warm und klar",
            sub_path="xtts-v2/eng/RayPorter/",
            sample_filename="RayPorter.wav",
            tags=["audiobook", "professional", "warm"],
        ),
        # Weibliche Stimmen
        VoiceProfile(
            id="rosamund_pike",
            name="RosamundPike",
            display_name="Rosamund Pike Stil",
            language="en",
            gender=VoiceGender.FEMALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.DRAMATIC,
            description="Dramatische, ausdrucksstarke weibliche Stimme",
            sub_path="xtts-v2/eng/RosamundPike/",
            sample_filename="RosamundPike.wav",
            tags=["dramatic", "british", "expressive", "narrator"],
        ),
        VoiceProfile(
            id="scarlett_johansson",
            name="ScarlettJohansson",
            display_name="Scarlett Johansson Stil",
            language="en",
            gender=VoiceGender.FEMALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
            description="Professionelle, angenehme weibliche Stimme",
            sub_path="xtts-v2/eng/ScarlettJohansson/",
            sample_filename="ScarlettJohansson.wav",
            tags=["professional", "smooth", "american"],
        ),
        VoiceProfile(
            id="julia_whelan",
            name="JuliaWhenlan",
            display_name="Julia Whelan Stil",
            language="en",
            gender=VoiceGender.FEMALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
            description="Professionelle Audiobook-Sprecherin, vielseitig",
            sub_path="xtts-v2/eng/JuliaWhenlan/",
            sample_filename="JuliaWhenlan.wav",
            tags=["audiobook", "professional", "versatile"],
        ),
        # Tech/YouTube Stimmen
        VoiceProfile(
            id="ai_explained",
            name="AiExplained",
            display_name="AI Explained Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.PROFESSIONAL,
            description="Tech-YouTube Stimme, klar und informativ",
            sub_path="xtts-v2/eng/AiExplained/",
            sample_filename="AiExplained.wav",
            tags=["tech", "youtube", "educational", "clear"],
        ),
        # Entspannende/ASMR Stimmen
        VoiceProfile(
            id="bob_ross",
            name="BobRoss",
            display_name="Bob Ross Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.CALM,
            description="Beruhigende, sanfte Stimme",
            sub_path="xtts-v2/eng/BobRoss/",
            sample_filename="BobRoss.wav",
            tags=["calm", "soothing", "educational", "relaxing"],
        ),
        # News/Anchorman Stimmen
        VoiceProfile(
            id="bryan_cranston",
            name="BryanCranston",
            display_name="Bryan Cranston Stil",
            language="en",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            style=VoiceStyle.DRAMATIC,
            description="Dramatische, intensive Stimme",
            sub_path="xtts-v2/eng/BryanCranston/",
            sample_filename="BryanCranston.wav",
            tags=["dramatic", "intense", "american"],
        ),
    ]

    def __init__(self, voices_dir: str = "voices"):
        self.voices_dir = Path(voices_dir)
        self.all_voices = self.GERMAN_VOICES + self.ENGLISH_VOICES
        self._index_voices()

    def _index_voices(self):
        """Erstelle Indizes für schnelle Suche"""
        self.by_language = {}
        self.by_gender = {}
        self.by_style = {}
        self.by_id = {}

        for voice in self.all_voices:
            # Nach Sprache
            if voice.language not in self.by_language:
                self.by_language[voice.language] = []
            self.by_language[voice.language].append(voice)

            # Nach Geschlecht
            if voice.gender not in self.by_gender:
                self.by_gender[voice.gender] = []
            self.by_gender[voice.gender].append(voice)

            # Nach Stil
            if voice.style not in self.by_style:
                self.by_style[voice.style] = []
            self.by_style[voice.style].append(voice)

            # Nach ID
            self.by_id[voice.id] = voice

    def get_voice(self, voice_id: str) -> Optional[VoiceProfile]:
        """Hole Stimme nach ID"""
        return self.by_id.get(voice_id)

    def search(
        self,
        language: Optional[str] = None,
        gender: Optional[VoiceGender] = None,
        age: Optional[VoiceAge] = None,
        style: Optional[VoiceStyle] = None,
        tags: Optional[List[str]] = None,
    ) -> List[VoiceProfile]:
        """Suche Stimmen nach Kriterien"""
        results = self.all_voices

        if language:
            results = [v for v in results if v.language == language]
        if gender:
            results = [v for v in results if v.gender == gender]
        if age:
            results = [v for v in results if v.age == age]
        if style:
            results = [v for v in results if v.style == style]
        if tags:
            results = [v for v in results if any(tag in v.tags for tag in tags)]

        return results

    def suggest_for_podcast_style(
        self, style: PodcastStyle, language: str = "de", num_speakers: int = 2
    ) -> List[VoiceProfile]:
        """
        Schlage optimale Stimmen für Podcast-Stil vor
        """
        suggestions = []

        if style == PodcastStyle.INTERVIEW:
            # Host: Professional, Guest: Authoritative
            host = self.search(
                language=language, style=VoiceStyle.PROFESSIONAL, gender=VoiceGender.MALE
            )
            guest = self.search(language=language, style=VoiceStyle.AUTHORITATIVE)

            if host and guest:
                suggestions = [
                    host[0],
                    guest[0] if guest else host[1] if len(host) > 1 else host[0],
                ]

        elif style == PodcastStyle.DOCUMENTARY:
            # Dokumentarfilm-Stimme
            doc_voices = self.search(language=language, style=VoiceStyle.DOCUMENTARY)
            if doc_voices:
                suggestions = [doc_voices[0]]
            else:
                # Fallback: Authoritative
                auth_voices = self.search(language=language, style=VoiceStyle.AUTHORITATIVE)
                if auth_voices:
                    suggestions = [auth_voices[0]]

        elif style == PodcastStyle.DISCUSSION:
            # Mix aus verschiedenen Stimmen
            male_voices = self.search(language=language, gender=VoiceGender.MALE)
            female_voices = self.search(language=language, gender=VoiceGender.FEMALE)

            if num_speakers >= 2 and male_voices and female_voices:
                suggestions = [male_voices[0], female_voices[0]]
                if num_speakers >= 3 and len(male_voices) > 1:
                    suggestions.append(male_voices[1])
            elif male_voices:
                suggestions = male_voices[:num_speakers]

        elif style == PodcastStyle.NEWS:
            # News-Anchor Stimme
            news_voices = self.search(language=language, tags=["news"])
            if news_voices:
                suggestions = news_voices[:num_speakers]
            else:
                # Fallback: Professional
                prof_voices = self.search(language=language, style=VoiceStyle.PROFESSIONAL)
                suggestions = prof_voices[:num_speakers]

        elif style == PodcastStyle.EDUCATIONAL:
            # Klare, professionelle Stimmen
            edu_voices = self.search(language=language, tags=["educational"])
            if not edu_voices:
                edu_voices = self.search(language=language, style=VoiceStyle.PROFESSIONAL)
            suggestions = edu_voices[:num_speakers]

        elif style == PodcastStyle.NARRATIVE:
            # Storytelling-Stimmen
            story_voices = self.search(language=language, style=VoiceStyle.STORYTELLING)
            if story_voices:
                suggestions = story_voices[:num_speakers]

        # Fallback: Verfügbare Stimmen der Sprache
        if not suggestions:
            available = self.search(language=language)
            suggestions = available[:num_speakers]

        return suggestions

    def list_languages(self) -> List[str]:
        """Liste alle verfügbaren Sprachen"""
        return list(self.by_language.keys())

    def get_voice_count(self, language: Optional[str] = None) -> int:
        """Zähle verfügbare Stimmen"""
        if language:
            return len(self.by_language.get(language, []))
        return len(self.all_voices)

    def print_library(self, language: Optional[str] = None):
        """Gebe Bibliothek formatiert aus"""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Voice Library{f' ({language})' if language else ''}")

        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Gender", style="yellow")
        table.add_column("Style", style="magenta")
        table.add_column("Tags", style="blue")

        voices = self.search(language=language) if language else self.all_voices

        for voice in voices:
            table.add_row(
                voice.id,
                voice.display_name,
                voice.gender.value,
                voice.style.value,
                ", ".join(voice.tags[:3]),
            )

        console.print(table)
        console.print(f"\n[bold]Total: {len(voices)} voices[/bold]")


# Globale Instanz
_voice_library = None


def get_voice_library() -> VoiceLibrary:
    """Singleton für Voice Library"""
    global _voice_library
    if _voice_library is None:
        _voice_library = VoiceLibrary()
    return _voice_library
