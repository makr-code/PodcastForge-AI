## YAML-Schema: Regieanweisung / Drehbuch für PodcastForge

Dieses Dokument definiert eine robuste, aber einfache YAML-Struktur für Drehbücher/Regieanweisungen, die sich direkt in den polyphonen Workflow einspeisen lässt. Ziel: sowohl menschlich lesbar als auch vollständig genug für automatisierte Verarbeitung (Parser → Utterances → TTS‑Orchestrator).

Beispiel (kommentiert):

```yaml
project:
  id: "episode-2025-11-15"
  title: "Titel der Episode"
  subtitle: "Kurzer Untertitel"
  language: "de"
  sample_rate: 22050
  metadata:
    author: "Redaktion"
    created_at: "2025-11-15T12:00:00Z"

sections:
  - id: "intro"
    title: "Intro"
    description: "Musikalische Einleitung und Begrüßung"
    items:
      - type: "direction"
        id: "intro_music"
        text: "Fade in: Hintergrundmusik 'theme_intro.mp3' (0.0 -> 8.0s)" 
        when: { start: 0.0 }

      - type: "utterance"
        id: "u1"
        speaker: "host"
        voice_hint: { style: "professional", gender: "male" }
        emotion: "friendly"
        text: "Willkommen bei unserem Podcast über Technik und Gesellschaft."
        pause_after: 0.6
        meta: { importance: "high" }

      - type: "direction"
        id: "cue_read"
        text: "Schnitt: nach kurzer Pause, Musik leiser fahren"

  - id: "chapter-1"
    title: "Interview mit Max"
    items:
      - type: "utterance"
        id: "u2"
        speaker: "guest_max"
        voice_hint: { profile: "max_voice_id", engine: "PIPER" }
        emotion: "thoughtful"
        text: "Danke, dass ich hier sein darf."
        pause_after: 0.5
        timing: { earliest: 5.0 }

      - type: "direction"
        id: "note_1"
        text: "Regie: Stimme leicht zurücknehmen, leichte Reverb"

speakers:
  - id: "host"
    name: "Host"
    voice_profile: "host_voice_01"
    role: "anchor"

  - id: "guest_max"
    name: "Max Mustermann"
    voice_profile: "max_voice_id"

assets:
  music:
    - id: "theme_intro"
      path: "assets/music/theme_intro.mp3"

notes:
  - "Dieses Format ist absichtlich pragmatisch: 'items' kann sowohl Regieanweisungen als auch Utterances aufnehmen."
```


Schema‑Erklärung (Kurz):
- `project`: Metadaten der Episode (language, sample_rate, timestamps).
- `sections`: Logische Gliederung (Kapitel/Abschnitte). Jedes Section enthält `items`.
- `items`: Liste mit Einträgen vom Typ `utterance` oder `direction` (oder `marker`, `sound_effect`).
  - `utterance`: enthält `id`, `speaker` (verweis auf `speakers`), `text`, optionale `voice_hint`, `emotion`, `pause_after`, `timing` und `meta`.
  - `direction`: Freitext-Regieanweisung, kann `when` (time cue) oder `target` (channel/track) enthalten.
- `speakers`: Projektweite Sprecher-Definitionen (canonical mapping zu VoiceLibrary IDs).
- `assets`: Verzeichnisreferenzen für Musik / FX.

Integrationsempfehlungen für Parser/Orchestrator
- Beim Einlesen: Erzeuge stabile `utterance.id` (falls fehlend) mittels `sha256(section_id + index + short_text)`.
- Erzeuge Draft‑Manifest `out/{project}/draft_manifest.yaml` nach Ingestion + User‑Edit.
- Unterstütze `voice_hint.profile` oder `voice_hint.style` und mappe zu `voice_profile_id` via `VoiceLibrary`.


---

UI/UX Struktur für Darstellung & Editierfunktionen

