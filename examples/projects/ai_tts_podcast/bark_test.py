import os
import numpy as np
import wave

try:
    from bark import generate_audio, SAMPLE_RATE
except Exception as e:
    print('Failed to import bark:', e)
    raise

text = "Hallo, das ist ein kurzer Bark-Test. Wenn diese Datei erzeugt wird, funktioniert Bark."
print('Generating audio...')
audio = generate_audio(text)
arr = np.array(audio)
if arr.ndim == 2 and arr.shape[1] == 1:
    arr = arr[:, 0]
# clamp
arr = np.clip(arr, -1.0, 1.0)
arr_int16 = (arr * 32767).astype(np.int16)

outdir = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(outdir, exist_ok=True)
outpath = os.path.join(outdir, 'bark_test.wav')
with wave.open(outpath, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(arr_int16.tobytes())

print('Wrote', outpath)
