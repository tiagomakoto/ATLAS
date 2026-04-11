# ADVANTAGE — Especificação: Data Layer
**Versão:** 3.1
**Destino:** Agente `plan` — Qwen3 Coder 480B A35B
**Autorização:** CEO Tiago
**Base:** Spec v1 (em execução) + Schema v2 (referência canônica)
**Atualização 3.1:** ABPO substituída por IBGE SIDRA Tabela 8889 — dado primário confirmado

---

## INSTRUÇÃO INICIAL OBRIGATÓRIA

A Spec v1 já está em execução parcial.
**Antes de planejar qualquer implementação**, o agente deve:

1. Inspecionar `advantage/src/data_layer/` e `advantage/data/raw/`
2. Para cada item da Seção 11 (Definição de Pronto da v1), verificar se está implementado
3. Produzir um relatório de estado antes de propor qualquer código:

```
ESTADO v1:
[x] item implementado e funcional
[~] item implementado parcialmente
[ ] item ausente
```

4. Implementar **apenas o que está ausente ou parcial**
5. Nunca sobrescrever código funcional existente

---

## 1. DECISÕES ARQUITETURAIS — IMUTÁVEIS

| Decisão | Valor |
|---|---|
| Banco de dados | SQLite (fase atual). PostgreSQL é fase futura. |
| Scheduler | APScheduler — `BlockingScheduler` com timezone `America/Sao_Paulo` |
| Acesso ao banco | Direto via Python — sem API REST, JWT ou OAuth2 |
| Série temporal | Append-only — nunca UPDATE em dados históricos |
| Linguagem | Python 3.10+ |
| Scheduler em produção | `python -m src.data_layer.scheduler` — independente de VS Code |

**Critério de rejeição imediato:**
- UPDATE em dados históricos
- API REST para acesso interno
- PostgreSQL, Airflow ou Docker
- Scheduler dependente de VS Code

---

## 2. ESTRUTURA DE PASTAS — REFERÊNCIA

```
advantage/
├── data/
│   └── raw/
│       ├── preco_volume.db
│       ├── macro.db
│       ├── alternativo.db
│       └── portfolio.db
├── src/
│   └── data_layer/
│       ├── __init__.py
│       ├── db/
│       │   ├── schema.py
│       │   └── connection.py
│       ├── collectors/
│       │   ├── preco_volume.py
│       │   ├── macro_brasil.py
│       │   ├── macro_global.py
│       │   ├── alternativo.py
│       │   └── noticias.py
│       ├── scheduler.py
│       └── utils.py
└── tests/
    └── data_layer/
```

---

## 3. DELTA v1 → v3: O QUE MUDA

### 3.1 Tabelas novas — ausentes na Spec v1, presentes no Schema v2

As tabelas abaixo não existiam na Spec v1. Criar no `schema.py` e
adicionar coletores ou cálculos correspondentes.

#### `retornos_historicos` → `preco_volume.db`
```sql
CREATE TABLE IF NOT EXISTS retornos_historicos (
    ticker          TEXT NOT NULL,
    data            DATE NOT NULL,
    retorno_diario  REAL,
    retorno_log     REAL,
    data_calculo    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data)
);
```
**Calculado por:** `calcular_indicadores` no scheduler,
após inserção em `preco_volume`.
Fórmula: `retorno_diario = (fechamento_adj / fechamento_adj_anterior) - 1`
Fórmula: `retorno_log = ln(fechamento_adj / fechamento_adj_anterior)`

#### `taxa_conversao` → `portfolio.db`
```sql
CREATE TABLE IF NOT EXISTS taxa_conversao (
    ticker                  TEXT NOT NULL,
    data_avaliacao          DATE NOT NULL,
    total_sinais_causa      INTEGER,
    confirmados_expressao   INTEGER,
    nao_confirmados         INTEGER,
    taxa_conversao          REAL,
    n_minimo_valido         INTEGER DEFAULT 30,
    status                  TEXT DEFAULT 'insuficiente',
    data_coleta             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data_avaliacao)
);
```
**Nota:** Populada pela Camada 2, não pelo Data Layer.
Criar tabela vazia — estruturada desde o início.

