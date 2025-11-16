# Contributing to PodcastForge-AI

Vielen Dank für dein Interesse, zu PodcastForge-AI beizutragen! 🎉

## Wie kann ich beitragen?

### 1. Issues erstellen

- 🐛 **Bug Reports**: Beschreibe das Problem detailliert
- 💡 **Feature Requests**: Schlage neue Features vor
- 📝 **Dokumentation**: Verbesserungsvorschläge für Docs

### 2. Pull Requests

1. **Fork das Repository**
   ```bash
   git clone https://github.com/makr-code/PodcastForge-AI.git
   cd PodcastForge-AI
   ```

2. **Erstelle einen Branch**
   ```bash
   git checkout -b feature/mein-feature
   ```

3. **Installiere Dev-Dependencies**
   ```bash
   make install-dev
   ```

4. **Mache deine Änderungen**
   - Folge dem bestehenden Code-Stil
   - Füge Tests hinzu für neue Features
   - Update die Dokumentation

5. **Teste deine Änderungen**
   ```bash
   make test
   make lint
   make format
   ```

6. **Commit und Push**
   ```bash
   git commit -m "feat: Beschreibung der Änderung"
   git push origin feature/mein-feature
   ```

7. **Erstelle einen Pull Request**

## Code-Standards

- **Python 3.8+** Kompatibilität
- **Black** für Code-Formatierung
- **Type Hints** wo sinnvoll
- **Docstrings** für alle öffentlichen Funktionen (Google-Style)
- **Tests** für neue Features

## Commit-Messages

Wir folgen [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Neues Feature
- `fix:` Bugfix
- `docs:` Dokumentation
- `style:` Formatierung
- `refactor:` Code-Refactoring
- `test:` Tests
- `chore:` Wartung

Beispiele:
```
feat: Add support for custom voice samples
fix: Resolve audio export issue with MP3 format
docs: Update installation guide for Windows
```

## Testing

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=podcastforge

# Spezifische Tests
pytest tests/test_forge.py
```

## Dokumentation

- `README.md` für Hauptdokumentation
- Docstrings im Google-Style
- Beispiele in `/examples`
- Guides in `/docs/guides`
 - **Dokumentationspflicht & PR-Template:** Bitte nutze `docs/todo.md` als Leitfaden für Dokumentationspflichten und die PR-Dokumentationsvorlage.
 - **Copilot / Assistenz-Richtlinie:** Automatisierte Assistenten (z. B. GitHub Copilot) sollten sich an die Vorgaben in `./.github/indroduction` halten. Änderungen, die automatisch vorgeschlagen wurden, müssen in der PR-Beschreibung klar ausgewiesen werden.

## Pull Request Hinweise

- Nutze die in `docs/todo.md` beschriebene PR-Template (Kurzbeschreibung, Motivation, Tests, Dokumentation, Migrationshinweise).
- Wenn Änderungen CLI-Flags, API-Signaturen oder Konfigurationsoptionen betreffen, dokumentiere die Änderungen in `docs/guides/` und aktualisiere `README.md` falls nötig.

## Fragen?

Erstelle ein [Issue](https://github.com/makr-code/PodcastForge-AI/issues) oder starte eine [Discussion](https://github.com/makr-code/PodcastForge-AI/discussions)!

## Code of Conduct

Sei freundlich und respektvoll. Wir wollen eine einladende Community für alle schaffen.
