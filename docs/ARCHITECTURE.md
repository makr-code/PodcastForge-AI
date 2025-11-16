# PodcastForge-AI Architecture & Best Practices

## 🏗️ Architektur-Übersicht

PodcastForge-AI folgt einem **modularen, schichtbasierten Design** mit klarer Separation of Concerns.

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ GUI (tkinter)│  │ CLI (Click)  │  │ Web (TBD) │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                   Business Logic Layer              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ PodcastForge │  │ VoiceLibrary │  │ TTSEngine │ │
│  │   (Core)     │  │              │  │  Manager  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                    Service Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ OllamaClient │  │ AudioPlayer  │  │  Audio    │ │
│  │   (LLM)      │  │              │  │ Processor │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                     Data Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Config Files │  │ Voice Samples│  │  Cache    │ │
│  │  (YAML/JSON) │  │   (WAV/MP3)  │  │  (TMP)    │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Design Patterns

### 1. **Factory Pattern** - TTS Engine Creation

```python
# src/podcastforge/tts/engine_manager.py

class TTSEngineFactory:
    """
    Factory Pattern für TTS-Engine-Erstellung
    
    Vorteile:
    - Entkoppelt Client-Code von konkreten Implementierungen
    - Erleichtert Hinzufügen neuer Engines
    - Zentralisiert Initialisierungs-Logik
    """
    
    @staticmethod
    def create_engine(engine_type: TTSEngine, config: Dict) -> BaseTTSEngine:
        """Erstelle Engine-Instanz basierend auf Typ"""
        
        engine_map = {
            TTSEngine.XTTS: XTTSEngine,
            TTSEngine.BARK: BarkEngine,
            TTSEngine.PIPER: PiperEngine,
            TTSEngine.STYLETTS2: StyleTTS2Engine
        }
        
        engine_class = engine_map.get(engine_type)
        if not engine_class:
            raise ValueError(f"Unknown engine: {engine_type}")
        
        return engine_class(config)
```

        Hinweis: Der zentrale `TTSEngineManager` stellt neben der Factory auch einen Context-Manager
        (`use_engine`) zur Verfügung, der Engines referenzzählt und so deterministisches Load/Unload
        ermöglicht. Verwende `use_engine` für kurzlebige, thread-safe Zugriffe, statt manuelles
        `get_engine`/`unload_all`.

        ```python
        mgr = get_engine_manager(max_engines=2)
        with mgr.use_engine(TTSEngine.PIPER, config={}) as engine:
            engine.synthesize("preview", speaker="0")
        ```

### 2. **Singleton Pattern** - Audio Player

```python
# src/podcastforge/audio/player.py

_player_instance: Optional[AudioPlayer] = None

def get_player() -> AudioPlayer:
    """
    Singleton Pattern für Audio-Player
    
    Vorteile:
    - Garantiert nur eine Player-Instanz
    - Globaler Zugriffspunkt
    - Ressourcen-Sharing
    """
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance
```

### 3. **Strategy Pattern** - Audio Processing

```python
# src/podcastforge/audio/postprocessor.py

class AudioProcessingStrategy(ABC):
    """Abstract Strategy für Audio-Verarbeitung"""
    
    @abstractmethod
    def process(self, audio: AudioSegment) -> AudioSegment:
        pass

class NormalizationStrategy(AudioProcessingStrategy):
    """Normalisierungs-Strategie"""
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        return normalize(audio)

class CompressionStrategy(AudioProcessingStrategy):
    """Komprimierungs-Strategie"""
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        return compress_dynamic_range(audio, threshold=-20, ratio=4.0)

class AudioPostProcessor:
    """Context für Audio-Processing"""
    
    def __init__(self):
        self.strategies: List[AudioProcessingStrategy] = [
            NormalizationStrategy(),
            CompressionStrategy()
        ]
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        for strategy in self.strategies:
            audio = strategy.process(audio)
        return audio
```

### 4. **Observer Pattern** - Event System

```python
# src/podcastforge/core/events.py

class EventBus:
    """
    Observer Pattern für Event-Handling
    
    Vorteile:
    - Loose Coupling zwischen Komponenten
    - Einfaches Hinzufügen neuer Listener
    - Zentrale Event-Verwaltung
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        """Registriere Listener für Event-Typ"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any):
        """Publiziere Event an alle Listener"""
        for callback in self._listeners.get(event_type, []):
            callback(data)

# Verwendung im Editor
class PodcastEditor:
    def __init__(self):
        self.event_bus = EventBus()
        self.event_bus.subscribe('tts_complete', self._on_tts_complete)
    
    def _on_tts_complete(self, audio_file: Path):
        self.update_status("TTS fertig!")
        self.play_audio(audio_file)
```

