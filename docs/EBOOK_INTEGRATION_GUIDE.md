**Ebook -> Podcast Integration Guide**

Ziel
- Vorlage und Anleitung, wie Teile aus `ebook2audiobook` als Basis für eine
  gezielte Podcast-Integration verwendet werden können. Fokus: Kapitel- und
  Absatzweise Verarbeitung, TTS-Orchestrierung pro Einheit und einfache
  Integration in die PodcastForge-Pipeline.

Package
- `src/podcastforge/integrations/ebook2audiobook` enthält:
  - `api.py` — Adapter, die die upstream-CLI oder util-Funktionen nutzen.
  - `orchestrator.py` — Template-Funktionen: Kapitel-Extraktion, Paragraph-Splitting und `generate_podcast_from_ebook`.
  - `__init__.py` — Exports.

Arbeitsweise (Empfohlen)
1. Klone upstream-Repo in `third_party/ebook2audiobook` (oder nutze `setup.sh`).
2. Verwende `orchestrator.generate_podcast_from_ebook(..., per_paragraph=True)`
   um eine strukturierte Planliste (Kapitel/Absatz) zu erhalten.
3. Für jedes Element im Plan rufst du deinen TTS-Service an (z. B. vorhandene
   PodcastForge-TTS-Engine) und speicherst die erzeugten Audioclips als Clips
   (z. B. in `src/podcastforge/projects/{project}/audio/`).
4. Optional: benutze `api.run_upstream_cli()` wenn du die komplette upstream
   Pipeline benötigst (viele Abhängigkeiten erforderlich).

Designentscheidungen
- Orchestrator ist bewusst leichtgewichtig: es baut eine Plan-Schicht, aber
  delegiert die tatsächliche TTS-Erzeugung an die existierende PodcastForge
  TTS-Engines (so bleibt Kontrolle über Stimmen, Speed, Emotion und Mix).
- Kapitel/Absatz-Granularität ermöglicht: Kapitel-Intro, Kapitel-Fußnoten,
  oder feingranulares Audiobook-to-Podcast Mapping (z. B. kurze Snippets als
  Segmente für Multitrack).

Erweiterungsvorschlag
- Implementiere `orchestrator.to_podcast_project(project, plan)` — erzeugt
  ein PodcastForge-Projekt aus der Plan-Liste (erstellt Clips, Tracks, Metadaten).
- Füge optionale Post-Processing-Schritte hinzu: Normalize, Silence-Removal,
  Kapitel-Marker (Timeline markers) und Kapitel-Intro-Templates.

Beispiel
- Demo-Skript: `examples/ebook_to_podcast_demo.py` (zeigt dry-run Plan-Erzeugung).
- Adapter-Demo: `examples/ebook2audiobook_demo.py` zeigt basics der Adapter-API.

Hinweis zu Abhängigkeiten
- Voller Funktionsumfang verlangt oft native Tools und Python-Packages. Für
  Entwicklung teste zuerst mit `dry_run=True` oder einem minimalen EPUB-Parser.
