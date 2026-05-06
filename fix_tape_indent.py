import re, py_compile

# Read file
with open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 'r', encoding='utf-8') as f:
    content = f.read()

func_start = content.find('def tape_historico_carregar(')
if func_start == -1:
    print("Function not found"); exit(1)

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

# 1. Add _tape_current = 0
old1 = '    total   = len(anos) * len(ativos)\n    with _tqdm'
new1 = '    total   = len(anos) * len(ativos)\n    _tape_current = 0\n    with _tqdm'
func = func.replace(old1, new1)

# 2. if not txts
old2 = '            if not txts:\n                pbar.update(len(ativos)); continue'
new2 = '''            if not txts:
                pbar.update(len(ativos))
                _tape_current += len(ativos)
                if _atlas_disponivel and total > 0:
                    emit_dc_event("dc_module_progress", "TAPE", "running",
                        progress=round((_tape_current / total) * 100), ticker=ativo)
                continue'''
func = func.replace(old2, new2)

# 3. cache else block (else at 20 spaces, body at 24)
old3 = '                        else:\n                            pbar.update(1)\n                            continue'
new3 = '''                        else:
                            pbar.update(1)
                            _tape_current += 1
                            if _atlas_disponivel and total > 0:
                                emit_dc_event("dc_module_progress", "TAPE", "running",
                                    progress=round((_tape_current / total) * 100), ticker=ativo)
                            continue'''
func = func.replace(old3, new3)

# 4. COTAHIST except (except at 16, body at 20)
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
func = func.replace(old4, new4)

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
func = func.replace(old5, new5)

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
func = func.replace(old6, new6)

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
func = func.replace(old7, new7)

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
func = func.replace(old8, new8)

# 9. success path
old9 = '                    frames.append(df_enr)\n                    pbar.update(1)'
new9 = '''                    frames.append(df_enr)
                    pbar.update(1)
                    _tape_current += 1
                    if _atlas_disponivel and total > 0:
                        emit_dc_event("dc_module_progress", "TAPE", "running",
                            progress=round((_tape_current / total) * 100), ticker=ativo)'''
func = func.replace(old9, new9)

# Reconstruct
new_content = content[:func_start] + func + content[func_end:]
with open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 'w', encoding='utf-8', newline='') as f:
    f.write(new_content)

print("Edits applied. Verifying...")
try:
    py_compile.compile(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', doraise=True)
    print("✓ Syntax OK")
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    with open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if e.lineno:
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        for i in range(start, end):
            mark = '>>>' if i+1 == e.lineno else '   '
            print(f"{mark} {i+1}: {repr(lines[i])}")