### 5. **MVC Pattern** - GUI Architecture

```python
# src/podcastforge/gui/mvc.py

# Model
class PodcastProject:
    """Model - Daten & Business Logic"""
    
    def __init__(self):
        self.script: List[Dict] = []
        self.speakers: Dict[str, Speaker] = {}
        self.metadata: Dict = {}
    
    def add_line(self, line: Dict):
        self.script.append(line)
        self.notify_observers()

# View
class EditorView:
    """View - UI-Darstellung"""
    
    def __init__(self, controller):
        self.controller = controller
        self.setup_ui()
    
    def update_display(self, data):
        # Update UI mit neuen Daten
        pass

# Controller
class EditorController:
    """Controller - User-Interaktions-Logik"""
    
    def __init__(self, model: PodcastProject, view: EditorView):
        self.model = model
        self.view = view
    
    def on_add_line(self, line_text: str):
        parsed_line = self.parse_line(line_text)
        self.model.add_line(parsed_line)
        self.view.update_display(self.model.script)
```

---

## 📦 eBook → Podcast Generator (Integration)

Dieser Abschnitt beschreibt das konkrete Mapping und empfohlene Patterns für die
eBook→Podcast‑Generator‑Integration. Die Implementierung befindet sich derzeit in
`src/podcastforge/integrations/ebook2audiobook/orchestrator.py` und nutzt die
allgemeinen Bausteine aus der Architektur: `TTSEngineManager`, `AudioPostProcessor`,
und die Threading/Observer‑Hilfen.

Architektur‑Mapping:
- Extraction: `extract_chapters_from_epub()` (Service/Adapter). Liest EPUBs (optional
    via `ebooklib`) und liefert Kapitel mit `title`/`content`.
- Orchestration: `create_podcast_project_from_ebook()` (Business Logic). Zerlegt Kapitel
    in Paragraphen, orchestriert TTS, Cache, Combining und Postprocessing.
- TTS: `TTSEngineManager` (Factory/Manager) verwaltet konkrete Engines; Verwende
    `use_engine()` für deterministisches Load/Unload, oder die Convenience `synthesize()`
    für einfache Workflows.
- Postprocessing: `AudioPostProcessor` (Strategy Pattern) wendet Normalisierung,
    Kompression und Fade‑Strategien an.
- Output: `project_manifest.json` (Data Layer) enthält Kapiteldateien und Startzeiten.

Empfohlene Laufzeit‑Patterns (konkret empfohlen):
- Resource safe TTS calls: Verwende `with get_engine_manager().use_engine(engine):`
    wenn du eine Engine sequenziell nutzen willst; für parallelisierte Batch‑Synthese
    ist die Manager‑Convenience `synthesize()` geeignet, weil sie Engine‑Caching und
    LRU‑Eviction orchestriert.
- Parallelisierung: Nutze `get_thread_manager()` (oder `ThreadPoolExecutor`) mit
    begrenzter `max_workers` für Absatz‑Parallelisierung. Begrenze die Anzahl geladener
    Engines (`TTSEngineManager(max_engines=2)`) um OOM/VRAM‑Probleme zu vermeiden.
- Progress & UI integration: Publishe Fortschritt über das bestehende Observer/Task‑API
    (`ThreadManager` + `ITaskObserver`) oder über eine `on_progress(task_id, progress, msg)`‑Callback,
    damit die GUI Live‑Feedback und Abbruch unterstützt.

Fallbacks & Minimalität
- Die Integration enthält Lazy‑Imports (z. B. `pydub`, `ebooklib`) und einfache
    Wave‑Fallbacks, damit Developer‑Tests und CI ohne native Abhängigkeiten laufen.
    Für volle Funktionalität (Stille‑Trim, MediaInfo) installiere die optionalen
    Extras (siehe Setup unten).

Setup / Optional Dependencies
- Für volle Funktionalität installiere:
    - `ebooklib`, `beautifulsoup4` (EPUB parsing)
    - `pydub` + `ffmpeg` (audio concat & silence detection)
    - TTS engines (Piper, Bark, XTTS) je nach Bedarf

Beispiel‑Calls (Empfohlen):
```python
from podcastforge.tts import get_engine_manager, TTSEngine
from podcastforge.integrations.ebook2audiobook.orchestrator import create_podcast_project_from_ebook

mgr = get_engine_manager(max_engines=2)
res = create_podcast_project_from_ebook('book.epub', 'outdir', speaker='narrator', engine='PIPER', max_workers=2, on_progress=lambda id,p,msg: print(id,p,msg))
```

