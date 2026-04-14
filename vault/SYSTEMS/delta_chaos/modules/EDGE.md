---
uid: mod-delta-005
version: 1.3.6
status: validated
owner: Chan

function: Orquestrador central do sistema. Coordena o fluxo completo por ativo — carrega config, chama ORBIT, aplica sizing do REFLECT, delega execucao ao FIRE, registra no BOOK. Opera em modo backtest, paper e live.
file: delta_chaos/edge.py
role: Orquestrador — unico modulo que conhece o fluxo completo e todos os outros modulos

input:
  - ticker: str — codigo do ativo
  - modo: str — backtest | paper | live
  - cfg_ativo: dict — configuracao completa do ativo

output:
  - resultado_backtest: dict — P&L, IR, Sharpe, drawdown, breakdown por regime
  - posicao_aberta: dict — estrutura aberta no paper/live
  - estado_reflect: str — estado atual do REFLECT (A-E) por ativo

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

depends_on_condition:
  - reflect_permanent_block_flag=True: bloqueia abertura antes de chamar FIRE

used_by:
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/atlas/modules/dc_runner]]

intent:
  - EDGE e o unico ponto de orquestracao. Nenhum outro modulo chama modulos irmaos.
  - FIRE nao conhece REFLECT — EDGE multiplica sizing antes de passar ao FIRE.

constraints:
  - Multiplica sizing do ORBIT pelo multiplicador do REFLECT antes de passar ao FIRE
  - reflect_permanent_block_flag verificado antes de abrir — bloqueia estado E
  - tape_reflect_cycle chamado no fechamento de cada ciclo mensal
  - configs_ativos carregado uma vez por ativo no inicio do backtest
  - configs_ativos definido no modo paper — bug SCAN-11 corrigido
  - tape_process_eod_file chamado no paper antes de solicitar preco ao CEO
  - reflect_all_cycles_history limpo antes de cada backtest — evita contaminacao
  - _executar_paper normaliza XLSX — aceita YYYY-MM-DD TICKER.xlsx via shutil.copy2
  - manutencao() publico — verifica defasagem ORBIT, validade GATE e estado REFLECT por ativo
  - executar_eod() implementado — arquiva xlsx + GATE EOD + paper

notes:
  - 2026-04-14: código modificado — edge.py
  - 2026-04-14: código modificado — edge.py
  - 2026-04-13: código modificado — edge.py
  - 2026-04-12: código modificado — edge.py
  - 2026-04-12: código modificado — edge.py
  - 2026-04-12: código modificado — edge.py
  - opcoes_historico/ — padrao YYYY-MM-DD TICKER.xlsx — snapshots permanentes no Drive
  - B35 aberto: backtest atual nao inclui sizing do REFLECT — sequencia obrigatoria pre-capital real
---
