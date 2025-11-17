# Multitrack Editor Guide

**Version:** 1.0  
**Stand:** 2025-11-17  
**Implementation:** 560 LOC (vollständig implementiert)

---

## 🎛️ Übersicht

Der Multitrack-Editor ist ein professioneller Audio-Mixer für komplexe Podcast-Produktionen mit mehreren Spuren (Voice, Musik, Sound Effects).

**Status:** ✅ Vollständig implementiert (560 LOC)

---

## ✨ Features

### Kern-Funktionen
- ✅ **Multi-Track-System** - Unbegrenzte Anzahl an Tracks
- ✅ **Track-Typen** - Voice, Music, SFX, Master
- ✅ **Audio-Clip-Verwaltung** - Drag & Drop, Trim, Split
- ✅ **Volume & Pan** - Pro Track und pro Clip
- ✅ **Mute/Solo** - Track-Isolation für Mixing
- ✅ **Fade In/Out** - Automatische oder manuelle Fades
- ✅ **Waveform-Display** - Visuelle Audio-Darstellung
- ✅ **Timeline-Sync** - Integration mit Timeline-Editor
- ✅ **Real-time Mixing** - Sofortige Vorschau
- ✅ **Export** - Mix-Down zu WAV/MP3

---

## 🎯 Wann Multitrack verwenden?

**Ideal für:**
- Podcasts mit Hintergrundmusik
- Sound-Effects-Integration (Intro/Outro, Jingles)
- Mehrere Sprecher auf separaten Spuren
- Professionelles Audio-Mixing
- Komplexe Audio-Produktionen

**Nicht nötig für:**
- Einfache Dialoge (nutze Standard-Editor)
- Schnelle TTS-Tests
- Single-Voice-Podcasts ohne Musik

---

## 🚀 Multitrack-Editor starten

### Via GUI-Editor

```bash
# Editor starten
podcastforge edit

# Multitrack-Ansicht öffnen
# Menü: View → Multitrack Editor
# Oder: Ctrl+M
```

### Programmatisch

```python
import tkinter as tk
from podcastforge.gui.multitrack import MultitrackEditor

root = tk.Tk()
editor = MultitrackEditor(root)
editor.pack(fill='both', expand=True)
root.mainloop()
```

---

## 📐 Benutzeroberfläche

### Layout

```
┌────────────────────────────────────────────────────────────┐
│ Toolbar: [Add Track] [Import] [Export] [Play] [Stop]      │
├──────────────┬─────────────────────────────────────────────┤
│ Track List   │  Timeline Canvas                            │
│              │                                             │
│ 🎙️ Voice 1   │  ▬▬▬▬▬  ▬▬▬  ▬▬▬▬▬▬                      │
│ 🔇 🔊 Pan    │                                             │
│              │                                             │
│ 🎵 Music     │  ━━━━━━━━━━━━━━━━━━━━━━━━━━               │
│ 🔇 🔊 Pan    │                                             │
│              │                                             │
│ 🔔 SFX       │     ▬  ▬  ▬                                │
│ 🔇 🔊 Pan    │                                             │
│              │                                             │
│ 🎚️ Master    │  Mix-Bus                                   │
│ 🔇 🔊        │                                             │
└──────────────┴─────────────────────────────────────────────┘
│ Transport: [⏮] [▶] [⏸] [⏹] [⏭]  Time: 00:00 / 10:30      │
└────────────────────────────────────────────────────────────┘
```

### Komponenten

**Track List (links):**
- Track-Name und Typ-Icon
- Mute-Button (🔇)
- Solo-Button (S)
- Volume-Slider (🔊)
- Pan-Control (-L/C/R+)

**Timeline Canvas (rechts):**
- Horizontale Zeitachse
- Audio-Clips als Blöcke
- Waveform-Anzeige
- Grid-Lines

**Transport Controls (unten):**
- Play/Pause/Stop
- Skip Forward/Back
- Zeit-Anzeige

---

## 🎵 Mit Tracks arbeiten

### Track hinzufügen

**Via UI:**
1. Klicke "Add Track" Button
2. Wähle Track-Typ:
   - Voice (für Sprecher)
   - Music (für Hintergrundmusik)
   - SFX (für Sound Effects)
3. Gib Track-Namen ein

**Via Code:**
```python
from podcastforge.gui.multitrack import Track, TrackType

# Voice-Track erstellen
voice_track = Track(
    id="track_1",
    name="Host",
    type=TrackType.VOICE,
    volume=1.0,
    pan=0.0,
    color="#569cd6"
)

editor.add_track(voice_track)
```

### Track-Typen

