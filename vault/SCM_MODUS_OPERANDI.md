# SCM — Modus Operandi do Vault Semântico

**Última atualização:** 2026-04-12  
**Escopo:** Delta Chaos · ATLAS · Advantage  
**Leitura estimada:** 5 minutos

---

## O que é o vault semântico

O vault é uma base de conhecimento em Markdown que descreve cada módulo do sistema em linguagem semântica — legível por LLMs sem acesso direto ao código. Cada arquivo `.md` de módulo captura: o que o módulo faz, o que recebe, o que entrega, de quem depende, quem o usa, qual a sua intenção de design e quais os seus invariantes técnicos.

O objetivo é que qualquer LLM (board, Gemini, Claude) possa raciocinar sobre o sistema com precisão, sem precisar ler o código-fonte a cada sessão.

---

## Participantes e responsabilidades

| Agente | Faz | Não faz |
|---|---|---|
| **PLAN** | Lê código real, analisa impacto, decompõe spec em tarefas atômicas, obtém aprovação do CEO | Escreve código |
| **BUILD** | Executa tarefas cirurgicamente, uma por vez | Planeja, expande escopo |
| **COMMIT** | Coleta arquivos modificados, roda o SCM, commita código + vault, emite log de pendências semânticas | Edita código ou vault |
| **Gemini** | Preenche a semântica dos drafts gerados pelo SCM | Executado automaticamente — sempre convocado pelo CEO |
| **CEO** | Aprova planos, julga natureza das mudanças, convoca Gemini quando necessário | — |

---

## Fluxo completo

### Fase 1 — Desenvolvimento

```
CEO entrega spec ao PLAN
  → PLAN lê o código real antes de qualquer análise
  → PLAN analisa impacto e decompõe em tarefas atômicas
  → CEO aprova o plano (linguagem de negócio)
  → PLAN delega ao BUILD tarefa por tarefa
  → BUILD executa, confirma cada tarefa, aguarda autorização para a próxima
  → BUILD sinaliza conclusão do conjunto de tarefas
  → CEO invoca o agente COMMIT
```

### Fase 2 — Fechamento do ciclo (agente COMMIT)

**Passo 1 — Coleta de arquivos**

O COMMIT roda três comandos git e concatena + deduplica os resultados:

```bash
# Arquivos rastreados modificados
git diff --name-only HEAD

# Arquivos staged (adicionados mas não commitados)
git diff --name-only --cached

# Arquivos novos não rastreados
git ls-files --others --exclude-standard
```

Os três comandos juntos garantem cobertura total: arquivos modificados pelo BUILD em qualquer estado git são capturados.

**Passo 2 — update_scm.py**

O COMMIT passa a lista completa para o script:

```bash
python vault/scripts/update_scm.py <arquivo1> <arquivo2> ...
```

Para cada arquivo, o script percorre esta árvore de decisão:

```
arquivo
  │
  ├─ should_ignore()? → SKIP (sem .md gerado)
  │     extensões: .json .md .xlsx .parquet .db .css .html .log etc.
  │     pastas:    /tests/ /test/ /__pycache__/ /node_modules/
  │     nomes:     test_*.py · conftest.py · pytest.ini · __init__ · SPEC_* · README
  │
  ├─ detect_system() → delta_chaos | atlas | advantage
  │     não reconhecido → SKIP
  │
  ├─ find_coverage() → arquivo bate com padrão no COVERAGE_MAP?
  │     Sim → update_module_md() no .md conceitual mapeado
  │
  ├─ get_module_md_path() → existe .md com mesmo stem do arquivo?
  │     Sim → update_module_md() no .md encontrado
  │
  └─ nenhum dos dois → create_module_md() → novo draft com [BOARD_REVIEW_REQUIRED]
```

**O que `update_module_md()` faz:**
- Incrementa versão patch (ex: 1.2.3 → 1.2.4)
- Insere nota datada em `notes:` → `2026-04-12: código modificado — arquivo.py`
- Detecta campos `[BOARD_REVIEW_REQUIRED]` remanescentes → classifica como Categoria C

