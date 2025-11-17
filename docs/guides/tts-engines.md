# TTS Engines Vergleich & Setup

**Version:** 1.0  
**Stand:** 2025-11-17

---

## 🎙️ Übersicht

PodcastForge-AI unterstützt 4 verschiedene Text-to-Speech (TTS) Engines, jede mit eigenen Stärken und Einsatzgebieten.

**Verfügbare Engines:**
- **XTTS** (Coqui XTTSv2) - Voice Cloning, höchste Qualität
- **Bark** (Suno BARK) - Natürliche Emotionen, expressiv
- **Piper** - Schnell, CPU-optimiert, gut für Batch-Processing
- **StyleTTS2** - State-of-the-Art, 3-Sekunden Voice Cloning

---

## 📊 Vergleichstabelle

| Feature | XTTS | Bark | Piper | StyleTTS2 |
|---------|------|------|-------|-----------|
| **Geschwindigkeit** | Mittel | Langsam | Sehr schnell | Mittel |
| **Qualität** | Sehr hoch | Hoch | Gut | Sehr hoch |
| **Voice Cloning** | ✅ Ja (3s+) | ❌ Nein | ❌ Nein | ✅ Ja (3s) |
| **Emotionen** | ⚠️ Begrenzt | ✅ Ja | ❌ Nein | ✅ Ja |
| **Sprachen** | 13+ | Englisch | 40+ | Englisch |
| **VRAM Bedarf** | ~4-6 GB | ~8-10 GB | ~100 MB | ~4-6 GB |
| **CPU-Modus** | ⚠️ Langsam | ⚠️ Sehr langsam | ✅ Optimal | ⚠️ Langsam |
| **Modellgröße** | ~2 GB | ~10 GB | ~10 MB | ~2 GB |
| **Realtime** | ❌ Nein | ❌ Nein | ✅ Ja | ❌ Nein |
| **Lizenz** | Apache 2.0 | MIT | MIT | MIT |

---

## 🚀 XTTS (Coqui XTTSv2)

### Überblick

**Bestes für:** Voice Cloning, mehrsprachige Projekte, professionelle Qualität

XTTS ist eine fortgeschrittene TTS-Engine mit Voice-Cloning-Fähigkeiten. Sie kann mit nur 3-6 Sekunden Audio-Sample eine Stimme nachahmen.

### Features

✅ **Voice Cloning** - 3-6 Sekunden Audio ausreichend  
✅ **Mehrsprachig** - Deutsch, Englisch, Spanisch, Französisch, etc.  
✅ **Hohe Qualität** - Natürliche Prosodie  
⚠️ **VRAM-hungrig** - 4-6 GB GPU-Speicher  
⚠️ **Langsamer** - ~5-10 Sekunden pro Satz (GPU)

### Installation

```bash
# Basis-Installation
pip install TTS

# Mit GPU-Support (empfohlen)
pip install TTS torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Modell herunterladen (automatisch beim ersten Start)
# Alternativ manuell:
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 --text "Test"
```

### Verwendung

**CLI:**
```bash
# Mit XTTS generieren
podcastforge generate \
    --topic "KI im Alltag" \
    --engine xtts \
    --duration 10
```

**Python:**
```python
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()
with mgr.use_engine(TTSEngine.XTTS, config={}) as engine:
    audio = engine.synthesize(
        text="Hallo Welt",
        speaker="de_female_1"
    )
```

### Voice Cloning

```python
from podcastforge.voices import VoiceCloner

cloner = VoiceCloner()
profile = cloner.clone_voice(
    audio_file="my_voice.wav",
    name="Meine Stimme",
    language="de"
)

# Verwenden
with mgr.use_engine(TTSEngine.XTTS) as engine:
    audio = engine.synthesize(
        text="Text in meiner Stimme",
        speaker=profile.id
    )
```

### Performance-Optimierung

**GPU verwenden:**
```python
config = {
    "device": "cuda",  # oder "cpu"
    "use_deepspeed": True  # Schneller
}
```