**Voice Track (🎙️):**
- Für Sprecher/Dialog
- Optimiert für Sprach-Frequenzen
- Standard-Pan: Center
- Farbe: Blau

**Music Track (🎵):**
- Für Hintergrundmusik
- Stereo-Verarbeitung
- Standard-Volume: 70% (leiser als Voice)
- Farbe: Grün

**SFX Track (🔔):**
- Für Sound Effects
- Jingles, Intro/Outro
- Positionierbar in Stereo-Field
- Farbe: Orange

**Master Track (🎚️):**
- Mix-Bus (automatisch)
- Steuert Gesamt-Output
- Kann nicht gelöscht werden
- Farbe: Grau

### Track bearbeiten

**Umbenennen:**
- Doppelklick auf Track-Namen
- Neuen Namen eingeben
- Enter drücken

**Farbe ändern:**
- Rechtsklick auf Track → "Change Color"
- Farbe auswählen

**Löschen:**
- Track auswählen
- Del-Taste
- Oder: Rechtsklick → "Delete Track"

---

## 🎬 Audio-Clips verwalten

### Clip hinzufügen

**Methode 1: Import**
```
1. Track auswählen
2. Rechtsklick → "Import Audio"
3. WAV/MP3-Datei auswählen
4. Clip erscheint auf Timeline
```

**Methode 2: Drag & Drop**
```
1. Datei aus Explorer/Finder ziehen
2. Auf Track droppen
3. Position beim Drop = Start-Zeit
```

**Methode 3: Programmatisch**
```python
from podcastforge.gui.multitrack import AudioClip
from pathlib import Path

clip = AudioClip(
    id="clip_1",
    file=Path("audio.wav"),
    start_time=5.0,      # Startet bei 5 Sekunden
    duration=10.5,       # 10.5 Sekunden lang
    volume=0.8,          # 80% Lautstärke
    fade_in=0.5,         # 500ms Fade In
    fade_out=1.0         # 1s Fade Out
)

track.add_clip(clip)
```

### Clip verschieben

**Maus:**
- Klicke und halte Clip
- Ziehe zu neuer Position
- Loslassen

**Keyboard:**
- Clip auswählen
- `←` / `→` für 0.1s Schritte
- `Shift+←` / `Shift+→` für 1s Schritte

**Exakt:**
- Doppelklick auf Clip
- "Start Time" Feld bearbeiten
- Enter

### Clip trimmen

**Trim Start:**
- Maus am linken Rand des Clips
- Cursor wird zu `⇄`
- Ziehen nach rechts = Start später

**Trim End:**
- Maus am rechten Rand
- Ziehen nach links = Ende früher

**Keyboard:**
- `[` - Trim Start am Playhead
- `]` - Trim End am Playhead

### Clip splitten

1. Setze Playhead an Split-Position
2. Clip auswählen
3. `S` drücken oder Rechtsklick → "Split"
4. Clip wird in zwei Clips geteilt

### Clip duplizieren

- Clip auswählen
- `Ctrl+D` - Duplizieren
- Duplikat wird nach Original platziert

---

## 🔊 Volume & Pan

### Track-Volume

**Volume-Slider:**
- 0% = Stumm
- 50% = -6 dB
- 100% = 0 dB (Unity)
- Über 100% möglich (Boost)

**Via Code:**
```python
track.volume = 0.8  # 80%
```

### Clip-Volume

Clip-Volume ist relativ zu Track-Volume:
```
Finale Lautstärke = Track-Volume × Clip-Volume
```

**Beispiel:**
```
Track: 80% (0.8)
Clip:  50% (0.5)
→ Resultat: 40% (0.4)
```

### Pan (Stereo-Position)

**Pan-Werte:**
- `-1.0` = Ganz links (100% L)
- `0.0` = Center (50% L, 50% R)
- `+1.0` = Ganz rechts (100% R)

**Standard-Positionen:**
- Voice: Center (0.0)
- Music: Leicht links (-0.2) oder rechts (+0.2)
- SFX: Je nach Effekt

**Via UI:**
- Pan-Knob unter Track
- Drehen oder Zahlenwert eingeben

**Via Code:**
```python
track.pan = -0.3  # Leicht links
```

---

## 🎚️ Mute & Solo

### Mute (Stummschalten)

**Zweck:** Track temporär ausblenden

**Via UI:**
- Klicke Mute-Button (🔇)
- Button leuchtet = Muted
- Nochmal klicken = Unmute

**Via Code:**
```python
track.muted = True   # Mute
track.muted = False  # Unmute
```

**Alle Muten:**
- Rechtsklick auf Master → "Mute All"

### Solo

**Zweck:** Nur diesen Track hören

