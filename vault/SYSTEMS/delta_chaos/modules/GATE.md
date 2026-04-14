---
uid: mod-delta-006
version: 1.0.2
status: validated
owner: Chan

function: Protocolo de qualificacao de ativo em 8 gates sequenciais antes de declarar status OPERAR. Inclui backtest interno, validacao de TP/STOP, regime, REFLECT e liquidez. Tambem opera em modo EOD leve (gate_eod) para verificacao diaria.
file: delta_chaos/gate.py
role: Porteiro — nenhum ativo opera sem aprovacao do GATE. Decisao de presente, nao calibracao historica.

input:
  - ticker: str — codigo do ativo (lido via input — sem hardcode)
  - master_json: dict — estado do ativo carregado pelo TAPE
  - cfg_ativo: dict — configuracao do ativo (TP, STOP, anos_validos, regimes_sizing)

output:
  - gate_decisao: str — OPERAR | MONITORAR | BLOQUEADO | GATE VENCIDO
  - historico_config: dict — resultado registrado no master JSON do ativo
  - gate_eod: dict — resultado da verificacao leve diaria (modo EOD)

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

depends_on_condition:

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]

intent:
  - GATE e decisao operacional de presente — nao calibracao historica.
  - Distingue de TUNE: TUNE calibra parametros em janela longa, GATE decide se opera hoje.

constraints:
  - 8 gates sequenciais — todos devem passar para OPERAR
  - Leitura de TP/STOP do master JSON do ativo — nao do config global
  - Backtest interno adicionado antes das etapas — roda EDGE antes de avaliar gates
  - Master JSON recarregado apos edge.executar() dentro do GATE — evita leitura de historico vazio
  - regimes_sizing completo configurado antes do GATE para todos os ativos novos
  - GATE EOD — tres verificacoes: ultimo GATE completo + regime atual + REFLECT
  - Validade do GATE completo — aviso em 20 dias, bloqueio em 30 dias
  - Defasagem ORBIT — 0m=OK, 1m=MONITORAR, 2m+=BLOQUEADO
  - Filtro de GATE completo aceita campos resultado, gate_decisao e valor_novo — retroativo
  - anos_validos por ativo no master JSON — nao global

notes:
  - 2026-04-14: código modificado — gate_eod.py
  - 2026-04-12: código modificado — gate_eod.py
  - VALE3 — 8/8 OPERAR — 2026-03-22
  - PETR4 — 8/8 OPERAR — 2026-03-23 (rodou com TP=0.50 provisorio — robustez confirmada)
  - BOVA11 — 8/8 OPERAR — 2026-03-23
  - BBAS3 — 7/8 MONITORAR — bloqueado em E5 (ORBIT estabilidade 2024-2025)
  - ITUB4 — 5/8 EXCLUIDO — IR negativo estrutural 28 ciclos consecutivos
  - B21 aberto: anos_validos como parametro dinamico no GATE v2.0
  - B22 aberto: GATE v2.0 com duas janelas de validacao
---