#### `scores_causa` → `portfolio.db`
```sql
CREATE TABLE IF NOT EXISTS scores_causa (
    ticker                      TEXT NOT NULL,
    data                        DATE NOT NULL,
    score_fluxo                 REAL,
    score_ciclo_global          REAL,
    score_ciclo_local           REAL,
    score_fundamentals          REAL,
    score_qualitativo           REAL,
    score_dados_alt             REAL,
    score_temperatura           REAL,
    score_polymarket            REAL,
    score_google_trends         REAL,
    score_composto              REAL,
    intervalo_conf_inf          REAL,
    intervalo_conf_sup          REAL,
    classificacao               TEXT,
    trigger_barbell             INTEGER DEFAULT 0,
    trigger_barbell_motivo      TEXT,
    estilo_candidato            TEXT,
    threshold_atingido          INTEGER DEFAULT 0,
    pesos_versao                TEXT,
    versao_modelo               TEXT,
    data_calculo                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data)
);
```
**Nota:** Populada pela Camada 1, não pelo Data Layer.
Criar tabela vazia — estruturada desde o início.

#### `documentos_qualitativos` → `alternativo.db`
```sql
CREATE TABLE IF NOT EXISTS documentos_qualitativos (
    ticker              TEXT,
    data_publicacao     DATE NOT NULL,
    tipo_documento      TEXT NOT NULL,
    texto_extraido      TEXT,
    score_sentimento    REAL,
    score_guidance      REAL,
    score_risco         REAL,
    score_narrativa     REAL,
    peso_confianca      REAL DEFAULT 0.3,
    modelo_llm          TEXT,
    prompt_versao       TEXT,
    data_processamento  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fonte_original      TEXT,
    PRIMARY KEY (ticker, data_publicacao, tipo_documento)
);
```
**Nota:** Populada sob demanda (fatos relevantes, calls de resultado).
Criar tabela vazia — estruturada desde o início.

#### `polymarket_eventos` → `alternativo.db`
```sql
CREATE TABLE IF NOT EXISTS polymarket_eventos (
    data                DATE NOT NULL,
    timestamp           TIMESTAMP NOT NULL,
    market_id           TEXT NOT NULL,
    descricao_evento    TEXT,
    categoria           TEXT,
    probabilidade       REAL,
    variacao_24h        REAL,
    liquidez_usd        REAL,
    data_resolucao      DATE,
    impacto_b3          TEXT,
    ticker_afetado      TEXT,
    fonte               TEXT DEFAULT 'polymarket',
    data_coleta         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (market_id, timestamp)
);
```
**Frequência:** Diária — adicionar ao `job_diario` do scheduler.
**Coletor:** adicionar `polymarket.py` em `collectors/`.
**API:** `https://gamma-api.polymarket.com/markets` — pública, sem chave.
Filtrar por categorias: copom, fed, politica_brasil, recessao_global, commodity.

#### `intraday_slot` → `preco_volume.db`
```sql
CREATE TABLE IF NOT EXISTS intraday_slot (
    ticker      TEXT NOT NULL,
    timestamp   TIMESTAMP NOT NULL,
    preco       REAL,
    volume      INTEGER,
    lado        TEXT,
    tipo_agente TEXT,
    fonte_api   TEXT,
    status      TEXT DEFAULT 'vazio_fase_atual',
    PRIMARY KEY (ticker, timestamp)
);
```
**Nota:** Tabela criada vazia — slot para fase futura de APIs intraday.
Não implementar coletor. Apenas garantir que a tabela existe.

---

### 3.2 Tabelas existentes na v1 — campos adicionais do Schema v2

#### `portfolio_estado` — adicionar campos ausentes

A v1 tem a tabela com campos básicos. Adicionar via `ALTER TABLE IF NOT EXISTS`
(verificar se campo já existe antes de alterar — idempotente):

