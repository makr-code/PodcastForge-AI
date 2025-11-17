# Audio Processing Guide

**Version:** 1.0  
**Stand:** 2025-11-17  
**Implementation:** 1,044 LOC (vollständig implementiert)

---

## 🎵 Übersicht

PodcastForge-AI bietet umfassende Audio-Processing-Funktionen für professionelle Podcast-Produktion. Dieser Guide dokumentiert alle verfügbaren Audio-Features.

**Implementierte Module:**
- **AudioPostProcessor** - Normalisierung, Kompression, Fade
- **Breath Synthesis** (117 LOC) - Realistische Atem-Simulation
- **FFmpeg Pipe** (152 LOC) - Streaming-Konvertierung
- **Waveform Generator** (163 LOC) - Visualisierung
- **Audio Player** (214 LOC) - Multi-Backend-Playback
- **TK Audio Player** (282 LOC) - GUI-Integration

---

## 📊 Audio Post-Processing

### AudioPostProcessor

Der AudioPostProcessor wendet automatische Verbesserungen auf generiertes Audio an.

**Features:**
- ✅ Lautstärke-Normalisierung
- ✅ Dynamik-Kompression
- ✅ Fade In/Out
- ✅ Stille-Entfernung
- ✅ Headroom-Verwaltung

### Verwendung

**Python API:**
```python
from podcastforge.audio import AudioPostProcessor
from pydub import AudioSegment

processor = AudioPostProcessor()

# Audio laden
audio = AudioSegment.from_wav("input.wav")

# Processing anwenden
processed = processor.process(audio, options={
    "normalize": True,
    "compress": True,
    "fade_in": 0.5,  # 500ms
    "fade_out": 1.0,  # 1 Sekunde
    "remove_silence": True,
    "headroom_db": -1.0
})

# Speichern
processed.export("output.wav", format="wav")
```

### Normalisierung

**Zweck:** Einheitliche Lautstärke über alle Audio-Segmente

**Parameter:**
```python
options = {
    "normalize": True,
    "target_dbfs": -20.0,  # Ziel-Lautstärke
    "headroom_db": -1.0    # Sicherheitsabstand
}
```

**Empfohlene Werte:**
- **Podcast:** -20 to -16 LUFS
- **Dialog:** -23 to -20 LUFS
- **Musik:** -14 to -10 LUFS

### Dynamik-Kompression

**Zweck:** Reduziert Lautstärke-Unterschiede, verbessert Verständlichkeit

**Parameter:**
```python
options = {
    "compress": True,
    "threshold_db": -20,  # Ab dieser Lautstärke komprimieren
    "ratio": 4.0,         # Kompressions-Verhältnis (4:1)
    "attack_ms": 5,       # Reaktionszeit
    "release_ms": 50      # Rückkehrzeit
}
```

**Ratio-Guide:**
- **2:1** - Leichte Kompression (natürlich)
- **4:1** - Standard für Podcasts
- **8:1** - Starke Kompression (Radio-Stil)
- **∞:1** - Limiter (verhindert Clipping)

### Fade In/Out

**Zweck:** Sanfte Übergänge am Anfang/Ende

**Parameter:**
```python
options = {
    "fade_in": 0.5,   # 500ms Fade In
    "fade_out": 1.0,  # 1s Fade Out
    "fade_type": "linear"  # oder "exponential"
}
```

**Fade-Typen:**
- **linear:** Gleichmäßiger Anstieg/Abfall
- **exponential:** Natürlicher klingend für Sprache

### Stille-Entfernung

**Zweck:** Entfernt übermäßige Pausen

**Parameter:**
```python
options = {
    "remove_silence": True,
    "silence_thresh": -40,     # dB (leiser = Stille)
    "min_silence_len": 1000,   # ms (mindest Länge)
    "keep_silence": 200        # ms (Pause beibehalten)
}
```

