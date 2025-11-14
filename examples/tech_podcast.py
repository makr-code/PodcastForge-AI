#!/usr/bin/env python3
"""
Beispiel: Tech-Podcast über aktuelle Trends
"""

from podcastforge import PodcastForge, Speaker, PodcastStyle

def main():
    forge = PodcastForge(language="de")
    
    # Definiere Custom-Sprecher
    speakers = [
        Speaker(
            id="host",
            name="Max Tech",
            role="Moderator und Tech-Enthusiast",
            personality="begeistert, technikaffin, erklärt komplexe Dinge einfach",
            voice_profile="de_male_1",
            gender="male"
        ),
        Speaker(
            id="expert",
            name="Dr. Lisa Müller",
            role="KI-Forscherin",
            personality="kompetent, visionär, wissenschaftlich fundiert",
            voice_profile="de_female_1",
            gender="female"
        ),
        Speaker(
            id="critic",
            name="Tom Schmidt",
            role="Tech-Kritiker",
            personality="skeptisch, hinterfragt, bodenständig",
            voice_profile="de_male_2",
            gender="male"
        )
    ]
    
    # Generiere Podcast
    podcast = forge.create_podcast(
        topic="ChatGPT, Gemini und die Zukunft der KI-Assistenten",
        style=PodcastStyle.DISCUSSION,
        speakers=speakers,
        duration=15,
        output="tech_podcast.mp3"
    )
    
    print(f"✅ Tech-Podcast erstellt: {podcast}")

if __name__ == "__main__":
    main()