```sql
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    sizing_inicial REAL;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    sizing_atual REAL;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    score_causa_entrada REAL;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    classificacao_entrada TEXT;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    causa_alternativa_compartilhada TEXT;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    data_saida DATE;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    preco_saida REAL;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    resultado_pct REAL;
ALTER TABLE portfolio_estado ADD COLUMN IF NOT EXISTS
    motivo_saida TEXT;
```

**Valores válidos de `motivo_saida`:**
`stop / target / deterioracao_causa / deterioracao_expressao /
temperatura_noticias / polymarket_evento / manual`

#### `temperatura_noticias` — campos adicionais do Schema v2

A v1 tem campos básicos. O Schema v2 adiciona fórmula completa de temperatura.
Se os campos abaixo não existirem, adicionar:

```sql
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    escopo TEXT DEFAULT 'ticker';
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    referencia TEXT;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    polaridade REAL;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    intensidade REAL;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    urgencia TEXT DEFAULT 'rotineiro';
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    volume_tipico REAL;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    temperatura REAL;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    temperatura_zscore REAL;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    fontes_rss TEXT;
ALTER TABLE temperatura_noticias ADD COLUMN IF NOT EXISTS
    modelo_llm TEXT;
```

**Fórmula de temperatura** (implementar em `utils.py`):
```python
import math

def calcular_temperatura(
    polaridade: float,
    intensidade: float,
    volume_atual: int,
    volume_tipico: float
) -> float:
    """
    temperatura = polaridade × intensidade × log(volume / volume_típico)
    Retorna 0.0 se volume_tipico == 0.
    """
    if volume_tipico == 0:
        return 0.0
    return polaridade * intensidade * math.log(volume_atual / volume_tipico)

def calcular_temperatura_zscore(
    temperatura: float,
    media_historica: float,
    desvpad_historico: float
) -> float:
    if desvpad_historico == 0:
        return 0.0
    return (temperatura - media_historica) / desvpad_historico
```

#### `indicadores_compartilhados` — reconciliação v1 vs Schema v2

A v1 tem: `sma_20`, `sma_50`, `sma_200`, `ema_9`, `ema_21`, `rsi_14`,
`macd`, `macd_signal`, `macd_hist`, `atr_14`, `bb_upper`, `bb_lower`,
`bb_width`, `vwap`, `obv`, `dist_sma200_pct`, `acima_vwap`.

O Schema v2 adiciona: `atr_10`, `atr_60`, `vol_media_20`, `vol_media_60`,
`maxima_52s`, `minima_52s`, `maxima_3a`, `minima_3a`, `parametros_ver`.

**Decisão:** manter tudo da v1 (não remover nada) e adicionar os campos
do Schema v2 que estiverem ausentes:

```sql
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS atr_10 REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS atr_60 REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS vol_media_20 REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS vol_media_60 REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS maxima_52s REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS minima_52s REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS maxima_3a REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS minima_3a REAL;
ALTER TABLE indicadores_compartilhados ADD COLUMN IF NOT EXISTS parametros_ver TEXT DEFAULT 'v1';
```

Atualizar `calcular_indicadores` no scheduler para calcular e persistir
os novos campos.

---

### 3.3 Tabelas existentes na v1 com nome diferente no Schema v2

| Nome na Spec v1 | Nome no Schema v2 | Ação |
|---|---|---|
| `macro_brasil` | `CICLO_LOCAL_BRASIL` (Tabela 5) | Manter nome v1 no SQLite — diferença é apenas de nomenclatura conceitual |
| `macro_global` | `CICLO_GLOBAL` (Tabela 4) | Idem |
| `focus_bcb_historico` | `FOCUS_BCB` (Tabela 13) | Idem |
| `scores_historico` | `SCORES_CAUSA` (Tabela 8) | A v1 tem `scores_historico` simplificado. O Schema v2 tem `scores_causa` com muitos campos novos. **Criar `scores_causa` como tabela nova** — não renomear nem alterar `scores_historico` |
| `google_trends` | `GOOGLE_TRENDS` (Tabela 16) | Adicionar campos: `ticker_relacionado`, `setor_relacionado`, `variacao_vs_media`, `tipo` |
| `abpo_papelao` | parte de `DADOS_SETORIAIS_BR` (Tabela 14) | Manter `abpo_papelao` separada — pipeline próprio em andamento |

