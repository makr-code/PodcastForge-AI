# PodcastForge v1.1 & v1.2 - Neue Features

## 📋 Übersicht

Diese Dokumentation beschreibt die neu implementierten Features in Version 1.1 und 1.2 von PodcastForge-AI.

**Alle Features folgen OOP Best Practices:**
- Type Hints für alle Methoden
- Docstrings (Google Style)
- Design Patterns (Factory, Singleton, Observer, MVC)
- Thread-safe Implementierung
- Proper Error-Handling
- Logging

---

## 🧵 Threading & Queue System (v1.1)

### ThreadManager

**Datei:** `src/podcastforge/gui/threading_base.py`

Professionelles Thread-Management mit Queue-basiertem Event-System.

#### Features
- `ThreadPoolExecutor` für Worker-Threads (max 4)
- Priority Queue für Tasks
- Observer Pattern für Events
- Thread-safe Operations
- Graceful Shutdown

#### Verwendung

```python
from podcastforge.gui.threading_base import get_thread_manager, UITaskObserver

# Hole ThreadManager (Singleton)
manager = get_thread_manager(max_workers=4)

# Erstelle Observer für UI-Updates
observer = UITaskObserver(root_widget)

# Registriere Callbacks
observer.on_started(lambda task_id, metadata: print(f"Started: {task_id}"))
observer.on_completed(lambda task_id, result: print(f"Done: {result}"))

# Register Observer
manager.add_observer(observer)

# Submit Task
def my_task(task_id, progress_callback):
    for i in range(10):
        progress_callback(i / 10.0, f"Step {i+1}")
        time.sleep(0.1)
    return "Success!"

manager.submit_task(
    task_fn=my_task,
    task_id="my_task_1",
    priority=TaskPriority.NORMAL
)

# Get Result (non-blocking)
result = manager.get_result(timeout=None)
if result:
    print(f"Status: {result.status}, Result: {result.result}")

# Cleanup
manager.shutdown()
```

#### Design Patterns
- **Singleton:** `get_thread_manager()` gibt immer dieselbe Instanz zurück
- **Observer:** Tasks benachrichtigen Observer über Events
- **Strategy:** Verschiedene Task-Typen mit einheitlichem Interface

---

## 🎙️ TTS Engine Manager (v1.1)

**Datei:** `src/podcastforge/tts/engine_manager.py`

Modulares Multi-Engine TTS-System mit Factory Pattern und LRU-Caching.

### Unterstützte Engines

| Engine | Qualität | Geschwindigkeit | GPU | Voice Cloning | Emotionen |
|--------|----------|----------------|-----|---------------|-----------|
| XTTS | ⭐⭐⭐⭐ | Mittel | Ja | ✅ 10s+ | ❌ |
| BARK | ⭐⭐⭐⭐⭐ | Langsam | Ja | ❌ | ✅ |
| Piper | ⭐⭐⭐ | Sehr schnell | Nein | ❌ | ❌ |
| StyleTTS2 | ⭐⭐⭐⭐⭐ | Mittel | Ja | ✅ 3s! | ✅ |

### Verwendung

```python
from podcastforge.tts.engine_manager import get_engine_manager, TTSEngine

# Hole Manager (Singleton)
manager = get_engine_manager(max_engines=2)

# Lade Engine (automatisch)
# Empfohlene, thread-safe Nutzung mit Context-Manager:
with manager.use_engine(TTSEngine.BARK, config={"model": "default"}) as engine:
    # engine ist geladen und kann direkt verwendet werden
    audio = engine.synthesize("Hello [laughter] world!", speaker="v2/en_speaker_6")

# Synthese
audio, sample_rate = manager.synthesize(
    text="Hello [laughter] world!",
    speaker="v2/en_speaker_6",
    engine_type=TTSEngine.BARK,
    temperature=0.7
)

# Stats
stats = manager.get_stats()
print(f"Loaded engines: {stats['loaded_engines']}")
print(f"Total memory: {stats['total_memory']:.2f} GB")
```

