import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"

# Check ALL non-ASCII chars in the "partial" files to find real issues
files_to_check = ['book.py', 'gate.py', 'init.py', 'orbit.py', 'tape.py', 'tune.py']

# Valid Portuguese accented chars + box drawing + punctuation
VALID_HIGH_CHARS = set(
    # Portuguese accented letters (lowercase)
    'áàãâéêíóôõúüç'
    # Portuguese accented letters (uppercase)  
    'ÁÀÃÂÉÊÍÓÔÕÚÜÇ'
    # Common punctuation
    '—–""''…°'
    # Box drawing
    '═─│┌┐└┘├┤┬┴┼'
    # Symbols
    '⚠✓✗→'
    # Math/misc
    '±×÷≤≥'
)

for fname in files_to_check:
    fpath = os.path.join(DC_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    for line_num, line in enumerate(content.split('\n'), 1):
        for i, ch in enumerate(line):
            if ord(ch) > 127 and ch not in VALID_HIGH_CHARS:
                snippet = line.strip()[:100]
                issues.append((line_num, i, f'U+{ord(ch):04X}', ch, snippet))
    
    if issues:
        print(f'{fname}: {len(issues)} invalid high chars')
        for ln, pos, code, ch, snippet in issues[:10]:
            print(f'  L{ln} pos={pos}: {code} ({ch}) in: {snippet}')
        if len(issues) > 10:
            print(f'  ... e mais {len(issues)-10}')
        print()
    else:
        print(f'{fname}: OK - todos os caracteres são válidos')
        print()
