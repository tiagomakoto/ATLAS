---
uid: mod-atlas-026
version: 1.0.2
status: validated
owner: Chan | Lilian | Board

function: Computa os 8 critérios GATE (E0-E7) para qualificação de ativo — integridade, IR por regime, acerto, P&L, sensibilidade TP/STOP, estabilidade ORBIT, séries externas e stress/drawdown.
file: atlas_backend/core/gate_helper.py
role: Motor de critérios GATE — computa e avalia os 8 gates de qualificação para o backend ATLAS.

input:
- ticker: str — código do ativo

output:
- compute_gate_criterios: dict — {ticker, ciclo, criterios (E0-E7 com id/nome/passou/valor/detalhe), resultado (OPERAR|MONITORAR|EXCLUIDO), falhas, n_passou, anos_validos, anos_cobertos, fonte_dados}

depends_on:
- [[SYSTEMS/atlas/modules/DATA_READERS]]
- [[SYSTEMS/delta_chaos/modules/GATE]]

depends_on_condition: []

used_by:
- [[SYSTEMS/atlas/modules/DATA_READERS]]
- [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
- Replicar a lógica de critérios GATE do Delta Chaos no backend ATLAS, permitindo consulta via API sem executar o pipeline completo.

constraints:
- IR_GATE_E1 = 0.10 — threshold mínimo de IR por regime
- IR_GATE_E4 = 0.20 — threshold mínimo de IR na sensibilidade TP/STOP
- DD_GATE_E7 = 3.0 — drawdown máximo permitido (múltiplo do prêmio)
- _get_anos_validos calcula a partir de gate.anos_passados (default 3)
- _get_tp_stop lê do ativo JSON (defaults: TP=0.50, STOP=2.0)
- _compute_e4_sensitivity faz grid search sobre combinações de TP/STOP
- Resultado: 8/8=OPERAR, 6-7/8=MONITORAR, <6=EXCLUIDO
- Lê de book_backtest.parquet + master JSON

notes:
  - 2026-04-30: código modificado — gate_helper.py
- 2026-04-17 — módulo criado automaticamente a partir de atlas_backend/core/gate_helper.py
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código