---
uid: mod-delta-008
version: 1.2
status: validated
owner: Chan

function: Metamodelo de monitoramento da qualidade do edge ao longo do tempo. Opera em dois modos — diario (fotografia de componentes EOD) e ciclo mensal (estado A-E agregado). Vive dentro do TAPE. Dominio primario de Eifert.
file: delta_chaos/tape.py
role: Guardiao do edge — monitora qualidade, modula sizing via multiplicador, bloqueia permanentemente em estado E

input:
  - daily_history: list — componentes diarios acumulados no ciclo corrente
  - reflect_all_cycles_history: list — historico completo de ciclos (limpo antes de cada backtest)
  - cfg_reflect: dict — pesos, thresholds e parametros de janela (delta_chaos_config.json secao reflect)

output:
  - estado_reflect: str — Edge A | Edge B | Edge C | Edge D | Edge E
  - reflect_score: float — score agregado do ciclo
  - sizing_reflect: float — multiplicador de sizing (retornado por tape_sizing_reflect())
  - reflect_permanent_block_flag: bool — True apenas em Edge E

depends_on:
  - [[SYSTEMS/delta_chaos/modules/TAPE]]

depends_on_condition:
  - divergencia_iv_premio: ativo somente apos primeiro arquivo EOD disponivel
  - alpha_edge_A: ativo somente apos primeiro trimestre de paper com divergencia real (B29)

used_by:
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/delta_chaos/modules/BOOK]]
  - [[SYSTEMS/delta_chaos/modules/GATE]]

intent:
  - REFLECT em vol elevada nao diz "pare" — diz "confirme que ainda esta capturando o que acha que esta capturando".
  - Sinal mais valioso nas deterioracoes graduais e silenciosas, nao nos extremos.
  - Vocabulario exclusivo (A-E) — nao misturar com vocabulario do ORBIT (regimes).

constraints:
  - Tres componentes com pesos 0.33/0.33/0.33 (prior inicial — B11 aberto)
  - Componente 1: Aceleracao — derivada segunda do score_vel do ORBIT
  - Componente 2: Divergencia bidirecional — iv_prem_ratio e ret_vol_ratio normalizados
  - Componente 3: Delta_IR — IR medio ultimos 3 ciclos menos IR medio ultimos 6 ciclos
  - Normalizacao via z-score rolling, min_periods = max(3, window//2)
  - Pesos em delta_chaos_config.json secao reflect.weights — nao hardcoded
  - Estado E — bloqueio permanente ate protocolo A6 completo (5 gates)
  - Sizing assimetrico — sobe devagar, desce rapido
  - Edge A: 1.0 + alpha (alpha baseado no score do REFLECT, nao no IR do ORBIT)
  - Edge B: 1.0
  - Edge C: 0.5 (degrau direto, sem gradacao)
  - Edge D: 0.0 (para temporariamente)
  - Edge E: 0.0 + bloqueio permanente
  - Alpha: clip((reflect_score - threshold_A) x alpha_factor, 0, max_cap_alpha)
  - reflect_all_cycles_history limpo no inicio de _executar_backtest — evita contaminacao
  - Vocabulario exclusivo — nao misturar com regimes do ORBIT

notes:
  - Convexidade assimetrica validada: perda media caiu 25% (-R$281 -> -R$212), ganho medio caiu 3%
  - Backtest retroativo VALE3+PETR4 2019-2025 — P&L R$+9.339, IR +3.28, Calmar 2.59
  - Edge A com alpha validado: score=0.892 -> mult=1.288
  - Paper trading com sizing B fixo 1.0 — REFLECT passivo durante coleta
  - B1 aberto: max_cap_alpha nao calibrado
  - B2 aberto: protocolo retomada Edge E nao implementado em codigo
  - B3 aberto: N dias de divergencia para alerta diario
  - B4 aberto: thresholds A-E aguardam Optuna apos 15 ciclos EOD
  - B11 aberto: pesos aguardam calibracao pos primeiro trimestre
  - B28 aberto: bootstrap ciclos 1-3 — estados artificiais, excluir no backtest
  - B29 aberto: alpha Edge A inativo ate primeiro trimestre de paper
  - B35 aberto: backtest sem REFLECT — sequencia obrigatoria pre-capital real
---
