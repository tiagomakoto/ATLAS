# ATLAS Backend - Delta Chaos Integration

Sistema de trading quantitativo com modulos GATE, TUNE, ORBIT e streaming de logs via WebSocket.

## Quick Start

```bash
# 1. Iniciar servidor
python -m uvicorn atlas_backend.main:app --reload --host 0.0.0.0 --port 8000

# 2. Testar WebSocket (Terminal separado)
python ws_test.py

# 3. Disparar endpoints (Terminal separado)
curl -X POST http://localhost:8000/delta-chaos/gate -H "Content-Type: application/json" -d '{"ticker":"VALE3","confirm":true}'
```

## Endpoints Delta Chaos

### WebSocket

| Metodo | Rota       | Descricao                                    |
|--------|------------|----------------------------------------------|
| WS     | /ws/logs   | Streaming de logs em tempo real de todos os modulos |

**Cliente de teste:** ws_test.py
- URI: ws://localhost:8000/ws/logs
- Recebe: {"type":"terminal_log","level":"info","message":"..."}

### REST API

| Metodo | Endpoint                    | Descricao                      | Payload                           | Resposta                           |
|--------|-----------------------------|--------------------------------|-----------------------------------|------------------------------------|
| POST   | /delta-chaos/eod/preview    | Preview GATE EOD por ativo     | {}                                | {aprovados:[], excluidos:[]}       |
| POST   | /delta-chaos/eod/executar   | Executa EOD apos confirmacao   | {xlsx_dir?, confirm:true}         | {status:"ok", book_linhas:N}       |
| POST   | /delta-chaos/orbit          | Atualiza ORBIT mensal          | {ticker, confirm:true}            | {ticker, ciclos, ultimo_ciclo}     |
| POST   | /delta-chaos/tune           | Calibra TP/STOP (nao aplica)   | {ticker, confirm:true}            | {melhor_ir_valido, todas_combinacoes} |
| POST   | /delta-chaos/gate           | GATE completo 8 etapas         | {ticker, confirm:true}            | {resultado:"OPERAR|MONITORAR|EXCLUIDO"} |

**Payload comum:**
```json
{
  "ticker": "VALE3",
  "confirm": true,
  "description": "opcional"
}
```

**Exemplos de resposta:**

GATE:
```json
{
  "resultado": "MONITORAR",
  "ticker": "VALE3",
  "detalhes": {}
}
```

TUNE:
```json
{
  "status": "ok",
  "aviso": "Resultado registrado. NAO aplicado - requer confirmacao do CEO.",
  "melhor_ir_valido": {
    "label": "baseline",
    "tp": 0.5,
    "stop": 2.0,
    "ir_valido": 1.891
  }
}
```

## Seguranca

- Todos os endpoints de execucao requerem "confirm":true
- O backend nao valida sequencia preview->executar - responsabilidade do frontend
- CORS: allow_origins=["*"] para teste local (producao: restringir)

## Testes

```bash
# Validar sintaxe
python -m py_compile delta_chaos/tune.py

# Testar import chain
python -c "from delta_chaos.tune import executar_tune; print('OK')"

# Health check
curl http://localhost:8000/
```

## Estrutura

```
ATLAS/
├── atlas_backend/
│   ├── main.py                     # App FastAPI + WebSocket centralizado
│   ├── api/routes/delta_chaos.py   # Endpoints REST
│   └── core/terminal_stream.py     # emit_log() + broadcast
├── delta_chaos/
│   ├── tune.py                     # Calibracao TP/STOP
│   ├── gate.py                     # GATE 8 etapas
│   ├── orbit.py                    # Regimes ORBIT
│   └── init.py                     # Configs globais
├── ws_test.py                      # Cliente WebSocket de teste
└── README.md
```

## Notas Importantes

**TUNE:**
- Calcula e registra em historico_config[]
- NAO APLICA automaticamente
- Requer acao explicita do operador/CEO

**EOD:**
- Fluxo obrigatorio: preview -> operador confirma -> executar
- O backend nao verifica a sequencia

**WebSocket:**
- Conexao unica em /ws/logs recebe logs de todos os modulos
- Arquitetura centralizada em main.py

## Fluxo Completo (Fase 2)

1. POST /eod/preview -> Lista ativos aprovados/excluidos
2. Operador revisa no frontend
3. POST /eod/executar -> Processa BOOK
4. POST /gate -> Decide: OPERAR/MONITORAR/EXCLUIR
5. POST /tune (opcional) -> Calibra parametros
6. WebSocket /ws/logs -> Logs em tempo real durante todo o fluxo

---

ATLAS Backend - Delta Chaos Integration - Fase 1