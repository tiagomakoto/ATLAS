---
uid: mod-adv-001
version: 1.0.1
status: validated
owner: Chan

function: Fonte unica de verdade para todos os dados do sistema Advantage. Quatro dominios isolados em SQLite — preco_volume, macro, alternativo, portfolio. Nenhuma camada de analise acessa fonte externa diretamente.
file: advantage/src/data_layer/db/connection.py, advantage/src/data_layer/db/schema.py
role: Camada de acesso a dados — get_connection(domain) como unico ponto de entrada por dominio e schema.py para DDL idempotente.

input:
  - domain: Literal["preco_volume", "macro", "alternativo", "portfolio"]

output:
  - conn: sqlite3.Connection — com row_factory=sqlite3.Row, WAL mode, foreign_keys=ON

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/advantage/modules/COLLECTORS]]
  - [[SYSTEMS/advantage/modules/SCHEDULER]]

intent:
  - Isolar completamente o acesso a dados. Nenhuma camada conhece caminhos de arquivo diretamente.
  - Append-only: serie temporal nunca sobrescrita — apenas INSERT, nunca UPDATE de historico.

constraints:
  - SQLite fase atual — PostgreSQL e fase futura, nao implementar agora
  - Acesso direto via Python — sem API REST, sem JWT, sem OAuth2 nesta fase
  - PRAGMA journal_mode=WAL obrigatorio — concorrencia de leitura/escrita
  - PRAGMA foreign_keys=ON obrigatorio
  - INSERT OR IGNORE para evitar duplicatas — nunca UPDATE de historico
  - DB_ROOT = advantage/data/raw/ — quatro arquivos .db por dominio
  - Criar arquivo se nao existir — path.parent.mkdir(parents=True, exist_ok=True)

notes:
  - 2026-04-11: código modificado — schema.py
  - Quatro dominios: preco_volume.db, macro.db, alternativo.db, portfolio.db
  - schema.py — create_all_tables() idempotente — seguro chamar multiplas vezes
---
