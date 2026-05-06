import py_compile

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tune.py'
with open(path, 'rb') as f:
    d = f.read()

old = b'if (i + 1) % 100 == 0 or (i + 1) == len(datas):'
new = b'if (i + 1) % 25 == 0 or (i + 1) == len(datas):'

count = d.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    d = d.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(d)
    print('Changed % 100 to % 25')
    py_compile.compile(path, doraise=True)
    print('Syntax OK')
else:
    print('ERROR: unexpected count')