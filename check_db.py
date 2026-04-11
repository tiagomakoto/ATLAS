import sqlite3

conn = sqlite3.connect('advantage/data/raw/alternativo.db')
cursor = conn.cursor()

# Verificar estrutura da tabela ABPO
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='abpo_papelao'")
schema = cursor.fetchone()
print('Schema ABPO:')
print(schema[0] if schema else 'Tabela nao existe')

# Verificar se ha dados
cursor.execute('SELECT * FROM abpo_papelao LIMIT 5')
rows = cursor.fetchall()
print(f'\nDados na tabela: {len(rows)} registros')

conn.close()
