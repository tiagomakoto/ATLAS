# SANDBOX ATLAS — ESCOPO REAL v1.0
#
# RESTRIÇÕES IMPLEMENTADAS:
#   ✅ Timeout de execução: 100ms
#
# RESTRIÇÕES NÃO IMPLEMENTADAS (backlog):
#   ❌ Isolamento de filesystem
#   ❌ Restrição de rede
#   ❌ Restrição de importações
#
# CONSEQUÊNCIA:
# Este sandbox NÃO isola código malicioso.
# Uso seguro: apenas funções internas confiáveis.

import time

def run_sandboxed(fn, *args, **kwargs):
    start = time.time()

    result = fn(*args, **kwargs)

    elapsed = time.time() - start

    if elapsed > 0.1:
        raise RuntimeError(
            f"SANDBOX_TIMEOUT: execução levou {elapsed:.3f}s > 100ms"
        )

    return result