import shutil
from pathlib import Path
import time

p = Path.home() / '.cache' / 'suno' / 'bark_v0'
print('Target cache path:', p)
if not p.exists():
    print('Cache dir not present')
    exit(0)

bak = p.with_name(p.name + '.disabled')
# if bak exists, append timestamp
if bak.exists():
    bak = p.with_name(p.name + '.disabled.' + str(int(time.time())))

try:
    p.rename(bak)
    print('Renamed cache to:', bak)
    exit(0)
except Exception as e:
    print('Rename failed:', e)
    # try rmtree
    try:
        shutil.rmtree(p)
        print('Removed cache dir')
        exit(0)
    except Exception as e2:
        print('Failed to remove cache dir:', e2)
        exit(2)
