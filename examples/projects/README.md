# PodcastForge Editor - Beispiel-Projekte

Diese Beispiele zeigen verschiedene Podcast-Formate und Skript-Stile.

## 📁 Verfügbare Beispiele

### 1. `simple_example.txt` - Structured Format
**Stil:** Einfaches Interview  
**Format:** Structured Text (am einfachsten!)  
**Dauer:** ~2 Minuten  
**Sprecher:** 2

Ideal für Einsteiger - zeigt das einfache Text-basierte Format:
```
Host [excited]: Willkommen! [0.8s]
Gast [neutral]: Danke! [0.5s]
```

### 2. `interview_example.yaml` - Interview-Podcast
**Stil:** Professionelles Interview  
**Format:** YAML  
**Dauer:** ~5 Minuten  
**Sprecher:** Host + Dr. Anna Müller (KI-Forscherin)

Vollständiges Interview über künstliche Intelligenz mit:
- Natürliche Gesprächsführung
- Verschiedene Emotionen
- Professionelle Pausen
- Experten-Content

### 3. `educational_example.yaml` - Bildungs-Podcast
**Stil:** Lern-Format  
**Format:** YAML  
**Dauer:** ~4 Minuten  
**Sprecher:** Lehrer + Schüler

"Physik für Anfänger" - Erklärt warum der Himmel blau ist:
- Didaktischer Aufbau
- Frage-Antwort-Stil
- Verständliche Erklärungen
- Motivierende Emotionen

### 4. `news_example.json` - Nachrichten-Podcast
**Stil:** Tech-News  
**Format:** JSON  
**Dauer:** ~3 Minuten  
**Sprecher:** 2 Nachrichtensprecher

Tech News Daily mit aktuellen Meldungen:
- Professioneller News-Stil
- Kurze, prägnante Sätze
- Neutrale Emotionen
- Strukturierte Themen

## 🚀 Verwendung

### Im Editor öffnen
```bash
# Starte Editor mit Beispiel
podcastforge edit examples/projects/interview_example.yaml

# Oder manuell im Editor: Datei → Öffnen → Beispiel auswählen
```

### Direkt zu Audio konvertieren
```bash
# Mit PodcastForge CLI
podcastforge generate-from-script examples/projects/interview_example.yaml \
    --output mein_podcast.mp3
```

### Als Template verwenden
```bash
# Kopiere Beispiel als Ausgangspunkt
cp examples/projects/interview_example.yaml mein_projekt.yaml

# Bearbeite mit Editor
podcastforge edit mein_projekt.yaml
```

## 📝 Format-Vergleich

### Structured Format (`.txt`)
**Vorteile:**
- ✅ Am einfachsten zu schreiben
- ✅ Keine Syntax-Kenntnisse nötig
- ✅ Schnell für kurze Podcasts

**Nachteile:**
- ❌ Weniger Meta-Informationen
- ❌ Schwerer zu parsen

**Beispiel:**
```
Host [excited]: Hallo Welt! [0.8s]
```

### YAML Format (`.yaml`)
**Vorteile:**
- ✅ Sehr lesbar
- ✅ Vollständige Meta-Daten
- ✅ Gut für Versionskontrolle
- ✅ Unterstützt Kommentare

**Nachteile:**
- ❌ Indentation-sensitiv

**Beispiel:**
```yaml
script:
  - speaker: Host
    text: Hallo Welt!
    emotion: excited
    pause_after: 0.8
```

### JSON Format (`.json`)
**Vorteile:**
- ✅ Programmatisch einfach zu verarbeiten
- ✅ Strikte Struktur
- ✅ Ideal für APIs

**Nachteile:**
- ❌ Weniger menschenlesbar
- ❌ Keine Kommentare möglich

**Beispiel:**
```json
{
  "script": [
    {
      "speaker": "Host",
      "text": "Hallo Welt!",
      "emotion": "excited",
      "pause_after": 0.8
    }
  ]
}
```

## 🎨 Emotionen-Referenz

Alle Beispiele nutzen diese Emotionen:

- `neutral` - Standard, sachlich
- `excited` - Begeistert, energetisch
- `thoughtful` - Nachdenklich, überlegend
- `serious` - Ernst, wichtig
- `humorous` - Humorvoll, witzig
- `dramatic` - Dramatisch, intensiv
- `friendly` - Freundlich, warm
- `professional` - Professionell, geschäftlich
- `curious` - Neugierig, interessiert
- `enthusiastic` - Enthusiastisch, leidenschaftlich
- `explanatory` - Erklärend, lehrend
- `concerned` - Besorgt, vorsichtig
- `optimistic` - Optimistisch, hoffnungsvoll
- `grateful` - Dankbar, wertschätzend

## 🎯 Pausen-Guide

**Natürliche Pausen:**
- `0.3-0.4s` - Zwischen Satzteilen
- `0.5-0.6s` - Am Satzende
- `0.7-0.8s` - Nach Fragen
- `0.9-1.2s` - Bei Themenwechsel
- `1.5-2.0s` - Zwischen Szenen

## 💡 Tipps zum Anpassen

### Sprecher ändern
```yaml
speakers:
  - name: MeinHost        # Ändere Namen
    voice: thorsten       # Nutze andere Voice aus Library
    description: Mein Moderator
```

### Länge anpassen
- Mehr/weniger Zeilen hinzufügen
- Pausen verkürzen/verlängern
- Dialog-Dichte ändern

### Stil anpassen
```yaml
style: discussion  # Ändere zu: interview, news, educational, etc.
```

### Sprache wechseln
```yaml
language: en  # Englisch statt Deutsch
speakers:
  - voice: david_attenborough  # Englische Voice
```

## 🔧 Fehlersuche

### Editor öffnet Beispiel nicht
1. Prüfe Dateipfad
2. Stelle sicher, dass Format korrekt ist
3. Validiere YAML/JSON Syntax

### TTS-Fehler
1. Prüfe, ob alle Voices verfügbar sind
2. Teste mit `podcastforge voices`
3. Nutze fallback-Voices

### Audio-Qualität
1. Passe Pausen an
2. Variiere Emotionen
3. Nutze professionelle Voices aus Library

## 📚 Weitere Ressourcen

- **Editor-Guide**: `docs/EDITOR_GUIDE.md`
- **Voice Library**: `podcastforge voices`
- **CLI-Hilfe**: `podcastforge --help`
- **Dokumentation**: `README.md`

---

**Viel Erfolg beim Erstellen deines ersten Podcasts! 🎙️**
