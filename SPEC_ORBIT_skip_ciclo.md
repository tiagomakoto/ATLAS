# SPEC CIRÚRGICA — ORBIT skip por ciclo
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-04  
**Versão:** 1.0  
**Modo:** Cirúrgico — bug/lacuna de comportamento

---

## 1. Localização exata

**Arquivo:** `delta_chaos/orbit.py`  
**Classe:** `ORBIT`  
**Método:** `rodar(self, df_tape, anos, modo="pipeline")`  
**Função auxiliar afetada:** `_carregar_cache(self, anos)`

---

## 2. Comportamento atual vs comportamento esperado

**Atual:**

`_carregar_cache()` é tudo-ou-nada:
- Se **todos** os ciclos necessários existem em `historico[]` → retorna DataFrame do cache, `rodar()` encerra
- Se **qualquer** ciclo está ausente → retorna `None`, `rodar()` reprocessa **todos** os ciclos desde o primeiro ano informado

Na virada do mês, apenas o ciclo do mês novo está ausente. O ORBIT reprocessa todos os ciclos desde 2002 — leva minutos. Inaceitável no contexto do Check Status diário.

**Esperado:**

`rodar()` deve processar **apenas os ciclos ausentes** em `historico[]` do master JSON de cada ativo. Ciclos já presentes devem ser skipped sem reprocessamento. O resultado deve ser idêntico ao atual para o ciclo novo — os dados históricos para calibração Ridge já estão em `historico[]` e o OHLCV está em cache local.

**Exemplo concreto:**

```
historico[] tem ciclos: 2002-01 até 2026-03  (286 ciclos)
_gerar_ciclos([2002..2026]) gera: 2002-01 até 2026-04  (287 ciclos)
ciclos ausentes: ["2026-04"]
rodar() deve processar: apenas "2026-04"
```

---

## 3. Constraint crítico — o que não pode ser alterado

- A assinatura de `rodar(self, df_tape, anos, modo)` não muda
- A assinatura de `_carregar_cache(self, anos)` não muda — mas seu comportamento interno muda
- O resultado gravado em `historico[]` via `tape_salvar_ciclo()` deve ser idêntico ao atual
- O z-score rolling do REFLECT não é afetado — `tape_reflect_cycle()` é chamado pelo EDGE, não pelo ORBIT
- O modo `"pipeline"` (backtest completo) deve continuar funcionando sem skip — o skip é aplicado apenas quando `modo="mensal"` ou quando chamado pelo novo `--modo orbit` do CLI

---

## 4. Implementação esperada

**4.1 — Modificar `_carregar_cache()` para retornar ciclos faltantes**

Substituir retorno binário (`DataFrame | None`) por retorno que indica quais ciclos processar:

```python
def _carregar_cache(self, anos) -> tuple[pd.DataFrame | None, list[str]]:
    """
    Retorna (df_cache, ciclos_faltantes).
    df_cache: DataFrame com ciclos existentes (pode ser vazio)
    ciclos_faltantes: lista de ciclo_ids ausentes em historico[]
    """
    necessarios = set()
    for ano in anos:
        for mes in range(1, 13):
            if date(ano, mes, 1) <= date.today():
                necessarios.add(f"{ano}-{mes:02d}")

    rows = []
    ciclos_existentes = set()

    for ativo in self.ativos:
        dados = tape_carregar_ativo(ativo)
        historico = dados.get("historico", [])
        existentes_ativo = {c["ciclo_id"] for c in historico}
        ciclos_existentes |= existentes_ativo
        rows.extend(historico)

    ciclos_faltantes = sorted(necessarios - ciclos_existentes)

    if not ciclos_faltantes:
        # Cache completo — nada a processar
        df = pd.DataFrame(rows)
        if not df.empty:
            df["ciclo_id"] = df["ciclo_id"].astype(str)
            print(f"  ✓ Cache completo — {len(df):,} registros, nenhum ciclo novo")
        return df, []

    if rows:
        df_existente = pd.DataFrame(rows)
        df_existente["ciclo_id"] = df_existente["ciclo_id"].astype(str)
        print(f"  ~ Cache parcial — {len(ciclos_faltantes)} ciclo(s) ausente(s): {ciclos_faltantes}")
        return df_existente, ciclos_faltantes

    print(f"  ~ Cache vazio — processando {len(ciclos_faltantes)} ciclos")
    return pd.DataFrame(), ciclos_faltantes
```

**4.2 — Modificar `rodar()` para usar ciclos faltantes**

```python
def rodar(self, df_tape, anos, modo="pipeline"):
    df_cache, ciclos_faltantes = self._carregar_cache(anos)

    # Cache completo — retorna sem processar
    if not ciclos_faltantes:
        return df_cache

    # Modo pipeline (backtest): processa todos os ciclos faltantes
    # Modo mensal (atualização): processa apenas ciclos faltantes
    # Comportamento é o mesmo — a diferença está em quantos ciclos faltam
    ciclos_a_processar = ciclos_faltantes

    # ... resto do rodar() existente, substituindo:
    #   ciclos = self._gerar_ciclos(anos)
    # por:
    #   ciclos = ciclos_a_processar
```

O loop interno de `rodar()` itera sobre `ciclos_a_processar` em vez de `self._gerar_ciclos(anos)`. O `score_hist` e `vol_hist` precisam ser inicializados com os dados de `df_cache` (ciclos existentes) para que a calibração Ridge do ciclo novo tenha contexto histórico correto.

**4.3 — Inicializar score_hist a partir do cache existente**

Antes do loop de ciclos a processar, popular `score_hist` e `vol_hist` com os dados já existentes em `df_cache`:

```python
score_hist = {}
vol_hist = {}

# Popular com ciclos existentes para contexto histórico
if not df_cache.empty:
    for ativo in self.ativos:
        df_ativo_cache = df_cache[df_cache["ativo"] == ativo].sort_values("ciclo_id")
        if not df_ativo_cache.empty:
            score_hist[ativo] = df_ativo_cache["score"].tolist()[-6:]
            vol_hist[ativo] = df_ativo_cache["vol_21d"].tolist()[-6:]
```

---

## 5. Definição de pronto

- `rodar()` com `anos=[2002..2026]` quando `historico[]` tem todos os ciclos até 2026-03 processa **apenas "2026-04"** — verificável por log `"1 ciclo(s) ausente(s): ['2026-04']"`
- `rodar()` com `historico[]` vazio processa todos os ciclos — comportamento de backtest completo preservado
- `tape_salvar_ciclo()` é chamado apenas para o ciclo novo — não regrava ciclos existentes
- O resultado do ciclo novo (`regime`, `ir`, `sizing`, `score`) é numericamente equivalente ao que seria gerado pelo reprocessamento completo

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec Cirúrgica v1.0 — 2026-04-04*  
*Entregar antes ou junto com SPEC_ATLAS_v2.6 Prompt 1 — o --modo orbit do CLI depende deste comportamento*