**Batch-Processing:**
```python
# Mehrere Texte auf einmal
texts = ["Satz 1", "Satz 2", "Satz 3"]
for text in texts:
    audio = engine.synthesize(text, speaker="...")
```

### Systemanforderungen

- **GPU:** NVIDIA mit 4-6 GB VRAM (empfohlen)
- **CPU:** Multicore (falls GPU nicht verfügbar)
- **RAM:** 8 GB+
- **Speicher:** 2 GB für Model

---

## 🎭 Bark (Suno BARK)

### Überblick

**Bestes für:** Emotionale Ausdrucksstärke, natürliche Variationen, kreative Projekte

Bark ist spezialisiert auf ausdrucksstarke, natürliche Sprache mit Emotionen, Lachen, Seufzen, etc.

### Features

✅ **Natürliche Emotionen** - Lachen, Seufzen, Betonung  
✅ **Expressiv** - Sehr menschlich klingende Sprache  
✅ **Non-verbal Sounds** - [lacht], [seufzt], etc.  
❌ **Nur Englisch** - Keine anderen Sprachen  
⚠️ **Sehr langsam** - ~15-30 Sekunden pro Satz  
⚠️ **VRAM-hungrig** - 8-10 GB GPU-Speicher

### Installation

```bash
# Bark installieren
pip install git+https://github.com/suno-ai/bark.git

# CUDA-Support (empfohlen)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Modelle werden automatisch heruntergeladen (~10 GB)
```

### Verwendung

**CLI:**
```bash
podcastforge generate \
    --topic "Comedy Podcast" \
    --engine bark \
    --style comedy \
    --duration 5
```

**Python:**
```python
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()
with mgr.use_engine(TTSEngine.BARK) as engine:
    # Mit Emotionen
    audio = engine.synthesize(
        text="That's hilarious! [laughs]",
        speaker="v2/en_speaker_6"
    )
```

### Emotionen und Non-Verbal Sounds

**Unterstützte Markierungen:**
```
[lacht] / [laughs]
[seufzt] / [sighs]
[räuspert sich] / [clears throat]
[Pause] / ...
♪ Musik ♪ (experimentell)
```

**Beispiel:**
```python
text = """
Well, that's interesting! [laughs] 
I mean, seriously? [sighs] 
Let me think about this...
"""
audio = engine.synthesize(text, speaker="...")
```

### Sprecher-Varianten

Bark hat verschiedene Sprecher-Presets:
- `v2/en_speaker_0` - Männlich, tief
- `v2/en_speaker_1` - Männlich, mittel
- `v2/en_speaker_6` - Weiblich, freundlich
- `v2/en_speaker_9` - Weiblich, professionell

### Performance-Tipps

⚠️ **Sehr rechenintensiv!**

```python
# GPU verwenden (zwingend empfohlen)
config = {
    "device": "cuda",
    "use_small_models": False  # Höhere Qualität
}

# Für schnellere Generierung (niedrigere Qualität)
config = {
    "use_small_models": True,
    "text_use_gpu": True,
    "coarse_use_gpu": True,
    "fine_use_gpu": True
}
```

### Systemanforderungen

- **GPU:** NVIDIA mit 8-10 GB VRAM (erforderlich)
- **RAM:** 16 GB+
- **Speicher:** 10 GB für Modelle
- **Zeit:** 15-30s pro Satz

---

## ⚡ Piper

### Überblick

**Bestes für:** Batch-Processing, schnelle Generierung, CPU-Systeme, Echtzeitanwendungen

Piper ist optimiert für Geschwindigkeit und läuft sehr gut auf CPUs.

### Features

✅ **Sehr schnell** - 0.5-2 Sekunden pro Satz (CPU)  
✅ **CPU-optimiert** - Kein GPU erforderlich  
✅ **Viele Sprachen** - 40+ Sprachen  
✅ **Kleine Models** - ~10 MB pro Stimme  
✅ **Realtime** - Streaming möglich  
⚠️ **Mittlere Qualität** - Gut, aber nicht exzellent  
❌ **Kein Voice Cloning** - Nur vortrainierte Stimmen

### Installation

