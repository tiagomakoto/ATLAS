import sys
import os

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar a função de criação de tabelas
from src.data_layer.db.schema import create_all_tables

# Executar a criação de tabelas
create_all_tables()
print("Tabelas inicializadas com sucesso!")