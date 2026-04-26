---
uid: mod-atlas-025
version: 1.0.2
status: validated
owner: Chan | Lilian | Board

function: Computa diagnóstico FIRE por regime — trades, acerto, IR, profit factor, expectancy, estratégia dominante e cobertura, a partir de book_backtest.parquet com fallback para master JSON.
file: atlas_backend/core/fire_helper.py
role: Motor de diagnóstico FIRE — computa métricas de desempenho por regime para o backend ATLAS.

input:
- ticker: str — código do ativo

output:
- compute_fire_diagnostico: dict — {ticker, regimes (lista com trades/wins/losses/acerto_pct/IR/worst/best/avg_win/avg_loss/profit_factor/expectancy/estrategia_dominante/estrategias/motivos_saida), cobertura (ciclos_com_operacao/total_ciclos/total_trades/acerto_geral_pct/pnl_total), stops_por_regime, fonte_dados}

depends_on:
- [[SYSTEMS/atlas/modules/DATA_READERS]]
- [[SYSTEMS/delta_chaos/modules/FIRE]]

depends_on_condition: []

used_by:
- [[SYSTEMS/atlas/modules/DATA_READERS]]
- [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
- Replicar a lógica de diagnóstico FIRE do Delta Chaos no backend ATLAS, permitindo consulta via API sem executar o pipeline completo.

constraints:
- Lê book_backtest.parquet como fonte primária — fallback para master JSON historico
- Suporta schemas flat e nested (core/orbit dict) no parquet
- _compute_ir: IR = (mean/std) * sqrt(252/21) — anualizado
- Agregação por regime com métricas: acerto_pct, IR, profit_factor, expectancy
- Stops por regime rastreados separadamente

notes:
- 2026-04-22: código modificado — fire_helper.py
- 2026-04-17 — módulo criado automaticamente a partir de atlas_backend/core/fire_helper.py
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código