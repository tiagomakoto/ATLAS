import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'rb') as f:
    d = f.read()

# Old: Tempo decorrido {elapsedForStep2()} (est. restante {estimatedForStep2()})
# New: Tempo decorrido {step2Tick, elapsedForStep2()} (est. restante {estimatedForStep2()})
# Using the comma operator pattern: step2Tick is evaluated (triggering React dependency tracking)
# then discarded, and elapsedForStep2() result is returned.

old = b'Tempo decorrido {elapsedForStep2()} (est. restante {estimatedForStep2()})'
new = b'Tempo decorrido {step2Tick, elapsedForStep2()} (est. restante {estimatedForStep2()})'

count = d.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    d = d.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(d)
    print('SUCCESS: step2Tick now referenced in render')
else:
    print('ERROR: unexpected count')