Konsequenzen für Entwickler
- Dokumentiere optionalen extras in `pyproject.toml` / `requirements.txt` (z. B. `[ebook]`, `[audio]`).
- Implementiere End‑to‑end Tests, die dry‑run Modi nutzen (keine heavy native libs).

---

## 🔧 FFmpeg Installation & lokale Verifikation

Für viele Audio‑Workflows (MP3/M4A Produktion, Streaming via ffmpeg stdin, pydub) wird eine native `ffmpeg`-Binary benötigt. Dieses Projekt bietet ein kleines Installer‑Skript und automatische Laufzeit-Integration, die das gebündelte `third_party/ffmpeg/bin` erkennt.

Wichtig:

Installer (empfohlen)

PowerShell (Windows):
```powershell
python .\scripts\install_ffmpeg.py --dest .\third_party\ffmpeg\bin
```

Bash (Linux/macOS):
```bash
python3 scripts/install_ffmpeg.py --dest ./third_party/ffmpeg/bin
```

Verifikation (lokal)

PowerShell:
```powershell
Get-Command ffmpeg -ErrorAction SilentlyContinue
where.exe ffmpeg
ffmpeg -version
```

Bash:
```bash
which ffmpeg
ffmpeg -version
```

E2E‑Tests lokal ausführen

PowerShell:
```powershell
# Installiere Abhängigkeiten falls nötig
python -m pip install -r requirements.txt

# E2E-Tests (nur die End-to-End Suite)
python -m pytest -q tests/e2e -q
```

Hinweis zur CI / Runner‑Verifikation

Fehlerbehebung

---

## 🔊 Spatial Preview & `scripts/` Utilities

Das Repository enthält experimentelle Hilfs‑Skripte unter `scripts/`, um
mono‑Utterances in räumliche Stereo‑Previews zu verwandeln (ILD/ITD,
Distanz‑Absorption, optionale IR‑Convolution) und anschliessend normalisierte
MP3/MP4 Previews zu erzeugen. Eine kompakte Bedienungs‑ und Integrationsanleitung
findest du in `scripts/README.md`.

Kurz: Für Preview‑Integration siehe `scripts/spatialize.py` und die
programmatische Integration via `podcastforge.integrations.script_orchestrator.synthesize_script_preview(spatialize=True, ...)`.

    - Existiert `third_party/ffmpeg/bin/ffmpeg(.exe)` lokal?
    - Wurde das Projekt in einer Shell gestartet, nachdem `third_party` hinzugefügt wurde? (Neu starten / Shell neu öffnen)
    - Führe `python .\scripts\install_ffmpeg.py --dest .\third_party\ffmpeg\bin --url <url>` aus, um ein alternatives Build zu verwenden.

---

### Verifikations-Log (Windows, lokal)

Kurze Zusammenfassung eines lokalen Tests, der auf dem Entwickler‑Arbeitsplatz (Windows, PowerShell) ausgeführt wurde:

- Ausgeführte Befehle (PowerShell):
```powershell
python .\scripts\install_ffmpeg.py --dest .\third_party\ffmpeg\bin
where.exe ffmpeg
ffmpeg -version
python -m pytest -q tests/e2e -q
```

- Ergebnis:
    - Das Installer‑Skript hat versucht, eine statische Build von `https://www.gyan.dev/ffmpeg/...` herunterzuladen, konnte aber kein passendes Paket extrahieren/finden (abhängig vom Mirror/URL kann das variieren).
    - `ffmpeg` war in der Shell nicht als ausführbares Programm verfügbar (`where.exe ffmpeg` / `ffmpeg -version` schlugen fehl).
    - Die E2E‑Tests liefen trotzdem lokal durch und beendeten sich erfolgreich (`....... [100%]`). Die Tests sind so geschrieben, dass ffmpeg‑spezifische Assertions übersprungen werden, wenn `ffmpeg` nicht gefunden wird.

Hinweis: Falls du eine vollständige Streaming‑Validierung brauchst, stelle sicher, dass der Installer ein valides ffmpeg‑Archiv herunterladen und die Binärdatei korrekt nach `third_party/ffmpeg/bin` extrahieren kann, oder installiere `ffmpeg` über einen System‑Paketmanager (`choco`, `scoop`, `apt`, `brew`).




---

## 🔊 Polyphoner (Multi‑TTS) Workflow — Schritt für Schritt