```bash
# Piper installieren
pip install piper-tts

# Oder von Source
git clone https://github.com/rhasspy/piper.git
cd piper/src/python
pip install -e .

# Modelle herunterladen (separat)
# Siehe: https://github.com/rhasspy/piper/releases
```

### Verwendung

**CLI:**
```bash
podcastforge generate \
    --topic "Nachrichten" \
    --engine piper \
    --duration 10
```

**Python:**
```python
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()
with mgr.use_engine(TTSEngine.PIPER) as engine:
    audio = engine.synthesize(
        text="Schnelle Generierung",
        speaker="de_DE-thorsten-high"
    )
```

### Verfügbare Stimmen

**Deutsch:**
- `de_DE-thorsten-high` - Männlich, hohe Qualität
- `de_DE-thorsten-medium` - Männlich, mittlere Qualität
- `de_DE-eva_k-x_low` - Weiblich

**Englisch:**
- `en_US-lessac-medium` - Männlich
- `en_GB-alan-medium` - Männlich, britisch

**Weitere:** Spanisch, Französisch, Italienisch, etc.

### Batch-Processing

**Ideal für große Mengen:**
```python
texts = ["Satz 1", "Satz 2", ..., "Satz 100"]

with mgr.use_engine(TTSEngine.PIPER) as engine:
    for i, text in enumerate(texts):
        audio = engine.synthesize(text, speaker="...")
        # Speichern
        save_audio(f"output_{i}.wav", audio)
```

**Geschwindigkeit:** ~100 Sätze in 2-3 Minuten (CPU)

### Systemanforderungen

- **GPU:** Nicht erforderlich
- **CPU:** Beliebige moderne CPU
- **RAM:** 1-2 GB
- **Speicher:** 10-50 MB pro Stimme

---

## 🎨 StyleTTS2

### Überblick

**Bestes für:** State-of-the-Art Qualität, Ultra-schnelles Voice Cloning (3s)

StyleTTS2 ist eine moderne Engine mit hervorragender Qualität und sehr schnellem Voice Cloning.

### Features

✅ **SOTA Qualität** - State-of-the-Art Sprach-Synthese  
✅ **3s Voice Cloning** - Nur 3 Sekunden Audio benötigt  
✅ **Hohe Natürlichkeit** - Sehr menschlich  
⚠️ **Hauptsächlich Englisch** - Beste Ergebnisse  
⚠️ **VRAM-Bedarf** - 4-6 GB GPU  
⚠️ **Experimentell** - Noch in Entwicklung

### Installation

```bash
# StyleTTS2 installieren
pip install git+https://github.com/yl4579/StyleTTS2.git

# Dependencies
pip install phonemizer espeak-ng

# CUDA Support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Verwendung

**Python:**
```python
from podcastforge.tts import get_engine_manager, TTSEngine

mgr = get_engine_manager()
with mgr.use_engine(TTSEngine.STYLETTS2) as engine:
    audio = engine.synthesize(
        text="High quality synthesis",
        speaker="default"
    )
```

### Ultra-schnelles Voice Cloning

```python
from podcastforge.voices import VoiceCloner

cloner = VoiceCloner()

# Nur 3 Sekunden Audio!
profile = cloner.clone_voice(
    audio_file="3_seconds.wav",
    name="Quick Clone",
    engine="styletts2"
)

# Verwenden
with mgr.use_engine(TTSEngine.STYLETTS2) as engine:
    audio = engine.synthesize(
        text="In my cloned voice",
        speaker=profile.id
    )
