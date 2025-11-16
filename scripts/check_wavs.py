#!/usr/bin/env python3
import wave, contextlib, os
p = os.path.join('out', 'example', 'cache')
if not os.path.isdir(p):
    print('No cache dir:', p); raise SystemExit(1)
files = sorted(os.listdir(p))
print('file,count=', len(files))
for f in files:
    fp = os.path.join(p, f)
    try:
        with contextlib.closing(wave.open(fp, 'rb')) as wf:
            sr = wf.getframerate(); nch = wf.getnchannels(); sampw = wf.getsampwidth(); frames = wf.getnframes(); dur = frames / float(sr)
            print(f, 'sr=', sr, 'ch=', nch, 'sampw=', sampw, 'dur={:.3f}s'.format(dur), 'size=', os.path.getsize(fp))
    except Exception as e:
        print(f, 'ERR', e)
