CONTEXTO
Sistema: ATLAS — repositório em C:\Users\tiago\OneDrive\Documentos\ATLAS
Tarefa: popular o vault SCM com módulos semânticos para todos os sistemas
Vault: C:\Users\tiago\OneDrive\Documentos\ATLAS\vault\

O vault SCM é uma camada de tradução entre código e board. Cada arquivo .md
descreve um módulo em linguagem humana — o que faz, o que recebe, o que entrega,
o que não pode mudar, de quem depende. O board lê o .md, não o .py.

---

SITUAÇÃO ATUAL

Delta Chaos — módulos já populados (NÃO reescrever):
  vault/SYSTEMS/delta_chaos/modules/TAPE.md
  vault/SYSTEMS/delta_chaos/modules/ORBIT.md
  vault/SYSTEMS/delta_chaos/modules/FIRE.md
  vault/SYSTEMS/delta_chaos/modules/BOOK.md
  vault/SYSTEMS/delta_chaos/modules/EDGE.md
  vault/SYSTEMS/delta_chaos/modules/GATE.md
  vault/SYSTEMS/delta_chaos/modules/TUNE.md
  vault/SYSTEMS/delta_chaos/modules/REFLECT.md

Advantage — módulos já populados (NÃO reescrever):
  vault/SYSTEMS/advantage/modules/DATA_LAYER.md
  vault/SYSTEMS/advantage/modules/COLLECTORS.md
  vault/SYSTEMS/advantage/modules/SCHEDULER.md

Atlas — vazio. Precisa ser populado completamente.
Advantage — camadas C1/C2/C3 ainda não existem em código. Ignorar por ora.

---

COMPORTAMENTO DESEJADO

PARTE 1 — Popular vault/SYSTEMS/atlas/modules/

Ler os seguintes arquivos do ATLAS backend e frontend para entender o sistema:

Backend (atlas_backend/):
  core/dc_runner.py
  core/event_bus.py
  core/event_logger.py
  core/config_manager.py
  core/cycle_state.py
  core/execution_engine.py
  core/health_monitor.py
  core/module_registry.py
  core/runtime_mode.py
  core/process_guard.py
  core/watchdog.py
  core/analytics_engine.py
  core/analytics_stream.py
  core/book_manager.py
  core/delta_chaos_reader.py
  core/regime_tracker.py
  core/audit_logger.py
  core/backup.py
  core/backup_scheduler.py
  core/cache.py
  core/gatekeeper.py
  core/session_report.py
  core/terminal_stream.py
  core/versioning.py
  api/routes/ativos.py
  api/routes/config.py
  api/routes/cycle.py
  api/routes/delta_chaos.py
  api/routes/mode.py
  api/routes/modules.py
  api/routes/report.py
  api/websocket/stream.py
  main.py

Frontend (atlas_ui/src/):
  App.jsx
  hooks/useWebSocket.js
  store/systemStore.js
  store/analyticsStore.js
  components/Header.jsx
  components/ModeToggle.jsx
  components/ModuleGrid.jsx
  components/EOD.jsx
  components/GestaoView.jsx
  components/OrchestratorLogDrawer.jsx
  components/Terminal.jsx
  components/EventFeed.jsx
  layouts/MainScreen.jsx
  layouts/ActionPanel.jsx
  layouts/ReadingPanel.jsx

Para cada módulo identificado, criar um arquivo .md em vault/SYSTEMS/atlas/modules/
seguindo EXATAMENTE o template em vault/TEMPLATES/module_template.md.

