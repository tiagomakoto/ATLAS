# SPEC CIRÚRGICA — reflect_cycle: renormalização de pesos quando divergência ausente
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-07  
**Versão:** 1.1 (corrigida — remove nova função desnecessária)  
**Modo:** Cirúrgico — correção de dependência implícita + bug ValueError

---

## 1. Problema identificado

`reflect_cycle_calcular()` em `edge.py` depende de `reflect_daily_history{}` para calcular a componente de divergência (`iv_prem_ratio`, `ret_vol_ratio`). Quando `reflect_daily_history` está vazio — porque o CEO não rodou EOD no ciclo — a função falha com `ValueError`.

Isso trava o TUNE após 126 dias úteis e o `orbit_update` mensal.

**Causa raiz:** ausência de condicional para o caso em que divergência não está disponível. A solução é renormalizar os pesos dentro da função existente — sem nova função, sem nova fonte de dados.

---

## 2. Localização exata

**Arquivo:** `delta_chaos/edge.py`  
**Função:** `reflect_cycle_calcular(ativo, ciclo_id)`  
**Seção afetada:** bloco de leitura de `reflect_daily_history` e cálculo de score final

---

## 3. Comportamento atual vs esperado

| | Atual | Esperado |
|---|---|---|
| `reflect_daily_history` presente | calcula divergência, aplica 0.33/0.33/0.33 | idem |
| `reflect_daily_history` vazio | lança `ValueError` | renormaliza para 0.00/0.50/0.50, continua |

---

## 4. Implementação esperada

Substituir o bloco de cálculo de score por lógica com condicional de pesos:

```python
# Lê pesos base da config
w_base = carregar_config()["reflect"]["weights"]
# Esperado: {"aceleracao": 0.33, "divergencia": 0.33, "delta_ir": 0.33}

# Verifica se divergência está disponível no ciclo
daily_hist = cfg.get("reflect_daily_history", {})
divergencia_disponivel = False
iv_prem_avg = None
ret_vol_avg = None

if daily_hist:
    daily_df = pd.DataFrame.from_dict(daily_hist, orient="index")
    daily_df.index = pd.to_datetime(daily_df.index)
    try:
        mask = daily_df.index.to_period("M") == pd.Period(ciclo_id)
        df_ciclo = daily_df[mask].copy()
        if not df_ciclo.empty:
            iv_prem_avg = float(df_ciclo["iv_prem_ratio"].mean())
            ret_vol_avg = float(df_ciclo["ret_vol_ratio"].mean())
            divergencia_disponivel = True
    except Exception:
        pass

# Define pesos efetivos conforme disponibilidade
if divergencia_disponivel:
    w = {
        "aceleracao":  w_base["aceleracao"],   # 0.33
        "divergencia": w_base["divergencia"],  # 0.33
        "delta_ir":    w_base["delta_ir"]      # 0.33
    }
    fonte_divergencia = "eod_diario"
else:
    # Renormaliza: divergência = 0.00, restante dividido entre aceleração e delta_IR
    total = w_base["aceleracao"] + w_base["delta_ir"]
    w = {
        "aceleracao":  w_base["aceleracao"] / total,  # 0.50
        "divergencia": 0.0,                           # 0.00
        "delta_ir":    w_base["delta_ir"] / total     # 0.50
    }
    fonte_divergencia = "ausente_renormalizado"

# Score com pesos efetivos
reflect_score = (
    norm_acel     * w["aceleracao"] +
    norm_dir      * w["divergencia"] +
    norm_delta_ir * w["delta_ir"]
)
```

Registrar auditoria no ciclo gravado:

```python
entrada_completa["fonte_divergencia"]      = fonte_divergencia
entrada_completa["divergencia_disponivel"] = divergencia_disponivel
if not divergencia_disponivel:
    entrada_completa["diagnostico"] = (
        (entrada_completa.get("diagnostico", "") +
         " | divergencia ausente — pesos renormalizados 0.00/0.50/0.50").strip(" | ")
    )
```

---

## 5. O que não deve ser tocado

- `reflect_daily_calcular()` e `reflect_daily_salvar()` — sem modificações
- `gate_eod_verificar()` — sem modificações
- Lógica de aceleração e delta_IR — sem modificações
- Estrutura do `reflect_all_cycles_history[]` — apenas adiciona campos novos
- `tape.py` — **sem modificações**. Nenhuma função nova em tape.

---

## 6. Testes obrigatórios

```python
# delta_chaos/tests/test_reflect_cycle.py

def test_reflect_cycle_sem_daily_history_nao_lanca():
    """reflect_daily_history vazio → não lança ValueError"""
    # cfg com reflect_daily_history = {}
    # reflect_cycle_calcular() deve retornar score válido

def test_reflect_cycle_sem_daily_history_usa_pesos_renormalizados():
    """reflect_daily_history vazio → pesos 0.00/0.50/0.50"""
    # resultado["fonte_divergencia"] == "ausente_renormalizado"
    # resultado["divergencia_disponivel"] == False

def test_reflect_cycle_com_daily_history_usa_pesos_normais():
    """reflect_daily_history presente → pesos 0.33/0.33/0.33"""
    # resultado["fonte_divergencia"] == "eod_diario"
    # resultado["divergencia_disponivel"] == True

def test_reflect_cycle_registra_campos_auditoria():
    """Campos fonte_divergencia e divergencia_disponivel gravados no ciclo"""
    # cfg["reflect_all_cycles_history"][-1] contém ambos os campos

def test_reflect_cycle_score_valido_sem_divergencia():
    """Score calculado com aceleração + delta_IR quando divergência ausente"""
    # norm_acel e norm_delta_ir não-nulos → score > 0
    # componente divergência = 0.0 × 0.0 = 0.0
```

---

## 7. Definição de pronto

- `reflect_cycle_calcular("VALE3", "2026-04")` com `reflect_daily_history={}` não lança `ValueError`
- Score calculado com pesos `0.00/0.50/0.50` quando divergência ausente
- Score calculado com pesos `0.33/0.33/0.33` quando divergência disponível
- `reflect_all_cycles_history[-1]` contém `fonte_divergencia` e `divergencia_disponivel`
- TUNE após 126 dias úteis executa sem depender de EOD ter sido rodado
- Todos os 5 testes passam com `pytest -v`
- `tape.py` inalterado

---

## 8. Relação com outras specs

- **SPEC_RENOMEACAO** — aplicar antes desta. Nomenclatura canônica já usada aqui.
- **SPEC_ARCH_delimitacao_camadas** — reforça: lógica de pesos vive no EDGE, não no TAPE.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec Cirúrgica v1.1 — 2026-04-07*  
*Corrigida: remove tape_reflect_divergencia_ciclo; solução via condicional de pesos na função existente*
