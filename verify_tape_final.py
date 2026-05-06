import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Count dc_module_progress occurrences (regardless of line breaks)
count = content.count('dc_module_progress')
print(f'dc_module_progress total occurrences: {count}')

# Count _tape_current += occurrences
increment_count = content.count('_tape_current +=')
print(f'_tape_current += occurrences: {increment_count}')

# Count _atlas_disponivel and total > 0 guards
guard_count = content.count('_atlas_disponivel and total > 0')
print(f'_atlas_disponivel and total > 0 guards: {guard_count}')

# Expected: 9 progress emissions, 9 increments (8 += 1, 1 += len(ativos)), 8 guards (not txts uses different guard)
print()
print('Expected: 9 dc_module_progress, 9 _tape_current increments, 8 guards')
print(f'Match: {count == 9 and increment_count == 9 and guard_count == 8}')