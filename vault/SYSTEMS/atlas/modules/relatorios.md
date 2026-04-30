---
uid: mod-atlas-019
version: 1.0.10
status: validated
owner: Chan

function: Geração de relatórios de TUNE e ONBOARDING em formato Markdown, com index.json para rastreio de aplicação. Inclui diagnóstico executivo determinístico (regras de IR, confiança, amostra) e formatação completa para pasting em sessão com board.
file: atlas_backend/core/relatorios.py
role: Gerador de relatórios operacionais — único ponto de emissão de documentos para decisão do CEO/Board.

input:
  - ticker: str — código do ativo
  - ciclo: str — ciclo de referência (ex: "2026-04")
  - tipo: str — "TUNE" ou "ONBOARDING"
  - params: dict — tp_atual, stop_atual, tp_sugerido, stop_sugerido, delta_tp, delta_stop, recomendacao, detalhes

output:
  - dict: {id, arquivo, ciclo, tipo, data_execucao} — metadados do relatório gerado
  - markdown: str — relatório completo formatado em Markdown (via gerar_relatorio_tune)

depends_on:
  - [[SYSTEMS/atlas/modules/DATA_READERS]]

depends_on_condition:

used_by:
  - [[SYSTEMS/atlas/modules/API_ROUTES]]

intent:
  - Centralizar a geração de documentos de decisão para que o CEO avalie parâmetros antes de aplicar. Nunca aplicar automaticamente.
  - Diagnóstico executivo determinístico — regras explícitas por IR, confiança e amostra.

constraints:
  - RELATORIOS_DIR = atlas_backend/core/relatorios/ — relatórios gravados como .md
  - INDEX_PATH = RELATORIOS_DIR/index.json — append-only, escrita atômica via os.replace
  - _gerar_id() sequencial baseado no index atual
  - gerar_diagnostico_executivo: IR>=1.0 + alta → APLICAR | IR>=0.5 + baixa → REVISAR | IR<0.5 → MANTER | amostra_insuficiente → NÃO APLICAR
  - Alerta adicional se reflect_mask_pct > 30% — IR pode estar inflado
  - Alerta adicional se janela_anos <= 3 — eventos extremos históricos excluídos
  - gerar_relatorio_tune extrai dados via regex do campo motivo do historico_config — TP, STOP, IR, confiança, trials, reflect_mask
  - marcar_aplicado atualiza campo aplicado=True e data_aplicado no index.json

notes:
  - 2026-04-29: código modificado — relatorios.py
  - 2026-04-29: código modificado — relatorios.py
  - 2026-04-27: código modificado — relatorios.py
  - 2026-04-26: código modificado — relatorios.py
  - 2026-04-26: código modificado — relatorios.py
  - 2026-04-25: código modificado — relatorios.py
  - 2026-04-22: código modificado — relatorios.py
  - 2026-04-22: código modificado — relatorios.py
  - 2026-04-17: código modificado — relatorios.py
  - Funções públicas: gerar_relatorio, marcar_aplicado, obter_relatorio, obter_todos_relatorios, gerar_relatorio_tune, gerar_diagnostico_executivo, formatar_relatorio_markdown
  - Template TUNE v2.0 inclui: limitação de simulação, qualidade da otimização, máscara REFLECT, distribuição de saídas, pior trade, histórico de TUNEs
---