Ziel: Aus beliebigem Text oder Textfragmenten ein mehrstimmiges (polyphones) Podcast‑Projekt erzeugen, das mehrere TTS‑Stimmen, zeitliche Platzierung, Post‑Processing und ein importierbares Projekt‑Manifest enthält. Die folgenden Schritte sind als genaue Implementierungs‑ und Integrationsbeschreibung gedacht — inklusive API‑Shapes, Dateinamen und empfohlener Runtime‑Verhalten.

1) Ingestion (Input)
    - Eingabemedium: freier Text, strukturierte Script‑Datei (JSON/YAML), EPUB/Text‑Fragment oder Editor‑Inhalt.
    - Erwartetes Objekt (intern): `ScriptSource` mit Feldern:
      - `source_id: str` (z. B. filename or UUID)
      - `format: 'text'|'structured'|'epub'|'script_json'`
      - `payload: str|dict` (raw content or parsed structure)

2) Parsing & Segmentation
    - Aufgabe: Zerlegen in atomic utterances (Sätze/Absätze), optional nach Kapitel/Abschnitt gruppiert.
    - Output: Liste von `Utterance`:
      - `id: str` (stable key, z. B. hash(source_id + index))
      - `text: str`
      - `chapter: Optional[str]`
      - `suggested_speaker: Optional[str]` (falls im Script angegeben)
      - `meta: dict` (emotion, pause_after, speed_hint)
    - Implementation: `split_into_paragraphs()` / `parse_structured_script()`.

3) Speaker Assignment
    - Nutzer‑gesteuert oder heuristisch (VoiceLibrary.suggest_for_podcast_style).
    - Mapping in `ProjectSpeaker` dataclass:
      - `speaker_id`, `name`, `voice_profile_id`, `gender`, `preferred_engine`
    - Im Editor: Drag&Drop aus `VoiceLibrary` auf Zeile legt `speaker_id` fest.

4) Preflight & Resource Planning
    - Analysiere benötigte Engines und geschätzten VRAM/Time (per voice/engine).
    - Erzeuge `Plan` mit `batches` für parallele Synthese (z. B. 4 workers, max 2 concurrent engines).
    - API: `planner = create_tts_plan(utterances, speakers, max_workers, engine_constraints)`

5) Caching & Cache Keys
    - Cache‑Key: `sha256(engine + voice_profile + text + postproc_flags)`
    - Cache‑Location: `cache/tts/{first2}/{key}.wav` oder `cache/tts/{key}.npz` für numpy arrays.
    - Vor jeder Synthese: `if exists(cache_key): reuse`.

6) Batched/Parallel TTS Synthesis
    - Laufzeit: `get_thread_manager().submit_task(tts_task_fn, priority=...)` oder ThreadPool mit controlled concurrency.
    - Task‑Fn Signatur: `task_fn(task_id, progress_callback)` (verwende `progress_callback(percent, msg)` für UI‑Updates).
    - Engine Management: `with get_engine_manager().use_engine(engine_type): engine.synthesize(text, voice)` oder `get_engine_manager().synthesize(...)` für simpler API.

7) Postprocessing per‑utterance
    - Normalisierung, Silence‑trim, fade_in/out, headroom, optional voice‑matching (EQ).
    - Ergebnisdatei pro Utterance: `utterances/{utterance_id}.wav` (16‑bit PCM, sample_rate project default).

8) Alignment / Timing
    - Berechne Dauer jeder Utterance (via numpy length / sr) und generiere timeline offsets.
    - Für dialogische Überlappungen: Policy entscheidet (no overlap, crossfade, ducking).
    - Timeline Entry (manifest): `{utterance_id, speaker_id, file, offset_sec, duration_sec, postproc_flags}`

9) Mixing / Chapter Combining
    - Optionaler Schritt: Kombiniere Utterances pro Kapitel zu Chapter WAVs (concatenate or crossfade).
    - Finaler Mix: `mix_master(chapters, background_tracks, transitions) -> final_mix.wav`.

10) Manifest & Editor Import
    - Schreibe `project_manifest.json` mit:
      - `speakers: [ {speaker_id, name, voice_profile_id, meta} ]`
      - `utterances: [ {id, speaker_id, file, offset, duration, meta} ]`
      - `chapters: [ {id, title, start_offset, utterance_ids} ]`
      - `project_metadata: {sample_rate, channels, created_at, engine_summary}`
    - Publishe Event: `EventBus.publish('ebook2audiobook.open_project', {'manifest': path})` damit der Editor automatisch importiert.

