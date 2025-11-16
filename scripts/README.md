Spatialize scripts — Kurzanleitung
=================================

Zweck
-----
Die `scripts/`-Tools enthalten experimentelle Hilfen, um mono‑Utterances in
realistischere Stereo‑Vorschaudateien (44.1 kHz) zu verwandeln. Ziel ist es,
die Editor‑Vorschau und die generierten Previews räumlich zu platzieren (ILD,
ITD, Distanz‑Absorption, optionale IR‑Convolution) und anschließend ein
normalized MP3/MP4 Preview zu erzeugen.

Wichtige Dateien
-----------------
- `scripts/spatialize.py` — CLI + programmatische Funktion `spatialize_mono_to_stereo()`.
- `scripts/spatialize_batch.py` — Batch‑Runner, der mehrere Sprecher/Utterances
  räumlich anordnet, pro‑Sprecher Dateien erzeugt und einen Stereo‑Master mischt.
- `scripts/generate_example_irs.py` — Erzeugt simple Beispiel‑IRs unter
  `third_party/irs/` (small_room, large_room, hrtf_example).
- `scripts/spatialize_test_config.json` — Beispielkonfiguration für den Batch‑Runner.

Abhängigkeiten
--------------
- Python: `numpy`, `scipy`, `soundfile` (pysoundfile).
- Optional: `librosa` für qualitativ hochwertiges Resampling (falls installiert.
  sonst wird `scipy.signal.resample_poly` verwendet).
- FFmpeg: Wird nur für Normalisierung/MP3/MP4 Encoding benötigt. Entweder
  auf dem PATH verfügbar machen oder das Repo‑bundled `third_party/ffmpeg/bin`
  nutzen (die Helpers suchen automatisch dort).

Single‑File Spatialize — Beispiele
---------------------------------
Spatialize eine mono WAV und erzeuge eine Stereo WAV:

```powershell
python scripts\spatialize.py --input path\to\mono.wav --out_wav out\stereo.wav --azimuth -30 --distance 1.2
```

Mit anschließender Loudness‑Normalisierung (erzeugt MP3, benötigt `ffmpeg`):

```powershell
python scripts\spatialize.py --input path\to\mono.wav --out_wav out\stereo.wav --azimuth -30 --distance 1.2 --normalize -16 --out_mp3 out\stereo_normalized.mp3
```

Batch‑Verarbeitung (Beispielkonfig):
----------------------------------
Nutze die Beispielkonfiguration `scripts/spatialize_test_config.json` oder erstelle
eine eigene JSON Datei mit folgendem Schema (vereinfachte Ansicht):

- `speakers`: Liste von Speakern; jeder Speaker hat `name` und optional `azimuth`, `distance`.
- `utterances`: Liste von Einträgen mit `speaker`, `file` (Pfad zur mono WAV) und `start_offset` (optional).
- `output_dir`: Verzeichnis für erzeugte Dateien.

Ausführen:

```powershell
python scripts\spatialize_batch.py --config scripts\spatialize_test_config.json
```

Programmatische Nutzung
-----------------------
Die Orchestrator‑Funktion `podcastforge.integrations.script_orchestrator.synthesize_script_preview`
unterstützt nun optionale Parameter zur Spatialization:

- `spatialize` (bool): ob spatialize angewendet werden soll.
- `spatial_params` (dict): Konfiguration mit `default`, `per_speaker`, `per_idx`.
- `spatial_target_sr` (int): Ziel‑Sample‑Rate (standard: 44100).

Beispiel Aufruf:

```python
from podcastforge.integrations.script_orchestrator import synthesize_script_preview
res = synthesize_script_preview('script.json', 'out', cache_dir='out/cache', spatialize=True, spatial_params={'default':{'azimuth':-20,'distance':1.2}})
```

Schema für `spatial_params`
---------------------------
- `default`: globale Defaults, z. B. `{'azimuth': -20, 'distance': 1.2}`
- `per_speaker`: Mapping von Speaker‑Name → params, z. B.
  `{'Host': {'azimuth': -30}, 'Guest': {'azimuth': 30}}`
- `per_idx`: Mapping von `idx` (als String) → params, z. B. `{'3': {'azimuth': 0}}`

Editor‑Integration
------------------
- Im Editor (`src/podcastforge/gui/editor.py`) gibt es eine `Spatialize` Checkbox
  in der Audio‑Vorschau (rechte Panel). Zusätzlich kleine Eingabefelder für
  `Az` (Azimuth) und `Dist` (Distance). Diese Werte werden als `spatial_params`
  an `synthesize_script_preview()` weitergereicht.

Hinweise & Troubleshooting
--------------------------
- Loudness/NORMALIZE: Das Skript versucht eine two‑pass `ffmpeg loudnorm`.
  Manche ffmpeg Builds geben die Messwerte in stderr in einem anderen Format;
  es gibt einen Single‑Pass Fallback (funktioniert zuverlässig).
- Resampling: Ziel‑SR ist 44100 Hz; bei Bedarf kann `librosa` installiert
  werden, um die Resampling‑Qualität zu verbessern.
- Wenn `ffmpeg` nicht gefunden wird, legt der Orchestrator standardmäßig eine
  WAV‑Vorschau ab und gibt eine Warnung zurück.

Weitere Schritte
----------------
- Erweiterung der `spatialize` Logik um realistischere Mikrofon‑Patterns und
  HRTF‑Konvolution (optional). 
- Dokumentation in `docs/ARCHITECTURE.md` verlinken (kurzer Hinweis bereits vorhanden).

Kontakt
-------
Wenn du möchtest, kann ich die README noch mit Beispielen aus deinem Projekt
anreichern (z. B. typische `spatial_params` für Host/Guest), oder die
`docs/ARCHITECTURE.md` um eine detailliertere Sektion erweitern.
