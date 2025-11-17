# Voice Cloning Guide

**Version:** 1.0  
**Stand:** 2025-11-17  
**Implementation:** 467 LOC (vollständig implementiert)

---

## 🎙️ Übersicht

Voice Cloning ermöglicht es, beliebige Stimmen mit nur 3-10 Sekunden Audio-Sample zu replizieren. PodcastForge-AI nutzt modernste TTS-Engines für qualitativ hochwertiges Voice Cloning.

**Status:** ✅ Vollständig implementiert (467 LOC)

---

## ✨ Features

### Kern-Funktionen
- ✅ **3-Sekunden Cloning** - Minimale Sample-Länge
- ✅ **Quality Assessment** - Automatische Sample-Bewertung
- ✅ **Voice Profile Management** - Speichern und Verwalten geclonter Stimmen
- ✅ **Embedding Cache** - Performance-Optimierung
- ✅ **Multi-Engine Support** - XTTS, StyleTTS2
- ✅ **Sample Preprocessing** - Automatische Audio-Optimierung

---

## 🚀 Schnellstart

### Minimales Beispiel

```python
from podcastforge.voices.cloner import VoiceCloner
from pathlib import Path

# Voice Cloner initialisieren
cloner = VoiceCloner()

# Stimme clonen (3-10 Sekunden Audio)
profile = cloner.clone_voice(
    sample_file=Path("my_voice.wav"),
    name="Meine Stimme"
)

# In TTS verwenden
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()
with mgr.use_engine(TTSEngine.XTTS) as engine:
    audio = engine.synthesize(
        text="Hallo, das ist meine geclonte Stimme!",
        speaker=profile.id
    )
```

---

## 📋 Voraussetzungen

### Hardware

**Minimum:**
- CPU: Quad-Core
- RAM: 8 GB
- GPU: Optional (empfohlen)

**Empfohlen:**
- CPU: 8-Core+
- RAM: 16 GB+
- GPU: NVIDIA mit 4-6 GB VRAM

### Software

```bash
# TTS Engine installieren
pip install TTS  # XTTS
# oder
pip install git+https://github.com/yl4579/StyleTTS2.git  # StyleTTS2

# Audio-Processing
pip install pydub librosa soundfile

# Optional: GPU-Support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 🎬 Audio-Sample vorbereiten

### Sample-Anforderungen

**Dauer:**
- ✅ Minimum: 3 Sekunden
- ✅ Empfohlen: 6-10 Sekunden
- ❌ Zu kurz: < 3 Sekunden
- ⚠️ Zu lang: > 30 Sekunden (nur erste 10s werden genutzt)

**Qualität:**
- ✅ Klar und deutlich
- ✅ Wenig Hintergrundgeräusche
- ✅ Konstante Lautstärke
- ✅ Keine Musik
- ❌ Verzerrung, Clipping
- ❌ Echo, Hall
- ❌ Starkes Hintergrundrauschen

**Format:**
- ✅ WAV (bevorzugt)
- ✅ MP3 (wird konvertiert)
- ✅ M4A, FLAC, OGG
- Sample-Rate: 16kHz+ (wird automatisch auf 24kHz resampled)

### Sample aufnehmen

**Mit Audacity:**
1. Aufnahme starten
2. Klar und deutlich sprechen
3. 6-10 Sekunden aufnehmen
4. Stille am Anfang/Ende entfernen
5. Normalisieren auf -3 dB
6. Als WAV exportieren (24kHz, Mono)

**Mit Python:**
```python
import sounddevice as sd
import soundfile as sf

# 10 Sekunden aufnehmen
duration = 10  # Sekunden
sample_rate = 24000

print("Aufnahme startet in 3 Sekunden...")
import time
time.sleep(3)

print("Sprechen Sie jetzt!")
recording = sd.rec(int(duration * sample_rate), 
                   samplerate=sample_rate, 
                   channels=1)
sd.wait()

print("Aufnahme beendet!")
sf.write("my_voice.wav", recording, sample_rate)
```

### Sample aus Video extrahieren

```python
from podcastforge.voices.extraction import extract_voice_from_video

# Stimme aus Video extrahieren
voice_sample = extract_voice_from_video(
    video_file="interview.mp4",
    start_time=120.0,  # Sekunde 2:00
    duration=10.0,     # 10 Sekunden
    output_file="extracted_voice.wav"
)
```

---

## 🔬 Voice Cloning

### Basis-Cloning

```python
from podcastforge.voices.cloner import VoiceCloner
from pathlib import Path

cloner = VoiceCloner()

# Einfaches Cloning
profile = cloner.clone_voice(
    sample_file=Path("voice_sample.wav"),
    name="Speaker Name"
)

