# Princípios Empíricos — Delta Chaos
Registro de decisões que combinam teoria e pragmatismo operacional.
Cada entrada documenta: o que foi decidido, por que, e qual é a limitação conhecida.
Objetivo: resgatar via vault o raciocínio por trás de números e escolhas que
parecem arbitrárias fora de contexto.

Atualizado por: Dalio (Relojoeiro)
Criado em: 2026-04-12

---

## Como usar este documento

Quando uma decisão do board envolver um número, threshold ou critério que:
- Parece consenso mas não é derivado formalmente
- É compromisso entre rigor e operacionalidade
- Tem limitação estatística conhecida e aceita conscientemente

→ Registrar aqui com o template abaixo.

---

## Template de entrada

```
### PE-XXX — [título curto]
Data: YYYY-MM-DD
Tensão relacionada: [[uid]]
Decisão: [o número ou critério adotado]
Justificativa formal: [o que a teoria diz]
Limitação conhecida: [onde a teoria falha para este caso]
Compromisso operacional: [por que adotamos mesmo assim]
Condição de revisão: [quando rever]
```

---

## Registro de Princípios

---

### PE-001 — N mínimo por célula para confiança de amostra no TUNE
Data: 2026-04-12
Tensão relacionada: [[BOARD/tensoes_abertas/B47_janela_teste_tune]]

Decisão adotada:
  N ≥ 50  → confiança alta   (otimização Optuna normal)
  20–49   → confiança baixa  (otimização com aviso no relatório)
  N < 20  → amostra_insuficiente (default congelado, sem otimização)

Justificativa formal:
  O Teorema do Limite Central (TLC) estabelece convergência para a normal
  conforme N cresce — mas o N necessário depende da distribuição:
  - Distribuições simétricas bem comportadas: N ≈ 30 (heurística introdutória)
  - Distribuições moderadamente assimétricas: N ≈ 100 (consenso aplicado)
  - Fat tails financeiros: N = 100–500+ (literatura de risco)
  - Fat tails extremos (venda de vol, cauda esquerda pesada): indeterminado
    — convergência muito lenta, nenhum N finito garante robustez formal da cauda

Limitação conhecida:
  N=50 está abaixo do N=100 que seria o mínimo honesto para distribuições
  moderadamente assimétricas. Para a distribuição específica de P&L de venda
  de volatilidade — assimétrica positiva com cauda esquerda pesada — N=50
  é insuficiente para estimar a cauda com precisão. Trades de venda de vol
  têm autocorrelação entre ciclos consecutivos no mesmo regime, reduzindo
  o N efetivo abaixo do N observado.

Compromisso operacional:
  O sistema tem poucos ciclos históricos por célula de regime × estratégia.
  Elevar o threshold para N=100 bloquearia a maioria das células por
  amostra insuficiente, tornando o TUNE v2.0 inoperante. N=50 é o melhor
  que os dados disponíveis permitem — não é estatisticamente robusto no
  sentido formal. `confiança: alta` com N=50 significa "melhor que podemos
  fazer com os dados disponíveis", não "resultado confiável" no sentido
  clássico. O CEO deve ter isso em mente ao interpretar relatórios do TUNE.

Condição de revisão:
  Revisar após acúmulo de dados de paper trading por regime. Se o sistema
  acumular N ≥ 100 trades válidos por célula para algum ativo, elevar o
  threshold de confiança alta para N=100 naquele ativo.

Origem da confusão histórica:
  N=30 foi citado inicialmente pelo board como "consenso estatístico" —
  reconhecido e descartado explicitamente na sessão de 2026-04-12. N=30
  é heurística para distribuições simétricas e não tem aplicação válida
  para retornos de venda de volatilidade.

---

### PE-002 — Slippage de 10% na simulação do TUNE
Data: 2026-04-12
Tensão relacionada: [[BOARD/tensoes_abertas/B49_slippage_revisao_paper]]

Decisão adotada:
  Slippage de 10% aplicado na simulação como parâmetro provisório.

Justificativa formal:
  Nenhuma — não há base empírica de execução real para este sistema
  neste mercado com estes ativos. Foi definido antes do paper trading.

Limitação conhecida:
  Pode super ou subestimar o custo real de execução. Slippage varia por
  ativo (BOVA11 mais líquido que BBAS3), por regime (vol elevada aumenta
  spread bid-ask), e por tamanho de posição. Um valor único para todos
  os ativos é necessariamente uma aproximação grosseira.

