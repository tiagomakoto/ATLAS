# SPEC CIRÚRGICA — tape_externas() — séries externas saem do ORBIT
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board  
**Data:** 2026-04-06  
**Versão:** 1.0  
**Modo:** Cirúrgico — correção de responsabilidade

---

## 1. Localização exata

**Arquivos afetados:**
- `delta_chaos/tape.py` — nova função `tape_externas()`
- `delta_chaos/orbit.py` — `ORBIT.rodar()` e `ORBIT._processar_ativo()`

---

## 2. Comportamento atual vs comportamento esperado

**Atual:**

`ORBIT.rodar()` contém:

```python
self._externas_cache = {}
for ativo in ohlcv_ativos:
    cfg_ativo = tape_carregar_ativo(ativo)
    for nome_serie, ativa in cfg_ativo.get("externas", {}).items():
        if ativa and nome_serie not in self._externas_cache:
            serie = tape_serie_externa(nome_serie, anos)
            if serie is not None:
                self._externas_cache[nome_serie] = serie
```

O ORBIT decide quais séries baixar, quando baixar e mantém `_externas_cache` em memória. Viola o padrão já estabelecido onde `rodar()` recebe dados prontos (`df_tape`, `ibov_close`) sem buscar.

**Esperado:**

`tape.py` expõe `tape_externas(ativos, anos)` que:
- Lê configs dos ativos para identificar séries ativas
- Baixa e cacheia via `tape_serie_externa()` existente
- Retorna dict pronto `{nome_serie: pd.Series}`

`ORBIT.rodar()` recebe o dict como parâmetro — não busca, não cacheia, não itera configs.

---

## 3. Constraint crítico — o que não pode ser alterado

- `tape_serie_externa(nome, anos)` existente — não modificar, apenas chamar
- Lógica interna de `_calcular_camadas(df, ib, externas_dict)` — não modificar
- Cache em disco em `EXTERNAS_DIR` — comportamento preservado
- Assinatura de `_processar_ativo()` pode mudar internamente mas o resultado retornado deve ser idêntico

---

## 4. Implementação esperada

**4.1 — Nova função em tape.py**

```python
def tape_externas(ativos: list, anos: list) -> dict:
    """
    Identifica séries externas ativas na configuração dos ativos,
    baixa e cacheia via tape_serie_externa().

    Retorna dict {nome_serie: pd.Series} com todas as séries ativas.
    Segue o mesmo padrão de tape_ohlcv() e tape_ibov() —
    o chamador recebe dados prontos sem saber como foram obtidos.

    Extensibilidade: adicionar nova fonte = novo entry no mapa
    dentro de tape_serie_externa() — tape_externas() não muda.
    """
    series_ativas = set()

    for ticker in ativos:
        cfg = tape_carregar_ativo(ticker)
        for nome_serie, ativa in cfg.get("externas", {}).items():
            if ativa:
                series_ativas.add(nome_serie)

    externas = {}
    for nome_serie in sorted(series_ativas):
        serie = tape_serie_externa(nome_serie, anos)
        if serie is not None:
            externas[nome_serie] = serie
            print(f"  ✓ Série externa {nome_serie}: {len(serie):,} dias")
        else:
            print(f"  ~ Série externa {nome_serie}: indisponível")

    return externas
```

**4.2 — Modificar ORBIT.rodar()**

Adicionar parâmetro `externas_dict` com default `None` para compatibilidade:

```python
def rodar(self, df_tape, anos, modo="pipeline", externas_dict=None):
    # ...
    # Remover bloco:
    #   self._externas_cache = {}
    #   for ativo in ohlcv_ativos:
    #       cfg_ativo = tape_carregar_ativo(ativo)
    #       for nome_serie, ativa in cfg_ativo.get("externas", {}).items():
    #           ...
    
    # Substituir por:
    self._externas_cache = externas_dict or {}
    
    # resto do rodar() inalterado
```

**4.3 — Modificar chamadores de ORBIT.rodar()**

Em `edge.py` — modo `--modo orbit` (novo modo leve):

