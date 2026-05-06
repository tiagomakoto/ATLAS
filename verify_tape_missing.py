import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Map all _tape_current += lines with context
print('=== All _tape_current += lines ===')
for i, line in enumerate(lines, 1):
    if '_tape_current +=' in line:
        # Show 3 lines of context after
        print(f'\n  line {i}: {line.rstrip()[:90]}')
        for j in range(i, min(i+4, len(lines))):
            if j > i:
                print(f'  line {j+1}: {lines[j].rstrip()[:90]}')

# Also check: is there a 'continue' without _tape_current before it?
print('\n=== All continue statements in the function ===')
func_start = None
for i, line in enumerate(lines, 1):
    if 'def tape_historico_carregar(' in line:
        func_start = i
    if func_start and i > func_start and i < 1580:
        stripped = line.strip()
        if stripped == 'continue':
            # Check if _tape_current += appears within 5 lines before
            has_increment = any('_tape_current +=' in lines[k] for k in range(max(0, i-6), i-1))
            print(f'  line {i}: continue | _tape_current += nearby: {has_increment}')