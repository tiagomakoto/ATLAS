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

*Dalio (Relojoeiro) — atualizado em 2026-04-13*
*Este documento deve ser atualizado sempre que o board tomar decisão empírica consciente.*
*Convenção de uid: PE-XXX sequencial por data de registro.*
