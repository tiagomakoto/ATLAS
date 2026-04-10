import sys
sys.path.insert(0, "C:/Users/tiago/OneDrive/Documentos/ATLAS")

from atlas_backend.core.paths import get_paths
import json
import os

paths = get_paths()
config_path = os.path.join(paths["config_dir"], "PETR4.json")

print(f"Arquivo: {config_path}")
print(f"Existe: {os.path.exists(config_path)}")
print()

with open(config_path, 'r', encoding='utf-8') as f:
    dados = json.load(f)

print("=== historico_config ===")
print(json.dumps(dados.get("historico_config", []), indent=2, default=str))