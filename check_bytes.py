import os

files_to_check = [
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\book.py', 589),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\gate.py', 442),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\orbit.py', 222),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 1475),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tune.py', 53),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tune.py', 180),
    (r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tune.py', 621),
]

for filepath, line_num in files_to_check:
    with open(filepath, 'rb') as f:
        lines = f.read().split(b'\n')
    if line_num <= len(lines):
        line_bytes = lines[line_num - 1]
        fname = os.path.basename(filepath)
        # Find non-ASCII bytes
        for i, b in enumerate(line_bytes):
            if b > 127:
                context = line_bytes[max(0,i-3):i+5]
                print(f'{fname}:{line_num}: byte {i} = 0x{b:02x} context={context}')
