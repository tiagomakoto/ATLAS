import py_compile

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\edge.py'
with open(path, 'rb') as f:
    d = f.read()

old = b'    else:\n        emit_dc_event("dc_module_complete", modulo, status, ticker=ticker, **kwargs)'
new = b'    elif status == "progress":\n        emit_dc_event("dc_module_progress", modulo, "running", ticker=ticker, **kwargs)\n    else:\n        emit_dc_event("dc_module_complete", modulo, status, ticker=ticker, **kwargs)'

count = d.count(old)
print(f'Found {count} occurrence(s)')

if count == 1:
    d = d.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(d)
    print('SUCCESS: Added status=progress support')
    py_compile.compile(path, doraise=True)
    print('Syntax OK')
else:
    print('ERROR: expected exactly 1 occurrence')