**Via UI:**
- Klicke Solo-Button (S)
- Alle anderen Tracks werden gemuted
- Mehrere Tracks können solo sein

**Via Code:**
```python
track.solo = True   # Solo
track.solo = False  # Un-Solo
```

**Solo-Verhalten:**
```
Solo aktiv: Nur Solo-Tracks hörbar
Solo inaktiv: Normale Mute-Zustände
```

---

## 🎨 Fade In/Out

### Auto-Fades

**Pro Clip:**
```python
clip.fade_in = 0.5   # 500ms Fade In
clip.fade_out = 1.0  # 1s Fade Out
```

**Via UI:**
1. Clip doppelklicken
2. "Fade In" und "Fade Out" Felder
3. Werte eingeben (in Sekunden)

**Visual:**
- Fade In: Dreieck links im Clip
- Fade Out: Dreieck rechts im Clip

### Crossfade

Überlappende Clips werden automatisch crossfaded:

```
Clip 1: ▬▬▬▬▬▬▬
Clip 2:     ▬▬▬▬▬▬▬
         ↑ Crossfade-Zone
```

**Dauer:** Überlappungs-Länge

---

## ⏯️ Playback & Transport

### Transport Controls

| Button | Funktion | Shortcut |
|--------|----------|----------|
| ⏮ | Zum Anfang | `Home` |
| ▶ | Play | `Space` |
| ⏸ | Pause | `Space` |
| ⏹ | Stop | `Esc` |
| ⏭ | Zum Ende | `End` |

### Playback-Optionen

**Loop:**
- Aktiviere Loop-Modus
- Markiere Loop-Region
- Playback wiederholt sich

**Scrubbing:**
- Klicke in Timeline
- Playhead springt zu Position
- Audio spielt ab

**Follow Playhead:**
- Timeline scrollt mit Playhead
- Deaktivieren: Lock-Icon

---

## 💾 Export

### Mix-Down

**Zweck:** Alle Tracks zu einer Audio-Datei mischen

**Schritte:**
1. `File` → `Export Mix`
2. Format wählen (WAV/MP3)
3. Qualität/Bitrate einstellen
4. Speicherort wählen
5. Export startet

**Optionen:**
```python
export_options = {
    "format": "mp3",           # oder "wav"
    "bitrate": "192k",         # für MP3
    "sample_rate": 44100,      # Hz
    "normalize": True,         # Auf -16 LUFS
    "include_master_fx": True  # Master-Effekte anwenden
}
```

### Track Solo Export

**Nur einen Track exportieren:**
1. Track auf Solo setzen
2. Export wie oben
3. Nur Solo-Track wird exportiert

### Time-Range Export

**Nur einen Bereich exportieren:**
1. Markiere Region (Klicke + Ziehe auf Timeline)
2. `Export Selected Region`
3. Nur markierter Bereich wird exportiert

---

## 🎛️ Erweiterte Features

### Automation (geplant v1.2)

Volume/Pan über Zeit ändern:
```python
# Automation-Points setzen
track.add_automation_point(
    time=5.0,
    parameter="volume",
    value=1.0
)
track.add_automation_point(
    time=10.0,
    parameter="volume",
    value=0.3  # Fade zu 30%
)
```

### Master-Effekte (geplant v1.2)

- Kompressor
- EQ
- Limiter
- Reverb

### Markers & Regions

**Marker setzen:**
- `M` drücken an aktueller Position
- Marker-Name eingeben

**Region erstellen:**
- Klicke + Ziehe auf Timeline
- Rechtsklick → "Create Region"

---

## 🔧 Workflows

### Workflow 1: Podcast mit Musik

```
1. Voice-Track erstellen
   - Import Dialog-Audio

2. Music-Track erstellen
   - Import Hintergrundmusik
   - Volume auf 30% setzen

3. Clip-Platzierung
   - Musik startet bei 0:00
   - Dialog startet bei 0:05
   - Musik endet bei Ende + 0:05

4. Fades
   - Musik: Fade In 2s, Fade Out 3s
   - Dialog: Fade In 0.5s

5. Mix-Down zu MP3
```

### Workflow 2: Interview mit Intro/Outro

```
1. Tracks erstellen
   - Voice Track (Interview)
   - SFX Track (Intro Jingle)
   - SFX Track (Outro Jingle)
   - Music Track (Background)

2. Platzierung
   - Intro: 0:00 - 0:10
   - Interview: 0:10 - 30:00
   - Outro: 30:00 - 30:10
   - Music: Durchgehend (leise)

3. Volume
   - Intro/Outro: 100%
   - Interview: 100%
   - Music: 20% während Interview

4. Export
```

