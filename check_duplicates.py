import json
from collections import Counter

path = "G:/Meu Drive/Delta Chaos/ativos/PETR4.json"
with open(path, encoding='utf-8') as f:
    data = json.load(f)

historico = data.get("historico", [])

# Checar duplicatas por data_ref (usando a chave correta do schema)
datas = [c.get("data_ref") for c in historico]
duplicatas = {d: n for d, n in Counter(datas).items() if n > 1}
print(f"Total ciclos: {len(historico)}")
print(f"Datas únicas: {len(set(datas))}")
print(f"Duplicatas: {len(duplicatas)}")
if duplicatas:
    print("Exemplos:", list(duplicatas.items())[:5])