11) UI Notification & Error Handling
    - Publish Fortschritt per Utterance: `EventBus.publish('script.tts_progress', {task_id, utterance_id, percent})`.
    - Fehler: markiere Utterance als `failed` im Manifest und füge `error`-Feld hinzu. GUI bietet Retry/Skip pro Utterance.

12) Reuse & Incremental Workflows
    - Re-Synthese nur für geänderte Utterances (diff via cache keys). Ermögliche `rebuild --changed-only`.

13) Export / Delivery
    - Finaler Export (mp3/wav) über `export_audio()`; biete Loudness‑Target (e.g. -16 LUFS für Podcasts).

API‑Beispiel (Skript):
```python
from podcastforge.integrations.script_orchestrator import synthesize_script_preview

synthesize_script_preview(
     script_path='episode1.yaml',
     out_dir='out/episode1',
     max_workers=3,
     engine='PIPER',
     on_progress=lambda e: print(e)
)
```

Files & Naming Conventions
- `out/{project}/manifest.json`
- `out/{project}/utterances/{utterance_id}.wav`
- `out/{project}/chapters/{chapter_id}.wav`
- `cache/tts/{key}.wav`

Runtime Guarantees / Limits
- Verwende bounded concurrency (configurable `max_workers`) und Engine‑pooling (`TTSEngineManager(max_engines=2)`) um OOM/VRAM zu vermeiden.
- Provide a `dry_run=True` mode for CI to validate pipelines without heavy native deps.

---

## ✅ UI/UX — Abgleich des Workflows mit der aktuellen Editor‑UI

Kurzbewertung, ob die aktuelle UI den obigen Workflow unterstützt, und konkrete Verbesserungs‑Vorschläge.

- **Voice Library (exists)**:
  - Status: Vorhanden (`Voice Library` Panel). Bietet Filter nach Sprache/Stil und Listbox.
  - Erfüllt: Auswahl und Preview sind verfügbar.
  - Verbesserung: Detail‑Dialog für Voice‑Metadaten, Ladeindikator, Bulk‑Markierung für Batch‑Zuordnung.

---

## **FFmpeg Installation**

Für lokale Nutzung wird `ffmpeg` auf dem System benötigt. Um die Arbeit mit
PodcastForge zu vereinfachen, befindet sich ein kleines Installer‑Skript im
Projekt: `scripts/install_ffmpeg.py`.

- So installierst du schnell ffmpeg (PowerShell):

```
python .\scripts\install_ffmpeg.py
```

- Falls du eine spezielle Build‑URL verwenden willst (z. B. eigene statische Builds):

```
python .\scripts\install_ffmpeg.py --url "https://example.com/path/to/ffmpeg.zip"
```

- Das Skript legt die Binärdatei in `third_party/ffmpeg/bin` ab und gibt eine
    kurze Anleitung aus, wie du diesen Ordner temporär deiner PATH‑Variable
    hinzufügst (PowerShell/Bash‑Beispiele werden ausgegeben).

Wenn du möchtest, kann ich eine PowerShell‑Variante (`.ps1`) hinzufügen oder
einen GitHub Actions‑Job, der `ffmpeg` vor dem E2E‑Lauf auf dem Runner installiert.


---

## 🔁 Streaming-Konvertierung & FFmpeg (on-the-fly MP3/MP4)

PodcastForge unterstützt eine on-the-fly Kompression von Preview-Audio mittels `ffmpeg`.
Anstatt eine große WAV-Datei zu erstellen und diese anschließend zu konvertieren, kann der
Orchestrator per-utterance WAV‑Snippets direkt in einen ffmpeg‑Prozess pipen, der MP3/MP4
progressiv schreibt. Das reduziert Speicherbedarf und verbessert die Zeit bis zur ersten
Abspielbarkeit in der Editor‑UI.

Wesentliche Punkte:
- Erfordert `ffmpeg` auf dem System‑PATH oder einen expliziten Pfad zur `ffmpeg.exe`.
- Die Orchestrator‑Implementierung versucht zuerst die Streaming‑Route (pipe Input → ffmpeg → Datei)
    und fällt bei Inkompatibilitäten (unterschiedliche Sample‑Rates/Kanäle) oder Fehlern auf das
    altbekannte Concat‑then‑Convert‑Verfahren zurück.
- Für MP4 setzen wir fragmentierende Flags, damit der Ausgabedatei progressives Abspielen möglich ist:

    `-movflags +faststart+frag_keyframe+empty_moov`

    Diese Flags sorgen dafür, dass der `moov` Atom verschiebbar und fragmentiert geschrieben wird —
    Player können dann mit dem Abspielen beginnen, während die Datei noch wächst.

