---
date: 2026-04-30
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: GATE deve persistir pnl_e5_ano_anterior, pnl_e5_ano_recente e demais campos E5 no historico_config
    porque: E5 falhava silenciosamente — sem os P&L gravados era impossível auditar a causa post-hoc sem rodar o GATE novamente. Confirmado pelo novo relatório VALE3 (2026-04-30) que mostra IR(2026)=+0.206 P&L=R$-124.73 — causa exata identificada.
    rejeitado: nenhuma alternativa deliberada

  - id: D02
    o_que: Relatório de calibração deve ler campos estruturados do historico_config, não regex sobre campo motivo
    porque: SCAN identificou ~12 campos extraídos por regex frágil — qualquer refatoração de string silencia campos sem erro. Causa-raiz dos campos "—" no Step 2 do relatório.
    rejeitado: manter regex como fonte primária

  - id: D03
    o_que: TUNE deve persistir campos estruturados por regime — n_trades_reais, eleicao_status, anomalia_motivos, etc.
    porque: O historico_config foi projetado como log de texto para humanos — não como fonte de dados para relatórios. A correção estrutural é gravar o que o relatório precisa no momento da execução.
    rejeitado: continuar usando campo motivo como fonte

  - id: D04
    o_que: Bug matemático na seção distribuição de saídas corrigido — percentual individual por tipo calculado corretamente
    porque: Três linhas (TP, STOP, VENC) usavam acerto_pct para todas — percentuais individuais não eram calculados.
    rejeitado: nenhuma alternativa

  - id: D05
    o_que: Budget Optuna TUNE v3.1 proposto para 150 trials / patience=40 / startup=30 (PE-010)
    porque: Simons identificou que 100 trials com startup=30 deixa apenas 70 trials TPE efetivos — margem estreita para discriminar platôs adjacentes. 150 trials → 120 trials TPE efetivos, cobertura confortável para espaço 2D.
    rejeitado: manter 100 (insuficiente), voltar para 200 B23 (conservador demais)
    status: pendente confirmação CEO

  - id: D06
    o_que: Bug de timezone no gerador de relatórios — arquivo gerado às 21h+ de 29/04 recebe data 30/04 por usar UTC
    porque: datetime.now() em servidor retorna UTC. Brasil é GMT-3 — às 21h local são 00h UTC do dia seguinte.
    rejeitado: nenhuma alternativa deliberada

tensoes_abertas:
  - B65_timezone_relatorio (nova — ver abaixo)

tensoes_fechadas:
  - nenhuma nesta sessão

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/GATE]]
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/atlas/modules/relatorios]]

next_actions:
  - CEO: confirmar D05 (budget 150/40/30) para Chan aplicar patch no config
  - Chan: aplicar SPEC rastreabilidade relatório (3 módulos — gate.py, tune.py, relatorios.py) após confirmação CEO
  - Chan: corrigir timezone em relatorios.py (B65)
  - Dalio: PE-010 gravado em principios_empiricos.md
---

# Ata — 2026-04-30 — Rastreabilidade do relatório de calibração

## Contexto

Sessão motivada por duas evidências concretas:
1. Relatório GATE VALE3 (2026-04-29) com campos "—" em toda a seção de qualidade da otimização e E5 sem P&L visível
2. CEO identificou que sem os dados no relatório, rastreabilidade de decisões é impossível

SCAN realizou auditoria completa do relatório e seus módulos fonte.

## Achados SCAN

### Bug E5 — confirmado e corrigido em produção
O relatório de 2026-04-30 já mostra o patch aplicado:
`E5 ORBIT | ✗ | IR(2025)=+0.124 P&L=R$+1,259.03 | IR(2026)=+0.206 P&L=R$-124.73`

Causa da falha E5 confirmada: P&L 2026 = -R$124,73 com apenas 4 ciclos ORBIT em jan–abr/2026.
IR alto (+0.206) é eficiência por trade — não lucro agregado.

### Inventário de falhas (SCAN completo)
- 3 bugs matemáticos (distribuição de saídas, janela_anos=0, IR via regex sobre registro v3.1)
- 10+ campos calculados não persistidos
- ~12 campos extraídos por regex frágil sobre campo `motivo`
- 6 campos estruturalmente ausentes

Causa-raiz: `historico_config` projetado como log de texto — relatório tenta reverter engenharia do texto.

### Spec produzida por Lilian
Três módulos, escopo cirúrgico:
1. `gate.py` — adicionar 9 campos E5 ao historico_config
2. `tune.py` — adicionar ~14 campos estruturados por regime
3. `relatorios.py` — ler campos estruturados (não regex), corrigir bug matemático, adicionar seção E5

## Trials Optuna — divergência histórica documentada

Simons identificou que a implementação atual (100 trials) diverge do B23 original (200 trials)
sem registro de decisão consciente. Recomendação: 150/40/30 como ponto médio razoável.
PE-010 registrado no vault. Aguarda confirmação CEO para Chan aplicar.

## Bug de timezone

Arquivo gerado às 21h+ de 29/04 (horário de Brasília) recebe data 30/04 no nome.
Causa: `datetime.now()` usa UTC no servidor — às 21h local = 00h UTC do dia seguinte.
Correção: `datetime.now(tz=ZoneInfo('America/Sao_Paulo'))` ou equivalente.
Tensão B65 aberta.