---

### 3.4 Tabelas novas do Schema v2 sem coletor na v1

#### `fluxo_investidores` (Tabela 6) → `macro.db`
```sql
CREATE TABLE IF NOT EXISTS fluxo_investidores (
    data                    DATE NOT NULL,
    fluxo_estrangeiro       REAL,
    fluxo_local_inst        REAL,
    fluxo_pf                REAL,
    saldo_liquido           REAL,
    tesouro_direto_liquido  REAL,
    fonte                   TEXT,
    data_coleta             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (data)
);
```
**Coletor:** stub — retorna 0 e loga aviso. Fonte B3 IR não tem API pública
estruturada. Pipeline manual por enquanto.

#### `dados_setoriais_br` (Tabela 14) → `alternativo.db`
```sql
CREATE TABLE IF NOT EXISTS dados_setoriais_br (
    data_referencia     DATE NOT NULL,
    indicador           TEXT NOT NULL,
    valor               REAL,
    variacao_mensal     REAL,
    variacao_anual      REAL,
    setor_primario      TEXT,
    fonte               TEXT NOT NULL,
    defasagem_dias      INTEGER,
    data_publicacao     DATE,
    data_coleta         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (data_referencia, indicador, fonte)
);
```
**Coletor:** expandir `alternativo.py` para incluir:
- IBGE SIDRA Tabela 8889: Produção Física Industrial — Índices Especiais
  de Embalagens. **Substitui ABPO definitivamente** — confirmado que ABPO
  e ABRE derivam seus dados desta tabela. Séries a coletar:
  - `3`   → Total de Embalagens
  - `3.4` → Embalagens de papel e papelão ← proxy principal de atividade
  - `3.5` → Embalagens de material plástico
  Variável: PIMPF - Número-índice (2022=100)
  Série histórica: janeiro 2012 em diante
  URL: `https://servicodados.ibge.gov.br/api/v3/agregados/8889/periodos/all/variaveis/all`
  Insere em `dados_setoriais_br` com `fonte='IBGE_SIDRA_8889'`
- IBGE SIDRA: PMC (comércio), PMS (serviços), PIM (produção industrial)
  via mesma API SIDRA — agregados distintos
- MDIC balança comercial via API dados.gov.br
- ANEEL consumo industrial (já existe em `aneel_energia` na v1 —
  migrar para `dados_setoriais_br` ou manter ambas)

#### `commodities_setoriais` (Tabela 15) → `macro.db`
```sql
CREATE TABLE IF NOT EXISTS commodities_setoriais (
    data                DATE NOT NULL,
    minerio_ferro_usd   REAL,
    niquel_lme          REAL,
    aluminio_lme        REAL,
    litio_spot          REAL,
    celulose_foex       REAL,
    milho_cbot          REAL,
    soja_cbot           REAL,
    boi_gordo_b3        REAL,
    acucar_nybot        REAL,
    cafe_nybot          REAL,
    fonte               TEXT,
    data_coleta         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (data)
);
```
**Coletor:** expandir `macro_global.py` com tickers yfinance:
`TIO=F` (minério), `HG=F` (cobre já existe), `LNGG.L` (níquel),
`ALI=F` (alumínio), `ZS=F` (soja), `ZC=F` (milho),
`GF=F` (boi gordo), `SB=F` (açúcar), `KC=F` (café).
Celulose FOEX e lítio: stub documentado (sem API gratuita disponível).

---

## 4. NOVOS COLETORES A IMPLEMENTAR

