---
description: Diagnóstico Automático do ATLAS (v2.5.2) — Verifica Rotas, APIs e Arquivos XLSX
---

Este workflow deve ser executado no início de qualquer nova conversa ou ao detectar erros 404/500 no sistema. Ele utiliza comandos do terminal para validar o estado real do ecossistema ATLAS.

// turbo-all
## PASSO 1: VALIDAR BACKEND (FASTAPI)
Execute os comandos abaixo para verificar se as rotas vitais do Delta Chaos estão registradas no servidor:

1.  Listar rotas registradas (Script de Sanidade):
    Crie e rode um arquivo temporário `tmp_check_routes.py`:
    ```python
    from atlas_backend.main import app
    for route in app.routes:
        print(f"Path: {route.path} | Methods: {route.methods}")
    ```

2.  Checar a URL Base:
    `Invoke-RestMethod -Uri "http://localhost:8000/"`

3.  Checar a URL do Orquestrador (v2.5.2):
    `Invoke-RestMethod -Uri "http://localhost:8000/delta-chaos/orchestrator/run" -Method POST -ContentType "application/json" -Body '{}'`

## PASSO 2: VALIDAR DATA FLOW (DELTA CHAOS)
Verifique se os diretórios de ativos e excel estão acessíveis pelo backend:

1.  Listar ativos parametrizados:
    `Invoke-RestMethod -Uri "http://localhost:8000/ativos"`

2.  Verificar existência da pasta de ativos:
    `ls c:\Users\tiago\OneDrive\Documentos\ATLAS\ativos_parametrizados`

## PASSO 3: VALIDAR FRONTEND (UI)
Verifique se o `API_BASE` no arquivo `atlas_ui/src/layouts/MainScreen.jsx` aponta para a porta correta:
- Terminal: `Get-Content c:\Users\tiago\OneDrive\Documentos\ATLAS\atlas_ui\src\layouts\MainScreen.jsx | grep "API_BASE"`

---
*Assinado: Antigravity v1.0 — Skill System Engine*
