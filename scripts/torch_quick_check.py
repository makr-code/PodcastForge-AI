import sys
print('PYTHON', sys.executable)
try:
    import torch
    print('TORCH', torch.__version__)
    print('CUDA available', torch.cuda.is_available())
except Exception as e:
    import traceback
    traceback.print_exc()
    print('IMPORT_ERROR', e)