Compromisso operacional:
  Sem dados reais de execução, qualquer valor é arbitrário. 10% foi
  escolhido como conservador o suficiente para não inflar artificialmente
  o P&L simulado. É placeholder consciente — não calibração.

Condição de revisão:
  Após mínimo de 10 trades executados por ativo em paper trading.
  Calcular slippage real como (prêmio_alvo - prêmio_executado) / prêmio_alvo
  por ativo. Substituir valor único por parâmetro por ativo em
  delta_chaos_config.json.

---

### PE-003 — Entrada close d0 como proxy de open d1 no TUNE
Data: 2026-04-12
Tensão relacionada: [[BOARD/tensoes_abertas/B48_entrada_close_d0_vs_open_d1]]

Decisão adotada:
  TUNE v1.1 usa fechamento de d0 como preço de entrada.
  Na operação real, a entrada é no open de d1.

Justificativa formal:
  Nenhuma — é um viés de implementação, não uma decisão consciente.
  Foi identificado como bug de simulação na sessão de 2026-04-12.

Limitação conhecida:
  O backtest é sistematicamente otimista na entrada. Em dias de alta
  volatilidade — quando o sinal de entrada é mais forte — o gap entre
  fechamento de d0 e abertura de d1 é maior, amplificando o viés
  exatamente nos dias mais relevantes. O P&L simulado do TUNE v1.1
  está inflado por viés de entrada em magnitude desconhecida.

Compromisso operacional:
  Mantido no TUNE v1.1 por não ter dado de abertura de opções facilmente
  disponível no TAPE atual. Correção obrigatória no TUNE v2.0.
  Proxy alternativo se abertura não estiver disponível:
  fechamento_d0 × (1 + fator_gap) com fator calibrável por ativo.

Condição de revisão:
  Corrigir em TUNE v2.0 — obrigatório antes de migração para capital real.
  Verificar se GATE e FIRE têm o mesmo viés (impacto sistêmico provável).

---

### PE-004 — Janela de teste fixa 2019 no TUNE v1.1
Data: 2026-04-12
Tensão relacionada: [[BOARD/tensoes_abertas/B47_janela_teste_tune]]

Decisão adotada:
  ANO_TESTE_INI = 2019 fixo no código do TUNE v1.1.

Justificativa formal:
  Nenhuma formalizada à época — escolha qualitativa não documentada.
  Validada retrospectivamente na sessão de 2026-04-12 por conter:
  - Covid março 2020: choque agudo de vol (IV rank extremo, duração < 60 dias)
  - Ciclo de juros 2021–2022: vol persistente (Selic 2% → 13.75%, ~18 meses)
  Dois tipos de regime de estresse distintos — relevantes para vendedores de vol.

Limitação conhecida:
  A cobertura de dois eventos de estresse foi acidental — resultado da
  história do mercado brasileiro 2019–2026, não de critério projetado.
  Em outro período histórico, a mesma janela poderia não conter nenhum
  evento de estresse relevante.

Compromisso operacional:
  Mantido no v1.1 por ausência de critério formal melhor à época.
  No TUNE v2.0, a janela vira hiperparâmetro do Optuna com restrições
  formalizadas em B47.

Condição de revisão:
  TUNE v2.0 — janela deixa de ser fixa.

---

### PE-005 — Thresholds de transição entre estados REFLECT A–E
Data: 2026-04-13
Tensão relacionada: [[BOARD/tensoes_abertas/B04_thresholds_A_E_optuna]]

Decisão adotada:
  Thresholds de classificação do score_reflect em estados Edge:
  A  → score ≥  0.70
  B  → score ∈ [-0.30, 0.70)
  C  → score ∈ [-0.70, -0.30)
  D  → score ∈ [-1.20, -0.70)
  E  → score <  -1.20
  (valores em delta_chaos_config.json → reflect.thresholds)

Justificativa formal:
  Nenhuma derivação teórica. Os thresholds não emergem de distribuição
  estatística conhecida do score_reflect. A distribuição empírica do score
  ao longo dos ciclos históricos não foi diagnosticada antes da fixação
  dos valores — o que significa que os cortes A/B/C/D/E não correspondem
  necessariamente a percentis significativos da distribuição real.

