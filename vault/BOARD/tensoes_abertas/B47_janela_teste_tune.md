---
uid: B47
title: Janela de teste TUNE — critério de definição não formalizado
status: closed
opened_at: 2026-04-12
closed_at: 2026-04-13
opened_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
closed_in: [[BOARD/atas/2026-04-12_tune_v2_escopo]]
decided_by: CEO
system: delta_chaos

description: >
  O TUNE v1.1 fixa ANO_TESTE_INI = 2019 sem critério documentado.
  O período 2019–hoje contém dois eventos de cauda relevantes para
  vendedores de vol no Brasil: Covid março 2020 e ciclo de juros
  2021–2022 (Selic 2% → 13.75%). A escolha foi qualitativa e não
  estava registrada no vault. Três critérios candidatos mapeados pelo
  board para formalização em TUNE v2.0.

gatilho:
  - TUNE v2.0
  - decisão antes de implementar Optuna (janela pode virar hiperparâmetro)

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]

resolution: >
  Resolução parcial — sessão 2026-04-12.

  JANELA COMO HIPERPARÂMETRO OPTUNA:
  O parâmetro janela_anos entra no espaço de busca do Optuna com as
  seguintes restrições hard:

  Restrição 1 — Mandelbrot (máximo temporal):
    Janela máxima de 10 anos. Não extrapola para trás independentemente
    de N por célula. Dados muito antigos têm estrutura de mercado
    diferente — liquidez, microestrutura, comportamento de IV distintos
    do mercado atual.

  Restrição 2 — Taleb/Thorp (cobertura de estresse, abrandada):
    A janela deve conter pelo menos um ciclo com IV rank > P75 do
    próprio ativo (calculado sobre histórico de IV do ativo — nunca
    threshold absoluto). Se o ativo não tiver nenhum ciclo acima de P75
    em toda a sua história disponível, a restrição é dispensada
    automaticamente e a janela máxima de 10 anos é usada.
    DECISÃO DE ABRANDAMENTO: a restrição original exigia dois tipos de
    evento (choque agudo + vol persistente). CEO rejeitou — ativo pode
    legitimamente não ter dois eventos de estresse na janela disponível.
    Forçar dois eventos seria rejeitar janelas válidas por ausência de
    eventos que talvez não existam para aquele ativo.

  Dependência de dados:
    iv_rank por ciclo precisa estar salvo no ORBIT para que a restrição 2
    seja verificável. Mesma dependência de RF03 (delta dinâmico por IV
    rank). Se iv_rank não estiver disponível, apenas restrição 1 é aplicada.

  SISTEMA GRADUADO DE CONFIANÇA POR CÉLULA (regime × estratégia):
    N ≥ 50   → confiança: alta   — otimização Optuna normal
    20 ≤ N < 50 → confiança: baixa  — otimização com aviso explícito no relatório
    N < 20   → amostra_insuficiente — estratégia default congelada, sem otimização

  NUANCE ESTATÍSTICA FORMALIZADA — DECISÃO EMPÍRICA CONSCIENTE:
    O threshold N=50 para confiança alta é um compromisso operacional,
    não um resultado estatístico formal. O board deliberou explicitamente:

    - TLC para distribuições simétricas bem comportadas: N ≈ 30
      (heurística introdutória — não se aplica aqui)
    - TLC para distribuições moderadamente assimétricas: N ≈ 100
      (consenso aplicado — o que o CEO conhecia, está correto)
    - TLC para fat tails financeiros: N = 100–500+
      (literatura de risco — Taleb, Mandelbrot)
    - TLC para fat tails extremos (venda de vol): indeterminado
      (convergência muito lenta — nenhum N finito razoável garante
      robustez formal para a cauda esquerda de P&L de venda de vol)

    N=50 foi escolhido porque o sistema tem poucos dados históricos por
    célula de regime × estratégia. É o melhor que os dados permitem —
    não é estatisticamente robusto no sentido formal. O CEO deve
    interpretar `confiança: alta` com N=50 como "melhor que podemos
    fazer com os dados disponíveis", não como "resultado confiável"
    no sentido estatístico clássico.

    N=30 anterior era chute com verniz estatístico — reconhecido e
    descartado explicitamente pelo board nesta sessão.

  VALIDAÇÃO RETROSPECTIVA DO TUNE v1.1:
    A janela 2019–hoje do TUNE v1.1, antes qualitativa, foi validada
    retrospectivamente por via quantitativa: é o mínimo que cobre dois
    tipos de estresse no mercado brasileiro (choque agudo Covid 2020 +
    vol persistente ciclo de juros 2021–2022). A escolha não foi
    acidente — foi intuição correta sem formalização. Agora está
    documentada.

notes:
  - Conecta com B42 (TUNE v2.0), B11 (Optuna stack), B48 (close d0 vs open d1)
  - Restrição 2 dispensável automaticamente para ativos de baixa vol estrutural
  - Sistema graduado substitui binário N=30 — CEO decide com informação de qualidade
  - iv_rank por ciclo no ORBIT é dependência compartilhada com RF03
  - Decisões empíricas conscientes devem ser registradas no vault — não deixar
    nas conversas. Este registro é modelo para tensões futuras com nuance estatística.
---
