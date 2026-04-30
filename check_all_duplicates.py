import json, os
from collections import defaultdict

base = "G:/Meu Drive/Delta Chaos/ativos"
ativos = ["VALE3", "PETR4", "BOVA11", "BBAS3", "BBDC4", "ITUB4", "PRIO3"]

for ticker in ativos:
    path = f"{base}/{ticker}.json"
    if not os.path.exists(path):
        print(f"{ticker}: arquivo não encontrado")
        continue
    
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    
    historico = data.get("historico", [])
    
    # Agrupar por data_ref
    grupos = defaultdict(list)
    for reg in historico:
        data_ref = reg.get("data_ref")
        if data_ref:
            grupos[data_ref].append(reg)
    
    duplicatas = {d: len(regs) for d, regs in grupos.items() if len(regs) > 1}
    total_duplicados = sum(len(regs) - 1 for regs in grupos.values() if len(regs) > 1)
    
    print(f"\n{ticker}:")
    print(f"  Total ciclos: {len(historico)}")
    print(f"  Datas únicas: {len(grupos)}")
    print(f"  Datas com duplicatas: {len(duplicatas)}")
    print(f"  Registros duplicados (extra): {total_duplicados}")
    
    if duplicatas:
        # Verificar se as duplicatas são idênticas
        data_teste = next(iter(duplicatas))
        registros = grupos[data_teste]
        sao_identicos = all(reg == registros[0] for reg in registros)
        print(f"  Duplicatas são idênticas? {sao_identicos}")
