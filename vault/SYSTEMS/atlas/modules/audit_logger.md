---
uid: mod-atlas-041
version: 1.0
status: validated
owner: Chan
function: Trail de auditoria append-only em JSONL — registra toda mutação do sistema (backup, config change, ordem) com timestamp, user, payload e response.
file: atlas_backend/core/audit_logger.py
role: Auditor — registro imutável de todas as ações do sistema para compliance e debugging.
input:
  - action: str — nome da ação
  - payload: dict — dados de entrada da ação
  - response: dict — dados de saída da ação
output:
  - log_action: None — append de linha JSONL em storage/logs/audit.log
  - load_audit_log: list — últimas N entradas (default 50)
depends_on: []
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/CONFIG_MANAGER]]
  - [[SYSTEMS/atlas/modules/backup]]
  - [[SYSTEMS/atlas/modules/API_ROUTES]]
  - [[SYSTEMS/atlas/modules/execution_engine]]
intent:
  - Garantir rastreabilidade completa de toda mutação no sistema. Append-only — nunca sobrescrito.
constraints:
  - LOG_PATH = storage/logs/audit.log
  - Formato JSONL — uma entrada por linha
  - User hardcoded como CEO
  - load_audit_log pula linhas malformadas — tolerante a corrupção parcial
  - Cria diretório pai se não existir
notes:
  - Audit log é append-only — rotação manual quando necessário