### 4.1 `collectors/polymarket.py`
```python
def coletar(tickers: list[str] | None = None) -> int:
    """
    Coleta mercados de predição do Polymarket relevantes para B3.
    API: https://gamma-api.polymarket.com/markets
    Filtros: categorias copom, fed, politica_brasil, recessao_global, commodity
    Mínimo de liquidez: USD 10.000 (filtrar ruído)
    Frequência: diária (adicionar ao job_diario)
    """
```

### 4.2 `collectors/alternativo.py` — expansão

Adicionar às funções existentes:

```python
def coletar_ibge_sidra_embalagens() -> int:
    """
    Coleta Tabela 8889 do IBGE SIDRA — Produção Física Industrial,
    Índices Especiais de Embalagens (PIM-PF).
    Substitui pipeline ABPO — dado primário confirmado.

    Séries coletadas:
      '3'   → Total de Embalagens
      '3.4' → Embalagens de papel e papelão
      '3.5' → Embalagens de material plástico

    URL: https://servicodados.ibge.gov.br/api/v3/agregados/8889/
         periodos/all/variaveis/all
    Insere em dados_setoriais_br com fonte='IBGE_SIDRA_8889'.
    Histórico disponível: janeiro 2012 em diante.
    Frequência de chamada: mensal (job_mensal).
    """

def coletar_ibge_sidra_atividade() -> int:
    """
    Coleta PMC, PMS e PIM via API SIDRA (agregados distintos do 8889).
    Insere em dados_setoriais_br com fonte='IBGE_SIDRA'.
    """

def coletar_mdic_balanca() -> int:
    """
    Coleta balança comercial via API MDIC/dados.gov.br.
    Insere em dados_setoriais_br com fonte='MDIC'.
    """
```

---

## 5. SCHEDULER — ATUALIZAÇÕES

Adicionar ao `scheduler.py` existente:

```python
# Diário — junto com macro_global (19h30)
scheduler.add_job(
    polymarket.coletar,
    CronTrigger(hour=19, minute=45, timezone="America/Sao_Paulo"),
    id='polymarket_diario',
    replace_existing=True
)

# Mensal — primeiro dia do mês às 08h
scheduler.add_job(
    alternativo.coletar_ibge_sidra_embalagens,
    CronTrigger(day=1, hour=8, timezone="America/Sao_Paulo"),
    id='ibge_embalagens_mensal',
    replace_existing=True
)
scheduler.add_job(
    alternativo.coletar_ibge_sidra_atividade,
    CronTrigger(day=1, hour=8, minute=15, timezone="America/Sao_Paulo"),
    id='ibge_atividade_mensal',
    replace_existing=True
)
```

---

## 6. `utils.py` — FUNÇÕES ADICIONAIS

Adicionar ao `utils.py` existente (não substituir funções existentes):

```python
def calcular_temperatura(polaridade, intensidade, volume_atual, volume_tipico) -> float:
    ...  # ver Seção 3.2

def calcular_temperatura_zscore(temperatura, media_historica, desvpad_historico) -> float:
    ...  # ver Seção 3.2

def alter_table_if_column_missing(conn, tabela: str, coluna: str, tipo: str) -> None:
    """
    Adiciona coluna a tabela existente apenas se não existir.
    Idempotente — seguro chamar múltiplas vezes.
    """
    cursor = conn.execute(f"PRAGMA table_info({tabela})")
    colunas_existentes = [row[1] for row in cursor.fetchall()]
    if coluna not in colunas_existentes:
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        conn.commit()
```

---

## 7. `requirements.txt` — ADIÇÕES

Verificar se já instalados. Adicionar se ausentes:

```
# já na v1 — verificar
apscheduler>=3.10.0
yfinance>=0.2.36
requests>=2.31.0
pandas>=2.0.0
pandas-ta>=0.3.14b
feedparser>=6.0.10
pytrends>=4.9.2
fredapi>=0.5.0
google-generativeai>=0.8.0

# novos na v3
python-dotenv>=1.0.0
```

---

## 8. DEFINIÇÃO DE PRONTO — v3

### 8.1 Herdado da v1 — verificar estado antes de marcar

