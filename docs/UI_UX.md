**UI/UX Dokumentation**

Dieses Dokument beschreibt die aktuelle UI-/UX-Implementierung von PodcastForge (Stand: Codebasis im Repository). Es fasst Aufbau, Haupt-Interaktionsflüsse, erreichbare UI-Elemente, Threading-/Performance-Überlegungen und Verbesserungsvorschläge zusammen.

**Übersicht**
- **Platform & Toolkit:** : `tkinter` (native Desktop-GUI, modulare Komponenten in `src/podcastforge/gui`).
- **Fensterstruktur:** Hauptfenster (`MainWindow`) und separater, vollwertiger Editor (`PodcastEditor`).
- **Wichtige Module:** `src/podcastforge/gui/main_window.py`, `editor.py`, `timeline.py`, `multitrack.py`, `components.py`, `threading_base.py`.

**Haupt-Layout / Regions**
- **Menü / Toolbar:** Datei-, Bearbeiten-, TTS- und Ansicht-Menüs; Toolbar-Schnellzugriffe (New/Open/Save/Preview/Play/Stop) — in `MainWindow` und `PodcastEditor` implementiert.
- **Linke Sidebar:** Voices / Speakers, Voice-Library-Filter (Sprache, Stil) und Suche. (`PodcastEditor.setup_left_panel`, `MainWindow._populate_left_sidebar`).
- **Zentrales Content-Areal:** Reiter mit Editor / Content / Timeline. Voller Editor (`PodcastEditor`) bietet ScrolledText mit Zeilennummern, Format-Selector (structured/yaml/json) und Syntax-Highlighting-Stub. (`PodcastEditor.setup_center_panel`, `MainWindow._populate_center_content`).
- **Rechte Sidebar:** Properties (Sprecher, Emotion, Pause, Speed), Audio-Vorschau (Play/Stop/Volume) und Podcast-Info. (`PodcastEditor.setup_right_panel`).
- **Timeline / Multitrack:** Canvas-basierte Timeline mit Drag&Drop, Zoom, Snap-to-Grid; Multi-Track-Audio-Editor mit Mixer-Strips, Volume/Pan, Mute/Solo. (`timeline.py`, `multitrack.py`).
- **Statusbar:** Wiederverwendbare `StatusBar`-Komponente in `components.py` (Label + Progressbar).

**Interaktionsmuster & UX-Flows**
- **Projekt erstellen/öffnen/speichern:** Menü/Toolbar-Punkte; Dateiauswahl via `filedialog`; Format-Auto-Erkennung für YAML/JSON. (`PodcastEditor.open_project/_save_to_file`).
- **Editor-Flow:** Text direkt editierbar, Zeilennummern aktualisieren sich (`update_line_numbers`), Änderungen markieren (`on_modified`), Einfügen/Löschen von Zeilen über Toolbar oder Shortcuts (Ctrl+Enter, Ctrl+D).
- **Sprecher-Management:** Add/Edit/Remove per Dialog (`SpeakerDialog` in `editor.py`), Voice-Library-Integration (Filter + „Als Sprecher verwenden“). UX: klare Trennung Left-Panel für Management, Right-Panel für Zeilen-Properties.
- **TTS-Interaktion:** Einzelne Zeile vorhören (F5), gesamtes Skript vorhören (F6), Auswahl einer TTS-Engine über Menü. Audio-Preview läuft im Hintergrund (Threading-Integration für lange Tasks).
- **Timeline-Interaktion:** Drag & Drop von Szenen, Double-Click für Edit, Playhead-Scrubbing durch Klick, Zoom-In/Out über Buttons oder Mausrad, Snap-to-Grid Toggle und Grid-Interval-Auswahl. (Callbacks: `on_scene_selected`, `on_time_changed`).
- **Multitrack-Interaktion:** Tracks hinzufügen, Clips importieren, Mixer-Strip für jeden Track mit Volume/Pan und Mute/Solo-Buttons; Drag & Drop zur Positionierung von Clips.

**Steuerung & Shortcuts**
- **Allgemeine Shortcuts:** `Ctrl+N` (Neu), `Ctrl+O` (Öffnen), `Ctrl+S` (Speichern), `Ctrl+E` (Export), `Ctrl+Q` (Beenden) — in `PodcastEditor.setup_shortcuts`.
- **Editor-spezifisch:** `Ctrl+Enter` (Zeile einfügen), `Ctrl+D` (Zeile löschen), `F5` (Vorhören), `F6` (Alles vorhören), `Ctrl+Z`/`Ctrl+Y` (Undo/Redo).

