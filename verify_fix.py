import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"

# Check specific lines to see if they're actually broken or false positives
checks = [
    ('book.py', 589, 'AÇÃO NECESSÁRIA'),
    ('gate.py', 442, 'DECISÃO'),
    ('orbit.py', 222, 'CALIBRAÇÃO'),
    ('tune.py', 53, 'CONFIGURAÇÃO'),
    ('tape.py', 382, 'em dash'),
]

for fname, line_num, expected in checks:
    fpath = os.path.join(DC_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if line_num <= len(lines):
        line = lines[line_num - 1].strip()[:120]
        # Check if expected text is present
        has_expected = expected in line if expected != 'em dash' else '—' in line or '\u2014' in line
        print(f'{fname}:{line_num}: {line}')
        print(f'  Has expected "{expected}": {has_expected}')
        # Show byte representation of suspicious chars
        for i, ch in enumerate(line):
            if ord(ch) > 127:
                print(f'  char[{i}] = U+{ord(ch):04X} ({ch})')
        print()
