import sqlite3
conn = sqlite3.connect('C:/Users/tiago/OneDrive/Documentos/ATLAS/tmp/tune_PETR4.db')
cur = conn.cursor()

# Contar trials completos
cur.execute("SELECT COUNT(*) FROM trials WHERE state='COMPLETE'")
print('Trials completos:', cur.fetchone()[0])

# Melhor IR
cur.execute("SELECT MAX(value) FROM trial_values")
best = cur.fetchone()[0]
print('Best IR:', best if best else 'N/A')

# Ver estrutura da tabela trials
print('\nEstrutura da tabela trials:')
cur.execute('PRAGMA table_info(trials)')
for col in cur.fetchall():
    print(f'  {col}')

conn.close()
