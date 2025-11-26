# UI/UX Dokumentation

Dieses Dokument beschreibt die UI-/UX-Implementierung von PodcastForge (Stand: aktualisiert November 2024).

---

## ✨ Neue UI-Komponenten (v1.2)

### 🎨 Erweiterte Theme-Unterstützung
- **3 Themes verfügbar:** Dunkel, Hell, Blau
- Vollständige Farbpaletten mit Akzent-, Erfolgs-, Warn- und Fehlerfarben
- Konsistentes Styling über alle Komponenten

### 💬 Tooltip-System
- Kontextuelle Hilfe für alle Buttons und Steuerelemente
- Konfigurierbare Verzögerung (Standard: 500ms)
- Automatisches Ausblenden bei Interaktion

### 🚀 Neue Komponenten

| Komponente | Beschreibung |
|------------|--------------|
| `Tooltip` | Kontextuelle Hilfe für Widgets |
| `IconButton` | Button mit Emoji-Icon und Tooltip |
| `WelcomePanel` | Willkommens-/Schnellstart-Panel |
| `QuickActionBar` | Schnellzugriffs-Leiste |
| `VoiceCard` | Anzeigekarte für Stimmen mit Preview |
| `StatusBar` (verbessert) | Statusleiste mit Info-Bereich und Prozentanzeige |

### ⚙️ Erweiterte Einstellungen
Der Settings-Dialog wurde komplett überarbeitet mit 4 Tabs:
- **Erscheinung:** Theme, Fenstergröße, Willkommensbildschirm, Tooltips
- **Editor:** Schriftgröße, Schriftart, Zeilennummern, Auto-Save, Zeilenumbruch
- **Audio:** Auto-Play, TTS-Engine, Qualitätsstufe, Sprache
- **Erweitert:** Cache-Verzeichnis, Debug-Modus, Thread-Anzahl

---

## Übersicht
- **Platform & Toolkit:** `tkinter` (native Desktop-GUI, modulare Komponenten in `src/podcastforge/gui`).
- **Fensterstruktur:** Hauptfenster (`MainWindow`) und separater, vollwertiger Editor (`PodcastEditor`).
- **Wichtige Module:** `main_window.py`, `editor.py`, `timeline.py`, `multitrack.py`, `components.py`, `threading_base.py`.

## Haupt-Layout / Regions
- **Menü / Toolbar:** Datei-, Bearbeiten-, TTS- und Ansicht-Menüs; Toolbar-Schnellzugriffe
- **Linke Sidebar:** Voices / Speakers, Voice-Library-Filter (Sprache, Stil) und Suche
- **Zentrales Content-Areal:** Reiter mit Editor / Content / Timeline
- **Rechte Sidebar:** Properties (Sprecher, Emotion, Pause, Speed), Audio-Vorschau
- **Timeline / Multitrack:** Canvas-basierte Timeline mit Drag&Drop, Zoom, Snap-to-Grid
- **Statusbar:** Verbesserte StatusBar mit Info-Bereich und Prozentanzeige

## Steuerung & Shortcuts
- **Ctrl+N** (Neu), **Ctrl+O** (Öffnen), **Ctrl+S** (Speichern), **Ctrl+E** (Export), **Ctrl+Q** (Beenden)
- **Ctrl+Enter** (Zeile einfügen), **Ctrl+D** (Zeile löschen)
- **F5** (Vorhören), **F6** (Alles vorhören)
- **Ctrl+Z/Ctrl+Y** (Undo/Redo)

## Design / Visuals
- **Theme:** 3 Themes (Dunkel, Hell, Blau) in `components.py`
- **Typography:** Konfigurierbare Monospace-Schrift (Standard: Consolas)
- **Icons:** Emoji-basierte Buttons via `IconButton`-Komponente
- **Tooltips:** Kontextuelle Hilfe via `Tooltip`-Komponente

## Code-Referenzen
- Editor: `src/podcastforge/gui/editor.py`
- UI-Komponenten: `src/podcastforge/gui/components.py`
- Settings-Dialog: `src/podcastforge/gui/settings_dialog.py`
- Threading: `src/podcastforge/gui/threading_base.py`
