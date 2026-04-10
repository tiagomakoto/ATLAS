import sys
sys.path.insert(0, "C:/Users/tiago/OneDrive/Documentos/ATLAS")

from atlas_backend.core.delta_chaos_reader import get_ativo
import json

# Testar PETR4
dados_petr4 = get_ativo('PETR4')
print("PETR4 - historico_config:", dados_petr4.get("historico_config"))

# Testar VALE3
dados_vale3 = get_ativo('VALE3')
print("VALE3 - historico_config:", dados_vale3.get("historico_config"))