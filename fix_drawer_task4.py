import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'rb') as f:
    d = f.read()

# Old: if (typeof progress === "number" && ["TAPE", "ORBIT", "FIRE", "GATE"].includes(modulo)) {
# New: if (typeof progress === "number" && step3Fase !== null && ["TAPE", "ORBIT", "FIRE", "GATE"].includes(modulo)) {

old = b'if (typeof progress === "number" && ["TAPE", "ORBIT", "FIRE", "GATE"].includes(modulo)) {'
new = b'if (typeof progress === "number" && step3Fase !== null && ["TAPE", "ORBIT", "FIRE", "GATE"].includes(modulo)) {'

count = d.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    d = d.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(d)
    print('SUCCESS: Added step3Fase !== null guard')
else:
    print('ERROR: unexpected count')