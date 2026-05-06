import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Final comprehensive verification of all edits
print('=== VERIFICACAO FINAL ===')
print()

# 1. tape.py - _tape_current
path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
tape_count = sum(1 for l in lines if '_tape_current' in l)
print(f'tape.py: _tape_current references = {tape_count} (expected 17)')
# Check initialization
init_found = any('_tape_current = 0' in l for l in lines)
print(f'tape.py: _tape_current = 0 init = {init_found}')
# Check emit_dc_event calls with dc_module_progress
progress_calls = sum(1 for l in lines if 'dc_module_progress' in l and 'emit_dc_event' in l)
print(f'tape.py: dc_module_progress emit calls = {progress_calls} (expected 9)')

print()

# 2. edge.py - emit_event progress + FIRE progress
path2 = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\edge.py'
with open(path2, 'r', encoding='utf-8') as f:
    lines2 = f.readlines()
progress_status = any('status == "progress"' in l for l in lines2)
print(f'edge.py: status="progress" in emit_event = {progress_status}')
fire_current = any('_fire_current = 0' in l for l in lines2)
print(f'edge.py: _fire_current = 0 init = {fire_current}')
fire_progress = any('_fire_current % 50' in l for l in lines2)
print(f'edge.py: _fire_current % 50 progress = {fire_progress}')

print()

# 3. tune.py - % 25
path3 = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tune.py'
with open(path3, 'r', encoding='utf-8') as f:
    lines3 = f.readlines()
tune_25 = any('% 25 == 0' in l for l in lines3)
tune_100 = any('% 100 == 0' in l for l in lines3)
print(f'tune.py: % 25 == 0 found = {tune_25}')
print(f'tune.py: % 100 == 0 still exists = {tune_100} (should be False)')

print()

# 4. CalibracaoDrawer.jsx - all 4 edits
path4 = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\components\GestaoView\CalibracaoDrawer.jsx'
with open(path4, 'r', encoding='utf-8') as f:
    lines4 = f.readlines()
task4 = any('step3Fase !== null' in l for l in lines4)
task5 = any('Math.max(typeof percent' in l for l in lines4)
task6 = any('step2Tick, elapsedForStep2' in l for l in lines4)
task8 = any('setStep3Progress({ TAPE: 0, ORBIT: 0, FIRE: 0, GATE: 0 })' in l for l in lines4)
print(f'CalibracaoDrawer.jsx: TAREFA 4 (step3Fase guard) = {task4}')
print(f'CalibracaoDrawer.jsx: TAREFA 5 (Math.max min 5%) = {task5}')
print(f'CalibracaoDrawer.jsx: TAREFA 6 (step2Tick in render) = {task6}')
print(f'CalibracaoDrawer.jsx: TAREFA 8 (step3Progress reset) = {task8}')

print()
all_ok = all([init_found, progress_calls >= 9, progress_status, fire_current, fire_progress, tune_25, not tune_100, task4, task5, task6, task8])
print(f'=== TODAS EDICOES VERIFICADAS: {"SIM" if all_ok else "NAO - VERIFICAR"} ===')