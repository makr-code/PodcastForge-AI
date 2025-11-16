# Engine Management (Kurzguide)

Diese kurze Anleitung erklärt, wie `TTSEngineManager` sicher und effizient verwendet
werden sollte. Sie konzentriert sich auf zwei Patterns:

- `get_engine(...)` — niedriger Level, manuelles Management
- `use_engine(...)` — empfohlener Context-Manager für deterministische Nutzung

## Wann `use_engine` verwenden

- Für kurzlebige oder begrenzte Operationen (z. B. Generieren eines Podcasts oder Previews).
- Wenn mehrere Threads gleichzeitig Engines verwenden könnten.
- Wenn deterministisches Freigeben von GPU/CPU-Ressourcen wichtig ist.

Beispiel (empfohlen):

```python
from podcastforge.tts.engine_manager import get_engine_manager, TTSEngine

mgr = get_engine_manager(max_engines=2)
with mgr.use_engine(TTSEngine.BARK, config={"model": "v2"}) as engine:
    audio = engine.synthesize("Hello world", speaker="v2/en_speaker_6")
# Nach dem with-Block: automatische Release/Unload bei letzter Referenz
```

## Wann `get_engine` noch Sinn macht

- Beim langfristigen Halten einer Engine über weite Teile der Anwendung.
- Für Tests, Debugging oder wenn man explizit volle Kontrolle über Cache/Eviction möchte.

Beispiel (manuell):

```python
mgr = get_engine_manager(max_engines=2)
engine = mgr.get_engine(TTSEngine.PIPER)
try:
    audio = engine.synthesize("Preview", speaker="0")
finally:
    # Optional: manuelles Unload aller Engines
    mgr.unload_all()
```

## Verhalten und Guarantees

- `use_engine` erhöht intern einen Referenzzähler für den Engine-Key.
- `release_engine` reduziert den Zähler; bei 0 wird die Engine entladen.
- Manager-Operationen sind thread-safe (RLock benutzt).
- LRU-Eviction kann auftreten, wenn die maximale Anzahl geladener Engines überschritten wird.

## Troubleshooting

- Wenn `use_engine` eine Exception beim Laden wirft, prüfe Logs und Fallback-Mechanismen.
- Bei Race-Conditions: prüfe, ob der gleiche Engine-Key mit unterschiedlichen `config`-Objekten
  erzeugt wird; der Cache-Key wird aus `engine_type` + Hash(gezogener config-items) gebildet.

## Empfehlung

- Verwende `use_engine` als Standard für alle kurzlebigen Engine-Zugriffe.
- Nutze `get_engine` nur, wenn du Engines bewusst persistieren möchtest.
