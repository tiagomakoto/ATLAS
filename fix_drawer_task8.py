import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add setStep3Progress reset after setStep3SubFases on line 822
# This is inside the GATE dc_module_start handler — the initiation point for Step 3
old = '            setStep3SubFases({ TAPE: "idle", ORBIT: "idle", FIRE: "idle", GATE: "running" });\n            const gateStatus'
new = '            setStep3SubFases({ TAPE: "idle", ORBIT: "idle", FIRE: "idle", GATE: "running" });\n            setStep3Progress({ TAPE: 0, ORBIT: 0, FIRE: 0, GATE: 0 });\n            const gateStatus'

count = content.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('SUCCESS: Added setStep3Progress reset when Step 3 initiates')
else:
    print('ERROR: unexpected count')