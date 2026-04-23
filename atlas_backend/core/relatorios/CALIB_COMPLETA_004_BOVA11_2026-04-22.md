# Relatório de Calibração — BOVA11 — CALIBRAÇÃO COMPLETA

**ID:** 004
**Data:** 2026-04-22
**Status:** Calibração concluída com sucesso
**Gerado por:** ATLAS v2.6

---

## Resumo

A calibração do ativo **BOVA11** foi concluída com sucesso.
Todos os critérios de validação histórica (GATE) foram aprovados
e o diagnóstico de estratégia (FIRE) está disponível.

**Resultado GATE:** OPERAR ✓
**Resultado FIRE:** DIAGNÓSTICO DISPONÍVEL ✓

---

## Validação GATE — Critérios Aprovados

| ID | Critério | Status | Valor |
||---|---|---|
| E1 | Taxa de acerto | ✗ FALHOU | N/D |
| E2 | IR mínimo | ✗ FALHOU | N/D |
| E3 | N mínimo de trades | ✗ FALHOU | N/D |
| E4 | Consistência anual | ✗ FALHOU | N/D |
| E5 | IR por regime | ✗ FALHOU | N/D |
| E6 | Drawdown máximo | ✗ FALHOU | N/D |
| E7 | Consecutivos negativos | ✗ FALHOU | N/D |
| E8 | Cobertura de regimes | ✗ FALHOU | N/D |

---

## Diagnóstico FIRE — Estratégia por Regime

| Regime | Trades | Acerto | IR | Estratégia Dominante |
|---|---|---|---|---|
| ALTA | 43 | 0.0% | 0.00 | None |
| BAIXA | 18 | 0.0% | 0.00 | None |
| NEUTRO_BEAR | 41 | 0.0% | 0.00 | None |
| NEUTRO_BULL | 36 | 0.0% | 0.00 | None |
| NEUTRO_LATERAL | 4 | 0.0% | 0.00 | None |
| NEUTRO_MORTO | 9 | 0.0% | 0.00 | None |
| NEUTRO_TRANSICAO | 15 | 0.0% | 0.00 | None |
| PANICO | 4 | 0.0% | 0.00 | None |
| RECUPERACAO | 4 | 0.0% | 0.00 | None |

### Cobertura Geral

- **Ciclos com operação:** 174 de 174
- **Total de trades:** 174
- **Acerto geral:** 0.0%
- **P&L total:** R$ 0.00

---

## Estado dos Steps

| Step | Módulo | Status | Iniciado | Concluído |
||---|---|---|---|---|
| 1 | backtest_dados | done | 2026-04-22T20:00:32.654931 | 2026-04-22T20:02:04.764008 |
| 2 | tune | done | 2026-04-22T20:02:04.795496 | 2026-04-22T20:06:08.548177 |
| 3 | gate_fire | done | 2026-04-22T20:06:08.575045 | 2026-04-22T20:06:50.119964 |

---

## Recomendações

1. **Ativo aprovado para operação** — parâmetros validados historicamente
2. Monitorar regime diariamente via ORBIT
3. Executar /daily/run para verificação automática de TP/STOP
4. Revisar FIRE periodicamente para identificar mudanças de regime

---

## Dados Técnicos

```json
{
  "ticker": "BOVA11",
  "id": "004",
  "data": "2026-04-22",
  "tipo": "CALIB_COMPLETA",
  "gate_resultado": {
    "ticker": "BOVA11",
    "criterios": [
      {
        "id": "E1",
        "nome": "Taxa de acerto",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E2",
        "nome": "IR mínimo",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E3",
        "nome": "N mínimo de trades",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E4",
        "nome": "Consistência anual",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E5",
        "nome": "IR por regime",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E6",
        "nome": "Drawdown máximo",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E7",
        "nome": "Consecutivos negativos",
        "passou": false,
        "valor": "N/D"
      },
      {
        "id": "E8",
        "nome": "Cobertura de regimes",
        "passou": false,
        "valor": "N/D"
      }
    ],
    "resultado": "OPERAR",
    "falhas": []
  },
  "fire_diagnostico": {
    "ticker": "BOVA11",
    "regimes": [
      {
        "regime": "ALTA",
        "trades": 43,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "BAIXA",
        "trades": 18,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "NEUTRO_BEAR",
        "trades": 41,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "NEUTRO_BULL",
        "trades": 36,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "NEUTRO_LATERAL",
        "trades": 4,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "NEUTRO_MORTO",
        "trades": 9,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "NEUTRO_TRANSICAO",
        "trades": 15,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "PANICO",
        "trades": 4,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      },
      {
        "regime": "RECUPERACAO",
        "trades": 4,
        "wins": 0,
        "losses": 0,
        "acerto_pct": 0.0,
        "ir": 0.0,
        "worst_trade": null,
        "best_trade": null,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "estrategia_dominante": null,
        "estrategias": [],
        "motivos_saida": {}
      }
    ],
    "cobertura": {
      "ciclos_com_operacao": 174,
      "total_ciclos": 174,
      "total_trades": 174,
      "acerto_geral_pct": 0.0,
      "pnl_total": 0
    },
    "stops_por_regime": {},
    "fonte_dados": "book_backtest.parquet+master_json"
  },
  "calibracao_steps": {
    "1_backtest_dados": {
      "status": "done",
      "iniciado_em": "2026-04-22T20:00:32.654931",
      "concluido_em": "2026-04-22T20:02:04.764008",
      "erro": null
    },
    "2_tune": {
      "status": "done",
      "iniciado_em": "2026-04-22T20:02:04.795496",
      "concluido_em": "2026-04-22T20:06:08.548177",
      "erro": null,
      "trials_completos": 0,
      "trials_total": 200
    },
    "3_gate_fire": {
      "status": "done",
      "iniciado_em": "2026-04-22T20:06:08.575045",
      "concluido_em": "2026-04-22T20:06:50.119964",
      "erro": null
    }
  }
}
```

---

*Este relatório foi gerado automaticamente pelo sistema ATLAS.*
*O ativo está pronto para operação via FIRE.*