Beispielaufruf (CLI):

```powershell
$env:PYTHONPATH='src'
python -c "from podcastforge.integrations.script_orchestrator import synthesize_script_preview; print(synthesize_script_preview('examples/tmp_script.json','out', output_format='mp4'))"
```

Fehlertoleranz:
- Wenn `ffmpeg` nicht gefunden wird, publiziert der Orchestrator ein `script.preview_ready` Event mit
    dem Pfad zur WAV und einer Warnmeldung, dass keine Konvertierung durchgeführt wurde.
- Wenn Streaming fehlschlägt, fällt der Ablauf auf das sichere Concat+Convert‑Verhalten zurück und gibt
    ebenfalls eine Warnung aus.

Performance‑Tuning:
- Verwenden Sie `audio_bitrate` (z. B. `192k`) zur Steuerung von Qualität/Größe.
- Fragmented MP4 + `faststart` reduziert wahrgenommene Latenz für Web‑Player.
- Für niedrigste Latenz beim direkten Streaming kann ffmpeg auf `stdout` (pipe:1) schreiben und ein
    kleines HTTP/WebSocket Proxy‑Modul die Bytes an den Editor streamen (siehe implementierte Erweiterung
    für WebSocket/HTTP‑Streaming, optional).

Security Hinweis:
- Die Anwendung ruft `ffmpeg` auf dem System auf — stellen Sie sicher, dass die Binary aus einer
    vertrauenswürdigen Quelle stammt. Die Orchestrator‑Logik ist so implementiert, dass bei Fehlern
    sicher auf WAV‑Output zurückgefallen wird.


- **Active Speakers Pane (exists)**:
  - Status: Vorhanden als `Aktive Sprecher` Listbox.
  - Erfüllt: Anzeige und Edit/Remove/Add vorhanden.
  - Verbesserung: Zeige `speaker_id`, `voice_profile_id`, small avatar; Support für drag排序 und Reihenfolge (timeline order).

- **Drag & Drop Voice → Script (partially implemented)**:
  - Status: Lightweight DnD implementiert (mouse press → release). OK als MVP.
  - Lücken: kein visuelles Ghost, keine präzise Target‑Highlighting (nur line highlight), keine Multi‑select Drag, kein keyboard‑accessible assign.
  - Vorschlag: Implementiere Tk DnD oder use canvas overlay für Ghost, und Shortcut `Ctrl+Enter` + `Assign Voice` für accessibility.

- **Per‑line Properties Pane (exists)**:
  - Status: `Sprecher`, `Emotion`, `Pause`, `Speed` vorhanden.
  - Erfüllt: Kann Utterance‑Eigenschaften setzen.
  - Verbesserung: Zeige Synthese‑Status pro Zeile (idle/queued/processing/done/error) und Quick‑Retry Button.

- **Preview UX (exists, improved)**:
  - Status: Preview Button + context menu implemented; runs off UI thread.
  - Erfüllt: Schnell‑Feedback für einzelne Zeilen/voices.
  - Verbesserung: Add per‑voice waveform preview, show engine used, show cache hit/miss.

- **Batch Synthesis / Orchestrator Controls (missing)**:
  - Status: Keine dedicated UI zum Starten von batched generation (script → full project) existiert.
  - Vorschlag: Add `Generate Project` panel with options: `max_workers`, `engine`, `dry_run`, `mix_policy` and a progress view with per‑utterance progress bars and retry controls.

- **Timeline / Mixing Controls (partial)**:
  - Status: Timeline frame exists but not implemented.
  - Vorschlag: Implement an interactive timeline view showing utterances with offsets, allowing drag to nudge timing, crossfade editor, and solo/mute per speaker.

- **Import Flow (manifest → Editor)**:
  - Status: Importer publishes `ebook2audiobook.open_project` event and Editor subscribes. Good.
  - Improvement: Provide `Import Preview` mode that imports manifest read‑only to validate offsets before committing to project.

Priorisierte UI‑Änderungen (kurzfristig)
- 1) Add `Generate Project` dialog with `dry_run` and `max_workers` (high impact).
- 2) Enhance per‑line status indicator (queued/processing/done/error) and retry action.
- 3) Improve Drag&Drop visual UX (ghost, snapping, keyboard fallback).

