import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
checks = [
    (823, 'setStep3Progress({ TAPE: 0'),
    (849, 'step3Fase !== null'),
    (420, 'Math.max(typeof percent'),
    (1471, 'step2Tick, elapsedForStep2'),
]
for line_num, expected in checks:
    line = lines[line_num - 1].rstrip()
    if expected in line:
        print(f'  OK line {line_num}: {line[:90]}')
    else:
        print(f'  MISSING line {line_num}: expected \"{expected}\"')
        print(f'    actual: {line[:90]}')