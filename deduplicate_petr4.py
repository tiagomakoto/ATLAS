import json, os, tempfile

path = "G:/Meu Drive/Delta Chaos/ativos/PETR4.json"
with open(path, encoding='utf-8') as f:
    data = json.load(f)

historico = data.get("historico", [])

# Deduplicar mantendo primeira ocorrência por data_ref
visto = set()
deduplicado = []
for c in historico:
    key = c.get("data_ref")
    if key not in visto:
        visto.add(key)
        deduplicado.append(c)

print(f"Antes: {len(historico)} | Depois: {len(deduplicado)}")

# Confirme o número antes de salvar
# Se Depois == 288 → está correto, pode salvar
data["historico"] = deduplicado

tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
os.replace(tmp, path)
print("PETR4.json salvo — deduplicado.")