Limitação conhecida:
  Com thresholds arbitrários sobre uma distribuição não diagnosticada,
  a frequência de ciclos em cada estado é desconhecida. Pode haver
  concentração excessiva em B (estado neutro) ou em A (estado ótimo),
  tornando os estados C/D/E raramente atingidos — ou o inverso.
  O score_reflect histórico foi calculado sem o componente de divergência
  IV (divergencia_disponivel: False em ~100% dos ciclos históricos),
  o que significa que a distribuição atual do score é parcial e mudará
  quando o componente de divergência for ativado com dados EOD reais.
  Os thresholds foram calibrados intuitivamente para uma distribuição
  que ainda não existe de forma completa.

Compromisso operacional:
  Placeholders conservadores suficientes para operar durante o período
  de coleta de dados. Estado B como default é seguro — não bloqueia
  nem amplifica sizing sem evidência. A fixação foi consciente:
  operar com thresholds provisórios é melhor que não operar.

Condição de revisão:
  Após 15 ciclos EOD com divergência ativa (componente IV/Prêmio e
  Ret/Vol preenchidos). Calibrar via Optuna maximizando Calmar ratio
  sobre a distribuição empírica completa do score. Quando recalibrado,
  reflect_cycle_history[] deve ser rerrodado para todos os ciclos
  históricos com os novos thresholds — o campo reflect_state salvo
  por ciclo (patch 2026-04-13) será atualizado nesse momento.

### PE-006 — Pesos dos componentes REFLECT (aceleração / divergência / delta_IR)
Data: 2026-04-13
Tensão relacionada: [[BOARD/tensoes_abertas/B11_pesos_reflect_optuna]]

Decisão adotada:
  Pesos iniciais: aceleração=0.33, divergência=0.33, delta_IR=0.33
  (prior de máxima ignorância — distribuição uniforme entre componentes)
  (valores em delta_chaos_config.json → reflect.weights)

Justificativa formal:
  Sem teoria que prescreva pesos ótimos entre os três componentes.
  Prior uniforme é o único estado epistêmico honesto na ausência de
  dados: afirmar que qualquer componente é mais informativo que outro
  sem evidência seria introduzir viés sem fundamento.

Limitação conhecida:
  0.33/0.33/0.33 não significa que os componentes têm igual impacto
  real sobre a qualidade do edge — significa que não sabemos qual
  importa mais. O componente de divergência (IV/Prêmio e Ret/Vol)
  está inativo em praticamente todos os ciclos históricos
  (divergencia_disponivel: False), o que significa que o peso de 0.33
  para divergência é nominal — na prática os outros dois dividem 1.0
  via renormalização automática. O prior uniforme está sendo aplicado
  sobre três componentes dos quais apenas dois funcionam atualmente.

Compromisso operacional:
  Mínimo de 24 ciclos com os três componentes ativos simultaneamente
  antes de qualquer recalibração. Condição de melhoria mínima: 20%
  de ganho no Calmar ratio como critério para mudar pesos — proteção
  contra overfitting em amostra pequena.

Condição de revisão:
  Após primeiro trimestre de paper trading com componente de divergência
  ativo. Optuna como stack compartilhado com TUNE v2.0 — mesma
  biblioteca, mesma filosofia, implementação conjunta (decisão B11
  sessão 2026-04-12).

---

### PE-008 — N mínimo para eleição competitiva de estratégia no TUNE e tabela de candidatos admissíveis
Data: 2026-04-25
Tensão relacionada: [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]

Decisão adotada:
  N mínimo para eleição competitiva: 15 trades por regime.
  Abaixo de 15: candidato estrutural fixo (definido por lógica de vol — Eifert),
  sem rodada de Optuna competitivo.

  Tabela de candidatos admissíveis por regime:
  ALTA:             [CSP, BULL_PUT_SPREAD]
  BAIXA:            [BEAR_CALL_SPREAD]           — estrutural fixo (N irrelevante)
  NEUTRO:           [BULL_PUT_SPREAD, CSP]
  NEUTRO_BULL:      [BULL_PUT_SPREAD, CSP]
  NEUTRO_BEAR:      [BEAR_CALL_SPREAD, BULL_PUT_SPREAD]
  NEUTRO_TRANSICAO: [BEAR_CALL_SPREAD, BULL_PUT_SPREAD]
  NEUTRO_LATERAL:   [BULL_PUT_SPREAD, BEAR_CALL_SPREAD]
  NEUTRO_MORTO:     []                           — bloqueado
  PANICO:           []                           — bloqueado
  RECUPERACAO:      [BULL_PUT_SPREAD]            — estrutural fixo (N irrelevante)

