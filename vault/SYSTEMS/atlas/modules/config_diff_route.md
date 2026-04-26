---
uid: mod-atlas-046
version: 1.0
status: validated
owner: Chan
function: Endpoint POST /config/diff — compara config proposta contra config vigente e retorna diff estruturado para preview antes de aplicar.
file: atlas_backend/api/routes/config_diff.py
role: Preview de mudanças — permite ao frontend mostrar diff antes de confirmar alteração de config.
input:
  - payload: dict — {data: dict} com config proposta
output:
  - diff: dict — {key: {before, after}} para cada campo alterado
depends_on:
  - [[SYSTEMS/atlas/modules/CONFIG_MANAGER]]
  - [[SYSTEMS/atlas/modules/config_diff]]
depends_on_condition: []
used_by:
  - [[SYSTEMS/atlas/modules/UI_CORE]]
intent:
  - Evitar aplicações cegas de config — o CEO deve ver o diff antes de confirmar qualquer mudança.
constraints:
  - POST /config/diff — recebe data no payload
  - Delega para config_diff.compute_diff
  - Não modifica config — apenas compara
notes:
  - Complementar ao POST /config/update que aplica a mudança
