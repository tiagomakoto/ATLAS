import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Count ALL dc_module_progress references (not just emit_dc_event)
print('=== dc_module_progress references ===')
for i, line in enumerate(lines, 1):
    if 'dc_module_progress' in line:
        print(f'  line {i}: {line.rstrip()[:90]}')

print()
print('=== emit_dc_event calls with progress ===')
count = 0
for i, line in enumerate(lines, 1):
    if 'emit_dc_event' in line and 'dc_module_progress' in line:
        count += 1
        print(f'  [{count}] line {i}: {line.rstrip()[:90]}')

print(f'\nTotal emit_dc_event + dc_module_progress: {count}')

# Also check for _atlas_disponivel guards
print('\n=== _atlas_disponivel guards ===')
guard_count = 0
for i, line in enumerate(lines, 1):
    if '_atlas_disponivel' in line:
        guard_count += 1
        print(f'  line {i}: {line.rstrip()[:90]}')
print(f'Total _atlas_disponivel references: {guard_count}')