#!/usr/bin/env python3
import sys,os
fp = os.path.join('out','example','script_preview.mp4')
if not os.path.exists(fp):
    print('MISSING', fp); sys.exit(1)
with open(fp,'rb') as f:
    data = f.read()
found = []
for token in (b'mp4a', b'aac ', b'AC-3', b'mp3 ', b'Opus'):
    if token in data:
        found.append(token.decode('latin1'))
print('size_bytes=', os.path.getsize(fp))
print('contains_atoms=', found)
# simple heuristic: search for 'mdat' box size
# find 'mdat' occurrences and print surrounding bytes
for i in range(len(data)):
    if data[i:i+4]==b'mdat':
        start=max(0,i-20)
        print('mdat@', i, data[start:i+20])
        break
print('done')
