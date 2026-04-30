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

# Analisar duplicatas de 2021-07-30 em detalhe
data_alvo = "2021-07-30"
if data_alvo in grupos:
    registros = grupos[data_alvo]
    print(f"{data_alvo}: {len(registros)} registros\n")
    
    # Coletar todas as chaves
    todas_chaves = set()
    for reg in registros:
        todas_chaves.update(reg.keys())
    
    print("Comparando campos entre registros:")
    for i, reg in enumerate(registros[:3]):  # Mostrar apenas os 3 primeiros
        print(f"\nRegistro {i}:")
        for chave in sorted(todas_chaves):
            valor = reg.get(chave, "N/A")
            print(f"  {chave}: {valor}")
