import json
from delta_chaos.init import ATIVOS_DIR
import os

path = os.path.join(ATIVOS_DIR, "VALE3.json")
with open(path) as f:
    dados = json.load(f)
historico = dados.get("historico", [])

print(f"Total de ciclos: {len(historico)}")
print(f"\nÚltimos 5 ciclos:")
for c in historico[-5:]:
    print(f" {c.get('ciclo_id')} | regime={c.get('regime')} | "
          f"regime_estrategia={c.get('regime_estrategia')} | "
          f"data_ref={c.get('data_ref')}")

print(f"\nPrimeiro ciclo pós 2024-Q1:")
pos_2024q1 = [c for c in historico if c.get('ciclo_id','') >= '2024-02']
if pos_2024q1:
    print(f" Encontrados: {len(pos_2024q1)} ciclos")
    print(f" Primeiro: {pos_2024q1[0]}")
else:
    print(f" NENHUM ciclo após 2024-Q1 — confirma Hipótese 1")