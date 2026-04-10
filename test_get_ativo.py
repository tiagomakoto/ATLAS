import sys
sys.path.insert(0, "C:/Users/tiago/OneDrive/Documentos/ATLAS")

from atlas_backend.core.delta_chaos_reader import get_ativo
import json

try:
    dados = get_ativo('PETR4')
    print(json.dumps(dados, indent=2, default=str))
except Exception as e:
    print(f'Erro: {e}')