Justificativa formal:
  Para comparar dois candidatos com poder discriminatório mínimo, o intervalo
  de confiança do IR de cada candidato não deve englobar zero. Com variância
  típica de sistemas de venda de vol (acerto ~85%, stop ocasional), o limiar
  prático é N ≈ 15 trades. Abaixo disso, a eleição é aleatória disfarçada
  de otimização.

  Candidatos por regime derivam de lógica estrutural de volatilidade
  (Eifert, sessão 2026-04-25):
  - ALTA: vendedor de put OTM natural (CSP). BPS adiciona proteção se rally violento.
  - BAIXA: BCS único — CSP em queda é posição estruturalmente incorreta.
  - NEUTRO_BEAR: BCS natural por convexidade. BPS alternativa se skew pronunciado.
  - NEUTRO_LATERAL: spread preferível a posição nua em vol comprimida.
  - RECUPERACAO: BPS único — Livermore: momentum emergente com risco definido.
  - NEUTRO_MORTO/PANICO: vol insuficiente ou fat tail ativo — bloqueados.

Limitação conhecida:
  N=15 está abaixo do N=100 formalmente adequado para distribuições assimétricas
  com fat tail. Para venda de vol, N efetivo é menor que N observado por dois
  motivos:
  1. Clustering temporal: ciclos de ALTA de BBAS3, por exemplo, ocorrem em
     blocos macroeconômicos — não são amostras independentes. N=22 trades em
     3 blocos temporais tem informação equivalente a N ≈ 8-10 observações
     independentes (Mandelbrot, sessão 2026-04-25).
  2. Autocorrelação: trades consecutivos no mesmo regime têm correlação positiva
     — o N efetivo é sistematicamente menor que o N contado.
  A tabela de candidatos é provisória — derivada de lógica estrutural de vol
  e não de evidência estatística por ativo.

Compromisso operacional:
  N=15 é o melhor threshold operável dado o histórico atual. N=30 bloquearia
  a maioria dos regimes; sem threshold, overfitting garantido.
  O CEO recebe ranking completo com N de trades por candidato — confiança
  real explícita, não encoberta pelo threshold.

Condição de revisão:
  1. Threshold N: revisar após 3+ ciclos de paper trading por regime por ativo.
     Se N efetivo superar 30 trades em algum ativo, elevar threshold para N=20.
  2. Tabela de candidatos: revisão anual ou após mudança estrutural de regime
     macroeconômico. Qualquer alteração requer deliberação do board.
  3. Estratégias estruturais fixas (BAIXA, RECUPERACAO): revisão somente após
     evidência empírica de paper trading — não por resultado de um ciclo adverso.

---

### PE-009 — Floor relativo de desvio padrão no cálculo de IR por regime no TUNE v3.0
Data: 2026-04-25
Tensão relacionada: [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva]]

Decisão adotada:
  `_std_floor = max(std, |mean| * 0.10, 1e-6)`
  aplicado antes da divisão `IR = mean / _std_floor * sqrt(252/21)`.
  Resulta em IR máximo teórico de ~34.6 (= 10 * sqrt(12)) para qualquer regime.

Justificativa formal:
  Com alta taxa de win e prêmios similares entre trades (ex: NEUTRO_BEAR
  BEAR_CALL_SPREAD em VALE3), `np.std(pnls)` pode ser ordens de magnitude
  menor que `np.mean(pnls)`. O IR calculado como `mean / (std + 1e-10)` gera
  valores de 50–300 — matematicamente corretos mas operacionalmente sem sentido.
  Nenhum sistema real de venda de vol sustenta IR > 5 em base anualizada com
  N suficiente para ser confiável. IR=264 observado em VALE3 NEUTRO_BEAR é
  artefato de dispersão baixa, não evidência de edge superior.

Limitação conhecida:
  O floor de 10% é arbitrário — não há teoria que justifique exatamente 10%
  como limiar de dispersão mínima "aceitável". Um floor muito alto comprime
  IR de regimes genuinamente estáveis; um floor muito baixo não resolve o
  problema. 10% foi escolhido por produzir um IR máximo (~35) que é
  plausível para sistemas reais de alta qualidade.
  O floor altera a função objetivo do Optuna — dois candidatos com mesmo
  P&L mas dispersões diferentes terão IRs distintos após o floor, o que
  é o comportamento desejado mas implica que o ranking competitivo passa
  a penalizar explicitamente estratégias com P&L muito concentrado
  (baixa dispersão = suspeita de regime de amostra pequena).

