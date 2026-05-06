import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'rb') as f:
    d = f.read()

# Edit 1: Line 420 — when running and percent is 0, show 5% instead of 0
# Old: const numericPercent = status === "done" ? 100 : status === "running" ? (typeof percent === "number" ? percent : 50) : 0;
# New: const numericPercent = status === "done" ? 100 : status === "running" ? Math.max(typeof percent === "number" ? percent : 50, 5) : 0;

old1 = b'const numericPercent = status === "done" ? 100 : status === "running" ? (typeof percent === "number" ? percent : 50) : 0;'
new1 = b'const numericPercent = status === "done" ? 100 : status === "running" ? Math.max(typeof percent === "number" ? percent : 50, 5) : 0;'

count1 = d.count(old1)
print(f'Edit 1: Found {count1} occurrence(s)')

if count1 == 1:
    d = d.replace(old1, new1, 1)
    print('Edit 1: SUCCESS — numericPercent now has 5% minimum when running')
else:
    print('Edit 1: FAILED')

with open(path, 'wb') as f:
    f.write(d)

print('File written successfully')