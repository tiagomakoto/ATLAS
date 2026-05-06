import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Search for the two missing edits
for i, line in enumerate(lines, 1):
    if 'step3Fase !== null' in line:
        print(f'  FOUND line {i}: {line.rstrip()[:100]}')
    if 'step2Tick, elapsedForStep2' in line:
        print(f'  FOUND line {i}: {line.rstrip()[:100]}')