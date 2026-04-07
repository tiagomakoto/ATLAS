# SPEC RENOMEAÇÃO — Nomenclatura Canônica de Funções
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-06  
**Versão:** 1.0  
**Modo:** Refatoração — sem alteração de lógica

---

## 1. Princípio de nomenclatura

```
<módulo>_<substantivo>_<verbo>()

módulo    → quem é responsável
substantivo → o objeto da operação
verbo     → a ação executada
```

Prefixos por camada:

```
tape_    → busca, lê, escreve dados brutos
orbit_   → classificação de regime
reflect_ → estado do edge (vive no EDGE)
gate_    → validação
dc_      → protocolo ATLAS↔Delta Chaos (dc_runner.py)
```

---

## 2. Mapa de renomeação

### tape.py

| Nome atual | Nome novo | Observação |
|---|---|---|
| `tape_carregar_ativo()` | `tape_ativo_carregar()` | |
| `tape_salvar_ativo()` | `tape_ativo_salvar()` | |
| `tape_inicializar_ativo()` | `tape_ativo_inicializar()` | |
| `tape_salvar_ciclo()` | `tape_ciclo_salvar()` | |
| `tape_regime_para_data()` | `tape_ciclo_para_data()` | |
| `tape_ohlcv()` | `tape_ohlcv_carregar()` | |
| `tape_ibov()` | `tape_ibov_carregar()` | |
| `tape_serie_externa()` | `tape_externa_carregar()` | |
| `tape_externas()` | `tape_externas_carregar()` | SPEC_TAPE_externas |
| `tape_backtest()` | `tape_historico_carregar()` | baixa COTAHIST + gregas |
| `tape_paper()` | `tape_eod_carregar()` | |
| `tape_verificar_dados()` | `tape_dados_verificar()` | SPEC_TAPE_verificar_dados |
| `tape_sizing_reflect()` | **remover** | move para EDGE como `reflect_sizing_calcular()` |
| `tape_process_eod_file()` | **remover** | move para EDGE via `--modo reflect_daily` |
| `tape_reflect_daily()` | **dividir** | cálculo → `tape_reflect_calcular()` em tape.py; persistência → EDGE |
| `tape_reflect_cycle()` | **remover** | move para EDGE via `--modo orbit` |

### orbit.py

| Nome atual | Nome novo | Observação |
|---|---|---|
| `ORBIT.rodar()` | `orbit_rodar()` | método da classe |
| `ORBIT.regime_para_data()` | `orbit_regime_para_data()` | |
| `ORBIT._processar_ativo()` | `orbit_ativo_processar()` | privado |
| `ORBIT._carregar_cache()` | `orbit_cache_carregar()` | privado |

### gate.py

| Nome atual | Nome novo | Observação |
|---|---|---|
| `executar_gate()` | `gate_executar()` | |

### gate_eod.py

| Nome atual | Nome novo | Observação |
|---|---|---|
| `gate_eod()` | `gate_eod_verificar()` | |

### Funções novas no EDGE (saem do TAPE)

| Nome novo | Origem | Onde vive |
|---|---|---|
| `reflect_daily_calcular()` | `tape_reflect_daily()` — só cálculo | `edge.py` ou módulo `reflect.py` |
| `reflect_daily_salvar()` | `tape_reflect_daily()` — persistência | `edge.py` |
| `reflect_cycle_calcular()` | `tape_reflect_cycle()` | `edge.py` |
| `reflect_sizing_calcular()` | `tape_sizing_reflect()` | `edge.py` |

### Modos CLI — edge.py

| Nome atual | Nome novo | Observação |
|---|---|---|
| `--modo orbit` | `--modo orbit_update` | atualização mensal leve |
| `--modo backtest_dados` | `--modo orbit_backtest` | onboarding — COTAHIST completo |
| `--modo backtest_gate` | `--modo gate_backtest` | |
| `--modo reflect_daily` | mantém | |
| `--modo gate_eod` | mantém | |
| `--modo eod` | mantém | |
| `--modo eod_preview` | **remover** | coberto pelo orquestrador |
| `--modo tune` | mantém | |

### dc_runner.py — protocolo

| Nome atual | Nome novo | Observação |
|---|---|---|
| `run_orbit()` | `dc_orbit_backtest()` | onboarding |
| `run_orbit_update()` | `dc_orbit_update()` | atualização mensal |
| `run_gate()` | `dc_gate_backtest()` | |
| `run_gate_eod()` | `dc_gate_eod()` | |
| `run_reflect_daily()` | `dc_reflect_daily()` | |
| `run_tune()` | `dc_tune()` | |
| `run_eod()` | `dc_eod()` | |
| `run_eod_preview()` | **remover** | |
| `run_orchestrator()` | `dc_orchestrator()` | |

---

## 3. Procedimento de execução

**Regra crítica:** substituição global antes de remover qualquer nome antigo.

Para cada renomeação:

```
1. grep -r "nome_antigo" . --include="*.py"
   → listar TODOS os arquivos que referenciam o nome
2. substituir em todos os arquivos encontrados
3. verificar imports explícitos em cada arquivo afetado
4. rodar testes se existirem
5. só então remover o nome antigo
```

Nenhum alias de compatibilidade — nomes antigos não permanecem como wrappers.

---

## 4. O que não muda

- Lógica interna de nenhuma função
- Assinaturas de parâmetros
- Comportamento de retorno
- Endpoints HTTP em `delta_chaos.py`
- Estrutura dos arquivos JSON
- Escrita atômica — obrigatória em todos os `_salvar()`

---

## 5. Ordem de execução recomendada

```
1. tape.py          — renomear funções mantidas + dividir tape_reflect_daily()
2. gate.py          — renomear gate_executar()
3. gate_eod.py      — renomear gate_eod_verificar()
4. orbit.py         — renomear métodos da classe ORBIT
5. edge.py          — renomear modos CLI + adicionar funções reflect_*
6. dc_runner.py     — renomear todas as run_* para dc_*
7. delta_chaos.py   — atualizar chamadas para dc_*
8. grep global      — verificar referências remanescentes
```

---

## 6. Definição de pronto

- `grep -r "tape_backtest\|tape_reflect_daily\|tape_reflect_cycle\|tape_sizing_reflect\|tape_process_eod_file\|run_orbit\|run_gate\|run_tune\|run_eod\|executar_gate\|gate_eod(" . --include="*.py"` retorna zero resultados
- Todos os endpoints do ATLAS continuam funcionando
- Check Status via ATLAS produz resultado equivalente ao anterior

---

## 7. Relação com outras specs

Esta spec é **pré-requisito** para todas as specs futuras — novas specs já usam a nomenclatura canônica. Specs anteriores desta sessão usam nomes antigos — o Plan deve aplicar esta spec primeiro e adaptar as demais.

**Exceção:** SPEC_TAPE_verificar_dados e SPEC_TAPE_externas já usam nomes próximos do padrão — o Plan adapta os nomes ao aplicar.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec v1.0 — 2026-04-06*  
*Pré-requisito para todas as specs futuras desta sessão*