```

### Systemanforderungen

- **GPU:** NVIDIA mit 4-6 GB VRAM
- **RAM:** 8 GB+
- **Speicher:** 2 GB für Modelle

---

## 🎯 Auswahl-Guide

### Welche Engine wann?

**Für Voice Cloning:**
```
1. StyleTTS2 (3s Sample, beste Qualität)
2. XTTS (3-6s Sample, mehrsprachig)
```

**Für mehrsprachige Projekte:**
```
1. XTTS (13+ Sprachen)
2. Piper (40+ Sprachen)
```

**Für schnelle Generierung:**
```
1. Piper (CPU, sehr schnell)
2. XTTS (GPU)
```

**Für emotionale Ausdrucksstärke:**
```
1. Bark (Lachen, Seufzen, etc.)
2. StyleTTS2 (natürliche Prosodie)
```

**Für Batch-Processing:**
```
1. Piper (CPU-effizient)
2. XTTS (wenn GPU verfügbar)
```

**Für beste Qualität:**
```
1. StyleTTS2 (SOTA)
2. XTTS (sehr gut)
```

---

## ⚙️ Konfiguration

### Engine Manager

**Maximale gleichzeitige Engines:**
```python
from podcastforge.tts import get_engine_manager

# Max 2 Engines gleichzeitig im RAM
mgr = get_engine_manager(max_engines=2)
```

**Engine-Wechsel:**
```python
# Automatisches Load/Unload
with mgr.use_engine(TTSEngine.XTTS) as xtts:
    audio1 = xtts.synthesize("Text 1", "speaker1")

with mgr.use_engine(TTSEngine.PIPER) as piper:
    audio2 = piper.synthesize("Text 2", "speaker2")
```

### GPU/CPU Auswahl

**Automatische Erkennung:**
```python
# Wählt automatisch beste verfügbare Device
engine = TTSEngineFactory.create_engine(TTSEngine.XTTS)
```

**Manuell festlegen:**
```python
config = {"device": "cuda"}  # oder "cpu", "mps" (Mac)
engine = TTSEngineFactory.create_engine(TTSEngine.XTTS, config)
```

---

## 🔧 Troubleshooting

### Problem: "CUDA out of memory"

**Lösung:**
```python
# 1. Kleineres max_engines
mgr = get_engine_manager(max_engines=1)

# 2. CPU verwenden
config = {"device": "cpu"}

# 3. Piper verwenden (CPU-optimiert)
with mgr.use_engine(TTSEngine.PIPER) as engine:
    ...
```

### Problem: "Model not found"

**Lösung:**
```bash
# Modelle manuell herunterladen
# XTTS
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 --text "test"

# Bark (automatisch beim ersten Mal)
python -c "from bark import SAMPLE_RATE, generate_audio; generate_audio('test')"

# Piper (siehe Releases)
wget https://github.com/rhasspy/piper/releases/download/v1.0.0/de_DE-thorsten-high.tar.gz
```

### Problem: Sehr langsam

**Lösung:**
```python
# 1. GPU verwenden statt CPU
config = {"device": "cuda"}

# 2. Schnellere Engine wählen
# Piper für CPU
# XTTS für GPU

# 3. Batch-Größe reduzieren
# Einzelne Sätze statt lange Absätze
```

### Problem: Schlechte Qualität

**Lösung:**
```python
# 1. Hochwertigere Engine
# StyleTTS2 oder XTTS

# 2. Bessere Sprecher-Samples
# Für Voice Cloning: 6+ Sekunden, klar, rauschfrei

# 3. Text-Preprocessing
# Satzzeichen, klare Struktur
```

---

## 📚 Weiterführende Ressourcen

- **Voice Integration:** [VOICE_INTEGRATION.md](../VOICE_INTEGRATION.md)
- **Voice Cloning:** [voice-cloning.md](voice-cloning.md) (in Planung)
- **Script Orchestrator:** [integrations/script_orchestrator.md](integrations/script_orchestrator.md)
- **CLI Reference:** [cli-reference.md](cli-reference.md)

---

## 📊 Performance-Benchmarks

**Test-Setup:** RTX 3080 (10GB), Intel i7, 32GB RAM

| Engine | Zeit/Satz | GPU VRAM | CPU% | Qualität (1-10) |
|--------|-----------|----------|------|-----------------|
| **XTTS** | 5-8s | 4-6 GB | 20% | 9/10 |
| **Bark** | 15-25s | 8-10 GB | 15% | 8/10 |
| **Piper** | 0.5-2s | - | 50% | 7/10 |
| **StyleTTS2** | 6-10s | 4-6 GB | 20% | 10/10 |

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
