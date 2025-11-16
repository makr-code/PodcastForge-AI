import sys
print('PYTHON', sys.executable)
print('start')
try:
    import torch
    print('TORCH_OK', torch.__version__, getattr(torch, '__file__', '<no __file__>'))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR', e)
input('press Enter to exit')