**O que `create_module_md()` faz:**
- Gera UID sequencial (`mod-delta-NNN`, `mod-atlas-NNN`, `mod-advantage-NNN`)
- Cria `.md` draft via template com todos os campos semânticos em `[BOARD_REVIEW_REQUIRED]`
- Insere nota de criação automática → classifica como Categoria B

**Passo 3 — Mensagem de commit**

Formato obrigatório:

```
<tipo>(<escopo>): <descrição em uma linha>

vault: <lista dos .md criados ou atualizados>
```

Tipos válidos: `feat` | `fix` | `refactor` | `chore` | `docs`  
Escopo: nome do módulo principal afetado (ex: `FIRE`, `ORBIT`, `dc_runner`)

**Passo 4 — git add -A + commit**

Código e vault são commitados juntos no mesmo hash. Nunca separados.

**Passo 5 — push**

**Passo 6 — Anúncio obrigatório**

O COMMIT sempre emite dois blocos ao final:

```
✅ COMMIT concluído
- Hash: <7 chars>
- Arquivos commitados: <N>
- Vault SCM: <N criados> criados | <N atualizados> atualizados
```

Se houver drafts (Categorias B ou C):

```
📋 PENDÊNCIAS SEMÂNTICAS — requerem preenchimento pelo Gemini

Arquivos draft (módulos novos sem semântica):
  - SYSTEMS/<sistema>/modules/<arquivo>.md
    arquivo de código: <caminho do .py>
    campos pendentes: function, role, intent, constraints

Arquivos com campos pendentes em módulos existentes:
  - SYSTEMS/<sistema>/modules/<arquivo>.md
    campos pendentes: <lista de campos>

Próximo passo: entregar este log ao Gemini com o código dos arquivos acima.
```

Se não houver pendências:

```
📋 Semântica do vault: completa — nenhum campo pendente de revisão.
```

### Fase 3 — Preenchimento semântico (Gemini)

Acionado pelo CEO quando o COMMIT emite o bloco `📋 PENDÊNCIAS SEMÂNTICAS`. O CEO entrega ao Gemini o log + o código-fonte dos arquivos pendentes usando o **Prompt padrão** na seção abaixo. O Gemini devolve os `.md` completos. O CEO cola no vault.

---

## COVERAGE_MAP — mapeamento atual

Define quais arquivos de código atualizam qual módulo conceitual no vault. Quando um arquivo bate com um padrão, o módulo conceitual é atualizado em vez de criar um `.md` granular por arquivo.

### Delta Chaos

| Arquivo de código | Módulo conceitual |
|---|---|
| `delta_chaos/tape.py` | `TAPE.md` |
| `delta_chaos/orbit.py` | `ORBIT.md` |
| `delta_chaos/fire.py` | `FIRE.md` |
| `delta_chaos/book.py` | `BOOK.md` |
| `delta_chaos/edge.py` | `EDGE.md` |
| `delta_chaos/gate.py` / `gate_eod` | `GATE.md` |
| `delta_chaos/tune.py` | `TUNE.md` |
| `delta_chaos/reflect.py` | `REFLECT.md` |

### ATLAS Backend

| Arquivo de código | Módulo conceitual |
|---|---|
| `atlas_backend/core/dc_runner` | `ATLAS_DC_RUNNER.md` |
| `atlas_backend/core/delta_chaos_reader` | `delta_chaos_reader.md` |
| `atlas_backend/core/event_bus` | `EVENT_BUS.md` |
| `atlas_backend/core/config` | `CONFIG_MANAGER.md` |
| `atlas_backend/api/routes/` | `API_ROUTES.md` |
| `atlas_backend/api/websocket/` | `WEBSOCKET.md` |

### Advantage

