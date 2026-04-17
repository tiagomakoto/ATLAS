# CONTRATO DE IMPLEMENTACAO CONGELADO - CALIBRACAO DRAWER v3.0
Data de congelamento: 2026-04-17
Status: CONGELADO PARA IMPLEMENTACAO

## Escopo congelado
- SPEC: `SPEC_CALIBRACAO_DRAWER_v3.0.md`
- Frontend:
  - `atlas_ui/src/components/GestaoView/CalibracaoDrawer.jsx`
  - `atlas_ui/src/components/GestaoView.jsx`
- Backend:
  - `atlas_backend/api/routes/delta_chaos.py`
  - `atlas_backend/api/routes/ativos.py`

## Contrato alvo (obrigatorio para implementacao)
1. Fluxo canônico de steps no drawer:
`1_backtest_dados -> 2_tune -> 3_gate_fire`

2. Step 3 com duas fases sequenciais no mesmo card:
- Fase A: GATE (8 criterios com pass/fail granular)
- Fase B: FIRE (somente se GATE pass)

3. Endpoints read-only obrigatorios:
- `GET /ativos/{ticker}/gate-resultado`
- `GET /ativos/{ticker}/fire-diagnostico`

4. Exportacao `.md` obrigatoria ao final do step 3:
- GATE bloqueado: `GATE_{TICKER}_{CICLO}_{DATA}_BLOQUEADO.md`
- GATE + FIRE: `CALIBRACAO_{TICKER}_{CICLO}_{DATA}.md`

5. Guard de dados recentes no step 1:
- Se ultimo COTAHIST < 7 dias: oferecer `[Pular step 1]` e `[Rodar mesmo assim]`

6. Itens que nao podem ser alterados:
- `useWebSocket.js`
- logica de WebSocket/parsing do fluxo atual
- progresso e watchdog do TUNE
- `OrchestratorProgress.jsx`
- variaveis CSS existentes
- posicionamento/dimensoes do drawer

## Contrato observado no codigo atual (baseline validado)
1. Frontend usa:
- `POST /delta-chaos/calibracao/iniciar` em `GestaoView.jsx`
- `GET /delta-chaos/calibracao/{ticker}` em `CalibracaoDrawer.jsx`
- `POST /delta-chaos/calibracao/{ticker}/retomar` em `CalibracaoDrawer.jsx`
- `GET /ativos/{ticker}` em `CalibracaoDrawer.jsx`
- WebSocket em `/ws/events` consumindo `dc_module_start`, `dc_module_complete`, `dc_tune_progress`, `terminal_log`

2. Modelo de step atual no frontend:
- `1_backtest_dados`
- `2_tune`
- `3_backtest_gate`

3. Backend existente para calibracao:
- `POST /delta-chaos/calibracao/iniciar`
- `GET /delta-chaos/calibracao/{ticker}`
- `POST /delta-chaos/calibracao/{ticker}/retomar`
- `GET /delta-chaos/calibracao/{ticker}/progresso-tune`

4. Endpoints ausentes no backend:
- `GET /ativos/{ticker}/gate-resultado` (nao existe)
- `GET /ativos/{ticker}/fire-diagnostico` (nao existe)

5. Sequencia de calibracao observada no backend:
- `/delta-chaos/calibracao` documenta e executa `ORBIT -> TUNE -> GATE`
- `/delta-chaos/calibracao/iniciar` documenta `backtest_dados -> tune -> backtest_gate`
- Nao ha trecho equivalente a FIRE no fluxo de calibracao observado nesses arquivos

## Divergencias validadas (frontend x backend x spec)
1. Nomenclatura do step 3:
- Spec: `3_gate_fire`
- Frontend atual: `3_backtest_gate`
- Impacto: incompatibilidade semantica e de estado final do fluxo

2. Contrato de dados do step 3:
- Spec: exige diagnostico granular GATE + painel FIRE
- Frontend atual: renderiza apenas GATE
- Backend atual: nao expoe endpoints de `gate-resultado` e `fire-diagnostico`

3. Regra de disparo FIRE:
- Spec: FIRE apenas apos GATE pass
- Frontend atual: sem fase FIRE no step 3
- Backend atual: sem trecho de calibracao com FIRE neste escopo

4. Guard de dados recentes:
- Spec: obrigatorio no step 1 com decisao do usuario
- Frontend atual: nao implementado
- Backend atual: sem endpoint/contrato explicito nesta camada para suportar esse guard

5. Exportacao de relatorio da calibracao:
- Spec: exportacao obrigatoria de GATE-only ou GATE+FIRE no final do step 3
- Frontend atual: sem botao/fluxo final de exportacao conforme spec
- Backend atual: sem contrato explicito neste escopo para os dois formatos da spec

## Decisoes de congelamento para os proximos passos
1. O contrato alvo prevalece sobre o contrato atual.
2. O contrato atual foi congelado apenas como baseline de migracao.
3. Toda implementacao subsequente deve:
- manter compatibilidade com eventos WebSocket existentes
- introduzir suporte a `3_gate_fire` sem alterar `useWebSocket.js`
- adicionar endpoints faltantes em `/ativos/*` antes de acoplar a UI final do step 3