Hinweis: Für deterministisches Ressourcen-Management und sichere Parallelnutzung bevorzugen wir jetzt
den Context-Manager `use_engine()`, der die Engine referenzzählt und nach dem Verlassen des Kontexts
automatisch freigibt. Beispiel:

```python
from podcastforge.tts.engine_manager import get_engine_manager, TTSEngine

manager = get_engine_manager(max_engines=2)
with manager.use_engine(TTSEngine.PIPER, config={"model": "default"}) as engine:
    audio = engine.synthesize("Quick preview", speaker="0")
# nach dem with-Block wird die Engine freigegeben (Release/Unload falls Refcount 0)
```

Die klassische `get_engine()`-API bleibt erhalten (Cache-Hit, manuelles Unload), aber `use_engine`
ist die empfohlene Variante für kurzlebige, deterministische Nutzung.

### BARK Engine - Emotionen

BARK unterstützt spezielle Tags für natürliche Sprache:

```python
text = """
Hello! [laughter] 
I'm so excited about this! [gasps]
... let me think about that. [sighs]
♪ La la la ♪ [music]
"""

audio = engine.synthesize(text, speaker="v2/en_speaker_6")
```

### Piper Engine - Schnelle Previews

```python
# Piper ist perfekt für schnelle TTS-Previews (CPU, Real-time)
with manager.use_engine(TTSEngine.PIPER, config={"model": "default"}) as engine:
    audio = engine.synthesize("Quick preview", speaker="0")
```

### Design Patterns
- **Factory:** `TTSEngineFactory.create()` erzeugt Engine-Instanzen
- **Singleton:** `get_engine_manager()` für globale Verwaltung
- **Strategy:** Einheitliches Interface für alle Engines
- **LRU Cache:** Automatisches Eviction bei Memory-Limit

---

## 📽️ Timeline-Editor (v1.1)

**Datei:** `src/podcastforge/gui/timeline.py`

Canvas-basierter visueller Timeline-Editor mit Drag & Drop.

### Features
- ✅ Canvas-basierter Timeline-View
- ✅ Drag & Drop für Szenen
- ✅ Visual Waveform-Anzeige
- ✅ Szenen-Marker
- ✅ Snap-to-Grid (0.1s, 0.5s, 1.0s)
- ✅ Zoom In/Out (10s - 10min Ansicht)
- ✅ Scrubbing (Audio-Position per Click)
- ✅ Keyboard-Navigation

### Verwendung

```python
import tkinter as tk
from podcastforge.gui.timeline import TimelineEditor, Scene

root = tk.Tk()

# Erstelle Timeline
timeline = TimelineEditor(
    root,
    width=1200,
    height=300,
    on_scene_selected=lambda scene: print(f"Selected: {scene.speaker}"),
    on_time_changed=lambda time: print(f"Time: {time:.2f}s")
)

# Füge Szene hinzu
scene = Scene(
    id="s1",
    speaker="Host",
    text="Welcome to the podcast!",
    start_time=0.0,
    duration=3.0,
    waveform_data=np.random.randn(1000)  # Optional
)
timeline.add_scene(scene)

# Füge Marker hinzu
timeline.add_marker(5.0, "Chapter 1")

# Setze Zeit
timeline.set_current_time(2.5)

timeline.pack(fill=tk.BOTH, expand=True)
root.mainloop()
```

### Keyboard-Shortcuts
- **Space:** Play/Pause
- **Left/Right:** Skip 5s backward/forward
- **Home/End:** Goto Start/End
- **Delete:** Delete selected scene
- **Mouse Wheel:** Zoom

### UI-Layout

```
┌─────────────────────────────────────────────────────┐
│ ⏮️  ⏪  ▶️  ⏸️  ⏩  ⏭️   │ 00:00.0 / 05:32.4 │ Zoom: [±]│
├─────────────────────────────────────────────────────┤
│ Timeline:                                           │
│ ├─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┤ │
│ 0s    10s   20s   30s   40s   50s  1:00  1:10  1:20│
│                                                     │
│ ┌──────────┐  ┌────────┐      ┌──────────────┐    │
│ │ Host     │  │ Gast   │      │ Host         │    │
│ │~~wave~~  │  │~~wave~ │      │~~~~waveform~~│    │
│ └──────────┘  └────────┘      └──────────────┘    │
│     ▲                              ▲               │
│   Marker 1                      Marker 2           │
└─────────────────────────────────────────────────────┘
```

