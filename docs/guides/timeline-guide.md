# Timeline-Editor Guide

**Version:** 1.0  
**Stand:** 2025-11-17

---

## 🎬 Übersicht

Der Timeline-Editor ist ein visueller, canvas-basierter Editor für präzise Podcast-Bearbeitung. Er ermöglicht das Anordnen, Bearbeiten und Timing von Audio-Szenen mit einer intuitiven Timeline-Ansicht.

**Status:** ✅ Vollständig implementiert (631 LOC)

---

## ✨ Features

### Kernfunktionen

- **Canvas-basierte Timeline** - Horizontale Timeline mit Zeitmarkierungen
- **Zoom In/Out** - Von 10 Sekunden bis 10 Minuten Ansicht
- **Drag & Drop** - Szenen per Maus verschieben
- **Visual Waveform** - Wellenform-Anzeige für jedes Audio-Segment
- **Szenen-Marker** - Benutzerdefinierte Marker und Kapitel
- **Snap-to-Grid** - Automatisches Einrasten (0.1s, 0.5s, 1.0s)
- **Scrubbing** - Audio-Position per Mausklick setzen
- **Multi-Track** - Mehrere Spuren für verschiedene Sprecher

---

## 🚀 Timeline-Editor starten

### Im GUI-Editor

Der Timeline-Editor ist integriert im Haupt-Editor:

1. Editor starten:
   ```bash
   podcastforge edit
   ```

2. Timeline-Panel ist standardmäßig sichtbar (unterer Bereich)

3. Oder Timeline-View umschalten:
   - Menü: `View → Timeline`
   - Keyboard: `Ctrl+T`

---

## 📐 Benutzeroberfläche

### Layout

```
┌────────────────────────────────────────────────────────┐
│  Timeline-Header (Zeit-Skala, Zoom, Controls)         │
├────────────────────────────────────────────────────────┤
│  Marker-Leiste (Kapitel, Bookmarks)                   │
├────────────────────────────────────────────────────────┤
│  Track 1 (Sprecher 1)  ▬▬▬▬  ▬▬▬  ▬▬▬▬▬               │
├────────────────────────────────────────────────────────┤
│  Track 2 (Sprecher 2)     ▬▬▬▬▬  ▬▬▬  ▬▬              │
├────────────────────────────────────────────────────────┤
│  Track 3 (Musik)       ━━━━━━━━━━━━━━━━━━━━━━         │
└────────────────────────────────────────────────────────┘
```

### Elemente

**Timeline-Header:**
- Zeit-Skala (0:00, 0:10, 0:20, ...)
- Zoom-Buttons (+/-)
- Aktueller Zeitstempel
- Playback-Position (roter Balken)

**Marker-Leiste:**
- Kapitel-Marker (blau)
- Bookmark-Marker (grün)
- Custom Marker (gelb)

**Tracks:**
- Audio-Szenen als farbige Blöcke
- Wellenform-Visualisierung
- Sprecher-Namen
- Längen-Anzeige

---

## 🎮 Bedienung

### Maus-Steuerung

| Aktion | Beschreibung |
|--------|--------------|
| **Linksklick auf Szene** | Szene auswählen |
| **Drag Szene** | Szene verschieben (zeitlich) |
| **Doppelklick auf Szene** | Szene bearbeiten |
| **Rechtsklick auf Szene** | Kontext-Menü öffnen |
| **Linksklick auf Timeline** | Playback-Position setzen |
| **Mausrad** | Horizontal scrollen |
| **Ctrl+Mausrad** | Zoom In/Out |

### Keyboard-Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Space` | Play/Pause |
| `←` / `→` | 1 Sekunde vor/zurück |
| `Ctrl+←` / `Ctrl+→` | Zur vorherigen/nächsten Szene |
| `+` / `-` | Zoom In/Out |
| `0` | Zoom Reset (1px = 0.1s) |
| `Home` | Zum Anfang springen |
| `End` | Zum Ende springen |
| `Del` | Ausgewählte Szene löschen |
| `Ctrl+D` | Szene duplizieren |
| `Ctrl+Z` | Rückgängig |
| `Ctrl+Y` | Wiederholen |
| `M` | Marker setzen |

---

## 📝 Arbeiten mit Szenen

### Szene hinzufügen

**Methode 1: Aus Editor**
1. Text im Script-Editor markieren
2. Rechtsklick → "Add to Timeline"
3. Szene erscheint am Ende der Timeline

**Methode 2: Direkt in Timeline**
1. Rechtsklick auf freien Bereich → "New Scene"
2. Sprecher und Text eingeben
3. TTS generieren

**Methode 3: Drag & Drop**
1. Zeile aus Editor auf Timeline ziehen
2. Position beim Drop bestimmt Start-Zeit

### Szene verschieben

**Methode 1: Drag & Drop**
1. Szene anklicken und halten
2. An neue Position ziehen
3. Loslassen (Snap-to-Grid aktiv)

**Methode 2: Präzise Eingabe**
1. Szene doppelklicken
2. "Start Time" Feld bearbeiten
3. Enter drücken

