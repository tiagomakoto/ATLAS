---
uid: mod-delta-011
version: 1.0
status: validated
owner: Chan

function: Inicializacao do ambiente Delta Chaos — leitura de DRIVE_BASE do paths.json, definicao de todos os caminhos do filesystem (TAPE, ORBIT, BOOK, etc.), verificacao de diretorios e cache, e carregamento de configuracao global.
file: delta_chaos/init.py
role: Bootstrap do Delta Chaos — inicializacao de ambiente, paths e config global.

input:
  - paths.json: dict — lido de atlas_backend/config/paths.json (fallback: ~/DeltaChaos)

output:
  - DRIVE_BASE: str — raiz do filesystem Delta Chaos
  - carregar_config(): dict — configuracao completa do delta_chaos_config.json
  - cfg_global(secao, chave): any — accessor de config por secao/chave

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]

intent:
  - Centralizar todos os paths derivados em um unico modulo. Nenhum outro modulo conhece caminhos absolutos.
  - Migrado do Google Colab (v1.0) para paths.json (v2.0) — sem dependencia de Colab.

constraints:
  - DRIVE_BASE lido de paths.json campo delta_chaos_base — fallback ~/DeltaChaos
  - paths.json localizado em Path(__file__).parent.parent / atlas_backend / config / paths.json
  - CAPITAL_PADRAO = 10000.0 — injetado em config.backtest.capital quando ausente
  - carregar_config() injeta backtest.capital se secao ou chave ausente
  - verificar_diretorios() cria diretorios inexistentes com os.makedirs(exist_ok=True)
  - verificar_cache() valida COTAHIST (>=50MB), gregas (>=1MB), OHLCV, externas, SELIC, master JSONs
  - Parquets SELIC fragmentados removidos automaticamente (cleanup)
  - CONFIG_PATH = DRIVE_BASE/delta_chaos_config.json
  - DIRETORIOS: TAPE_DIR, COTAHIST_DIR, GREGAS_DIR, OHLCV_DIR, EXTERNAS_DIR, ORBIT_DIR, TRADELOG_DIR, BOOK_DIR, OPCOES_HOJE_DIR, OPCOES_HISTORICO_DIR, ATIVOS_DIR

notes:
  - Prints de inicializacao sob if __name__ == "__main__" — nao poluem imports
  - Logging via emit_log/emit_error com fallback graceful para print quando ATLAS indisponivel
---