print(f"Voice ID: {profile.id}")
print(f"Qualität: {profile.quality}")
```

### Mit Optionen

```python
profile = cloner.clone_voice(
    sample_file=Path("voice_sample.wav"),
    name="Professional Speaker",
    
    # Optionen
    language="de",              # Sprache
    engine="styletts2",         # "xtts" oder "styletts2"
    force_quality_check=True,   # Quality-Check erzwingen
    preprocess=True,            # Auto-Preprocessing
    
    # Metadata
    metadata={
        "gender": "male",
        "age": "adult",
        "description": "Professionelle Stimme für Podcasts"
    }
)
```

### Quality Assessment

```python
# Automatisches Quality-Check
from podcastforge.voices.cloner import VoiceQuality

if profile.quality == VoiceQuality.EXCELLENT:
    print("✅ Exzellentes Sample!")
elif profile.quality == VoiceQuality.GOOD:
    print("✅ Gutes Sample")
elif profile.quality == VoiceQuality.ACCEPTABLE:
    print("⚠️ Akzeptables Sample - Qualität könnte besser sein")
else:
    print("❌ Schlechtes Sample - Aufnahme wiederholen empfohlen")
```

### Preprocessing

```python
# Sample automatisch optimieren
from podcastforge.voices.preprocessing import preprocess_voice_sample

optimized = preprocess_voice_sample(
    input_file="raw_voice.wav",
    output_file="processed_voice.wav",
    
    # Optionen
    remove_silence=True,        # Stille entfernen
    normalize=True,             # Normalisieren
    reduce_noise=True,          # Noise Reduction
    resample_rate=24000         # Auf 24kHz resampling
)
```

---

## 💾 Voice Profile Management

### Profile speichern

```python
# Automatisch gespeichert in data/voice_clones/
profile = cloner.clone_voice(...)

# Profil-Datei: data/voice_clones/{profile.id}.json
# Audio-Sample: data/voice_clones/{profile.id}.wav
```

### Profile laden

```python
# Alle Profile auflisten
profiles = cloner.list_profiles()

for p in profiles:
    print(f"{p.name} ({p.id}) - {p.quality.value}")

# Spezifisches Profil laden
profile = cloner.load_profile("profile_id")
```

### Profile löschen

```python
# Profil löschen
cloner.delete_profile("profile_id")

# Oder über Objekt
cloner.delete_profile(profile.id)
```

### Profile exportieren

```python
# Profil exportieren (JSON + WAV)
cloner.export_profile(
    profile_id="profile_id",
    output_dir=Path("exports/")
)

# Importieren
imported = cloner.import_profile(
    import_dir=Path("exports/profile_id/")
)
```

---

## 🎙️ Verwendung in TTS

### Mit XTTS

```python
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()

with mgr.use_engine(TTSEngine.XTTS) as engine:
    audio = engine.synthesize(
        text="Text in meiner geclonten Stimme",
        speaker=profile.id  # Cloned Voice Profile
    )
```

### Mit StyleTTS2

```python
with mgr.use_engine(TTSEngine.STYLETTS2) as engine:
    audio = engine.synthesize(
        text="Höchste Qualität mit StyleTTS2",
        speaker=profile.id
    )
```

### Im Editor

**GUI-Editor:**
1. Editor öffnen: `podcastforge edit`
2. Sprecher hinzufügen
3. "Voice" → "Cloned Voice" auswählen
4. Profil aus Liste wählen

**Skript:**
```yaml
speakers:
  - name: Host
    voice_profile: "cloned_voice_id_123"
    description: "Meine geclonte Stimme"

script:
  - speaker: Host
    text: "Willkommen zu meinem Podcast!"
```

---

## 🔧 Erweiterte Features

### Multi-Sample Cloning

**Bessere Qualität mit mehreren Samples:**

```python
# Mehrere Samples kombinieren
samples = [
    Path("sample1.wav"),  # Neutrale Stimme
    Path("sample2.wav"),  # Begeistert
    Path("sample3.wav")   # Nachdenklich
]

profile = cloner.clone_voice_from_multiple(
    samples=samples,
    name="Multi-Sample Voice"
)
```

### Voice Mixing

**Zwei Stimmen mischen:**

```python
# 70% Voice A + 30% Voice B
mixed = cloner.mix_voices(
    voice_a_id="profile_1",
    voice_b_id="profile_2",
    ratio=0.7,  # 70% A, 30% B
    name="Mixed Voice"
)
```

### Voice Adaptation

**Stimme anpassen (Pitch, Speed):**

```python
adapted = cloner.adapt_voice(
    profile_id="original_voice",
    pitch_shift=2,      # +2 Halbtöne (höher)
    speed_factor=0.9,   # 10% langsamer
    name="Adapted Voice"
)
```

---

## 📊 Quality Metrics

### Sample-Qualität bewerten

```python
from podcastforge.voices.quality import assess_sample_quality

