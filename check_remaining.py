import glob, os

DC_DIR = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos'

# Check what Ã is followed by in the remaining cases
for fp in sorted(glob.glob(os.path.join(DC_DIR, '*.py'))):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = 0
    while True:
        pos = content.find('\u00c3', idx)
        if pos == -1:
            break
        # Get context around the Ã
        context = content[max(0,pos-2):pos+5]
        fname = os.path.basename(fp)
        # Find line number
        line_num = content[:pos].count('\n') + 1
        snippet = context.encode('ascii', 'replace').decode('ascii')
        print(f'{fname}:{line_num}: pos={pos} context=[{snippet}]')
        idx = pos + 1
