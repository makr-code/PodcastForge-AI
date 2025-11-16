import inspect, torch
import traceback

try:
    import bark
except Exception as e:
    print('Failed to import bark:', e)
    raise

print('bark module:', bark)
print('preload_models signature:', inspect.signature(bark.preload_models))

import numpy.core.multiarray as m
print('multiarray.scalar exists:', hasattr(m, 'scalar'))

orig = torch.load
print('orig torch.load:', orig)


def wrapped(f, *a, **k):
    if 'weights_only' not in k:
        k['weights_only'] = False
    return orig(f, *a, **k)

try:
    torch.load = wrapped
    print('Calling preload_models with patched torch.load (device=cpu) ...')
    bark.preload_models(device='cpu')
    print('preload_models succeeded')
except Exception as e:
    print('preload_models raised:')
    traceback.print_exc()
finally:
    torch.load = orig
    print('Restored torch.load')
