"""
migrate_regime.py
Renomeia regime_estrategia → regime em todos os registros
do campo historico[] nos JSONs de ativos do Delta Chaos.

Execução:
    python migrate_regime.py

Seguro — faz backup antes de sobrescrever.
"""
import json
import os
import shutil
from datetime import datetime

ATIVOS_DIR = r"G:\Meu Drive\Delta Chaos\ativos"

def migrar(path: str) -> tuple[int, int]:
    """Retorna (total_ciclos, ciclos_migrados)."""
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    historico = dados.get("historico", [])
    migrados = 0
    for ciclo in historico:
        if "regime_estrategia" in ciclo:
            ciclo["regime"] = ciclo.pop("regime_estrategia")
            migrados += 1

    if migrados == 0:
        return len(historico), 0

    # Backup atômico antes de salvar
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path + f".bak_{ts}"
    shutil.copy2(path, bak)

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
    os.replace(tmp, path)

    return len(historico), migrados


def main():
    jsons = [f for f in os.listdir(ATIVOS_DIR) if f.endswith(".json")]
    if not jsons:
        print(f"Nenhum JSON encontrado em {ATIVOS_DIR}")
        return

    print(f"Migrando {len(jsons)} arquivo(s) em {ATIVOS_DIR}\n")
    total_migrados = 0

    for nome in sorted(jsons):
        path = os.path.join(ATIVOS_DIR, nome)
        try:
            total, migrados = migrar(path)
            if migrados:
                print(f"  ✓ {nome}: {migrados}/{total} ciclo(s) migrado(s)")
                total_migrados += migrados
            else:
                print(f"  ~ {nome}: nenhum ciclo com regime_estrategia")
        except Exception as e:
            print(f"  ✗ {nome}: erro — {e}")

    print(f"\nConcluído. {total_migrados} ciclo(s) migrado(s) no total.")
    print("Backups criados com sufixo .bak_<timestamp>")


if __name__ == "__main__":
    main()