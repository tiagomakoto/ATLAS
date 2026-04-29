SPEC_TUNE_v31 — Arquitetura em duas etapas: eleição de estratégia + calibração TP/Stop por regime
Versão: 1.0 | Data: 2026-04-29 | Refs: B61, B62 | Decisões: sessão board 2026-04-29

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCO 1 — CONTEXTO

Sistema: Delta Chaos — módulo TUNE
Arquivo principal: delta_chaos/tune.py
Camada: backend Python, sem interface direta com ATLAS nesta entrega
Tecnologias relevantes: Optuna (TPE), pandas, numpy, escrita atômica
  via tempfile + os.replace (padrão BUG-03 obrigatório)

O TUNE v3.0 atual faz eleição competitiva de estratégia por regime
rodando Optuna com TP, Stop e janela_anos como dimensões livres
simultaneamente. O TUNE v3.1 separa esse fluxo em duas etapas
sequenciais e distintas.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCO 2 — SITUAÇÃO ATUAL

Função principal: tune_eleicao_competitiva(ticker) em tune.py

Problemas a corrigir (P1 a P5, identificados por Chan em sessão board):

P1 — Objetivos misturados: o Optuna varia (tp, stop, janela_anos,
  estrategia) numa única função objetivo. TP/Stop que emergem são
  subproduto da busca de estratégia, não calibração independente.

P2 — N por regime incorreto: n_por_regime conta ciclos ORBIT,
  não trades reais simulados. A guarda N_MINIMO=15 protege contra
  ciclos — barreira mais frouxa do que aparenta.

P3 — IR floor PE-009 ativo sem revisão agendada:
  _std_floor = max(_std_v, abs(_mean_v) * 0.10, 1e-6)
  Provisório, mas sem gatilho de revisão explícito no código.

P4 — janela_anos livre no Optuna: o sampler escolhe a janela
  que maximiza IR — overfitting de janela implícito.

P5 — Confirmação CEO não persiste TP/Stop: o endpoint
  POST /delta-chaos/tune/confirmar-regime confirma estratégia_eleita
  mas não grava tp e stop por regime nos campos lidos por
  FIRE, GATE e BOOK. A cadeia de confirmação está incompleta.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCO 3 — COMPORTAMENTO DESEJADO

A função tune_eleicao_competitiva(ticker) deve ser reescrita
com fluxo sequencial A→B, passagem única, sem iteração.

─── ETAPA A — Eleição de estratégia (sem Optuna) ───────

Para cada regime:

  1. Se candidatos = [] → status "bloqueado". Nenhuma simulação.

  2. Se N_trades_reais < N_MINIMO → status "estrutural_fixo".
     Usa estrategia_estrutural_fixo[regime] do config.json.
     N_trades_reais é contado DENTRO da simulação com os
     parâmetros do grid neutro — não ciclos ORBIT.

  3. Se N_trades_reais >= N_MINIMO → eleição competitiva:
     Simula cada candidato UMA VEZ com o grid neutro fixo.
     Grid lido de config.json → tune.referencia_eleicao:
       tp_values:   [0.50, 0.75, 0.90]
       stop_values: [1.50, 2.00, 2.50]
       → 9 combinações por candidato
     Métrica de eleição: mediana do IR sobre as 9 combinações.
     Vencedora: candidato com maior mediana.
     IR da Etapa A é ORDINAL — não comparável ao IR da Etapa B.
     O relatório deve deixar isso explícito.

Gravação após Etapa A (atômica, por regime):
  tune_ranking_estrategia[regime]:
    eleicao_status: "bloqueado" | "estrutural_fixo" | "competitiva"
    estrategia_eleita: <string> | null
    ir_eleicao_mediana: <float>  ← novo campo
    ranking_eleicao: [{estrategia, ir_mediana, n_trades_reais}]
    confirmado: false

─── ETAPA B — Calibração TP/Stop (Optuna) ──────────────