metrics = assess_sample_quality("voice_sample.wav")

print(f"Dauer: {metrics['duration']}s")
print(f"SNR: {metrics['snr_db']} dB")  # Signal-to-Noise Ratio
print(f"Clipping: {metrics['clipping_percent']}%")
print(f"Qualität: {metrics['overall_quality']}")

# Empfehlungen
if metrics['duration'] < 3.0:
    print("⚠️ Sample zu kurz - mindestens 3 Sekunden empfohlen")
if metrics['snr_db'] < 20:
    print("⚠️ Zu viel Hintergrundrauschen")
if metrics['clipping_percent'] > 1:
    print("⚠️ Audio-Clipping erkannt - Aufnahme leiser wiederholen")
```

### Qualitäts-Stufen

| Qualität | Dauer | SNR | Verwendung |
|----------|-------|-----|------------|
| **Excellent** | 10s+ | >30 dB | Professionelle Projekte |
| **Good** | 6-10s | 25-30 dB | Podcast-Produktion |
| **Acceptable** | 3-6s | 20-25 dB | Test/Prototypen |
| **Poor** | <3s | <20 dB | Nicht empfohlen |

---

## 🎯 Best Practices

### 1. Sample-Aufnahme

```
✅ DO:
- Ruhige Umgebung
- Professionelles Mikrofon (optional, aber besser)
- 30cm Abstand zum Mikrofon
- Klare Aussprache
- Neutrale Emotion (für vielseitige Verwendung)

❌ DON'T:
- Aufnahme mit Handy-Mikrofon in lauter Umgebung
- Zu nah am Mikrofon (Plosive: P, B, T)
- Flüstern oder Schreien
- Hintergrundmusik
```

### 2. Sample-Länge

```
Minimum:  3s  ✅
Optimal:  6-10s  ⭐
Maximum:  30s (mehr wird ignoriert)
```

### 3. Sample-Inhalt

```
✅ Gut:
"Hallo, mein Name ist Max Mustermann. Ich spreche klar und 
deutlich in normalem Tempo. Diese Aufnahme wird für Voice 
Cloning verwendet."

❌ Schlecht:
"Ähm... also... hey?"  (zu kurz, Füllwörter)
```

### 4. Mehrere Versionen

```python
# Best Practice: 3 Samples aufnehmen
samples = [
    "neutral_sample.wav",    # Neutrale Stimme
    "expressive_sample.wav", # Leicht expressiv
    "professional_sample.wav" # Professionell
]

# Bestes auswählen
for sample in samples:
    metrics = assess_sample_quality(sample)
    if metrics['overall_quality'] == 'excellent':
        use_this = sample
        break
```

### 5. Testen vor Produktion

```python
# Test-TTS vor finaler Verwendung
test_audio = engine.synthesize(
    "Dies ist ein Test meiner geclonten Stimme.",
    speaker=profile.id
)

# Anhören und Qualität prüfen
# Falls schlecht: Neues Sample aufnehmen
```

---

## 🐛 Troubleshooting

### Problem: "Sample zu kurz"

**Symptom:** Error bei Cloning

**Lösung:**
```python
# Sample-Dauer prüfen
from pydub import AudioSegment

audio = AudioSegment.from_file("sample.wav")
duration_seconds = len(audio) / 1000

if duration_seconds < 3.0:
    print(f"⚠️ Sample zu kurz: {duration_seconds}s")
    print("Mindestens 3 Sekunden erforderlich")
```

### Problem: Schlechte Clone-Qualität

**Mögliche Ursachen:**
1. Sample zu kurz (<3s)
2. Zu viel Hintergrundrauschen
3. Inkonsistente Lautstärke
4. Audio-Clipping

**Lösungen:**
```python
# 1. Preprocessing anwenden
from podcastforge.voices.preprocessing import preprocess_voice_sample

processed = preprocess_voice_sample(
    "raw_sample.wav",
    "clean_sample.wav",
    remove_silence=True,
    normalize=True,
    reduce_noise=True
)

# 2. Neues Sample mit besser Bedingungen aufnehmen
```

### Problem: Clone klingt robotisch

**Ursachen:**
- Sample-Qualität zu niedrig
- TTS-Engine nicht optimal für Voice Cloning

**Lösungen:**
```python
# 1. StyleTTS2 statt XTTS versuchen
with mgr.use_engine(TTSEngine.STYLETTS2) as engine:
    audio = engine.synthesize(text, speaker=profile.id)

# 2. Besseres Sample aufnehmen (10s, rauschfrei)

# 3. Multi-Sample Cloning
profile = cloner.clone_voice_from_multiple([
    "sample1.wav",
    "sample2.wav", 
    "sample3.wav"
])
```

### Problem: Hoher VRAM-Verbrauch

**Lösung:**
```python
# CPU-Modus verwenden
cloner = VoiceCloner(device="cpu")

