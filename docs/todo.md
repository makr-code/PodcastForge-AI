# Dokumentationspflicht & ToDo-Vorlage

Diese Datei beschreibt, welche Dokumentationspflichten bei Änderungen im Projekt einzuhalten sind und bietet eine kurze Vorlage, die in PR-Beschreibungen oder Issues verwendet werden kann.

## Wann Dokumentieren?
- Jede Änderung, die API-Signaturen, CLI-Optionen, Konfigurationsdateien oder das Verhalten der GUI verändert, muss dokumentiert werden.
- Neue Features benötigen:
  - Eine kurze Erklärung in `docs/` (z. B. `docs/guides/<feature>.md`).
  - Ein Beispiel in `examples/` oder einen Code-Snippet in der Dokumentation.
  - Falls relevant: Update von `pyproject.toml`/`requirements*.txt` für Abhängigkeiten.
- Bugfixes müssen in `CHANGELOG.md` (wenn vorhanden) oder in der PR-Beschreibung dokumentiert werden.

## Minimalanforderungen für PRs
- PR-Description muss enthalten:
  - **Kurzbeschreibung**: Was wurde geändert?
  - **Warum**: Motivation / Problemstellung.
  - **Auswirkungen**: Betroffene Module/APIs/Komponenten.
  - **Testing**: Welche Tests wurden ausgeführt (Unit/Manuell)?
  - **Dokumentation**: Welche Dateien wurden aktualisiert oder neu hinzugefügt?

## ToDo / Documentation Template (für PRs)

```
# PR Documentation Template

## Titel
Kurze, prägnante Zusammenfassung der Änderung

## Beschreibung
- Was: (Kurzbeschreibung)
- Warum: (Motivation)
- Wie: (Implementations-Highlights)

## Betroffene Dateien / Module
- `src/podcastforge/...`

## Tests
- Unit tests: (ja/nein) — falls ja, welche
- Manuelle Tests: (Kurzbeschreibung)

## Dokumentation
- Neue oder geänderte Dokus:
  - `docs/guides/<file>.md`
  - `examples/<example>.py`

## Migrationshinweise
- (Wenn API-Änderungen vorhanden sind)

## Sonstiges
- (Optional)
```

## Zusätzliche Hinweise für Entwickler
- Ergänze `docs/` mit praxisnahen Anleitungen — kurze Beispiele sind wichtiger als lange Erklärungen.
- Bei Änderungen an Integrationen (z. B. `ebook2audiobook`) dokumentiere optionale Abhängigkeiten (`pydub`, `ffmpeg`, `ebooklib`) und mögliche Fallbacks.
- Verwende die `./.github/indroduction` als Style-Guide für automatische Assistenten und CI-Aktionen.

---

Diese Datei hilft, die Dokumentationsqualität stabil zu halten. Bitte halte sie bei Bedarf aktuell.
