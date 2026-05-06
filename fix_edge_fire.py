import py_compile

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\edge.py'
with open(path, 'rb') as f:
    d = f.read()

# 1. Add _fire_current = 0 before the with _tqdm block
old1 = b'        with _tqdm(total=len(datas), desc="FIRE",\n                     unit="preg\xc3\xa3o", ncols=None) as pbar:'
new1 = b'        _fire_current = 0\n        with _tqdm(total=len(datas), desc="FIRE",\n                     unit="preg\xc3\xa3o", ncols=None) as pbar:'

count1 = d.count(old1)
print(f'Edit 1: Found {count1} occurrence(s)')

if count1 == 1:
    d = d.replace(old1, new1, 1)
    print('Edit 1: Added _fire_current = 0')
else:
    # Try without the special char
    old1b = b'        with _tqdm(total=len(datas), desc="FIRE",'
    idx = d.find(old1b)
    if idx >= 0:
        # Show context
        print(f'Found at byte {idx}: {repr(d[idx:idx+100])}')
    print('ERROR on edit 1')

# 2. Add _fire_current increment and progress emission after pbar.update(1)
old2 = b'            pbar.update(1)\n            pbar.set_postfix('
new2 = b'            pbar.update(1)\n            _fire_current += 1\n            if _fire_current % 50 == 0:\n                emit_event("FIRE", "progress", ticker=ticker,\n                           progress=round((_fire_current / len(datas)) * 100))\n            pbar.set_postfix('

count2 = d.count(old2)
print(f'Edit 2: Found {count2} occurrence(s)')

if count2 == 1:
    d = d.replace(old2, new2, 1)
    print('Edit 2: Added progress emission every 50 pregões')
else:
    print('ERROR on edit 2')

with open(path, 'wb') as f:
    f.write(d)

py_compile.compile(path, doraise=True)
print('Syntax OK')