Executada somente para regimes com eleicao_status
"competitiva" ou "estrutural_fixo" com estrategia definida.

  1. Estratégia fixada pela Etapa A — não é variável do Optuna.

  2. janela_anos fixo, lido de config.json → tune.janela_anos.
     NUNCA livre no Optuna. Valor padrão: 5.

  3. N_trades_reais contado dentro da simulação da Etapa B
     com a estratégia fixada e janela fixa.
     Se N_trades_reais < tune.n_minimo_calibracao (config.json):
       status_calibracao: "fallback_global"
       tp e stop herdados dos campos globais tp e stop do
       JSON do ativo — não otimizados.

  4. Se N_trades_reais >= tune.n_minimo_calibracao:
       Optuna varia apenas tp e stop.
       Espaço de busca lido do config.json:
         tp:   min, max, step
         stop: min, max, step
       status_calibracao: "calibrado"

  5. IR floor PE-009 mantido como está — não alterar.
     Adicionar comentário explícito no código:
     # PE-009 provisório — revisão gatilhada por B62 após
     # 1 trimestre paper trading TUNE v3.1

Gravação após Etapa B (atômica, por regime):
  tune_ranking_estrategia[regime] atualizado com:
    status_calibracao: "calibrado" | "fallback_global"
    tp_calibrado: <float>
    stop_calibrado: <float>
    ir_calibrado: <float>  ← novo campo, distinto de ir_eleicao
    n_trades_calibracao: <int>
    janela_anos: <int>
    trials_rodados: <int>

─── CONFIRMAÇÃO CEO (P5) ────────────────────────────────

O endpoint POST /delta-chaos/tune/confirmar-regime deve,
após confirmação explícita do CEO, gravar atomicamente
no JSON do ativo os seguintes campos:

  estrategias[regime]: <estrategia_eleita>
  tp_por_regime[regime]: <tp_calibrado ou tp global se fallback>
  stop_por_regime[regime]: <stop_calibrado ou stop global se fallback>

Estes campos são os que FIRE, GATE e BOOK devem ler.
Se tp_por_regime ou stop_por_regime não existirem no JSON
do ativo (ativos migrados de v3.0), FIRE/GATE/BOOK fazem
fallback para os campos globais tp e stop — sem erro.

─── RELATÓRIO ───────────────────────────────────────────

O relatório gerado ao final deve exibir por regime:
  - Estratégia eleita (e se mudou em relação à atual)
  - IR_eleicao_mediana (Etapa A) — com label "ordinal"
  - IR_calibrado (Etapa B) — com label "calibrado"
  - TP e Stop calibrados (ou "fallback global" se aplicável)
  - N_trades_reais usado em cada etapa
  - status_calibracao por regime

Sinalização obrigatória:
  - Se estrategia_eleita != estrategias[regime] atual →
    exibir "MUDANÇA DE ESTRATÉGIA" em destaque
  - Se status_calibracao = "fallback_global" →
    exibir "N INSUFICIENTE — usando parâmetros globais"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCO 4 — O QUE NÃO DEVE SER TOCADO

- tune_diagnostico_estrategia(): mantida intacta — função
  independente de análise retrospectiva do BOOK.

- Gravação atômica via tempfile + os.replace: padrão
  BUG-03, obrigatório em todas as escritas. Não simplificar.

- Máscara REFLECT: lógica de bloqueio por estado C/D/E/T
  idêntica entre candidatos do mesmo regime — não alterar.

- Emissão de eventos WebSocket (emit_dc_event): manter
  todos os eventos existentes. Adicionar novos eventos para
  Etapa A e Etapa B separadamente se necessário, mas não
  remover os existentes.

- Campos globais tp e stop no JSON do ativo: não remover.
  São o fallback quando tp_por_regime/stop_por_regime
  não existem. FIRE/GATE/BOOK leem esses campos hoje —
  a migração para tp_por_regime é feita gradualmente
  via confirmação CEO, não por escrita automática do TUNE.

- FIRE, GATE, BOOK: fora do escopo desta SPEC.
  A leitura de tp_por_regime por esses módulos é escopo
  de SPEC separada (B61 — TUNE v3.1 completo).
  Esta SPEC entrega apenas o TUNE e o endpoint de confirmação.

- config.json: o Plan deve ler a estrutura atual de
  config.json["tune"] antes de adicionar campos novos.
  Não remover campos existentes. Adicionar apenas:
    tune.referencia_eleicao.tp_values
    tune.referencia_eleicao.stop_values
    tune.janela_anos
    tune.n_minimo_calibracao

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TENSÃO ABERTA ASSOCIADA

B62 — range Stop [1.50, 2.00, 2.50] reconhecido como amplo
para um sistema vendedor de vol. Grid implementado como
configurável em config.json (tune.referencia_eleicao.stop_values).
Revisão agendada após 1 trimestre de paper trading com v3.1.
O Plan NÃO deve alterar o range — apenas garantir que é
lido do config, nunca hardcoded.