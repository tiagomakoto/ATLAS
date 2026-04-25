---
date: 2026-04-24
session_type: board
system: delta_chaos

decisions:
  - REFLECT estados redesenhados — E renomeado para T (Tail — supra-REFLECT, evento de cauda)
  - Escala canônica aprovada: A/B/C/D/T
  - Semântica: A=edge forte, B=normal, C=enfraquecendo, D=deteriorado, T=Tail (bloqueio permanente)
  - Sizing canônico por estado: A=1.0+alpha, B=1.0, C=0.5(PE-007), D=0.0, T=0.0+protocolo
  - C=0.5 provisório — suportado por dados empíricos (20 ciclos, 90% reversão p/ B/A)
  - D=0.0 — sizing zero sem protocolo de retomada (retoma normalmente quando volta a B)
  - T mantém protocolo de 5 gates obrigatórios (B02)
  - Douglas (B07) opera na camada sistêmica transversal quando múltiplos ativos atingem D ou T
  - regimes_sizing no JSON do ativo é formalmente redundante — remover em 2 etapas (B56)
  - Fórmula canônica de sizing aprovada:
      sizing_final   = sizing_orbit × sizing_reflect
      sizing_orbit   = 1.0 se IR > threshold | 0.0 se IR ≤ threshold  (ORBIT binário puro)
      sizing_reflect = A→1.0 | B→1.0 | C→0.5(PE-007) | D→0.0 | T→0.0+protocolo(B02)
  - reflect_sizing_calcular() deve usar lookup por estado, não fórmula linear sobre score

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B55_reflect_estados_ABCDX_redesign]]
  - [[BOARD/tensoes_abertas/B56_reflect_sizing_por_estado]]

tensoes_fechadas:

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/TAPE]]
  - [[SYSTEMS/delta_chaos/modules/FIRE]]
  - [[SYSTEMS/atlas/modules/DASHBOARD]]

next_actions:
  - Chan implementar: reflect_sizing_calcular() com lookup A/B/C/D/T
  - Chan implementar: ORBIT binário puro — ignorar regimes_sizing, retornar 1.0 ou 0.0 via IR
  - Chan remover: campo regimes_sizing dos JSONs de todos os ativos
  - Chan remover: leitura de regimes_sizing em tape_ativo_inicializar() e tape_ativo_carregar()
  - Chan atualizar: delta_chaos_config.json — thresholds e nomenclatura T
  - Chan atualizar: reflect_state nos JSONs dos ativos — rerrodar histórico
  - Chan atualizar: ATLAS dashboard — badge e legenda de estados (T = Tail)
  - Dalio atualizar B02 e B04 para refletir renomeação E→T
---