### Szene bearbeiten

1. Doppelklick auf Szene
2. Edit-Dialog öffnet sich:
   - **Sprecher:** Dropdown
   - **Text:** Textfeld
   - **Start Time:** Präzise Zeit-Eingabe
   - **Duration:** Länge anpassen
   - **Emotion:** Emotion auswählen
   - **Fade In/Out:** An/Aus

### Szene löschen

- **Del-Taste:** Ausgewählte Szene löschen
- **Rechtsklick → Delete:** Über Menü
- **Undo:** Löschen rückgängig machen (Ctrl+Z)

### Szene duplizieren

- **Ctrl+D:** Schnell-Duplikation
- **Rechtsklick → Duplicate:** Über Menü
- Duplikat wird nach Original eingefügt

---

## 🎯 Marker & Kapitel

### Marker setzen

**Methode 1: Keyboard**
1. Playback-Position an gewünschte Stelle setzen
2. `M` drücken
3. Marker-Name eingeben

**Methode 2: Rechtsklick**
1. Rechtsklick auf Timeline-Header
2. "Add Marker" auswählen
3. Konfigurieren

### Marker-Typen

| Typ | Farbe | Verwendung |
|-----|-------|------------|
| **Chapter** | Blau | Kapitel-Grenzen |
| **Bookmark** | Grün | Wichtige Punkte |
| **Custom** | Gelb | Freie Verwendung |

### Marker bearbeiten

1. Doppelklick auf Marker
2. Label und Farbe ändern
3. Typ anpassen

### Marker löschen

- Rechtsklick → "Delete Marker"
- Marker ziehen → außerhalb der Timeline → loslassen

---

## 🔍 Zoom & Navigation

### Zoom-Stufen

| Stufe | Anzeige | Verwendung |
|-------|---------|------------|
| **Max Out** | 10 Min | Gesamtübersicht |
| **Normal** | 1 Min | Standard-Bearbeitung |
| **Detail** | 10 Sek | Präzises Timing |
| **Max In** | 1 Sek | Wellenform-Detail |

### Zoom-Bedienung

**Zoom In:**
- `+` Taste
- `Ctrl+Mausrad (up)`
- Zoom-Button in Toolbar

**Zoom Out:**
- `-` Taste
- `Ctrl+Mausrad (down)`
- Zoom-Button in Toolbar

**Zoom Reset:**
- `0` Taste
- Doppelklick auf Zoom-Anzeige

### Smart Zoom

**Zoom to Selection:**
- Szene auswählen
- Rechtsklick → "Zoom to Scene"
- Timeline zoomt auf Szene

**Zoom to All:**
- `Ctrl+0`
- Zeigt gesamten Podcast

---

## 🎨 Wellenform-Visualisierung

### Anzeige

Jede Szene zeigt automatisch ihre Wellenform:
- **Blau:** Positive Amplitude
- **Rot:** Negative Amplitude
- **Höhe:** Lautstärke
- **Länge:** Dauer

### Wellenform generieren

**Automatisch:**
- Nach TTS-Generierung automatisch erstellt

**Manuell:**
- Rechtsklick auf Szene → "Generate Waveform"

### Wellenform-Details

- **Auflösung:** Passt sich Zoom an
- **Performance:** Caching für schnelle Darstellung
- **Farben:** Pro Sprecher anpassbar

---

## ⚙️ Snap-to-Grid

### Was ist Snap-to-Grid?

Automatisches Einrasten von Szenen an Zeitraster.

### Snap-Intervalle

- **0.1s:** Sehr fein (Detail-Arbeit)
- **0.5s:** Normal (Standard)
- **1.0s:** Grob (Schnelle Planung)

### Snap aktivieren/deaktivieren

**Temporär:**
- `Shift` halten beim Drag = Snap deaktiviert

**Permanent:**
- Toolbar: Snap-Button (Magnet-Icon)
- `Ctrl+G`: Snap toggle

### Snap-Intervall ändern

- Rechtsklick auf Timeline → "Snap Settings"
- Intervall auswählen (0.1s / 0.5s / 1.0s)

---

## 🎵 Audio-Playback

### Playback-Controls

**Play/Pause:**
- `Space` Taste
- Play-Button in Toolbar

**Stop:**
- `Esc` Taste
- Stop-Button

**Position setzen:**
- Linksklick auf Timeline
- Setzt Playback-Position

### Playback-Modi

**Normal:**
- Spielt von aktueller Position bis Ende

**Loop:**
- Wiederholt ausgewählten Bereich
- Aktivieren: Toolbar → Loop-Button

**Selection:**
- Nur ausgewählte Szene abspielen
- Rechtsklick auf Szene → "Play Scene"

---

## 🔧 Erweiterte Funktionen

### Multi-Track-Editing

**Tracks hinzufügen:**
1. Rechtsklick auf Track-Bereich
2. "Add Track"
3. Track-Name eingeben

