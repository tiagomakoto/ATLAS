import json
from delta_chaos.init import ATIVOS_DIR
import os

ativos = ["PETR4", "BOVA11", "BBAS3"]
for ticker in ativos:
    path = os.path.join(ATIVOS_DIR, f"{ticker}.json")
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    h = d.get("historico", [])
    pos = [c for c in h if c.get('ciclo_id','') >= '2024-02']
    print(f"{ticker}: {len(h)} ciclos totais | "
          f"{len(pos)} ciclos pós 2024-Q1 | "
          f"último: {h[-1].get('ciclo_id') if h else 'vazio'}")