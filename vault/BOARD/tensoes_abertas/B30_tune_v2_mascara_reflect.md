---
uid: B30
title: TUNE v2.0 — máscara REFLECT e dimensão de estratégias alternativas
status: open
opened_at: 2026-03-23
closed_at:
opened_in: [[BOARD/atas/2026-03-23_paper_trading]]
closed_in:
decided_by:
system: delta_chaos

description: >
  TUNE v2.0 pendente Chan: (1) implementar máscara de ciclos REFLECT
  excluindo Edge C e D da simulação; (2) adicionar dimensão de estratégias
  alternativas por regime — CSP vs BULL_PUT_SPREAD em NEUTRO_BULL,
  BEAR_CALL_SPREAD vs outras em NEUTRO_BEAR.

gatilho:
  - após primeiro trimestre de paper trading
  - dependência: [[BOARD/tensoes_abertas/B42_TUNE_v2]]

impacted_modules:
  - [[SYSTEMS/delta_chaos/modules/TUNE]]
  - [[SYSTEMS/delta_chaos/modules/REFLECT]]

resolution: >
  Resolução parcial — sessão 2026-04-12.
  Dimensão 2 (estratégias alternativas por regime): direção confirmada pelo CEO.
  Abordagem: diagnóstico de estratégia vencedora por regime via análise histórica
  de P&L — não otimização de TP/STOP por regime. TUNE por regime descartado
  formalmente. A seleção de estratégia por regime (Nível 2) precede o TUNE global
  de TP/STOP (Nível 3) — hierarquia doutrinária confirmada por Thorp, Simons,
  Buffett e PRISM.
  Dimensão 1 (máscara REFLECT): pendente de implementação em TUNE v2.0.
  O diagnóstico de estratégia por regime requer TUNE v2.0 implementado —
  as duas dimensões são pré-requisito uma da outra para entrega coerente.

notes:
  - TUNE v2.0 deve rodar com máscara REFLECT — resultado sem máscara é subótimo
  - TUNE por regime explicitamente descartado — parâmetros TP/STOP permanecem globais por ativo
  - Diagnóstico estratégia × regime é pré-TUNE, usa full history disponível
  - TUNE global usa janela deslizante de 126 dias úteis — escalas temporais distintas por design
