import json, os

base = "G:/Meu Drive/Delta Chaos/ativos"
ativos = ["VALE3", "PETR4", "BOVA11"]

for ticker in ativos:
    path = f"{base}/{ticker}.json"
    if not os.path.exists(path): continue
    with open(path) as f:
        data = json.load(f)
    
    historico = data.get("historico_ciclos", [])
    from collections import Counter
    regimes = Counter(c.get("regime") for c in historico if c.get("regime"))
    neutros = {k: v for k, v in regimes.items() if "LATERAL" in k}
    print(f"\n{ticker} — {len(historico)} ciclos total")
    for r, n in sorted(neutros.items()):
        print(f"  {r}: {n} ciclos")
