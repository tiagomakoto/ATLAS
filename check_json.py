import json
import os

path = r"G:\Meu Drive\Delta Chaos\ativos\PETR4.json"
if os.path.exists(path):
    with open(path) as f:
        d = json.load(f)
    print(f"Total ciclos: {len(d.get('historico', []))}")
    print(f"Last ciclo: {d['historico'][-1]['ciclo_id'] if d['historico'] else 'NONE'}")
else:
    print("Path does not exist")