# Oder kleinere Batch-Size
config = {
    "batch_size": 1,  # Statt 4
    "max_samples": 1  # Nur 1 Sample gleichzeitig
}
```

### Problem: Clone funktioniert nicht in Produktion

**Checklist:**
```python
# 1. Profil vorhanden?
profiles = cloner.list_profiles()
assert profile.id in [p.id for p in profiles]

# 2. Engine unterstützt Cloning?
# XTTS ✅, Bark ❌, Piper ❌, StyleTTS2 ✅

# 3. Embedding generiert?
assert profile.embedding is not None

# 4. Sample-Datei vorhanden?
assert profile.sample_file.exists()
```

---

## 💡 Anwendungsfälle

### 1. Persönlicher Podcast-Host

```python
# Eigene Stimme clonen
my_voice = cloner.clone_voice(
    sample_file="my_recording.wav",
    name="Meine Stimme",
    metadata={
        "use_case": "podcast_host"
    }
)

# Podcast generieren ohne jede Episode sprechen zu müssen
podcast_script = """
Host: Willkommen zur Episode 42!
Host: Heute sprechen wir über KI...
"""

generate_podcast(script=podcast_script, 
                 host_voice=my_voice.id)
```

### 2. Charakter-Stimmen für Fiction

```python
# Mehrere Charaktere clonen
narrator = cloner.clone_voice("narrator_sample.wav", "Erzähler")
hero = cloner.clone_voice("hero_sample.wav", "Held")
villain = cloner.clone_voice("villain_sample.wav", "Bösewicht")

# Hörbuch mit verschiedenen Stimmen
audiobook_script = """
Narrator: Es war einmal...
Hero: Ich muss die Welt retten!
Villain: Niemals!
"""
```

### 3. Mehrsprachige Inhalte

```python
# Gleiche Stimme, verschiedene Sprachen
de_profile = cloner.clone_voice(
    "german_sample.wav",
    "Deutsch",
    language="de"
)

en_profile = cloner.clone_voice(
    "english_sample.wav",  # Gleiche Person, Englisch
    "English",
    language="en"
)

# Podcast in beiden Sprachen
```

### 4. Historische Stimmen rekonstruieren

```python
# Aus alten Aufnahmen
historical_voice = cloner.clone_voice(
    sample_file="historical_recording_1950.wav",
    name="Historical Figure",
    preprocess=True  # Extra Preprocessing für alte Aufnahmen
)
```

---

## 📚 API-Referenz

### VoiceCloner

```python
class VoiceCloner:
    def __init__(self, cache_dir: Path = Path("data/voice_clones"), 
                 device: str = "auto"):
        """
        Args:
            cache_dir: Verzeichnis für Voice-Profile
            device: "auto", "cuda", "cpu", "mps"
        """
        
    def clone_voice(self, sample_file: Path, name: str, 
                    language: str = "de", engine: str = "xtts",
                    **kwargs) -> ClonedVoiceProfile:
        """Clone eine Stimme aus Audio-Sample"""
        
    def clone_voice_from_multiple(self, samples: List[Path], 
                                   name: str) -> ClonedVoiceProfile:
        """Clone mit mehreren Samples (höhere Qualität)"""
        
    def list_profiles(self) -> List[ClonedVoiceProfile]:
        """Alle gespeicherten Profile auflisten"""
        
    def load_profile(self, profile_id: str) -> ClonedVoiceProfile:
        """Lade spezifisches Profil"""
        
    def delete_profile(self, profile_id: str):
        """Lösche Profil"""
        
    def export_profile(self, profile_id: str, output_dir: Path):
        """Exportiere Profil"""
        
    def import_profile(self, import_dir: Path) -> ClonedVoiceProfile:
        """Importiere Profil"""
```

### ClonedVoiceProfile

```python
@dataclass
class ClonedVoiceProfile:
    id: str                          # Eindeutige ID
    name: str                        # Name
    sample_file: Path                # Audio-Sample
    embedding: Optional[np.ndarray]  # Voice-Embedding
    quality: VoiceQuality            # Qualität
    sample_duration: float           # Dauer in Sekunden
    sample_rate: int                 # Sample-Rate
    metadata: Dict                   # Zusätzliche Daten
```

---

## 🔗 Weiterführende Ressourcen

- **TTS Engines:** [tts-engines.md](tts-engines.md)
- **Voice Integration:** [../VOICE_INTEGRATION.md](../VOICE_INTEGRATION.md)
- **Editor Guide:** [../EDITOR_GUIDE.md](../EDITOR_GUIDE.md)
- **Audio Processing:** [audio-processing.md](audio-processing.md)

---

## 🔄 Version History

- **v1.0** (2025-11-17): Initiale Dokumentation, vollständige Feature-Coverage

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
