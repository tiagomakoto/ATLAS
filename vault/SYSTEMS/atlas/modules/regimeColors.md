---
uid: mod-atlas-015
version: 1.0.2
status: validated
owner: Chan

function: Mapeamento centralizado de cores para regimes ORBIT. Exporta REGIME_COLORS (CSS vars), REGIME_BG_COLORS (rgba) e funções getRegimeColor/getRegimeBgColor com fallback por substring.
file: atlas_ui/src/store/regimeColors.js
role: Fonte única de verdade para cores de regime — importado por AtivoView, DigestPanel e demais componentes.

input:
  - regime: str — nome do regime ORBIT (ex: "ALTA", "NEUTRO_BULL")

output:
  - color: str — variável CSS ou valor rgba correspondente ao regime

depends_on:

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]

intent:
  - Eliminar duplicação de lógica de cor por regime em componentes. Fonte única importável.

constraints:
  - Match exato priorizado sobre fallback por substring
  - Regimes cobertos: ALTA, BAIXA, NEUTRO_BULL, NEUTRO_BEAR, NEUTRO_LATERAL, NEUTRO_TRANSICAO, NEUTRO_MORTO, RECUPERACAO, PANICO, NEUTRO
  - Fallback por substring: ALTA/BULL → verde, BAIXA/BEAR → vermelho, PANICO → vermelho, RECUPERACAO → verde, NEUTRO → azul
  - Retorno padrão: var(--atlas-text-secondary) para regime desconhecido

notes:
  - 2026-04-30: código modificado — regimeColors.js
  - Duas variantes: REGIME_COLORS (var CSS para foreground) e REGIME_BG_COLORS (rgba 0.2 para backgrounds)
---