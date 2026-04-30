import json
from collections import defaultdict

path = "G:/Meu Drive/Delta Chaos/ativos/PETR4.json"
with open(path, encoding='utf-8') as f:
    data = json.load(f)

historico = data.get("historico", [])

# Agrupar registros por data_ref
grupos = defaultdict(list)
for registro in historico:
    data_ref = registro.get("data_ref")
    if data_ref:
        grupos[data_ref].append(registro)

# Mostrar detalhes das duplicatas
print(f"Total ciclos: {len(historico)}")
print(f"Datas únicas: {len(grupos)}")
print(f"Datas com duplicatas: {sum(1 for v in grupos.values() if len(v) > 1)}")
print("\nTop 10 datas mais duplicadas:")
for data_ref, registros in sorted(grupos.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"{data_ref}: {len(registros)} registros")
    # Mostrar diferenças entre registros da mesma data
    if len(registros) > 1:
        print("  Diferenças encontradas:")
        for i, reg in enumerate(registros):
            print(f"    [{i}] ciclo_id={reg.get('ciclo_id')}, regime={reg.get('regime')}, score={reg.get('score')}")
