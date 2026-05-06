import py_compile

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\edge.py'
with open(path, 'rb') as f:
    d = f.read()

# The broken line is: '            pbar.set_postfix(fix(\n'
# It should be: '            pbar.set_postfix(\n'
old = b'            pbar.set_postfix(fix(\n'
new = b'            pbar.set_postfix(\n'

count = d.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    d = d.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(d)
    print('Fixed pbar.set_postfix line')
    py_compile.compile(path, doraise=True)
    print('Syntax OK')
else:
    print('ERROR: unexpected count')