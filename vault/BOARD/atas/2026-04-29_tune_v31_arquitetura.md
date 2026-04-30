---
date: 2026-04-29
session_type: board
system: delta_chaos

decisions:
  - id: D01
    o_que: TUNE v3.1 — arquitetura em duas etapas sequenciais (Etapa A + Etapa B)
    porque: >
      TUNE v3.0 colapsava eleição de estratégia e calibração de TP/Stop numa única
      função objetivo Optuna — objetivos misturados, janela_anos livre gerando
      overfitting, TP/Stop não persistidos no JSON operacional (P1–P5, Chan).
      Separação em Etapa A (eleição, sem Optuna) e Etapa B (calibração, Optuna com
      estratégia fixada) resolve todos os cinco problemas identificados.
    rejeitado: >
      Manter fluxo unificado com correções pontuais — rejeitado porque P1 e P4
      são estruturais e não corrigíveis sem separação de etapas.

  - id: D02
    o_que: Etapa A usa grid fixo (9 combinações) com mediana IR como métrica de eleição
    porque: >
      Grid empiricamente ancorado no histórico do sistema (TP 0.50/0.75/0.90 ×
      Stop 1.50/2.00/2.50). Mediana sobre 9 combinações mede robustez estrutural
      do edge, não performance num ponto ótimo específico. IR da Etapa A é ordinal —
      serve apenas para rankear candidatos, não comparável ao IR da Etapa B.
    rejeitado: >
      (a) TP/Stop neutro fixo único — benchmark arbitrário sem base empírica;
      (b) Optuna por candidato com comparação — overfitting garantido;
      (c) TP/Stop atual do ativo — dependência circular parcial;
      (d) Diagnóstico retrospectivo BOOK — dados ausentes por design para regimes
      com histórico de apenas uma estratégia. Grid fixo venceu por unanimidade
      em votação com fricção (9×0).

  - id: D03
    o_que: Simulação-piloto no ponto central do grid para guarda N_trades_reais
    porque: >
      A guarda que decide entre estrutural_fixo e eleição competitiva precisa de
      N_trades_reais contados dentro da simulação, não ciclos ORBIT (P2).
      Simular 1 vez com candidato estrutural_fixo no ponto central do grid
      (tp_values[1], stop_values[1]) é estimador suficiente para a guarda —
      N não varia materialmente entre pontos do grid para o mesmo regime.
      Resultado reutilizado no grid completo. Economiza 1 simulação por regime.
    rejeitado: >
      (a) Sweep completo antes da guarda — 9×N_candidatos simulações redundantes;
      (b) Manter contagem ORBIT — P2 não corrigido, barreira mais frouxa que aparenta.

  - id: D04
    o_que: janela_anos fixo em config.json — nunca livre no Optuna
    porque: >
      janela_anos livre no Optuna é overfitting de janela implícito — o sampler
      encontra a janela que maximiza IR por acidente, sem valor preditivo (P4).
      Valor padrão 5 anos, configurável, consistente com janela do GATE.
    rejeitado: >
      janela_anos como hiperparâmetro Optuna — rejeitado definitivamente.
      B47 fechada com implementação em v2.0 é obsoleta neste contexto.

  - id: D05
    o_que: Confirmação CEO substituída por aplicação automática com gate de anomalia
    porque: >
      Confirmação manual regime a regime cria compliance theater — CEO confirma
      sem avaliar quando há 20-30 itens por ciclo. O relatório exportado trazido
      ao board já é o mecanismo real de supervisão: o CEO nunca toma decisões
      sozinho. Confirmação manual é redundante com processo mais robusto já existente.
      Gate de anomalia preserva supervisão humana onde ela tem valor: resultados
      patológicos, mudança de estratégia, N insuficiente em regime crítico.
    rejeitado: >
      (a) Confirmação universal por regime — compliance theater, sem valor real;
      (b) Confirmação por ativo (agregada) — melhora UX mas mantém redundância
      com o processo de board.

  - id: D06
    o_que: Critérios de anomalia que pausam aplicação automática e pedem confirmação pontual
    porque: >
      Anomalia = qualquer regime onde o sistema não tem confiança suficiente para
      aplicar automaticamente. Critérios objetivos configuráveis no config.json.
    rejeitado: >
      Lista fechada hardcoded — rejeitado. Critérios devem ser configuráveis.

  - id: D07
    o_que: Nomenclatura — tp/stop na SPEC são apelidos de take_profit/stop_loss no JSON
    porque: >
      JSON real do ativo usa take_profit e stop_loss (lidos por FIRE/GATE/BOOK).
      Renomear fora do escopo desta SPEC — blast radius zero é prioritário.
      tp_por_regime e stop_por_regime são campos novos que convivem com os globais.
      Migração de FIRE/GATE/BOOK para ler tp_por_regime é escopo de B61 completo.
    rejeitado: >
      (a) Rename global take_profit→tp em todos os módulos — fora de escopo, risco real;
      (b) Aliases no JSON — duplicação de dados, sincronização futura problemática.

  - id: D08
    o_que: Cobertura de testes — opção 1 (confirmar atualizado + 2 novos focados)
    porque: >
      Dois vetores de risco distintos requerem testes separados: Etapa A (lógica
      nova sem Optuna) e Etapa B (lógica refatorada com Optuna). _simular_para_candidato
      mockado. Suite completa < 60 segundos. Testes existentes preservados.
    rejeitado: >
      (a) Só atualizar confirmar — Etapas A/B sem cobertura automatizada é risco real;
      (b) Cobertura completa com integração end-to-end — ideal mas não pré-requisito
      para merge nesta entrega.