---

## 🎤 Voice Cloning (v1.2)

**Datei:** `src/podcastforge/voices/cloner.py`

Voice Cloning System mit StyleTTS2 (3-Sekunden Samples).

### Features
- ✅ 3-Sekunden Voice Cloning
- ✅ Quality-Check für Samples
- ✅ Voice-Profil-Management
- ✅ Voice-Embedding-Cache
- 🔄 Vocal-Separation mit Demucs (geplant)

### Verwendung

```python
from podcastforge.voices.cloner import get_voice_cloner
from pathlib import Path

# Hole Cloner (Singleton)
cloner = get_voice_cloner(cache_dir=Path("data/voice_clones"))

# Clone Voice
profile = cloner.clone_voice(
    audio_file=Path("samples/my_voice.wav"),
    voice_name="My Voice",
    min_duration=3.0
)

print(f"Cloned: {profile.name} (quality={profile.quality.value})")

# Synthesize mit geclonter Voice
audio = cloner.synthesize_with_cloned_voice(
    text="Hello from my cloned voice!",
    voice_id=profile.id,
    style="neutral"
)

# Liste alle Profile
profiles = cloner.get_all_profiles()
for p in profiles:
    print(f"- {p.name}: {p.sample_duration:.1f}s ({p.quality.value})")
```

### Quality-Levels

| Quality | Dauer | Beschreibung |
|---------|-------|--------------|
| EXCELLENT | > 10s | Sehr klar, kein Hintergrund |
| GOOD | 5-10s | Klar |
| ACCEPTABLE | 3-5s | Leichtes Hintergrund |
| POOR | < 3s | Zu kurz oder starkes Hintergrund |

### Voice-Sample-Extraktion

```python
# Extrahiere 10s-Sample aus längerer Datei
sample = cloner.extract_voice_sample(
    audio_file=Path("long_audio.wav"),
    start_time=5.0,
    duration=10.0
)

# Clone from extracted sample
profile = cloner.clone_voice(sample, "Extracted Voice")
```

---

## 🎚️ Multi-Track Audio-Editor (v1.2)

**Datei:** `src/podcastforge/gui/multitrack.py`

Professioneller Audio-Mixer mit mehreren Tracks.

### Features
- ✅ Mehrere Tracks (Voice, Music, SFX)
- ✅ Volume-Mixer für jeden Track
- ✅ Pan-Control (Stereo)
- ✅ Solo/Mute Buttons
- ✅ Drag & Drop Clips
- ✅ Fade In/Out
- 🔄 Audio-Export (geplant)

### Verwendung

```python
import tkinter as tk
from podcastforge.gui.multitrack import MultiTrackEditor, TrackType

root = tk.Tk()
root.geometry("1200x600")

# Erstelle Editor
editor = MultiTrackEditor(root)

# Füge Track hinzu
voice_track = editor.add_track("Voice 1", TrackType.VOICE)
music_track = editor.add_track("Background Music", TrackType.MUSIC)
sfx_track = editor.add_track("Sound Effects", TrackType.SFX)

editor.pack(fill=tk.BOTH, expand=True)
root.mainloop()
```

### UI-Layout

```
┌───────────────────────────────────────────────┐
│ Mixer  │ Timeline                             │
├────────┼──────────────────────────────────────┤
│ Voice  │ ┌──────────┐  ┌────────┐            │
│ 🔊▓▓▓▓ │ │ Clip 1   │  │ Clip 2 │            │
│ 80%    │ └──────────┘  └────────┘            │
│ [M][S] │                                      │
├────────┼──────────────────────────────────────┤
│ Music  │ ┌────────────────────────────┐      │
│ 🔊▓▓▓░ │ │ Background Track           │      │
│ 60%    │ └────────────────────────────┘      │
│ [M][S] │                                      │
├────────┼──────────────────────────────────────┤
│ SFX    │   ┌───┐      ┌───┐                  │
│ 🔊▓▓░░ │   │SFX│      │SFX│                  │
│ 40%    │   └───┘      └───┘                  │
│ [M][S] │                                      │
└────────┴──────────────────────────────────────┘
```

