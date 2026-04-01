# Delta Chaos — Checklist de Migração (Seção 11)

Cada item corresponde a um critério de "Definição de Pronto" do prompt de migração.
Marcar como ✓ após validação manual.

## Critérios obrigatórios

- [x] `init.py` sem dependência do Colab — `DRIVE_BASE` lido do `paths.json`
- [x] Todos os módulos com imports explícitos — sem dependência de escopo global
- [x] `gate.py` com `executar_gate(ticker: str) -> str` — sem `input()`
- [x] `tune.py` com `executar_tune(ticker: str) -> dict` — sem `input()`
- [x] `gate.py` sem `raise SystemExit` — substituído por `raise ValueError`
- [x] Prints de inicialização sob `if __name__ == "__main__"`
- [x] `edge.py` expõe `executar_eod()`, `executar_orbit()` chamáveis por argumento
- [x] Endpoints FastAPI: `/delta-chaos/eod/preview`, `/delta-chaos/eod/executar`,
      `/delta-chaos/orbit`, `/delta-chaos/tune`, `/delta-chaos/gate`
- [x] Validação de arquivo EOD implementada — rejeita com HTTP 422
- [x] Output de cada endpoint transmitido via WebSocket `/ws/logs`
- [x] Dois estágios do EOD (preview + executar) verificáveis via ATLAS
- [ ] Protocolo de retomada após REFLECT E **não implementado** ← pendente do board
- [x] Nenhuma lógica de negócio alterada

## O que não foi feito (constraints do prompt)

- Protocolo de retomada após estado E — Seção 4 P6: pendente de aprovação do board
- Aplicação automática do resultado do TUNE — requer confirmação explícita do CEO
- Unificação dos três books — separação inviolável
- Divisão do tape.py — dependência circular interna

## Estrutura de arquivos gerada

```
delta_chaos/
├── init.py              ← v2.0 — sem Colab, lê paths.json
├── tape.py              ← v2.0 — imports explícitos de init
├── orbit.py             ← v4.0 — imports explícitos de init+tape
├── book.py              ← v2.0 — imports explícitos de init+tape
├── fire.py              ← v2.0 — imports explícitos de init+tape+book
├── gate_eod.py          ← v2.0 — imports explícitos de init+tape
├── gate.py              ← v2.0 — executar_gate(), ValueError, imports
├── edge.py              ← v2.0 — imports todos os módulos
├── tune.py              ← v2.0 — executar_tune(), ValueError, imports
└── atlas_backend/
    ├── __init__.py
    ├── config/
    │   └── paths.json       ← configurar DRIVE_BASE aqui
    ├── core/
    │   ├── __init__.py
    │   └── terminal_stream.py  ← emit_log, emit_error, StreamCapture
    └── api/
        ├── __init__.py
        └── routes/
            ├── __init__.py
            └── delta_chaos.py  ← 5 endpoints + WebSocket /ws/logs
```

## Configuração inicial

1. Editar `atlas_backend/config/paths.json`:
   ```json
   {
     "delta_chaos_base": "G:\\Meu Drive\\Delta Chaos"
   }
   ```

2. Registrar o router no app FastAPI principal:
   ```python
   from atlas_backend.api.routes.delta_chaos import router as dc_router
   app.include_router(dc_router)
   ```

3. Verificar que o diretório `delta_chaos/` está no PYTHONPATH.

## Critério de rejeição imediato

- Qualquer módulo que quebre ao ser importado em ambiente local sem Google Drive montado
- Qualquer endpoint que execute operações sem `confirm=true`