Compromisso operacional:
  Solução cirúrgica para impedir que eleição competitiva seja distorcida
  por artefato numérico. NEUTRO_BEAR de VALE3 pode continuar sendo
  BEAR_CALL_SPREAD — mas por margem de IR plausível (ex: 5.0 vs 3.5),
  não por margem de IR impossível (264 vs -0.56).

Condição de revisão:
  Após 24 ciclos de paper trading por regime. Se IR real observado em
  paper trading sistematicamente divergir dos IRs reportados pelo TUNE v3.0,
  recalibrar o floor. Candidato: substituir por Calmar ratio (PE-008 já
  menciona como alternativa para séries curtas).

---

### PE-010 — Budget Optuna do TUNE v3.1 (trials / patience / startup)
Data: 2026-04-30
Tensão relacionada: [[BOARD/decisoes/B23_criterio_parada_tune]] (fechada)

Histórico de decisões:
  B23 (2026-04-13, TUNE v2.0): 200 trials / patience=50 / startup=50
  Implementação TUNE v3.1 atual: 100 trials / patience=30 / startup=30
  Recomendação Simons (2026-04-30): 150 trials / patience=40 / startup=30

Decisão adotada (pendente confirmação CEO):
  Proposta Simons: trials_por_candidato=150, early_stop_patience=40, startup=30
  Parâmetros em delta_chaos_config.json → tune.trials_por_candidato
                                        → tune.early_stop_patience
  startup_trials é parâmetro interno do TPESampler — não exposto no config atual.

Justificativa formal (Simons, sessão 2026-04-30):
  O TPE (Tree-structured Parzen Estimator) opera em duas fases:
  1. Fase exploratória (startup): os primeiros N trials exploram o espaço
     uniformemente — sem modelo interno de probabilidade. A qualidade das
     estimativas do TPE só emerge após o startup.
  2. Fase explotativa: TPE usa os resultados anteriores para guiar busca.
     Em espaços de baixa dimensionalidade (2D: TP × Stop), convergência
     tipicamente ocorre em 50–80 trials TPE efetivos.

  Com startup=30:
  - Budget 100 (atual):    70 trials TPE efetivos — margem estreita para platôs
  - Budget 150 (proposto): 120 trials TPE efetivos — cobertura confortável 2D
  - Budget 200 (B23):     150 trials TPE efetivos — conservador, ~2× o necessário

  Risco principal não é não encontrar o ótimo global, mas não distinguir
  o ótimo de um platô adjacente quando dois candidatos têm IRs próximos
  após o floor PE-009.

Limitação conhecida:
  150 trials não deriva de análise de convergência específica para a distribuição
  de P&L de VALE3/PETR4/BOVA11/BBAS3 — é compromisso qualitativo.
  O espaço discreto TP × Stop tem 108 combinações — grid exaustivo seria
  viável neste subconjunto, mas o Optuna cobre também variações contínuas.
  Se janela_anos for adicionada como terceiro hiperparâmetro no TUNE v3.2,
  o startup=30 pode ser insuficiente para o espaço 3D resultante.

  Divergência entre B23 (200 trials) e implementação atual (100 trials)
  não foi documentada como decisão consciente — foi redução silenciosa
  durante implementação. Este PE registra a divergência formalmente.

Compromisso operacional:
  150/40/30 equilibra:
  - Tempo de execução (~4min estimado vs ~2m42s com 100 trials)
  - Cobertura do espaço de busca
  - Risco de não discriminar platôs adjacentes com IRs próximos

Condição de revisão:
  Após 1 trimestre de paper trading. Critério de estabilidade: duas rodadas
  consecutivas no mesmo ciclo produzindo TP/Stop dentro de ±0.05/±0.25
  indicam budget suficiente → reduzir para 120. Divergência maior → elevar
  para 200 (retornar ao B23 original).

---

*Dalio (Relojoeiro) — atualizado em 2026-04-30*
*Este documento deve ser atualizado sempre que o board tomar decisão empírica consciente.*
*Convenção de uid: PE-XXX sequencial por data de registro.*