### Track-Typen

```python
from podcastforge.gui.multitrack import TrackType

TrackType.VOICE   # Podcast-Stimmen
TrackType.MUSIC   # Hintergrund-Musik
TrackType.SFX     # Sound-Effekte
TrackType.MASTER  # Master-Track (geplant)
```

### Clip-Management

```python
from podcastforge.gui.multitrack import AudioClip
from pathlib import Path

# Erstelle Clip
clip = AudioClip(
    id="clip1",
    file=Path("audio/intro.wav"),
    start_time=0.0,
    duration=5.0,
    volume=0.8,
    fade_in=0.5,
    fade_out=1.0
)

# Füge zu Track hinzu
track.add_clip(clip)
```

---

## 🎯 Best Practices

### Threading

```python
# ✅ RICHTIG: Thread-safe UI-Update
def on_completed(task_id, result):
    root.after(0, lambda: update_ui(result))

# ❌ FALSCH: Direkter UI-Update aus Thread
def on_completed(task_id, result):
    label.config(text=result)  # Nicht thread-safe!
```

### Engine-Management

```python
# ✅ RICHTIG: Engine-Caching nutzen (empfohlen via Context-Manager)
manager = get_engine_manager(max_engines=2)
with manager.use_engine(TTSEngine.BARK, config={"model": "default"}) as engine:
    # innerer Block: Engine ist geladen und referenziert (Cache-Hit beim 2. Zugriff)
    pass

# ❌ FALSCH: Jedes Mal neue Engine erstellen
engine = BarkEngine()
engine.load_model()  # Langsam!
```

### Memory-Management

```python
# ✅ RICHTIG: Automatisches Cleanup
with ThreadManager(max_workers=4) as manager:
    manager.submit_task(task_fn, "task1")
    # ... work ...
# Manager wird automatisch heruntergefahren

# ✅ RICHTIG: Manuelles Cleanup
manager = get_thread_manager()
try:
    # ... work ...
finally:
    shutdown_thread_manager()
```

---

## 📊 Performance-Tipps

### TTS-Engines

1. **Piper für Previews:** Schnell, CPU-basiert
2. **BARK für Produktion:** Beste Qualität mit Emotionen
3. **XTTS für Voice Cloning:** Gute Balance

### Threading

- Max 4 Worker-Threads (CPU-bound Tasks)
- Batch-Processing für viele kleine Tasks
- LRU-Cache nutzen

### Memory

- Max 2 TTS-Engines gleichzeitig geladen
- Waveform-Daten lazy-loaden
- Audio-Clips nach Verwendung entladen

---

## 🐛 Troubleshooting

### BARK Installation

```bash
# Git-basierte Installation
pip install git+https://github.com/suno-ai/bark.git

# GPU-Unterstützung
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Piper Installation

```bash
pip install piper-tts

# Model downloaden
wget https://github.com/rhasspy/piper/releases/download/v1.0.0/de_DE-thorsten-high.tar.gz
tar -xzf de_DE-thorsten-high.tar.gz
```

### Threading-Probleme

```python
# Logging aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug-Modus
manager = get_thread_manager(max_workers=1)  # Single-threaded
```

---

## 📚 Weitere Ressourcen

- [ARCHITECTURE.md](ARCHITECTURE.md) - Design Patterns und Best Practices
- [ROADMAP.md](ROADMAP.md) - Geplante Features v2.0 und v3.0
- [EDITOR_GUIDE.md](EDITOR_GUIDE.md) - GUI-Editor Dokumentation

---

**Version:** 1.2.0  
**Letzte Aktualisierung:** November 14, 2024  
**Autor:** PodcastForge-AI Team
