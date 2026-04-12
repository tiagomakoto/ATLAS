---
uid: B46
title: ADVANTAGE — integração de dados externos ao Delta Chaos
status: open
opened_at: 2026-04-11
closed_at:
opened_in: [[BOARD/atas/2026-04-11_advantage_data_layer]]
closed_in:
decided_by:
system: transversal

description: >
  Proposta de integração do ADVANTAGE Data Layer como fonte de dados
  externos ao Delta Chaos. O ADVANTAGE oferece três níveis de dado:
  Nível 1 (OHLCV e séries brutas), Nível 2 (indicadores técnicos
  calculados) e Nível 3 (scores_causa, trigger_barbell,
  classificacao risco_calculavel / incerteza_genuina).

  O board avaliou a proposta e concluiu:
  - Não necessária para sobrevivência operacional atual.
  - Relevante para escalar capital com segurança na transição para
    capital real — o gap endereçado é sinal antecedente de regime,
    não coberto por nenhum módulo atual do Delta Chaos.
  - Urgência baixa durante paper trading; sobe proporcionalmente
    ao capital alocado.

  Arquitetura aprovada em princípio (sujeita a confirmação no gatilho):
  - score_causa entra pós-ORBIT como meta-sinal de confirmação —
    não substitui ORBIT, não é input pré-classificação.
  - Divergência ORBIT vs ADVANTAGE aciona sizing conservador
    (percentual a definir no gatilho — âncora Eifert: 25% do Kelly).
  - Período observacional mínimo de um trimestre antes de Nível 3
    alimentar produção ativamente.
  - data_quality_flag obrigatório: Delta Chaos verifica data_coleta
    antes de consumir qualquer score; ausência = dado ausente,
    nunca silencioso.
  - Mapeamento de sobreposição de inputs ORBIT vs Camada 1 do
    ADVANTAGE obrigatório antes de integração ativa.
  - Protocolo de divergência escrito antes do primeiro dado real —
    regra assimétrica: fácil apertar, difícil afrouxar.

  Posição dissidente registrada:
  - Buffett: não integrar antes de o Delta Chaos ter baseline
    próprio consolidado de pelo menos um ano.
  - Douglas: ADVANTAGE já em construção paralela — risco de
    racionalização post-hoc da necessidade de integração.

gatilho:
  - fim do primeiro trimestre de paper trading (alinhado a B29, B42, Q02b)

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/ORBIT]]
  - [[SYSTEMS/delta_chaos/modules/EDGE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution:

notes:
  - Relacionado a B06 (flag deterioração sistêmica — gap que ADVANTAGE endereça)
  - Relacionado a B10 (camadas adicionais Eifert — API de vol Fase 2)
  - Relacionado a B29 (condição Taleb — mesmo gatilho)
  - Nível 3 do ADVANTAGE não está em produção na data de abertura desta tensão
  - Interface de consumo: get_connection_readonly — acesso local, sem latência de rede
---