**Best Practices:**
- Nicht zu aggressiv (klingt unnatürlich)
- `keep_silence` >= 200ms für natürliche Pausen
- Threshold je nach Hintergrund-Rauschen anpassen

---

## 😮 Breath Synthesis

**NEU in v1.0** - 117 LOC vollständig implementiert

Fügt realistische Atem-Geräusche für natürlichere Sprache hinzu.

### Was ist Breath Synthesis?

Realistische Text-to-Speech klingt oft "zu perfekt". Menschen atmen zwischen Sätzen, besonders bei:
- Langen Sätzen
- Emotionalen Momenten
- Pausen zum Nachdenken

### Features

- ✅ Automatische Atem-Platzierung
- ✅ Verschiedene Atem-Typen (normal, tief, schnell)
- ✅ Intensitäts-Kontrolle
- ✅ Positions-Erkennung (nach Satzzeichen)

### Verwendung

**Automatisch:**
```python
from podcastforge.audio.postprocessors.breaths import add_breaths

audio = AudioSegment.from_wav("speech.wav")

# Automatische Atem-Einfügung
with_breaths = add_breaths(
    audio,
    intensity=0.3,      # 0.0-1.0 (Lautstärke)
    frequency="medium"  # "low", "medium", "high"
)
```

**Manuell:**
```python
from podcastforge.audio.postprocessors.breaths import insert_breath

# Atem an spezifischer Position (ms)
audio = insert_breath(
    audio,
    position_ms=5000,  # Nach 5 Sekunden
    breath_type="deep", # "normal", "deep", "quick"
    volume=-20         # dB (leiser = subtiler)
)
```

### Breath-Typen

| Typ | Dauer | Verwendung |
|-----|-------|------------|
| **normal** | 200-300ms | Standard-Pausen |
| **deep** | 400-600ms | Lange Sätze, Emotion |
| **quick** | 100-150ms | Schnelle Dialoge |

### Best Practices

```python
# Natürliches Atmen für Interview
options = {
    "intensity": 0.2,      # Subtil
    "frequency": "medium", # Nicht bei jedem Satz
    "breath_type": "normal"
}

# Emotionaler/dramatischer Moment
options = {
    "intensity": 0.5,
    "frequency": "high",
    "breath_type": "deep"
}
```

### Deaktivierung

Breath Synthesis ist standardmäßig aktiviert. Zum Deaktivieren:

```python
options = {
    "add_breaths": False
}
```

---

## 🎬 FFmpeg Pipe Integration

**152 LOC** - Streaming-Konvertierung

### Zweck

Konvertiert Audio on-the-fly ohne temporäre Dateien:
- WAV → MP3 (streaming)
- WAV → M4A/MP4 (fragmented)
- Reduziert Speicherbedarf
- Schnellere Zeit bis zur Abspielbarkeit

### Features

- ✅ Stdin Piping (kein Temp-File nötig)
- ✅ Fragmentiertes MP4 (progressives Abspielen)
- ✅ Bitrate-Kontrolle
- ✅ Metadata-Injection (ID3-Tags)
- ✅ Automatischer Fallback bei Fehlern

### Verwendung

**Streaming MP3:**
```python
from podcastforge.audio.ffmpeg_pipe import stream_to_mp3

audio_segments = [segment1, segment2, segment3]

# Streamt direkt zu MP3 (kein großes WAV-File)
stream_to_mp3(
    segments=audio_segments,
    output_path="podcast.mp3",
    bitrate="192k",
    sample_rate=44100
)
```

**Fragmentiertes MP4:**
```python
from podcastforge.audio.ffmpeg_pipe import stream_to_mp4

stream_to_mp4(
    segments=audio_segments,
    output_path="podcast.m4a",
    bitrate="128k",
    fragmented=True  # Wichtig für progressives Abspielen
)
```

### MP4 Fragmentation

**Flags für progressive Playback:**
```
-movflags +faststart+frag_keyframe+empty_moov
```