| Arquivo de código | Módulo conceitual |
|---|---|
| `advantage/src/data_layer/db/` | `DATA_LAYER.md` |
| `advantage/src/data_layer/collectors/` | `COLLECTORS.md` |
| `advantage/src/data_layer/scheduler` | `SCHEDULER.md` |
| `advantage/src/data_layer/utils` | `COLLECTORS.md` |

Arquivos fora do COVERAGE_MAP são tratados pelo stem do nome — se existir `.md` com o mesmo nome, é atualizado; se não existir, é criado como draft.

---

## Classificação de pendências semânticas

| Categoria | O que é | O que o Gemini faz |
|---|---|---|
| **A — Atualizado** | `.md` existente com versão incrementada e nota em `notes:`. Semântica intacta. | Nada necessário |
| **B — Draft novo** | `.md` criado do zero para arquivo sem cobertura prévia. Todos os campos em `[BOARD_REVIEW_REQUIRED]`. | Preencher todos os campos semânticos |
| **C — Campos pendentes** | `.md` existente com campos `function`, `role`, `intent` ou `constraints` ainda em `[BOARD_REVIEW_REQUIRED]`. | Preencher os campos específicos indicados |

**Regra de julgamento do CEO:**

O COMMIT não distingue automaticamente se uma mudança em módulo existente (Categoria A) é estrutural ou apenas um patch. Essa decisão é do CEO:

- **Bugfix / patch pontual** (mesma lógica, correção de detalhe) → a nota em `notes:` já é suficiente. Gemini não precisa ser convocado.
- **Mudança estrutural** (nova função pública, novo contrato de entrada/saída, novo constraint relevante) → convocar o Gemini para atualizar `function`, `constraints` ou `intent`.

---

## Formato obrigatório dos arquivos de módulo

Todo `.md` de módulo no vault segue este schema:

```markdown
---
uid: mod-<sistema>-<NNN>
version: <X.Y.Z>
status: draft | validated
owner: Chan

function: <descrição funcional em uma frase — o que o módulo faz>
file: <caminho relativo do arquivo de código>
role: <papel arquitetural em uma frase>

input:
  - <nome>: <tipo> — <significado>

output:
  - <nome>: <tipo> — <significado>

depends_on:
  - [[SYSTEMS/<sistema>/modules/<MODULO>]]

depends_on_condition:
  - <condição>: [[SYSTEMS/<sistema>/modules/<MODULO>]]

used_by:
  - [[SYSTEMS/<sistema>/modules/<MODULO>]]

intent:
  - <intenção de design — por que existe, qual invariante protege>

constraints:
  - <regras literais, thresholds reais, invariantes de código>

notes:
  - <edge cases, bugs abertos (BXX), modificações datadas>
---
```

**Regras de preenchimento:**
- `function` e `role`: uma frase cada, sem ambiguidade
- `input` / `output`: apenas o que o módulo de fato recebe/entrega — não inferir
- `depends_on`: apenas dependências reais — módulos que o código importa diretamente
- `constraints`: literais extraídos do código — não parafrasear, não generalizar
- `intent`: o "por que" arquitetural, não o "como"
- `status`: muda para `validated` após preenchimento completo pelo Gemini
- UIDs existentes nunca são alterados

---

## Prompt padrão para convocação do Gemini

Usar este prompt quando o COMMIT emitir o bloco `📋 PENDÊNCIAS SEMÂNTICAS`, ou quando houver mudanças estruturais acumuladas em módulos existentes que justifiquem atualização semântica.

Copiar o bloco abaixo integralmente, substituindo as duas seções marcadas com `[COLE AQUI]`.

---

