import py_compile

with open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find function
func_start = content.find('def tape_historico_carregar(')
idx = func_start + 1
while True:
    next_def = content.find('\ndef ', idx)
    if next_def == -1:
        func_end = len(content); break
    line_start = content.rfind('\n', 0, next_def) + 1
    if line_start == -1: line_start = 0
    if content[line_start:next_def].startswith('    def '):
        func_end = next_def; break
    idx = next_def + 1

func = content[func_start:func_end]

# 4. COTAHIST except
old4 = '                except Exception as e:\n                    pbar.write(f"  ⚠ {ativo} {ano} "\n                               f"erro COTAHIST: {e} — pulando")\n                    pbar.update(1)\n                    continue'
new4 = '''                except Exception as e:
                    pbar.write(f"  ⚠ {ativo} {ano} "
                               f"erro COTAHIST: {e} — pulando")
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)
                    continue'''
if old4 in func:
    func = func.replace(old4, new4)
    print("✓ Fixed COTAHIST except")
else:
    print("✗ Pattern 4 not found")

# 5. df_raw.empty
old5 = '                if df_raw.empty:\n                    pbar.write(f"  ~ {ativo} {ano}: "\n                               f"sem dados — pulando")\n                    pbar.update(1)\n                    continue'
new5 = '''                if df_raw.empty:
                    pbar.write(f"  ~ {ativo} {ano}: "
                               f"sem dados — pulando")
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)
                    continue'''
if old5 in func:
    func = func.replace(old5, new5)
    print("✓ Fixed df_raw.empty")
else:
    print("✗ Pattern 5 not found")

# 6. n_op == 0
old6 = '                if n_op == 0:\n                    pbar.write(f"  ~ {ativo} {ano}: "\n                               f"sem opções — pulando")\n                    pbar.update(1)\n                    continue'
new6 = '''                if n_op == 0:
                    pbar.write(f"  ~ {ativo} {ano}: "
                               f"sem opções — pulando")
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)
                    continue'''
if old6 in func:
    func = func.replace(old6, new6)
    print("✓ Fixed n_op == 0")
else:
    print("✗ Pattern 6 not found")

# 7. enrichment except
old7 = '                except Exception as e:\n                    pbar.write(f"  ⚠ {ativo} {ano} "\n                               f"erro enriquecimento: {e} "\n                               f"— pulando")\n                    pbar.update(1)\n                    continue'
new7 = '''                except Exception as e:
                    pbar.write(f"  ⚠ {ativo} {ano} "
                               f"erro enriquecimento: {e} "
                               f"— pulando")
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)
                    continue'''
if old7 in func:
    func = func.replace(old7, new7)
    print("✓ Fixed enrichment except")
else:
    print("✗ Pattern 7 not found")

# 8. df_enr.empty
old8 = '                if df_enr.empty:\n                    pbar.write(f"  ~ {ativo} {ano}: "\n                               f"enriquecimento vazio — pulando")\n                    pbar.update(1)\n                    continue'
new8 = '''                if df_enr.empty:
                    pbar.write(f"  ~ {ativo} {ano}: "
                               f"enriquecimento vazio — pulando")
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)
                    continue'''
if old8 in func:
    func = func.replace(old8, new8)
    print("✓ Fixed df_enr.empty")
else:
    print("✗ Pattern 8 not found")

# Reconstruct
new_content = content[:func_start] + func + content[func_end:]
with open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 'w', encoding='utf-8', newline='') as f:
    f.write(new_content)

print("\nVerifying syntax...")
try:
    py_compile.compile(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', doraise=True)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")