**Vorteile:**
- Player kann während des Schreibens abspielen
- Kein vollständiger Download nötig
- Ideal für Webplayer

### Metadata

```python
metadata = {
    "title": "Episode 1",
    "artist": "PodcastForge",
    "album": "Mein Podcast",
    "genre": "Podcast",
    "year": "2024"
}

stream_to_mp3(
    segments=audio_segments,
    output_path="podcast.mp3",
    metadata=metadata
)
```

### Fallback-Verhalten

Bei FFmpeg-Fehlern:
1. Versucht Streaming-Methode
2. Falls fehl schlägt → Concat-then-Convert
3. Falls auch das fehlschlägt → WAV-Output mit Warnung

### Troubleshooting

**Problem: "ffmpeg not found"**

```bash
# Installation
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Oder: Lokale Installation
python scripts/install_ffmpeg.py --dest ./third_party/ffmpeg/bin
```

**Problem: "Invalid codec"**

```python
# Explizite Codec-Angabe
options = {
    "audio_codec": "libmp3lame",  # MP3
    # oder "aac"  # M4A/MP4
}
```

---

## 📊 Waveform Visualisierung

**163 LOC** - Visual Audio-Darstellung

### WaveformGenerator

Erstellt Wellenform-Bilder für Audio-Dateien.

**Features:**
- ✅ PNG/JPEG-Export
- ✅ Anpassbare Größe und Farben
- ✅ Zoom-Levels
- ✅ Peak-Visualisierung

### Verwendung

**Einfache Wellenform:**
```python
from podcastforge.audio.waveform import WaveformGenerator

gen = WaveformGenerator()

# Erstelle Wellenform-Bild
gen.generate(
    audio_file="podcast.wav",
    output_image="waveform.png",
    width=1200,
    height=200,
    color="#569cd6"
)
```

**Erweiterte Optionen:**
```python
gen.generate(
    audio_file="podcast.wav",
    output_image="waveform.png",
    width=1200,
    height=200,
    
    # Farben
    foreground_color="#569cd6",  # Wellenform
    background_color="#1e1e1e",  # Hintergrund
    
    # Detail-Level
    samples_per_pixel=100,  # Höher = mehr Detail
    
    # Stil
    style="bars",  # oder "line", "filled"
    
    # Amplitude
    scale=1.0  # 0.5 = halbe Höhe, 2.0 = doppelte Höhe
)
```

### Stile

**Bars (Standard):**
```python
style="bars"  # Vertikale Balken (klassisch)
```

**Line:**
```python
style="line"  # Durchgehende Linie
```

**Filled:**
```python
style="filled"  # Gefüllte Fläche unter Linie
```

### Farbschemas

**Hell:**
```python
colors = {
    "foreground": "#0066cc",
    "background": "#ffffff"
}
```

**Dunkel:**
```python
colors = {
    "foreground": "#569cd6",
    "background": "#1e1e1e"
}
```

**Gradient (experimentell):**
```python
colors = {
    "gradient": ["#ff0000", "#00ff00", "#0000ff"]
}
```

### Integration in GUI

```python
# Für Timeline-Editor
waveform_image = gen.generate_for_timeline(
    audio_segment,
    width=canvas_width,
    zoom_level=1.0
)
```

---

## 🔊 Audio Player

**214 LOC** - Multi-Backend Playback

### Features

- ✅ Multi-Backend (pygame, simpleaudio, ffplay)
- ✅ Play/Pause/Stop
- ✅ Volume-Kontrolle
- ✅ Position-Seeking
- ✅ Loop-Modus

### Backends

**pygame (Standard):**
```python
from podcastforge.audio.player import AudioPlayer

player = AudioPlayer(backend="pygame")
```
- ✅ Cross-Platform
- ✅ Zuverlässig
- ✅ Volume-Kontrolle
- ⚠️ Benötigt pygame

**simpleaudio:**
```python
player = AudioPlayer(backend="simpleaudio")
```
- ✅ Leichtgewichtig
- ✅ Schneller Start
- ❌ Keine Volume-Kontrolle
- ⚠️ Platform-abhängig