```
# Tarefa — Preenchimento semântico do vault Delta Chaos / ATLAS

## Contexto

Delta Chaos é um sistema quantitativo de trading de opções no mercado brasileiro (B3).
O vault é uma base de conhecimento em Markdown onde cada módulo do sistema é descrito
em linguagem semântica para leitura por LLMs. Você vai preencher arquivos .md de módulos
que estão com campos em [BOARD_REVIEW_REQUIRED] ou com semântica desatualizada após
mudanças estruturais de código.

## Formato obrigatório de cada arquivo

Todo .md de módulo segue este schema YAML frontmatter:

---
uid: <preservar o existente>
version: <preservar — incrementar patch se for atualização de módulo existente>
status: validated
owner: Chan

function: <descrição funcional em uma frase — o que o módulo faz>
file: <caminho do arquivo de código>
role: <papel arquitetural em uma frase>

input:
  - <nome>: <tipo> — <significado>

output:
  - <nome>: <tipo> — <significado>

depends_on:
  - [[SYSTEMS/<sistema>/modules/<MODULO>]]

depends_on_condition:
  - <condição>: [[SYSTEMS/<sistema>/modules/<MODULO>]]

used_by:
  - [[SYSTEMS/<sistema>/modules/<MODULO>]]

intent:
  - <intenção de design — por que existe, qual invariante protege>

constraints:
  - <regras literais, thresholds reais, invariantes de código>

notes:
  - <preservar todas as entradas existentes — adicionar edge cases novos se houver>
---

## Regras de preenchimento

1. Leia o código antes de preencher qualquer campo. Não infira — extraia.
2. Se o código não deixar claro, marque: [REVISAR — comportamento não determinístico]
3. Preserve UIDs existentes. Não altere módulos que não estão na lista de pendências.
4. constraints devem ser literais: se o código diz timeout=1800, escreva timeout=1800.
5. depends_on: apenas módulos que o código importa diretamente — não inferir.
6. Formato WikiLink obrigatório em depends_on e used_by: [[SYSTEMS/<sistema>/modules/<MODULO>]]
7. status deve ser validated após preenchimento completo.
8. notes: preservar todas as entradas existentes. Adicionar apenas edge cases novos.
9. Não produza explicações entre arquivos — apenas os arquivos, separados por ---
   com o caminho canônico no topo de cada bloco.

## Arquivos pendentes

[COLE AQUI O BLOCO 📋 PENDÊNCIAS SEMÂNTICAS EMITIDO PELO COMMIT]

## Código dos arquivos pendentes

[COLE AQUI O CÓDIGO-FONTE COMPLETO DE CADA ARQUIVO LISTADO ACIMA]

## Output esperado

Um bloco Markdown completo por arquivo, na ordem dos arquivos pendentes.
Cada bloco encabeçado pelo caminho canônico no vault:

// SYSTEMS/<sistema>/modules/<arquivo>.md
<conteúdo completo do arquivo .md>

---

// SYSTEMS/<sistema>/modules/<próximo arquivo>.md
<conteúdo completo>
```

---

## Histórico de decisões sobre este sistema

| Data | Decisão |
|---|---|
| 2026-04-12 | COVERAGE_MAP corrigido: `edge.py` adicionado, `dc_runner` apontado para `ATLAS_DC_RUNNER.md`, `delta_chaos_reader` e `reflect.py` adicionados, entradas atlas normalizadas para nomes canônicos dos `.md` existentes |
| 2026-04-12 | `should_ignore()` corrigido: cobre `/tests/` em qualquer posição do caminho, `test_*.py` por stem, `conftest.py` e `pytest.ini` por nome exato |
| 2026-04-12 | `needs_board_review()` corrigido: regex multiline detecta `[BOARD_REVIEW_REQUIRED]` em bloco YAML (linha seguinte ao campo), com early-exit se marcador ausente |
| 2026-04-12 | Prompt do COMMIT atualizado: Passo 1 cobre três estados git (HEAD / cached / untracked) com instrução explícita de concatenar e deduplicar; Passo 6 emite log estruturado de pendências semânticas com caminho do `.py` original |
| 2026-04-12 | 8 arquivos de teste criados erroneamente no vault Advantage deletados manualmente pelo CEO |
