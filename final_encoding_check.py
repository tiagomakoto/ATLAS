import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

dc_dir = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"
files = sorted([f for f in os.listdir(dc_dir) if f.endswith('.py')])

# Mojibake patterns to check
MOJIBAKE = [
    'Ã©', 'Ã§', 'Ã£o', 'Ã£', 'Ã¡', 'Ã­', 'Ã³', 'Ãº',
    'Ãª', 'Ã´', 'Ãµ',
    'â€"', 'â€œ', 'â€˜', 'â€™',
    'â•', 'â"', 'â†', 'âœ', 'âš',
]

total_issues = 0
for fname in files:
    fpath = os.path.join(dc_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    issues = [m for m in MOJIBAKE if m in content]
    if issues:
        print(f'{fname}: STILL BROKEN - {issues}')
        total_issues += len(issues)
    else:
        print(f'{fname}: CLEAN')

print(f'\nTotal mojibake patterns found: {total_issues}')
if total_issues == 0:
    print('✅ TODOS OS ARQUIVOS ESTÃO COM ENCODING CORRETO!')