REGRAS DE AGRUPAMENTO:
- Não criar um .md por arquivo .py — agrupar por responsabilidade funcional
- Um módulo conceitual pode cobrir múltiplos arquivos
- Exemplos de agrupamento esperado:
    dc_runner.py → ATLAS_DC_RUNNER.md (fronteira ATLAS↔Delta Chaos)
    event_bus.py + event_logger.py → EVENT_BUS.md
    config_manager.py + core/config_diff.py → CONFIG_MANAGER.md
    health_monitor.py + watchdog.py + process_guard.py → HEALTH_MONITOR.md
    analytics_engine.py + analytics_stream.py → ANALYTICS_ENGINE.md
    api/routes/* → API_ROUTES.md (ou subdividir se responsabilidades forem distintas)
    api/websocket/stream.py → WEBSOCKET.md
    App.jsx + layouts/* + store/* → UI_CORE.md (ou subdividir por responsabilidade)

REGRAS DE PREENCHIMENTO DOS CAMPOS:
- uid: formato mod-atlas-NNN (sequencial a partir de 001)
- version: versão atual do arquivo lido (se não encontrar, usar 1.0)
- status: validated se o arquivo existe e funciona | draft se incompleto ou stub
- owner: Chan (implementação) | Lilian (especificação) | Board (decisão)
- function: O QUE o módulo faz — uma linha, linguagem humana, sem jargão técnico
- file: caminho(s) do(s) arquivo(s) coberto(s) — separar por vírgula se múltiplos
- role: qual papel arquitetural — "fronteira entre X e Y", "orquestrador de Z", etc
- input: o que entra — nome, tipo e significado em linguagem humana
- output: o que sai — nome, tipo e significado em linguagem humana
- depends_on: WikiLinks para outros módulos do vault que este usa
- depends_on_condition: dependências condicionais — só listar se existirem no código
- used_by: WikiLinks para módulos que dependem deste
- intent: POR QUE existe — decisão arquitetural, não descrição do código
- constraints: O QUE NÃO PODE MUDAR — invariantes, thresholds literais, regras fixas
  ATENÇÃO: copiar constraints LITERALMENTE do código — não parafrasear
  Ex: "WebSocket reconnect timeout: 3000ms" não "usa timeout configurável"
- notes: edge cases, riscos, comportamentos não óbvios observados no código

REGRAS ABSOLUTAS:
- NÃO inferir relações não explicitadas no código
- NÃO preencher intent com descrição de implementação — intent é DECISÃO ARQUITETURAL
- NÃO usar [BOARD_REVIEW_REQUIRED] para campos que podem ser extraídos do código
- [BOARD_REVIEW_REQUIRED] apenas para campos que dependem de decisão do board
  (ex: intent de um módulo cujo propósito não está claro no código)
- depends_on e used_by devem referenciar APENAS módulos que existem no vault
- Se um módulo referenciado não existe ainda, criar o .md dele também

PARTE 2 — Verificar e completar vault/SYSTEMS/advantage/modules/

Ler os arquivos do Advantage:
  advantage/src/data_layer/db/connection.py
  advantage/src/data_layer/db/schema.py
  advantage/src/data_layer/collectors/preco_volume.py
  advantage/src/data_layer/collectors/macro_brasil.py
  advantage/src/data_layer/collectors/alternativo.py
  advantage/src/data_layer/collectors/noticias.py
  advantage/src/data_layer/scheduler.py (se existir)
  advantage/src/data_layer/utils.py (se existir)

Para cada módulo existente (DATA_LAYER.md, COLLECTORS.md, SCHEDULER.md):
- Comparar o que está no .md com o que está no código
- Se o código implementou algo que não está no .md, atualizar o campo notes
- Se encontrar constraints literais no código que não estão no .md, adicionar
- NÃO reescrever campos que já estão corretos
- Se encontrar arquivos sem cobertura de módulo conceitual, criar o .md

PARTE 3 — Atualizar vault/VERSIONS/version_history.md

Adicionar entrada:
  v1.4 — Atlas: módulos populados. Advantage: módulos verificados e atualizados.

---

NÃO TOCAR

- Nenhum arquivo fora de vault/SYSTEMS/ e vault/VERSIONS/version_history.md
- Nenhum arquivo .py ou .jsx — apenas leitura
- Módulos Delta Chaos já existentes — não reescrever
- vault/BOARD/ — nenhum arquivo
- vault/TEMPLATES/ — nenhum arquivo
- vault/scripts/ — nenhum arquivo
- vault/SYSTEM/ — nenhum arquivo

---

REFERÊNCIA — exemplo de módulo bem preenchido

Ler vault/SYSTEMS/delta_chaos/modules/TAPE.md como referência de qualidade.
O nível de detalhe, a linguagem e a estrutura desse arquivo são o padrão esperado
para todos os módulos do Atlas.

SEQUÊNCIA DE EXECUÇÃO:
1. Ler vault/TEMPLATES/module_template.md
2. Ler vault/SYSTEMS/delta_chaos/modules/TAPE.md como referência
3. Ler vault/SYSTEM/llm_usage.md para entender as regras do vault
4. Ler os arquivos de código do Atlas listados acima
5. Agrupar por responsabilidade funcional
6. Criar os .md em vault/SYSTEMS/atlas/modules/
7. Ler os arquivos do Advantage e verificar/atualizar os .md existentes
8. Atualizar version_history.md