```python
elif args.modo == "orbit":
    anos = (list(map(int, args.anos.split(",")))
            if args.anos
            else list(range(2002, datetime.now().year + 1)))
    cfg_ativo = tape_carregar_ativo(args.ticker)
    df_ohlcv  = tape_ohlcv(args.ticker, anos)
    df_ibov   = tape_ibov(anos)
    externas  = tape_externas([args.ticker], anos)  # ← novo
    orbit = ORBIT(universo={args.ticker: cfg_ativo})
    orbit.rodar(df_ohlcv, anos, modo="mensal",
                externas_dict=externas)             # ← novo
    tape_reflect_cycle(args.ticker,
                       datetime.now().strftime("%Y-%m"))
```

Em `edge.py` — `EDGE._executar_backtest()`:

```python
# Antes do loop de ciclos, após carregar ohlcv_ativos:
externas = tape_externas(self.ativos, anos)  # ← novo

# Passar para orbit.rodar():
df_regimes = self.orbit.rodar(
    df_tape, anos, modo=modo_orbit,
    externas_dict=externas)                  # ← novo
```

---

## 5. Testes obrigatórios

```python
# delta_chaos/tests/test_tape_externas.py

def test_retorna_dict_vazio_sem_externas_ativas(monkeypatch):
    """Nenhum ativo com externas ativas → retorna {}"""
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": False, "minerio": False}})
    resultado = tape_externas(["VALE3"], [2025, 2026])
    assert resultado == {}

def test_retorna_serie_para_externa_ativa(monkeypatch):
    """Ativo com usdbrl=True → retorna série usdbrl"""
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": True, "minerio": False}})
    mock_serie = pd.Series([5.0, 5.1], index=pd.to_datetime(["2026-01-02", "2026-01-03"]))
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa",
                        lambda nome, anos: mock_serie if nome == "usdbrl" else None)
    resultado = tape_externas(["VALE3"], [2026])
    assert "usdbrl" in resultado
    assert "minerio" not in resultado

def test_deduplicacao_entre_ativos(monkeypatch):
    """Dois ativos com mesma série ativa → tape_serie_externa chamada uma vez"""
    calls = []
    monkeypatch.setattr("delta_chaos.tape.tape_carregar_ativo",
                        lambda t: {"externas": {"usdbrl": True}})
    mock_serie = pd.Series([5.0])
    def mock_tape(nome, anos):
        calls.append(nome)
        return mock_serie
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa", mock_tape)
    tape_externas(["VALE3", "PETR4"], [2026])
    assert calls.count("usdbrl") == 1  # não baixa duas vezes

def test_orbit_rodar_nao_acessa_externas_internamente(monkeypatch):
    """ORBIT.rodar() com externas_dict injetado não chama tape_serie_externa"""
    calls = []
    monkeypatch.setattr("delta_chaos.tape.tape_serie_externa",
                        lambda nome, anos: calls.append(nome) or pd.Series())
    # instancia ORBIT e chama rodar() com externas_dict pronto
    # verifica que tape_serie_externa não foi chamada
    assert calls == []
```

---

## 6. Definição de pronto

- `ORBIT.rodar()` não contém nenhuma referência a `tape_serie_externa()` ou `_externas_cache` construído internamente
- `tape_externas(["VALE3"], [2026])` com `usdbrl=True` retorna dict com série `usdbrl`
- `tape_externas(["VALE3", "PETR4"], [2026])` com mesma série em ambos baixa apenas uma vez
- Todos os 4 testes passam com `pytest -v`
- Resultado numérico de `_calcular_camadas()` para S6 é idêntico ao anterior

---

## 7. Relação com outras specs

- **SPEC_ORBIT_skip_ciclo** — já executada. Esta spec modifica `rodar()` — o Plan deve aplicar ambas as mudanças sem conflito. O parâmetro `externas_dict` é adição não-destrutiva.
- **SPEC_ARCH_delimitacao_camadas** — reforça o mesmo princípio: TAPE fornece dados, ORBIT processa.

---

*Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*  
*Spec Cirúrgica v1.0 — 2026-04-06*  
*Aplicar sobre código existente — SPEC_ORBIT_skip_ciclo já executada*