**Responsiveness & Background Tasks**
- **Threading-Model:** `threading_base.ThreadManager` verwaltet Worker-Threads und sendet Ergebnisse/Fortschritte via `UITaskObserver` an die UI (`after()`-sicher). Dadurch bleiben UI-Callbacks reaktiv während TTS-Generierung / Audio-Rendering läuft.
- **Status-Feedback:** `StatusBar` und progress callbacks werden genutzt, z. B. beim Export oder Engine-Loading.

**Design / Visuals**
- **Theme:** Leichtgewichtiges Theme in `components.apply_theme`, Palette wird als `theme_colors` am Root exposiert. Farben definieren Editor-Hintergrund, Akzente, Speaker-Farben, etc.
- **Typography:** Konsolen-/Monospace-Schrift (`Consolas`) für Editor; konfigurierbare Editor-Font-Size über Settings.
- **Icons / Labels:** Emoji- und Text-basierte Buttons (z. B. '▶️ Play', '🎤 Sprecher') für Kompatibilität und einfache Darstellung ohne Bild-Assets.

**Accessibility & Keyboard-First**
- Viele Funktionen besitzen Keyboard-Shortcuts; Fokussteuerung für Canvas-Elemente (Timeline) und Menüs ist vorhanden.
- Farbkontrast: Theme verwendet dunkle Palette; keine dedizierten Einstellungen für High-Contrast oder skalierbare UI-Elemente außer Editor-Font-Size.

**Fehlerzustände & Fallbacks**
- Headless-/Test-Umgebung: Viele GUI-Module haben Fallbacks (z. B. Tests skippen, wenn `tkinter` nicht verfügbar). Viele `try/except`-Blöcke verhindern Abstürze.
- Teilweise Platzhalter: Waveform-Anzeige ist an mehreren Stellen nur ein Canvas/Platzhalter oder ein `WaveformGenerator`-Wrapper; Syntax-Highlighting ist noch `TODO`.

**Bekannte Limitierungen**
- Syntax-Highlighting: `apply_syntax_highlighting()` noch nicht implementiert (TODO).
- Waveform-Rendering: Platzhalter-Canvas wird verwendet; tatsächliche Darstellung hängt von `WaveformGenerator`-Implementierung ab.
- Mobile / Web: Desktop-Only (tkinter). Keine responsive Web/Touch-Optimierung.
- Accessibility: Keine expliziten Screenreader-Labels oder High-Contrast-Presets.

**Code-Referenzen (wichtige Stellen)**
- Editor (Haupt): `src/podcastforge/gui/editor.py`
- Hauptfenster / Region-Layout: `src/podcastforge/gui/main_window.py`
- Timeline-Editor: `src/podcastforge/gui/timeline.py`
- Multitrack-Editor / Mixer: `src/podcastforge/gui/multitrack.py`
- Wiederverwendbare UI-Komponenten: `src/podcastforge/gui/components.py`
- Threading / UI-Observer: `src/podcastforge/gui/threading_base.py`

**UX-Verbesserungsvorschläge (priorisiert)**
1. **Syntax-Highlighting & Linting:** Implementieren der Regex-basierten Syntax-Highlighting-Engine (oder Integration mit Pygments) für bessere Lesbarkeit und Fehlerhinweise.
2. **Waveform-Detail:** Echtzeit-Wellenform-Darstellung mit Zoom/Pane; visuelles Feedback beim Scrubbing.
3. **Undo/Redo Granularität:** Aktuell textbasiert; erweitern für strukturierte Aktionen (Sprecher-Änderungen, Clip-Moves).
4. **Accessibility:** High-Contrast-Theme, ARIA-ähnliche Labels (sofern möglich), und bessere Keyboard-Navigation in Dialogen.
5. **Onboarding / Tooltips:** Kontextuelle Tooltips / kurze Tour für Erstnutzer (z. B. erste Schritte: Projekt → Sprecher → Vorhören → Export).
6. **Persistente UI-Layout-Einstellungen:** Fenster-/Panel-Positionen, zuletzt geöffnete Tabs/Projekte und Editor-Größen speichern und wiederherstellen.

**Anhang: Quick UX-Flows (Kurz)**
- **Skript erstellen → TTS exportieren:** Menü `Datei → Neu` → Editor ausfüllen → `TTS → Zeile vorhören` (F5) → `Datei → Exportieren`.
- **Neue Stimme einem Sprecher zuweisen:** Linkes Panel `Voice Library` → Stimme wählen → `Als Sprecher verwenden` → Sprecher zu Zeile zuweisen über rechte Sidebar.
- **Audio zusammensetzen (Multitrack):** `Timeline` Tab öffnen → `Import Clip` oder `Add Track` → Clips per Drag&Drop positionieren → Mixer anpassen → `Export Audio`.

Wenn Sie möchten, kann ich diese Datei noch erweitern mit: Screenshots (falls verfügbar), konkrete UI-Flow-Diagramme (SVG/MD), oder einer Liste offener Issues/Tasks für UX-Verbesserungen.
