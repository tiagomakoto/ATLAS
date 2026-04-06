import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"

MOJIBAKE_MARKERS = [
    'Ã©', 'Ã§', 'Ã£o', 'Ã£', 'Ã¡', 'Ã­', 'Ã³', 'Ãº',
    'Ãª', 'Ã´', 'Ãµ', 'Ã"', 'Ã‰', 'Ãš',
    'â€"', 'â€œ', 'â€', 'â€˜', 'â€™',
    'â•', 'â"', 'â†', 'âœ', 'âš',
    'Ã',
]

files_with_issues = ['book.py', 'gate.py', 'init.py', 'orbit.py', 'tape.py', 'tune.py']

for fname in files_with_issues:
    fpath = os.path.join(DC_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    issues = []
    for i, line in enumerate(lines, 1):
        for m in MOJIBAKE_MARKERS:
            if m in line:
                snippet = line.strip()[:100]
                issues.append((i, m, snippet))
                break
    print(f'{fname}: {len(issues)} issues')
    for ln, marker, snippet in issues[:5]:
        print(f'  L{ln}: [{repr(marker)}] {snippet}')
    if len(issues) > 5:
        print(f'  ... e mais {len(issues)-5} linhas')
    print()
