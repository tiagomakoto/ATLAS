# LLM Usage Instructions

## Este vault é a fonte de verdade entre código, board e planner.

### Regras para agentes LLM:
- NÃO inferir relações não explicitadas
- Usar APENAS WikiLinks declarados em depends_on e used_by
- Sugerir melhorias de forma explícita, nunca silenciosa
- Campos marcados [BOARD_REVIEW_REQUIRED] não podem ser preenchidos automaticamente

### Como interpretar campos:
- uid: identidade estável do módulo — não muda se o arquivo for renomeado
- status: draft = em discussão | validated = aprovado pelo board | deprecated = não usar
- status validated: requer pronunciamento explícito do board registrado em BOARD/atas/
- owner: responsável pela implementação (Chan) ou especificação (Lilian) ou decisão (Board)
- depends_on_condition: dependência condicional — só ativa sob a condição declarada
- constraints: inclui thresholds literais e invariantes — não parafrasear

### Injeção de contexto no Claude:
1. Carregar SYSTEM/system_overview.md primeiro
2. Carregar módulos relevantes de SYSTEMS/<system>/modules/
3. Carregar BOARD/decision_log.md para contexto de decisões ativas
4. Nunca carregar o vault inteiro — injeção seletiva por módulo