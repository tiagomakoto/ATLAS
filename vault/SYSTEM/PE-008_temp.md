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
     blocos macroeconômicos (expansão de crédito, política fiscal favorável)
     — não são amostras independentes. N=22 trades em 3 blocos temporais
     tem informação equivalente a N ≈ 8-10 observações independentes (Mandelbrot).
  2. Autocorrelação: trades consecutivos no mesmo regime têm correlação positiva
     — o N efetivo é sistematicamente menor que o N contado.
  A tabela de candidatos é provisória — derivada de lógica estrutural de vol
  e não de evidência estatística por ativo.

Compromisso operacional:
  N=15 é o melhor threshold operável dado o histórico atual. Alternativas:
  N=30 bloquearia a maioria dos regimes por amostra insuficiente, tornando
  a eleição competitiva inoperante. Sem threshold, o Optuna overfita
  garantidamente em amostras pequenas.
  O CEO recebe o ranking completo com N de trades por candidato — a confiança
  real é explícita, não encoberta pelo threshold.

Condição de revisão:
  1. Threshold N: revisar após acúmulo de 3+ ciclos de paper trading por regime
     por ativo. Se N efetivo por regime superar 30 trades em algum ativo,
     elevar threshold de eleição competitiva para N=20 naquele ativo.
  2. Tabela de candidatos: revisão anual ou após mudança estrutural de regime
     macroeconômico (ex: mudança de ciclo de juros). Qualquer alteração requer
     deliberação do board e atualização deste PE.
  3. Estratégias estruturais fixas (BAIXA, RECUPERACAO): revisão somente após
     evidência empírica de paper trading que contradiga a lógica de vol — não
     apenas por resultado de um ciclo adverso.