**ffplay:**
```python
player = AudioPlayer(backend="ffplay")
```
- ✅ Viele Formate
- ✅ Streaming-Support
- ❌ Benötigt FFmpeg
- ⚠️ Externe Abhängigkeit

### Verwendung

**Basis-Playback:**
```python
player = AudioPlayer()

# Laden und abspielen
player.load("podcast.mp3")
player.play()

# Pause
player.pause()

# Fortsetzen
player.resume()

# Stoppen
player.stop()
```

**Mit Volume-Kontrolle:**
```python
# Volume setzen (0.0 - 1.0)
player.set_volume(0.7)  # 70%

# Mute/Unmute
player.mute()
player.unmute()
```

**Position-Seeking:**
```python
# Zu Position springen (Sekunden)
player.seek(30.0)  # Zu 30 Sekunden

# Aktuelle Position
pos = player.get_position()  # in Sekunden
```

**Loop-Modus:**
```python
player.set_loop(True)  # Endlos-Loop
player.play()
```

### TK Audio Player

**282 LOC** - GUI-Integration für tkinter

```python
from podcastforge.audio.tk_player import TkAudioPlayer
import tkinter as tk

root = tk.Tk()
player_frame = TkAudioPlayer(root)
player_frame.pack()

# Lädt automatisch UI:
# [▶] [⏸] [⏹] [Seek-Bar] [Volume]
player_frame.load_audio("podcast.mp3")
```

**Features:**
- ✅ Play/Pause/Stop Buttons
- ✅ Seek-Bar (Fortschrittsanzeige)
- ✅ Volume-Slider
- ✅ Zeit-Anzeige (00:00 / 10:30)
- ✅ Waveform-Integration (optional)

---

## 🎚️ Audio-Pipeline Beispiele

### Kompletter Podcast-Workflow

```python
from podcastforge.audio import AudioPostProcessor
from podcastforge.audio.postprocessors.breaths import add_breaths
from podcastforge.audio.ffmpeg_pipe import stream_to_mp3
from pydub import AudioSegment

# 1. TTS-generierte Segmente
segments = [
    AudioSegment.from_wav("line1.wav"),
    AudioSegment.from_wav("line2.wav"),
    AudioSegment.from_wav("line3.wav")
]

# 2. Post-Processing pro Segment
processor = AudioPostProcessor()
processed_segments = []

for seg in segments:
    # Normalisierung
    seg = processor.normalize(seg, target_dbfs=-20)
    
    # Atem hinzufügen
    seg = add_breaths(seg, intensity=0.3)
    
    # Fade In/Out
    seg = seg.fade_in(500).fade_out(1000)
    
    processed_segments.append(seg)

# 3. Kombinieren mit Pausen
final = AudioSegment.silent(duration=500)  # Intro-Stille
for seg in processed_segments:
    final += seg
    final += AudioSegment.silent(duration=800)  # Pause zwischen Segmenten

# 4. Master-Processing
final = processor.compress(final, threshold=-20, ratio=4.0)
final = processor.normalize(final, target_dbfs=-16)

# 5. Export als MP3
stream_to_mp3(
    segments=[final],
    output_path="podcast_final.mp3",
    bitrate="192k",
    metadata={
        "title": "Episode 1",
        "artist": "PodcastForge"
    }
)
```

### Mit Hintergrundmusik

```python
# Hintergrundmusik laden
music = AudioSegment.from_mp3("background.mp3")

# Leiser machen
music = music - 20  # -20 dB

# Loop auf Länge des Podcasts
while len(music) < len(final):
    music += music

music = music[:len(final)]  # Auf exakte Länge kürzen

# Mischen
mixed = final.overlay(music)

# Export
mixed.export("podcast_with_music.mp3", format="mp3")
```

---

## 🔧 Konfiguration

### Audio-Einstellungen