**Track-Eigenschaften:**
- **Solo:** Nur diesen Track hören
- **Mute:** Track stumm schalten
- **Lock:** Track vor Änderungen schützen

### Fade In/Out

**Für Szene:**
1. Szene doppelklicken
2. "Fade In" aktivieren (z.B. 0.5s)
3. "Fade Out" aktivieren (z.B. 1.0s)

**Visuell:**
- Fade wird als Dreieck in Szene angezeigt

### Crossfade zwischen Szenen

**Automatisch:**
1. Zwei Szenen überlappen lassen
2. Rechtsklick → "Auto Crossfade"
3. Crossfade-Dauer einstellen

**Manuell:**
- Fade Out auf Szene 1 setzen
- Fade In auf Szene 2 setzen
- Überlappung anpassen

---

## 💾 Export & Integration

### Timeline exportieren

**Als JSON:**
```bash
File → Export → Timeline (JSON)
```

**Format:**
```json
{
  "total_duration": 120.5,
  "scenes": [
    {
      "id": "scene_1",
      "speaker": "Host",
      "start_time": 0.0,
      "duration": 5.2,
      "audio_file": "scene_1.wav"
    }
  ],
  "markers": [
    {
      "time": 60.0,
      "label": "Kapitel 2",
      "type": "chapter"
    }
  ]
}
```

### In Editor importieren

**Aus Timeline JSON:**
1. File → Import → Timeline
2. JSON-Datei auswählen
3. Szenen werden geladen

### Audio-Mix generieren

**Final Mix:**
1. Timeline → Export → Audio Mix
2. Format wählen (WAV/MP3)
3. Output-Datei angeben

**Optionen:**
- Normalisierung (empfohlen)
- Kompression (-20dB)
- Master-Lautstärke

---

## 🎓 Best Practices

### 1. Struktur planen

Vor dem Editing:
- Kapitel mit Markern planen
- Sprecher-Rollen festlegen
- Grobe Zeitplanung erstellen

### 2. Snap verwenden

- Snap-to-Grid für saubere Übergänge
- 0.5s Snap für normale Arbeit
- 0.1s Snap für Details

### 3. Wellenformen nutzen

- Visuelle Kontrolle der Lautstärke
- Pausen erkennen
- Schnitte planen

### 4. Marker setzen

- Kapitel markieren
- Wichtige Stellen kennzeichnen
- Export-Kapitel vorbereiten

### 5. Backup erstellen

- Regelmäßig speichern (Ctrl+S)
- Versionen anlegen
- JSON-Export als Backup

---

## 🐛 Troubleshooting

### Problem: Szenen überlappen sich

**Lösung:**
1. Snap-to-Grid aktivieren
2. Szenen neu anordnen
3. Oder: Rechtsklick → "Auto-Layout"

### Problem: Wellenform nicht sichtbar

**Lösung:**
1. Zoom vergrößern
2. Rechtsklick → "Generate Waveform"
3. Audio-Datei prüfen

### Problem: Playback ruckelt

**Lösung:**
1. Wellenform-Caching aktivieren
2. Zoom reduzieren
3. Buffering erhöhen (Settings)

### Problem: Drag & Drop funktioniert nicht

**Lösung:**
1. Szene anklicken und kurz warten
2. Dann ziehen (nicht sofort)
3. Lock-Status prüfen

---

## ⌨️ Keyboard-Shortcuts Übersicht

### Playback

| Shortcut | Aktion |
|----------|--------|
| `Space` | Play/Pause |
| `Esc` | Stop |
| `←` | 1s zurück |
| `→` | 1s vor |
| `Ctrl+←` | Vorherige Szene |
| `Ctrl+→` | Nächste Szene |
| `Home` | Zum Anfang |
| `End` | Zum Ende |

### Editing

| Shortcut | Aktion |
|----------|--------|
| `Del` | Szene löschen |
| `Ctrl+D` | Duplizieren |
| `Ctrl+Z` | Rückgängig |
| `Ctrl+Y` | Wiederholen |
| `Ctrl+X` | Ausschneiden |
| `Ctrl+C` | Kopieren |
| `Ctrl+V` | Einfügen |
| `M` | Marker setzen |

### View

| Shortcut | Aktion |
|----------|--------|
| `+` | Zoom In |
| `-` | Zoom Out |
| `0` | Zoom Reset |
| `Ctrl+0` | Zoom to All |
| `Ctrl+G` | Snap toggle |
| `Ctrl+T` | Timeline toggle |

---

## 📚 Weiterführende Ressourcen

- **Editor Guide:** [EDITOR_GUIDE.md](EDITOR_GUIDE.md)
- **Multitrack Guide:** [multitrack-guide.md](multitrack-guide.md) (in Planung)
- **Audio Processing:** [audio-processing.md](audio-processing.md) (in Planung)
- **Dokumentations-Index:** [docs/README.md](../README.md)

---

## 🔄 Version History

- **1.0** (2025-11-17): Initiale Dokumentation

---

**Letzte Aktualisierung:** 2025-11-17  
**Maintainer:** PodcastForge-AI Team
