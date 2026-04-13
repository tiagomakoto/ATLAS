---
uid: mod-delta-003
version: 1.2.1
status: validated
owner: Chan

function: Execucao de estrategias de opcoes. Seleciona, monta e valida estruturas (CSP, Bull Put Spread, Bear Call Spread) com base no regime do ORBIT e sizing modulado pelo REFLECT via EDGE.
file: delta_chaos/fire.py
role: Executor de estruturas — recebe regime e sizing, entrega estrutura validada ou motivo de nao entrada

input:
  - regime: str — regime atual do ORBIT
  - sizing: float — sizing ja modulado pelo REFLECT (vem do EDGE)
  - cotahist: DataFrame — opcoes disponiveis com preco, volume, delta, vencimento
  - cfg_ativo: dict — configuracao do ativo (TP, STOP, delta_alvo, regimes_sizing)

output:
  - estrutura: dict — opcoes selecionadas com preco, delta, contratos, premio
  - motivo_nao_entrada: str — razao para nao abrir posicao (quando aplicavel)

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]

depends_on_condition:
  - reflect_permanent_block_flag=True: bloqueia abertura permanentemente ate protocolo A6

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]

intent:
  - FIRE nao conhece o REFLECT — recebe apenas sizing final modulado pelo EDGE.
  - Separacao de responsabilidades: FIRE executa, EDGE orquestra.

constraints:
  - Iron Condor removido — indeferido permanentemente (liquidez insuficiente B3)
  - REGIME_ESTRATEGIA lido do config + master JSON — nao hardcoded
  - _fallback_sizing removido — era codigo morto
  - reflect_permanent_block_flag verificado antes de qualquer abertura
  - _montar_bear_call: strike vendida deve ter valor MENOR que strike comprada
  - Filtro de liquidez: volume > 0 — VOL_FIN_MIN removido (mercado BR tem liquidez estruturalmente baixa)
  - carregar_config() cacheado no __init__ e abrir() — nao recarrega em loop
  - verificar() recebe configs_ativos como parametro opcional — edge passa cache
  - Timezones: tz_localize(None) em verificar() e abrir()
  - Estrategias implementadas — CSP (ALTA), Bull Put Spread (NEUTRO_BULL), Bear Call Spread (NEUTRO_BEAR)

notes:
  - 2026-04-13: código modificado — fire.py
  - B8 aberto: Calendar Spread para NEUTRO_LATERAL aprovada, nao implementada
  - B39: inconsistencia filtro liquidez backtest vs paper — calibrar apos 1o trimestre
  - B40: Vol. Financeiro do XLSX nao mapeado — avaliar campo correto
  - B44: sem preferencia por vencimento mensal — solucao operacional ativa (CEO filtra XLSX)
  - B45: exercicio antecipado nao modelado — Black-Scholes assume europeia
---