**Globale Config:**
```python
from podcastforge.core.settings import AudioSettings

settings = AudioSettings(
    sample_rate=44100,      # 44.1kHz (Standard)
    bit_depth=16,           # 16-bit
    channels=1,             # Mono (Podcasts)
    default_format="mp3",
    default_bitrate="192k"
)
```

### Sample-Rates

| Rate | Verwendung |
|------|------------|
| 22050 Hz | TTS-Output (niedrige Qualität) |
| 44100 Hz | CD-Qualität (empfohlen) |
| 48000 Hz | Professional Audio |

### Bitrates (MP3)

| Bitrate | Qualität | Dateigröße |
|---------|----------|------------|
| 96k | Niedrig | ~11 MB/h |
| 128k | Gut | ~15 MB/h |
| 192k | Sehr gut (empfohlen) | ~23 MB/h |
| 256k | Exzellent | ~30 MB/h |
| 320k | Maximum | ~38 MB/h |

---

## 🐛 Troubleshooting

### Problem: Audio ist zu leise/laut

**Lösung:**
```python
# Normalisierung mit Target
processor.normalize(audio, target_dbfs=-16)

# Oder manuell
audio = audio + 5  # +5 dB
audio = audio - 3  # -3 dB
```

### Problem: Clipping (Verzerrung)

**Lösung:**
```python
# Limiter anwenden
from pydub.effects import compress_dynamic_range

audio = compress_dynamic_range(
    audio,
    threshold=-3,  # Sehr hoch für Limiter
    ratio=100,     # Fast unendlich
    attack=1,
    release=10
)
```

### Problem: Hörbare Artefakte

**Lösungen:**
```python
# 1. Sanftere Fades
audio = audio.fade_in(1000).fade_out(1500)

# 2. Crossfade zwischen Segmenten
combined = segment1.append(segment2, crossfade=500)

# 3. Breath-Intensität reduzieren
add_breaths(audio, intensity=0.1)
```

### Problem: FFmpeg-Fehler

**Lösungen:**
```bash
# 1. FFmpeg prüfen
ffmpeg -version
which ffmpeg

# 2. Neu installieren
sudo apt-get install --reinstall ffmpeg

# 3. PATH prüfen
echo $PATH
export PATH=$PATH:/path/to/ffmpeg
```

### Problem: Hoher Speicherverbrauch

**Lösungen:**
```python
# 1. Streaming statt Concat
stream_to_mp3(segments, "out.mp3")  # Statt AudioSegment.append

# 2. Segmente einzeln verarbeiten
for seg in segments:
    process_and_save(seg)
    del seg  # Speicher freigeben

# 3. Generator verwenden
def process_segments():
    for file in audio_files:
        yield process(AudioSegment.from_file(file))
```

---

## 📚 Weiterführende Ressourcen

- **Editor Guide:** [EDITOR_GUIDE.md](../EDITOR_GUIDE.md)
- **TTS Engines:** [tts-engines.md](tts-engines.md)
- **Timeline Guide:** [timeline-guide.md](timeline-guide.md)
- **CLI Reference:** [cli-reference.md](cli-reference.md)

---

## 💡 Best Practices

### 1. Immer normalisieren
```python
# Am Ende jeder Pipeline
final = processor.normalize(final, target_dbfs=-16)
```

### 2. Sanfte Übergänge
```python
# Crossfades zwischen Segmenten
combined = seg1.append(seg2, crossfade=300)
```

### 3. Kompression für Konsistenz
```python
# Standard-Kompression für Podcasts
final = processor.compress(final, threshold=-20, ratio=4.0)
```

### 4. Metadata nicht vergessen
```python
metadata = {
    "title": "Episode Title",
    "artist": "Podcast Name",
    "genre": "Podcast",
    "date": "2024"
}
```

### 5. Qualität vor Dateigröße
```python
# 192k ist der Sweet-Spot
bitrate = "192k"  # Nicht darunter für Podcasts
```

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
