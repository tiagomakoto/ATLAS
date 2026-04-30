---
uid: B65
title: Timezone UTC vs GMT-3 no gerador de relatórios
status: open
opened_at: 2026-04-30
closed_at:
opened_in: [[BOARD/atas/2026-04-30_rastreabilidade_relatorio_calibracao]]
closed_in:
decided_by:
system: atlas

description: >
  datetime.now() em relatorios.py retorna UTC. Brasil é GMT-3.
  Arquivos gerados após 21h local recebem data do dia seguinte no nome.
  Evidência: arquivo gerado às 21h+ de 29/04/2026 nomeado 2026-04-30.

gatilho:
  - imediato — afeta nomes de arquivos e campo data nos relatórios

impacted_modules:
  - [[SYSTEMS/atlas/modules/relatorios]]

resolution:

notes:
  - Correção: datetime.now(tz=ZoneInfo('America/Sao_Paulo'))
  - Requer import: from zoneinfo import ZoneInfo (Python 3.9+)
  - Verificar se mesmo bug existe em outros módulos que usam datetime.now() para gravar datas
---
