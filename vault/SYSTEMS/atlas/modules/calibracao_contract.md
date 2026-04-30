---
uid: mod-atlas-024
version: 1.0.4
status: validated
owner: Chan | Lilian | Board

function: Define e aplica o contrato de normalização calibracao.v3.0 entre backend e frontend — normaliza steps, GATE resultado, FIRE diagnóstico e guard em schemas estritos com defaults seguros.
file: atlas_backend/core/calibracao_contract.py
role: Contrato de dados — garante que toda resposta de calibração segue schema canônico antes de chegar ao frontend.

input:
- ticker: str — código do ativo
- calibracao: dict | None — estado dos 3 steps
- guard: dict | None — dados de frescor do cotahist
- gate_resultado: dict | None — resultado dos 8 critérios GATE
- fire_diagnostico: dict | None — diagnóstico FIRE por regime

output:
- build_calibracao_payload: dict — payload canônico calibracao.v3.0 com steps normalizados, gate, fire, guard e step_atual inferido

depends_on: []

depends_on_condition: []

used_by:
- [[SYSTEMS/atlas/modules/API_ROUTES]]
- [[SYSTEMS/atlas/modules/delta_chaos]]

intent:
- Eliminar inconsistências de schema entre backend e frontend. Toda resposta de calibração passa por este contrato antes de ser consumida pelo CalibracaoDrawer.

constraints:
- STEP_KEYS = ['1_backtest_dados', '2_tune', '3_gate_fire']
- STEP_STATUS = ['idle', 'running', 'done', 'error', 'paused', 'skipped']
- DEFAULT_STEP = {status: idle, iniciado_em: None, concluido_em: None, erro: None}
- normalize_gate_resultado clampa resultado para OPERAR ou BLOQUEADO
- normalize_guard_payload computa dados_recentes (dias < 7) e deve_exibir_guard
- build_calibracao_payload infere step_atual a partir dos status dos steps
- Compatibilidade com chave legada 3_backtest_gate mantida

notes:
  - 2026-04-29: código modificado — calibracao_contract.py
  - 2026-04-26: código modificado — calibracao_contract.py
- 2026-04-17: código modificado — calibracao_contract.py
- 2026-04-17 — módulo criado automaticamente a partir de atlas_backend/core/calibracao_contract.py
- 2026-04-25 — vault validado: campos BOARD_REVIEW_REQUIRED preenchidos via análise de código