- [ ] `data/raw/` com quatro arquivos `.db`
- [ ] `schema.py` — `create_all_tables()` cria todas as tabelas
- [ ] `connection.py` — `get_connection(domain)` para quatro domínios
- [ ] `collectors/preco_volume.py` — OHLCV funcional
- [ ] `collectors/macro_brasil.py` — Selic, IPCA, câmbio, Focus BCB
- [ ] `collectors/macro_global.py` — DXY, S&P500, WTI, BDI, soja, cobre
- [ ] `collectors/alternativo.py` — Google Trends funcional
- [ ] `collectors/noticias.py` — RSS + Gemini classifica e persiste score
- [ ] `scheduler.py` — roda autônomo sem VS Code
- [ ] `calcular_indicadores` — SMA, EMA, RSI, MACD, ATR, VWAP, OBV
- [ ] Append-only verificado

### 8.2 Novo na v3 — implementar apenas o ausente

**Tabelas novas:**
- [ ] `retornos_historicos` criada e populada pelo `calcular_indicadores`
- [ ] `taxa_conversao` criada vazia
- [ ] `scores_causa` criada vazia
- [ ] `documentos_qualitativos` criada vazia
- [ ] `polymarket_eventos` criada e coletor funcional
- [ ] `intraday_slot` criada vazia (sem coletor)
- [ ] `fluxo_investidores` criada com stub de coletor
- [ ] `dados_setoriais_br` criada com IBGE SIDRA funcional
- [ ] `commodities_setoriais` criada com yfinance funcional

**Campos adicionais em tabelas existentes:**
- [ ] `portfolio_estado` com campos do Schema v2
- [ ] `temperatura_noticias` com fórmula completa de temperatura
- [ ] `indicadores_compartilhados` com ATR 10/60, vol_media_60,
      maxima/minima 52s e 3a, parametros_ver
- [ ] `google_trends` com campos: ticker_relacionado, setor_relacionado,
      variacao_vs_media, tipo

**Novos coletores:**
- [ ] `collectors/polymarket.py` funcional — filtra por categoria e liquidez
- [ ] `collectors/alternativo.py` expandido com IBGE SIDRA 8889
      (embalagens) e IBGE SIDRA atividade (PMC, PMS, PIM) e MDIC

**Scheduler:**
- [ ] Job polymarket adicionado ao job_diario (19h45)
- [ ] Job `ibge_embalagens_mensal` adicionado (dia 1, 08h00)
- [ ] Job `ibge_atividade_mensal` adicionado (dia 1, 08h15)

**Pendência encerrada:**
- [x] ABPO pipeline de PDF — **cancelado**. Dado primário é IBGE SIDRA
      Tabela 8889, confirmado como fonte original que ABPO e ABRE utilizam.
      Sem perda de informação — mesma série, acesso direto e estruturado.

**Utils:**
- [ ] `calcular_temperatura()` implementada
- [ ] `calcular_temperatura_zscore()` implementada
- [ ] `alter_table_if_column_missing()` implementada

---

## 9. ORDEM DE EXECUÇÃO RECOMENDADA

1. **Inspecionar** estado atual da v1 — produzir relatório de estado
2. **`schema.py`** — adicionar tabelas novas e `alter_table` para campos novos
3. **`utils.py`** — adicionar funções novas sem tocar nas existentes
4. **`calcular_indicadores`** — adicionar cálculos dos campos novos
5. **`collectors/polymarket.py`** — coletor novo
6. **`collectors/alternativo.py`** — expandir com IBGE SIDRA e MDIC
7. **`scheduler.py`** — adicionar jobs novos
8. **Testes** — ao menos um teste por módulo novo

---

*Especificação v3.1 — reconcilia Spec v1 em execução com Schema v2*
*Princípio: nunca sobrescrever código funcional existente*
*Tabelas de slot futuro (taxa_conversao, scores_causa, intraday_slot):*
*criadas vazias desde o início — estruturadas mas sem coletor*
*v3.1: ABPO substituída por IBGE SIDRA Tabela 8889 — Pendência 6 encerrada*
