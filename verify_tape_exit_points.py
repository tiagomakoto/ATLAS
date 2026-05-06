import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r'C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\tape.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Map all exit points in tape_historico_carregar
print('=== Exit points in tape_historico_carregar ===')
exit_points = [
    ('if not txts:', 'skip entire year'),
    ('cache else:', 'skip - already cached'),
    ('except Exception as e: (COTAHIST)', 'skip - COTAHIST error'),
    ('if df_raw.empty:', 'skip - no data'),
    ('if n_op == 0:', 'skip - no options'),
    ('except Exception as e: (enrichment)', 'skip - enrichment error'),
    ('if df_enr.empty:', 'skip - empty enrichment'),
    ('frames.append + pbar.update', 'SUCCESS path'),
]

for label, desc in exit_points:
    found = False
    for i, line in enumerate(lines, 1):
        if label.split(':')[0] in line and 1440 < i < 1580:
            # Check if _tape_current += is nearby (within 5 lines)
            has_increment = any('_tape_current +=' in lines[j] for j in range(max(0,i-1), min(len(lines), i+5)))
            has_progress = any('dc_module_progress' in lines[j] for j in range(max(0,i-1), min(len(lines), i+8)))
            print(f'  {label:45s} | increment={has_increment} | progress={has_progress} | {desc}')
            found = True
            break
    if not found:
        print(f'  {label:45s} | NOT FOUND | {desc}')

# Also check the 'if not txts' block specifically
print('\n=== if not txts block detail ===')
for i, line in enumerate(lines, 1):
    if 'if not txts' in line and 1440 < i < 1460:
        for j in range(i-1, min(i+10, len(lines))):
            print(f'  line {j+1}: {lines[j].rstrip()[:90]}')
        break