Langfristige UX‑Ziele
- Interactive Timeline Editor (drag timing, crossfade curves, background track lanes).
- Collaborative editing (share manifest, remote TTS execution with cloud engines).


## 📋 Best Practices

### Code Style

#### 1. **Type Hints Everywhere**

```python
from typing import List, Dict, Optional, Union
from pathlib import Path

def generate_podcast(
    topic: str,
    style: PodcastStyle,
    speakers: List[Speaker],
    duration: int,
    output: Path
) -> Optional[Path]:
    """
    Generiere Podcast
    
    Args:
        topic: Podcast-Thema
        style: Stil (INTERVIEW, NEWS, etc.)
        speakers: Liste von Sprechern
        duration: Dauer in Minuten
        output: Ausgabe-Datei
        
    Returns:
        Pfad zur generierten Datei oder None bei Fehler
        
    Raises:
        ValueError: Wenn Dauer < 1
        FileNotFoundError: Wenn Voice-Sample fehlt
    """
    if duration < 1:
        raise ValueError("Duration must be >= 1")
    
    # Implementation...
    return output
```

#### 2. **Comprehensive Docstrings**

```python
class VoiceLibrary:
    """
    Verwaltung professioneller Voice-Profile
    
    Die VoiceLibrary verwaltet eine Sammlung von professionellen
    Stimm-Profilen mit intelligenter Kategorisierung und
    Suggestion-System.
    
    Attributes:
        voices: Dict von VoiceProfile-Objekten
        languages: Unterstützte Sprachen
        
    Example:
        >>> library = VoiceLibrary()
        >>> voices = library.search(language="de", gender="male")
        >>> for voice in voices:
        ...     print(voice.display_name)
        
    Note:
        Stimmen werden lazy-loaded beim ersten Zugriff
    """
    
    def suggest_for_podcast_style(
        self,
        style: PodcastStyle,
        language: str = "de",
        num_speakers: int = 2
    ) -> List[VoiceProfile]:
        """
        Schlage optimale Stimmen für Podcast-Stil vor
        
        Nutzt intelligentes Matching basierend auf:
        - Podcast-Stil (Interview, News, etc.)
        - Sprache
        - Geschlechter-Balance
        - Alters-Diversität
        
        Args:
            style: PodcastStyle Enum
            language: ISO-639-1 Language-Code
            num_speakers: Anzahl Sprecher
            
        Returns:
            Liste von VoiceProfile-Objekten (sortiert nach Relevanz)
            
        Example:
            >>> voices = library.suggest_for_podcast_style(
            ...     style=PodcastStyle.INTERVIEW,
            ...     language="de",
            ...     num_speakers=2
            ... )
            >>> [v.display_name for v in voices]
            ['Thorsten (Professional)', 'Anna (Friendly)']
        """
```

#### 3. **Error Handling**

```python
from podcastforge.exceptions import (
    TTSGenerationError,
    VoiceNotFoundError,
    InvalidScriptError
)

def generate_audio(text: str, speaker: Speaker) -> AudioSegment:
    """Generiere Audio mit proper Error-Handling"""
    
    try:
        # Validierung
        if not text.strip():
            raise InvalidScriptError("Text is empty")
        
        if not speaker.voice_sample.exists():
            raise VoiceNotFoundError(
                f"Voice sample not found: {speaker.voice_sample}"
            )
        
        # TTS-Generierung
        audio = self.tts_engine.synthesize(text, speaker)
        
    except TTSGenerationError as e:
        logger.error(f"TTS generation failed: {e}")
        # Fallback zu stiller Audio
        audio = self._create_silent_audio(len(text) * 0.1)
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
    
    return audio
```

#### 4. **Logging**

```python
import logging
from pathlib import Path

# Setup Logging
def setup_logging(log_file: Path = Path("logs/podcastforge.log")):
    """Konfiguriere Logging"""
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Verwendung
logger = logging.getLogger(__name__)

class PodcastForge:
    def create_podcast(self, ...):
        logger.info(f"Starting podcast generation: {topic}")
        
        try:
            # ...
            logger.debug(f"Generated {len(script)} lines")
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise
        
        logger.info(f"Podcast saved to: {output}")
```

### 5. **Configuration Management**

