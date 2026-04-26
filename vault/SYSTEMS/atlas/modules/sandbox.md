---
uid: mod-atlas-035
version: 1.0
status: validated
owner: Chan
function: Executa função com timeout pós-execução de 100ms — verificação de wall-time após retorno, não preempção.
file: atlas_backend/core/sandbox.py
role: Sandbox mínimo — protege contra funções que excedem 100ms de execução.
input:
  - fn: callable — função a executar
  - "*args, **kwargs": Any — argumentos para fn
output:
  - run_sandboxed: Any — retorno de fn, ou RuntimeError('SANDBOX_TIMEOUT') se > 100ms
depends_on: []
depends_on_condition: []
used_by: []
intent:
  - Fornecer execução com timeout mínimo para funções internas confiáveis. Não é sandbox de segurança — apenas timeout.
constraints:
  - Timeout = 100ms (hardcoded)
  - Verificação pós-execução — não interrompe função em andamento
  - Isolamento de filesystem, rede e imports NÃO implementados
  - Seguro apenas para funções internas confiáveis
notes:
  - Sandbox é mínimo — não substitui containerização ou isolamento real para código não confiável