tensoes_abertas:
  - [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao]]

tensoes_fechadas: []

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/config/delta_chaos_config.json]]

next_actions:
  - Lilian emitiu SPEC_TUNE_v31 v1.0 com 3 adendas — entregar ao Plan
  - Plan lê tune.py antes de qualquer patch (regra Chan)
  - SCAN audita após implementação — obrigatório antes de merge
  - Dalio atualiza decision_log com sessão registrada
---

# Ata — 2026-04-29 — TUNE v3.1 arquitetura

## Contexto
Chan auditou tune.py e identificou 5 problemas estruturais (P1–P5) no TUNE v3.0.
Board deliberou em duas rodadas sobre arquitetura correta, conduziu votação com
fricção sobre mecanismo da Etapa A, e revisou o requisito de confirmação manual CEO.

## Decisões

### D01 — Arquitetura em duas etapas sequenciais
**O que:** TUNE v3.1 separa fluxo em Etapa A (eleição de estratégia, sem Optuna)
e Etapa B (calibração TP/Stop, Optuna com estratégia fixada). Passagem única A→B.
**Por quê:** P1–P5 identificados por Chan são estruturais — não corrigíveis sem separação.
**Rejeitado:** Fluxo unificado com correções pontuais.

### D02 — Grid fixo + mediana IR na Etapa A
**O que:** 9 combinações TP×Stop empiricamente ancoradas no histórico do sistema.
Mediana IR como métrica ordinal de eleição. Lido do config.json, nunca hardcoded.
**Por quê:** Mede robustez estrutural do edge. Venceu votação com fricção por unanimidade (9×0).
**Rejeitado:** Benchmark neutro arbitrário, Optuna por candidato, TP/Stop atual do ativo,
diagnóstico retrospectivo BOOK.

### D03 — Simulação-piloto para guarda N_trades_reais
**O que:** 1 simulação com candidato estrutural_fixo no ponto central do grid antes
do loop de candidatos. N_trades_reais = trades_valido dessa simulação. Resultado reutilizado.
**Por quê:** Estimador suficiente para a guarda. Economiza simulações. Corrige P2.
**Rejeitado:** Sweep completo pré-guarda, manter contagem ORBIT.

### D04 — janela_anos fixo no config.json
**O que:** Nunca variável livre no Optuna. Padrão 5 anos, configurável.
**Por quê:** janela_anos livre é overfitting de janela implícito (P4).
**Rejeitado:** janela_anos como hiperparâmetro — definitivamente.

### D05 — Aplicação automática com gate de anomalia
**O que:** TUNE aplica automaticamente. Pausa e pede confirmação apenas quando
regime apresenta anomalia por critério objetivo.
**Por quê:** Confirmação manual regime a regime é compliance theater. O relatório
trazido ao board já é o mecanismo real de supervisão — CEO nunca decide sozinho.
**Rejeitado:** Confirmação universal por regime, confirmação agregada por ativo.

### D06 — Critérios de anomalia configuráveis
**O que:** Critérios que pausam aplicação automática definidos em config.json.
Incluem obrigatoriamente: mudança de estratégia em relação ao ciclo anterior,
IR abaixo de threshold, N insuficiente em regime crítico, fallback_global acionado.
**Por quê:** Critérios devem ser auditáveis e ajustáveis sem alteração de código.
**Rejeitado:** Lista fechada hardcoded.

### D07 — Apelidos semânticos tp/stop
**O que:** tp/stop na SPEC = take_profit/stop_loss no JSON. Sem rename.
tp_por_regime e stop_por_regime são campos novos. Migração FIRE/GATE/BOOK é B61.
**Por quê:** Blast radius zero prioritário nesta entrega.
**Rejeitado:** Rename global, aliases no JSON.

### D08 — Cobertura de testes: confirmar atualizado + 2 novos
**O que:** test_tune_etapa_a.py + test_tune_etapa_b.py (novos) +
test_tune_confirmar.py (atualizado). Suite < 60 segundos. Mocks obrigatórios.
**Por quê:** Dois vetores de risco distintos requerem cobertura separada.
**Rejeitado:** Só atualizar confirmar, cobertura completa com integração.

## Tensões abertas desta sessão
- [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao]]

## Tensões fechadas desta sessão
Nenhuma.