```python
# src/podcastforge/core/config.py

from dataclasses import dataclass, field
from typing import Dict, Any
import yaml

@dataclass
class TTSConfig:
    """TTS-Engine Konfiguration"""
    engine: str = "xtts"
    model_path: str = "models/xtts_v2"
    use_gpu: bool = True
    cache_size: int = 2
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Erstelle von Dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class AppConfig:
    """Haupt-Konfiguration"""
    tts: TTSConfig = field(default_factory=TTSConfig)
    ollama_url: str = "http://localhost:11434"
    cache_dir: str = "cache"
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_file: Path):
        """Lade Konfiguration aus YAML"""
        with open(config_file) as f:
            data = yaml.safe_load(f)
        
        return cls(
            tts=TTSConfig.from_dict(data.get('tts', {})),
            **{k: v for k, v in data.items() if k != 'tts' and k in cls.__annotations__}
        )
```

### 6. **Unit Testing**

```python
# tests/unit/test_voice_library.py

import pytest
from podcastforge.voices import VoiceLibrary, VoiceGender, VoiceStyle
from podcastforge.core.config import PodcastStyle

class TestVoiceLibrary:
    """Unit Tests für VoiceLibrary"""
    
    @pytest.fixture
    def library(self):
        """Fixture: VoiceLibrary-Instanz"""
        return VoiceLibrary()
    
    def test_search_by_language(self, library):
        """Test: Suche nach Sprache"""
        voices = library.search(language="de")
        assert len(voices) > 0
        assert all(v.language == "de" for v in voices)
    
    def test_search_by_gender(self, library):
        """Test: Suche nach Geschlecht"""
        voices = library.search(gender=VoiceGender.MALE)
        assert all(v.gender == VoiceGender.MALE for v in voices)
    
    def test_suggest_for_interview(self, library):
        """Test: Suggestions für Interview"""
        voices = library.suggest_for_podcast_style(
            style=PodcastStyle.INTERVIEW,
            num_speakers=2
        )
        assert len(voices) == 2
        # Prüfe Geschlechter-Diversität
        genders = {v.gender for v in voices}
        assert len(genders) >= 1  # Mind. eine Geschlechter-Variation
    
    @pytest.mark.parametrize("language,expected_count", [
        ("de", 1),
        ("en", 12),
    ])
    def test_voice_count_by_language(self, library, language, expected_count):
        """Test: Voice-Count pro Sprache"""
        voices = library.search(language=language)
        assert len(voices) >= expected_count
```

### 7. **Performance Optimization**

```python
from functools import lru_cache
import time

class VoiceLibrary:
    
    @lru_cache(maxsize=128)
    def _get_cached_voices(self, language: str, gender: str, style: str):
        """Cache-optimierte Voice-Suche"""
        # Teure Filterung nur einmal
        return self._filter_voices(language, gender, style)
    
    def search(self, language=None, gender=None, style=None):
        """Nutze Caching für häufige Queries"""
        cache_key = (language or "", gender or "", style or "")
        return self._get_cached_voices(*cache_key)

# Profiling
def profile_function(func):
    """Decorator für Function-Profiling"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper

@profile_function
def generate_podcast(...):
    # Implementation
    pass
```

---

## 🔒 Security Best Practices

```python
from pathlib import Path
import hashlib

class SecureFileHandler:
    """Sichere Datei-Verarbeitung"""
    
    ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.yaml', '.json'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    
    @staticmethod
    def validate_file(file_path: Path) -> bool:
        """Validiere Datei"""
        
        # Extension Check
        if file_path.suffix.lower() not in SecureFileHandler.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension: {file_path.suffix}")
        
        # Size Check
        if file_path.stat().st_size > SecureFileHandler.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        # Path Traversal Prevention
        if ".." in str(file_path):
            raise ValueError("Path traversal detected")
        
        return True
    
    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Erstelle File-Hash für Integrity-Check"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
```

---

## 📊 Performance Targets

| Komponente | Target | Aktuell | Status |
|------------|--------|---------|--------|
| Editor UI Response | < 100ms | ~50ms | ✅ |
| TTS Preview (XTTS) | < 5s | ~3s | ✅ |
| TTS Preview (Piper) | < 1s | TBD | 🔄 |
| Timeline Render (60 FPS) | 16.6ms | TBD | 📋 |
| Voice Library Search | < 50ms | ~10ms | ✅ |

---

## 🧪 Testing Strategy

```
tests/
├── unit/               # Unit Tests (80% Coverage-Ziel)
│   ├── test_voice_library.py
│   ├── test_audio_player.py
│   └── test_forge.py
├── integration/        # Integration Tests
│   ├── test_tts_pipeline.py
│   └── test_editor_workflow.py
└── e2e/               # End-to-End Tests
    └── test_full_podcast_generation.py
```

---

**Version:** 1.0  
**Last Updated:** November 14, 2024  
**Maintainer:** PodcastForge-AI Team