### Workflow 3: Multi-Sprecher auf Tracks

```
1. Track pro Sprecher
   - Voice Track "Host"
   - Voice Track "Gast 1"
   - Voice Track "Gast 2"

2. Pan-Positionen
   - Host: Center (0.0)
   - Gast 1: Leicht links (-0.3)
   - Gast 2: Leicht rechts (+0.3)

3. Clips platzieren
   - Chronologisch nach Dialog

4. Solo-Funktion
   - Einzelne Sprecher abhören
   - Levels anpassen

5. Mix-Down
```

---

## ⌨️ Keyboard-Shortcuts

### Navigation

| Shortcut | Aktion |
|----------|--------|
| `Space` | Play/Pause |
| `Esc` | Stop |
| `Home` | Zum Anfang |
| `End` | Zum Ende |
| `←` / `→` | Playhead 0.1s |
| `Shift+←` / `→` | Playhead 1s |
| `+` / `-` | Zoom In/Out |

### Editing

| Shortcut | Aktion |
|----------|--------|
| `S` | Split Clip |
| `Ctrl+D` | Duplizieren |
| `Del` | Löschen |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `[` | Trim Start |
| `]` | Trim End |
| `M` | Marker setzen |

### Tracks

| Shortcut | Aktion |
|----------|--------|
| `Ctrl+T` | Track hinzufügen |
| `Ctrl+M` | Mute ausgewählten Track |
| `Ctrl+S` | Solo ausgewählten Track |
| `↑` / `↓` | Track-Auswahl |

---

## 🐛 Troubleshooting

### Problem: Kein Audio bei Playback

**Lösungen:**
1. Track Mute-Status prüfen (🔇)
2. Clip-Volume > 0% prüfen
3. Master-Volume prüfen
4. Audio-Backend prüfen (Settings)

### Problem: Clips überlappen sich

**Lösungen:**
```
1. Clips manuell verschieben
2. Snap-to-Grid aktivieren
3. Oder: Automatisch layouten
   Rechtsklick → "Auto-Layout Track"
```

### Problem: Export schlägt fehl

**Lösungen:**
1. Speicherplatz prüfen (mindestens 1GB)
2. Schreibrechte prüfen
3. Kürzeren Bereich exportieren (Test)
4. WAV statt MP3 versuchen

### Problem: Hohe CPU-Last

**Lösungen:**
1. Waveform-Anzeige reduzieren (Settings)
2. Weniger Tracks gleichzeitig abspielen
3. Audio-Buffer erhöhen (Settings → Audio)

### Problem: Synchronisation verloren

**Lösungen:**
```
1. Snap-to-Grid aktivieren
2. Grid-Größe anpassen (0.1s, 0.5s, 1s)
3. Zoom vergrößern für Präzision
```

---

## 💡 Best Practices

### 1. Track-Organisation

```
✅ Gute Struktur:
- Voice Tracks oben
- Music in der Mitte
- SFX unten
- Master ganz unten

❌ Vermeiden:
- Unbenannte Tracks ("Track 1", "Track 2")
- Zu viele Tracks (max. 8-10 für Übersicht)
```

### 2. Volume-Hierarchie

```
Voice (Dialog):      100% (0 dB)
Music (Background):   20-30% (-10 to -15 dB)
SFX (Effects):        50-80% (-6 to -3 dB)
Master:              80-100% (Headroom für Kompression)
```

### 3. Fades verwenden

```
✅ Immer Fades setzen:
- Clip-Start: 50-200ms
- Clip-Ende: 200-500ms
- Musik: 1-3s

❌ Vermeiden:
- Harte Cuts (klingt unprofessionell)
- Zu kurze Fades (<50ms)
```

### 4. Panning für Klarheit

```
Single-Sprecher: Center (0.0)
Zwei Sprecher: -0.2 und +0.2
Musik: Stereo (-0.1 bis +0.1)
SFX: Je nach Kontext
```

### 5. Backup & Versioning

```
- Speichere häufig (Ctrl+S)
- Version-Nummern: projekt_v1.mtx, projekt_v2.mtx
- Backup vor großen Änderungen
```

---

## 📚 Weiterführende Ressourcen

- **Timeline Guide:** [timeline-guide.md](timeline-guide.md)
- **Audio Processing:** [audio-processing.md](audio-processing.md)
- **Editor Guide:** [../EDITOR_GUIDE.md](../EDITOR_GUIDE.md)
- **TTS Engines:** [tts-engines.md](tts-engines.md)

---

## 🔄 Version History

- **v1.0** (2025-11-17): Initiale Dokumentation, vollständige Feature-Coverage

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
