---
uid: mod-atlas-034
version: 1.0
status: validated
owner: Chan
function: Cria snapshot timestampado de storage/configs, storage/logs e storage/versions sob backups/ com audit logging.
file: atlas_backend/core/backup.py
role: Backup filesystem — protege dados críticos contra perda com cópias timestampadas.
input: []
output:
  - run_backup: None — cria diretório backups/YYYYMMDD_HHMMSS/ com cópias dos 3 diretórios fonte
depends_on:
  - [[SYSTEMS/atlas/modules/audit_logger]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/backup_scheduler]]
intent:
  - Garantir recoverabilidade de configurações, logs e versões contra corrupção ou deleção acidental.
constraints:
  - SOURCE_DIRS = [storage/configs, storage/logs, storage/versions]
  - BACKUP_DIR = backups/
  - Usa shutil.copytree para cópia recursiva
  - RuntimeError('BACKUP FAILED') em caso de falha
  - Audit log registra sucesso ou falha de cada backup
notes:
  - Backup é full copy — sem incremental. Considere rotação para evitar crescimento ilimitado.
