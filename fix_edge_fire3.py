import py_compile

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\edge.py'
with open(path, 'rb') as f:
    d = f.read()

# Edit 1: Add _fire_current = 0 before the with _tqdm block
# Use the exact bytes from the file
old1 = d[18973:18973+104]
new1 = b'        _fire_current = 0\n' + old1

count1 = d.count(old1)
print(f'Edit 1: Found {count1} occurrence(s)')

if count1 == 1:
    d = d.replace(old1, new1, 1)
    print('Edit 1: SUCCESS')
else:
    print('Edit 1: FAILED')

# Edit 2: Add _fire_current increment and progress emission after pbar.update(1)
# Find pbar.update(1) in the FIRE section (after byte 19000)
fire_tqdm_idx = d.find(b'with _tqdm(total=len(datas)')
pbar_idx = d.find(b'pbar.update(1)', fire_tqdm_idx)
# Get the exact bytes: 12 spaces + 'pbar.update(1)\n' + 12 spaces + 'pbar.set_postfix('
line_start = d.rfind(b'\n', 0, pbar_idx) + 1
# Find 'pbar.set_postfix(' after pbar.update(1)
set_postfix_idx = d.find(b'pbar.set_postfix(', pbar_idx)
set_postfix_line_start = d.rfind(b'\n', 0, set_postfix_idx) + 1

old2 = d[line_start:set_postfix_line_start + len(b'            pbar.set_postfix(')]
print(f'Edit 2 old: {repr(old2)}')

new2 = (b'            pbar.update(1)\n'
        b'            _fire_current += 1\n'
        b'            if _fire_current % 50 == 0:\n'
        b'                emit_event("FIRE", "progress", ticker=ticker,\n'
        b'                           progress=round((_fire_current / len(datas)) * 100))\n'
        b'            pbar.set_postfix(')

count2 = d.count(old2)
print(f'Edit 2: Found {count2} occurrence(s)')

if count2 == 1:
    d = d.replace(old2, new2, 1)
    print('Edit 2: SUCCESS')
else:
    print('Edit 2: FAILED')

with open(path, 'wb') as f:
    f.write(d)

py_compile.compile(path, doraise=True)
print('Syntax OK')