Ziel: Das UI soll die Schritte des Workflows (Ingest → User Edit → Assign → Synthesize) klar abbilden und gleichzeitig schnelle, atomare Aktionen ermöglichen.

Hauptbereiche (Panels)
- `Project Header` (oben): Titel, Subtitle, Sprache, Sample Rate, Quick Actions (Save Draft, Generate Project, Dry Run).
- `Left: Voice & Speakers`:
  - Voice Library Filter (Sprache, Stil), Voice List, Context Menu (Preview, Assign), Bulk select.
  - Active Speakers List: drag reorder, edit speaker properties, quick-add from Voice.
- `Center: Script Editor / Section View`:
  - Sektionale Ansicht: Sections collapsible. Jede Section zeigt `items` in Reihenfolge.
  - Item Types:
    - `Direction`: inline editable Regie-Text, optional cue timing field.
    - `Utterance`: editor line with fields: Speaker (dropdown), Emotion (icon), Text (editable multiline), Pause (spinbox), Quick Preview (▶), Status Badge (idle/queued/processing/done/error).
  - Inline Controls: drag handle (to reorder within section), speaker pill (shows assigned speaker, click to change), edit icon, trash.
  - Undo/Redo support for text edits.
- `Right: Inspector / Properties`:
  - Shows properties for selected item (utterance or direction) with granular controls: voice_hint dropdown (suggested voices), engine selection, per-item postproc flags (normalize, trim), and manual offset adjustment for timeline.
- `Bottom: Timeline / Progress`:
  - Visual timeline showing utterance bars with offsets and durations (zoomable). Allows drag-nudge, crossfade handle, mute/solo lanes per speaker.
  - Below timeline: batch progress view during generation with per-utterance progress bars and retry buttons.

Key Interactions
- Drag & Drop:
  - Voice → Utterance: assigns speaker (creates Speaker if missing) and shows a transient highlight + snackbar confirmation.
  - Reorder Utterances: drag handle in center view.
- Inline Preview:
  - Click ▶ on an Utterance to synthesize a short preview (runs off UI thread). Show waveform and play controls in inspector.
- Bulk Actions:
  - Select multiple items (shift/ctrl) and Assign Voice / Mark Skip / Export selection.
- Generate Project Dialog:
  - Config: `max_workers`, `engine`, `dry_run`, `mix_policy` (concat/crossfade/ducking), `background_track`.
  - On start: open progress modal with per-utterance rows, cancel button, and log stream.

Accessibility & Shortcuts
- Shortcuts:
  - `F5` – Preview current utterance
  - `Ctrl+Enter` – Insert new line/utterance
  - `Ctrl+S` – Save draft
  - `G` – Open Generate Project dialog (when focused)
- Keyboard navigation: arrow keys to move between utterances, space to toggle preview/play.

Persistence & Drafting
- Autosave draft manifest every N seconds to `out/{project}/draft_manifest.yaml` and on major actions (assign, reorder, edit).
- Provide `Compare Draft vs Generated` view to see which utterances were re-synthesized (cache hits/misses).

Error Handling UX
- Per‑utterance error badge with message & `Retry` button.
- Global `Problems` pane listing failed utterances and suggested fixes (e.g., missing voice profile, engine OOM).

Developer Hooks / Events
- `EventBus.publish('script.ingested', {manifest: path})` → opens Editor in Draft Mode.
- `EventBus.publish('script.tts_progress', {...})` → update per-utterance progress.
- `EventBus.publish('script.preview_ready', {...})` → inspector shows waveform and play control.

Design Notes / Rationale
- Keep editor minimal for quick edits (focus mode) but provide power tools (timeline, batch generation) for finalization.
- Prefer explicit user actions for destructive operations (delete, re-synthesize many) and show estimated cost/time for batch ops.

---

Wenn du möchtest, implementiere ich als nächstes eine einfache `Draft Pane` in `editor.py` (List view of utterances from ingestion) plus the `Generate Project` dialog skeleton. Soll ich das direkt anlegen? 
